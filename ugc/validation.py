from re import *
from telegram import Update


def is_mail(update: Update):
    if update.message.text is None:
        return None
    else:
        mail = update.message.text
        pattern = compile(r"(^|\s)[-a-z0-9_.]+@([-a-z0-9]+\.)+[a-z]{2,6}(\s|$)")
        is_valid = pattern.match(mail)
        if is_valid:
            return mail
        else:
            return None


# def is_phone_number(phone):
#     pattern = compile(r"^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$")
#     is_valid = pattern.match(phone)
#     if is_valid:
#         return phone
#     else:
#         return None


def is_phone_number(update: Update):
    if update.message.text is not None:
        phone = update.message.text
        pattern = compile(r"^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$")
        is_valid = pattern.match(phone)
        if is_valid:
            return phone
        else:
            return None
    elif update.message.contact is not None:
        phone = update.message.contact.phone_number
        return phone
    else:
        return None


def is_firstorlast_name(update: Update):
    if update.message.text is None:
        return None
    else:
        name = update.message.text
        pattern = compile(r"^([А-Я]{1}[а-яё]{1,23}|[A-Z]{1}[a-z]{1,23})$")
        is_valid = pattern.match(name)
        if is_valid:
            return name
        else:
            return None
