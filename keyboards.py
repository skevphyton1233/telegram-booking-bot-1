from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

SERVICES = [
    "💆 Массаж",
    "💅 Маникюр",
    "✂️ Стрижка",
    "🧖 SPA-процедура",
]


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Оставить заявку", callback_data="menu_request")
    builder.button(text="💰 Услуги и цены", callback_data="menu_services")
    builder.button(text="📍 Контакты", callback_data="menu_contacts")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в меню", callback_data="menu_back")
    return builder.as_markup()


def services_choice_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, service in enumerate(SERVICES):
        builder.button(text=service, callback_data=f"service_{index}")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel")
    return builder.as_markup()


def phone_request_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Поделиться контактом", request_contact=True)
    builder.button(text="❌ Отмена")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm")
    builder.button(text="🔄 Заполнить заново", callback_data="restart")
    builder.adjust(1)
    return builder.as_markup()
