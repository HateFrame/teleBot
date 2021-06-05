from django.core.management.base import BaseCommand
from teleBot.settings import TOKEN
from telegram import (
    Bot,
    Update,
    ReplyKeyboardRemove,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ParseMode,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext,
    Filters,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Updater
)
from telegram.utils.request import Request
from ugc import validation, bot_functions

from ugc.models import Profile, Message, CharacterData

FIRST_NAME = 'Имя'
LAST_NAME = 'Фамилия'
PHONE_NUMBER = 'Номер телефона'
EMAIL = 'Почта'
CALLBACK_WAITING = 'Ожидание ответа'


def log_errors(f):

    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f'ErrorFFFF: {e}'
            print(error_message)
            raise e
    return inner


def do_start(update: Update, context: CallbackContext):
    bot_functions.get_profile(update)
    text = "Привет! Нажмите /help для отображения команд."
    update.message.reply_text(text)


@log_errors
def do_dialogflow(update: Update, context: CallbackContext):
    text = update.message.text
    p = bot_functions.get_profile(update)
    Message(
        profile=p,
        text=text,
    ).save()
    if bot_functions.check_form_state(update):
        return

    reply = bot_functions.detect_intent_texts(text)
    update.message.reply_text(reply)


@log_errors
def do_help(update: Update, context: CallbackContext):
    if bot_functions.check_form_state(update):
        return
    text = "Command List:\n" \
           "/help - список команд\n" \
           "/form - заполнить анкету\n" \
           "/delete_form - удалить анкету\n" \
           "/edit_form - изменить анкету\n" \
           "/show_form - посмотреть анкету\n" \
           "/shop - открыть магазин\n" \
           "/show_cart - показать корзину"
    update.message.reply_text(
        text=text,
    )


def do_display_shop(update: Update, context: CallbackContext):
    if bot_functions.check_form_state(update):
        return
    text = "Выберете нужную категорию."
    update.message.reply_text(text=text, reply_markup=bot_functions.get_keyboardmarkup_shop())


def do_show_product(update: Update, context: CallbackContext):
    product_id = update.message.text.replace('/show', '')
    text = bot_functions.get_product(product_id)
    update.message.reply_text(text=text)


def do_callbackhandler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    text = bot_functions.get_menu(data)
    context.bot.sendMessage(chat_id=chat_id, text=text)


def do_add_to_cart(update: Update, context: CallbackContext):
    product_id = update.message.text.replace('/add', '')
    text = bot_functions.add_to_cart(product_id, update)
    update.message.reply_text(text=text)


def do_show_cart(update: Update, context: CallbackContext):
    text = bot_functions.show_cart(update)
    update.message.reply_text(text=text)


def do_clear_cart(update: Update, context: CallbackContext):
    text = bot_functions.clear_cart(update)
    update.message.reply_text(text=text)


def do_accept_order(update: Update, context: CallbackContext):
    text = bot_functions.accept_order(update)
    update.message.reply_text(text)


@log_errors
def do_form(update: Update, context: CallbackContext):
    if bot_functions.check_form_state(update):
        return
    Profile.objects.filter(external_id=update.message.chat_id).update(statement=True)

    update.message.reply_text(
        "Для отмены нажмите или введите /cancel\n"
        "Введите свое имя:",
        reply_markup=ReplyKeyboardRemove()
    )
    return FIRST_NAME


@log_errors
def first_name_handler(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data[FIRST_NAME] = validation.is_firstorlast_name(update)
    if user_data[FIRST_NAME] is None:
        update.message.reply_text("Ведите корректное имя. \nИли отмените заполнение командой /cancel")
        return FIRST_NAME
    update.message.reply_text(
        "Введите фамилию:"
    )
    return LAST_NAME


@log_errors
def last_name_handler(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data[LAST_NAME] = validation.is_firstorlast_name(update)
    if user_data[LAST_NAME] is None:
        update.message.reply_text(
            text="Ведите корректную фамилию. \nИли отмените заполнение командой /cancel"
        )
        return LAST_NAME
    button_phone = [
        [
            KeyboardButton(
                text="Отправить номер телефона",
                request_contact=True
            )
        ]
    ]
    keyboard = ReplyKeyboardMarkup(button_phone, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "Введите Номер телефона", reply_markup=keyboard
    )
    return PHONE_NUMBER


@log_errors
def phone_handler(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data[PHONE_NUMBER] = validation.is_phone_number(update)
    if user_data[PHONE_NUMBER] is None:
        update.message.reply_text(
            text="Введите корректный номер телефона. \nИли отмените заполнение командой /cancel"
        )
        return PHONE_NUMBER
    update.message.reply_text(
        text="Введите электронную почту:"
    )
    return EMAIL


@log_errors
def email_handler(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data[EMAIL] = validation.is_mail(update)
    if user_data[EMAIL] is None:
        update.message.reply_text(
            text="Введите корректную почту. \nИли отмените заполнение командой /cancel"
        )
        return EMAIL

    p = bot_functions.get_profile(update)

    bot_functions.put_form_data(p, user_data)
    Profile.objects.filter(external_id=update.message.chat_id).update(statement=False)
    update.message.reply_text('''
    *Вы зарегистрированы!*
    \nВаши данные: 
    {}'''.format(bot_functions.facts_to_str(user_data)), parse_mode='Markdown')
    return ConversationHandler.END


@log_errors
def do_cancel(update: Update, _):
    Profile.objects.filter(external_id=update.message.chat_id).update(statement=False)
    update.message.reply_text(
        "Отмена заполнения.\n"
        "Для повторного заполнения введите /form"
    )
    return ConversationHandler.END


@log_errors
def do_delete_form(update: Update, _):
    if bot_functions.check_form_state(update):
        return
    p = bot_functions.get_profile(update)
    CharacterData.objects.filter(profile=p).delete()
    update.message.reply_text(
        text="Ваша анкета успешно удалена."
    )


@log_errors
def do_edit_form(update: Update, _):
    if bot_functions.check_form_state(update):
        return
    if not bot_functions.user_form_exists(update):
        return
    form = bot_functions.get_form_values(update)
    update.message.reply_text(
        text='''
        <b>Какое поле вы хотите отредактировать?</b>
        \nВаши данные:
        {}'''.format(bot_functions.facts_to_str(form)), parse_mode=ParseMode.HTML,
        reply_markup=bot_functions.get_keyboardmarkup_form()
    )
    return CALLBACK_WAITING


def keyboard_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id

    query.edit_message_text("Редактирование поля \"" + data + "\".\n\nДля отмены нажмите или введите /decline_edit\n")
    if data == PHONE_NUMBER:
        button_phone = [
            [
                KeyboardButton(
                    text="Отправить номер телефона",
                    request_contact=True
                )
            ]
        ]
        keyboard = ReplyKeyboardMarkup(button_phone, resize_keyboard=True, one_time_keyboard=True)
        context.bot.sendMessage(
            chat_id=chat_id,
            text="Введите Номер телефона",
            reply_markup=keyboard
        )
    elif data == FIRST_NAME:
        context.bot.sendMessage(
            chat_id=chat_id,
            text="Введите свое имя:"
        )
    elif data == LAST_NAME:
        context.bot.sendMessage(
            chat_id=chat_id,
            text="Введите свою фамилию:"
        )
    elif data == EMAIL:
        context.bot.sendMessage(
            chat_id=chat_id,
            text="Введите электронную почту:"
        )
    return data


# ------------------------------------------- Edit handlers (some duplicate for validation)


@log_errors
def first_name_edit_handler(update: Update, _):
    name = validation.is_firstorlast_name(update)
    if name is None:
        update.message.reply_text(
            text="Ведите корректное имя. \nИли отмените редактирование командой /decline_edit")
        return FIRST_NAME

    bot_functions.edit_form_field(update, FIRST_NAME, name)

    return ConversationHandler.END


@log_errors
def last_name_edit_handler(update: Update, _):
    last_name = validation.is_firstorlast_name(update)
    if last_name is None:
        update.message.reply_text(
            text="Ведите корректную фамилию. \nИли отмените редактирование командой /decline_edit")
        return LAST_NAME

    bot_functions.edit_form_field(update, LAST_NAME, last_name)

    return ConversationHandler.END


@log_errors
def phone_edit_handler(update: Update, _):
    phone_number = validation.is_phone_number(update)
    if phone_number is None:
        update.message.reply_text(
            text="Введите корректный номер телефона. \nИли отмените редактирование командой /decline_edit")
        return PHONE_NUMBER

    bot_functions.edit_form_field(update, PHONE_NUMBER, phone_number)

    return ConversationHandler.END


@log_errors
def email_edit_handler(update: Update, _):
    email = validation.is_mail(update)
    if email is None:
        update.message.reply_text(
            text="Введите корректную почту. \nИли отмените редактирование командой /decline_edit")
        return EMAIL

    bot_functions.edit_form_field(update, EMAIL, email)

    return ConversationHandler.END


def do_send_form(update: Update, _):
    if bot_functions.check_form_state(update):
        return
    if not bot_functions.user_form_exists(update):
        return
    form = bot_functions.get_form_values(update)
    update.message.reply_text(
        text='''
        <b>Ваши данные:</b>
        {}'''.format(bot_functions.facts_to_str(form)), parse_mode=ParseMode.HTML
    )

# -------------------------------------------


def do_decline_edit(update: Update, _):
    update.message.reply_text(
        text="Отмена редактирования.\nДля вызова списка команд введите /help"
    )
    return ConversationHandler.END


class Command(BaseCommand):
    help = 'Telegram bot'

    def handle(self, *args, **options):
        request = Request(
            connect_timeout=0.5,
            read_timeout=1.0,
        )
        bot = Bot(
            request=request,
            token=TOKEN,
        )
        print(bot.getMe())

        updater = Updater(
            bot=bot,
            use_context=True,
        )

        # form handler for get data from user
        form_handler = ConversationHandler(
            entry_points=[
                CommandHandler("form", do_form),
            ],
            states={
                FIRST_NAME: [
                    MessageHandler(Filters.all & ~Filters.command, first_name_handler, pass_user_data=True),
                ],
                LAST_NAME: [
                    MessageHandler(Filters.all & ~Filters.command, last_name_handler, pass_user_data=True),
                ],
                PHONE_NUMBER: [
                    MessageHandler(Filters.all & ~Filters.command or Filters.contact, phone_handler, pass_user_data=True),
                ],
                EMAIL: [
                    MessageHandler(Filters.all & ~Filters.command, email_handler, pass_user_data=True),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", do_cancel),
            ],
        )

        edit_form_handler = ConversationHandler(
            entry_points=[
                CommandHandler("edit_form", do_edit_form),
            ],
            states={
                CALLBACK_WAITING: [
                    CallbackQueryHandler(callback=keyboard_callback_handler, pass_user_data=True),
                    MessageHandler(Filters.all, do_decline_edit)
                ],
                FIRST_NAME: [
                    MessageHandler(Filters.all & ~Filters.command, first_name_edit_handler, pass_user_data=True),
                ],
                LAST_NAME: [
                    MessageHandler(Filters.all & ~Filters.command, last_name_edit_handler, pass_user_data=True),
                ],
                PHONE_NUMBER: [
                    MessageHandler(Filters.all & ~Filters.command or Filters.contact, phone_edit_handler,
                                   pass_user_data=True),
                ],
                EMAIL: [
                    MessageHandler(Filters.all & ~Filters.command, email_edit_handler, pass_user_data=True),
                ]
            },
            fallbacks=[
                CommandHandler("decline_edit", do_decline_edit)
            ]
        )

        start_handler = CommandHandler("start", do_start)
        callback_handler = CallbackQueryHandler(callback=do_callbackhandler)
        help_handler = CommandHandler("help", do_help)
        delete_form_handler = CommandHandler("delete_form", do_delete_form)
        send_form_handler = CommandHandler("show_form", do_send_form)
        send_shop = CommandHandler("shop", do_display_shop)
        show_product_handler = MessageHandler(Filters.regex(r'/show[0-9]{1,9}'), do_show_product)
        add_to_cart_handler = MessageHandler(Filters.regex(r'/add[0-9]{1,9}'), do_add_to_cart)
        show_cart_handler = CommandHandler("show_cart", do_show_cart)
        clear_cart_handler = CommandHandler("clear_cart", do_clear_cart)
        accept_order_handler = CommandHandler("accept_order", do_accept_order)

        message_handler = MessageHandler(Filters.text, do_dialogflow)
        updater.dispatcher.add_handler(start_handler)
        updater.dispatcher.add_handler(help_handler)
        updater.dispatcher.add_handler(form_handler)
        updater.dispatcher.add_handler(delete_form_handler)
        updater.dispatcher.add_handler(edit_form_handler)
        updater.dispatcher.add_handler(send_form_handler)
        updater.dispatcher.add_handler(send_shop)
        updater.dispatcher.add_handler(callback_handler)
        updater.dispatcher.add_handler(show_product_handler)
        updater.dispatcher.add_handler(add_to_cart_handler)
        updater.dispatcher.add_handler(show_cart_handler)
        updater.dispatcher.add_handler(clear_cart_handler)
        updater.dispatcher.add_handler(accept_order_handler)

        updater.dispatcher.add_handler(message_handler)

        updater.start_polling()
        updater.idle()
        bot_functions.update_all_profiles()
