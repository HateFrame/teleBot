from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from ugc.models import Profile, CharacterData

FIRST_NAME = 'Имя'
LAST_NAME = 'Фамилия'
PHONE_NUMBER = 'Номер телефона'
EMAIL = 'Почта'


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
        facts.append('<b>{}</b>  -  {}'.format(key, value))
    return "\n".join(facts).join(['\n', '\n'])


def get_profile(update: Update):
    p, _ = Profile.objects.get_or_create(
        external_id=update.message.chat_id,
        defaults={
            'name': update.message.from_user.username,
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
