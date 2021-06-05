from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from ugc.models import Profile, CharacterData
from shop.models import Product, Category, Cart, CartItem, Order, OrderElement
from google.cloud import dialogflow
from teleBot.settings import PROJECT_ID, SESSION_ID, LANGUGE_CODE_DF
from google.cloud import dialogflow_v2beta1
import os

FIRST_NAME = 'Имя'
LAST_NAME = 'Фамилия'
PHONE_NUMBER = 'Номер телефона'
EMAIL = 'Почта'


# def detect_intent_texts(text_to_be_analyzed):
#     import os
#     import dialogflow
#     from google.api_core.exceptions import InvalidArgument
#
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/teleBot/telebot-ntov-a6ef8faa6380.json"
#     DIALOGFLOW_PROJECT_ID = 'telebot-ntov'
#     DIALOGFLOW_LANGUAGE_CODE = 'ru-RU'
#     SESSION_ID = 'me'
#
#     session_client = dialogflow.SessionsClient()
#     session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
#
#     text_input = dialogflow.types.TextInput(text=text_to_be_analyzed, language_code=DIALOGFLOW_LANGUAGE_CODE)
#     query_input = dialogflow.types.QueryInput(text=text_input)
#     try:
#         response = session_client.detect_intent(session=session, query_input=query_input)
#     except InvalidArgument:
#         raise
#
#     print("Query text:", response.query_result.query_text)
#     print("Detected intent:", response.query_result.intent.display_name)
#     print("Detected intent confidence:", response.query_result.intent_detection_confidence)
#     print("Fulfillment text:", response.query_result.fulfillment_text)


def dialog_flow_connection():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/teleBot/telebot-ntov-a6ef8faa6380.json"
    session_client = dialogflow_v2beta1.SessionsClient()

    session = session_client.session_path(PROJECT_ID, SESSION_ID)
    print("Session path: {}\n".format(session))
    return session, session_client


def detect_intent_texts(text):
    """Returns the result of detect intent with texts as inputs.

    Using the same `session_id` between requests allows continuation
    of the conversation."""

    session, session_client = dialog_flow_connection()
    text_input = dialogflow_v2beta1.types.TextInput(text=text, language_code=LANGUGE_CODE_DF)

    query_input = dialogflow_v2beta1.types.QueryInput(text=text_input)
    request = dialogflow_v2beta1.types.DetectIntentRequest(session=session, query_input=query_input)
    response = session_client.detect_intent(
        request=request
    )

    print("=" * 20)
    print("Query text: {}".format(response.query_result.query_text))
    print(
        "Detected intent: {} (confidence: {})\n".format(
            response.query_result.intent.display_name,
            response.query_result.intent_detection_confidence,
        )
    )
    print("Fulfillment text: {}\n".format(response.query_result.fulfillment_text))
    return response.query_result.fulfillment_text


def check_form_state(update: Update):
    p = Profile.objects.get(external_id=update.message.chat_id)
    if p.statement:
        update.message.reply_text(
            text="Вы находитесь в процессе заполнения анкеты. Для отмены введите /cancel"
        )
        return True
    else:
        return False


def facts_to_str(user_data: dict) -> str:
    facts = []
    for key, value in user_data.items():
        facts.append('{}  -  {}'.format(key, value))
    return "\n".join(facts).join(['\n', '\n'])


def get_profile(update: Update):
    name = update.message.from_user.username
    if not name:
        name = "Unnamed"
    p, _ = Profile.objects.get_or_create(
        external_id=update.message.chat_id,
        defaults={
            'name': name,
        })
    return p


def put_form_data(p, user_data):
    CharacterData.objects.update_or_create(
        profile=p,
        defaults={
            'first_name': user_data[FIRST_NAME],
            'last_name': user_data[LAST_NAME],
            'phone_number': user_data[PHONE_NUMBER],
            'email': user_data[EMAIL],
        }
    )


def edit_form_field(update: Update, type_field, data):
    p = get_profile(update)
    cd = CharacterData.objects.get(profile=p)
    if type_field == FIRST_NAME:
        cd.first_name = data
    elif type_field == LAST_NAME:
        cd.last_name = data
    elif type_field == EMAIL:
        cd.email = data
    elif type_field == PHONE_NUMBER:
        cd.phone_number = data
    else:
        return False
    cd.save()
    return True


def update_all_profiles():
    Profile.objects.filter(statement=True).update(statement=False)


def user_form_exists(update: Update):
    p = get_profile(update)
    if CharacterData.objects.filter(profile=p).exists():
        return True
    else:
        update.message.reply_text("Вы еще не заполнили анкету, либо она удалена.")
        return False


def get_keyboardmarkup_form():
    keyboard = [
        [
            InlineKeyboardButton(FIRST_NAME, callback_data=FIRST_NAME),
            InlineKeyboardButton(LAST_NAME, callback_data=LAST_NAME)
        ],
        [
            InlineKeyboardButton(PHONE_NUMBER, callback_data=PHONE_NUMBER),
            InlineKeyboardButton(EMAIL, callback_data=EMAIL)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_form_values(update):
    if user_form_exists(update):
        p = get_profile(update)
        cd = CharacterData.objects.get(profile=p)
        first_name = getattr(cd, 'first_name')
        last_name = getattr(cd, 'last_name')
        phone_number = getattr(cd, 'phone_number')
        email = getattr(cd, 'email')
        form = {
            FIRST_NAME: first_name,
            LAST_NAME: last_name,
            PHONE_NUMBER: phone_number,
            EMAIL: email
        }
        return form
    else:
        return None


def get_keyboardmarkup_shop():
    keyboard = [
        [
            InlineKeyboardButton("Роллы", callback_data="Роллы"),
            InlineKeyboardButton("Суши", callback_data="Суши")
        ],
        [
            InlineKeyboardButton("Сашими", callback_data="Сашими"),
            InlineKeyboardButton("Супы", callback_data="Супы")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def category_exists(name):
    if Category.objects.filter(name=name).exists():
        return True
    else:
        return False


def get_menu(data):
    if Category.objects.filter(name=data).exists():
        cat = Category.objects.get(name=data)
        product_list = Product.objects.filter(category=cat)
        text = "Все товары категории " + data + ":\n\n"
        for product_element in product_list:
            text += product_element.name + "  -  открыть /show" + str(product_element.id) + "\n"
        return text
    else:
        return "Ничего не найдено."


def get_product(product_id):
    if Product.objects.filter(id=product_id).exists():
        product = Product.objects.get(id=product_id)
        text = product.name + "\nОписание: " + product.description + "\nЦена: " + str(product.price)
        text += "\n\nДобавить в корзину - /add" + str(product.id)
        return text + "\n\nВернуться к категориям - /shop"
    else:
        return "Ошибка, такого товара не существует."


def add_to_cart(product_id, update):
    cart, _ = Cart.objects.get_or_create(user_id=get_profile(update))
    if Product.objects.filter(id=product_id).exists():
        product = Product.objects.get(id=product_id)
        if CartItem.objects.filter(cart=cart, product=product).exists():
            ci = CartItem.objects.get(cart=cart, product=product)
            ci.quantity += 1
            ci.save()
        else:
            CartItem.objects.create(cart=cart, product=product, price=product.price)
        text = product.name + " добавлен в корзину.\n\nПодтвердить заказ - /accept_order"
    else:
        return "Ошибка, такого товара не существует."
    return text


def show_cart(update):
    cart, _ = Cart.objects.get_or_create(user_id=get_profile(update))
    items = cart.cartitem_set.all()
    counter = 0
    text = "Ваша корзина:\n"
    for element in items:
        counter += 1
        text += str(counter) + ". "
        text += Product.objects.get(id=element.product_id).name
        text += "| Количество: " + str(element.quantity) + "\n"
    if counter == 0:
        text += "Ничего нет."
    return text + "\nОчистить корзину - /clear_cart\n\nПодтвердить заказ - /accept_order"


def clear_cart(update):
    cart, _ = Cart.objects.get_or_create(user_id=get_profile(update))
    CartItem.objects.filter(cart=cart).delete()
    return "Корзина очищена."


def accept_order(update):
    p = get_profile(update)
    order = Order.objects.create(user_id=p)
    cart = Cart.objects.get(user_id=p)
    items = cart.cartitem_set.all()
    for element in items:
        OrderElement.objects.create(
            order=order,
            product=element.product,
            quantity=element.quantity,
            price=element.price
        )
    clear_cart(update)
    return "Заказ успешно сформирован.\nОплатить и забрать его можно по адресу..."
