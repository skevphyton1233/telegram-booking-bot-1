import logging
from datetime import datetime
from html import escape as esc

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from config import ADMIN_ID
from database import get_last_requests, save_request
from keyboards import (
    SERVICES,
    back_to_menu_kb,
    cancel_kb,
    confirm_kb,
    main_menu_kb,
    phone_request_kb,
    services_choice_kb,
)

logger = logging.getLogger(__name__)
router = Router()


class RequestForm(StatesGroup):
    service = State()
    name = State()
    phone = State()
    datetime_comment = State()


WELCOME_TEXT = (
    "👋 Здравствуйте! Это бот студии <b>Beauty Space</b>.\n\n"
    "Здесь вы можете оставить заявку на услугу, узнать цены и наши контакты.\n"
    "Выберите нужный пункт в меню ниже 👇"
)

SERVICES_TEXT = (
    "💰 <b>Наши услуги и цены</b>\n\n"
    "💆 Массаж — от 1500 ₽\n"
    "💅 Маникюр — от 1200 ₽\n"
    "✂️ Стрижка — от 1000 ₽\n"
    "🧖 SPA-процедура — от 2500 ₽\n\n"
    "Точную стоимость уточнит администратор после обработки заявки."
)

CONTACTS_TEXT = (
    "📍 <b>Наши контакты</b>\n\n"
    "🏠 Адрес: г. Москва, ул. Примерная, д. 1\n"
    "📞 Телефон: +7 (999) 123-45-67\n"
    "🕐 Режим работы: ежедневно, 9:00–21:00\n"
    "🌐 Instagram: @beauty_space"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu_back")
async def cb_menu_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "menu_services")
async def cb_menu_services(callback: CallbackQuery):
    await callback.message.edit_text(SERVICES_TEXT, reply_markup=back_to_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "menu_contacts")
async def cb_menu_contacts(callback: CallbackQuery):
    await callback.message.edit_text(CONTACTS_TEXT, reply_markup=back_to_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "menu_request")
async def cb_menu_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RequestForm.service)
    await callback.message.edit_text(
        "Шаг 1 из 4. Выберите услугу:",
        reply_markup=services_choice_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    except TelegramBadRequest:
        await callback.message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
    await callback.answer("Заявка отменена")


@router.callback_query(RequestForm.service, F.data.startswith("service_"))
async def process_service(callback: CallbackQuery, state: FSMContext):
    try:
        index = int(callback.data.split("_")[1])
        service = SERVICES[index]
    except (ValueError, IndexError):
        await callback.answer("Пожалуйста, выберите услугу из списка.", show_alert=True)
        return

    await state.update_data(service=service)
    await state.set_state(RequestForm.name)
    await callback.message.edit_text(
        f"Услуга: <b>{service}</b>\n\nШаг 2 из 4. Как вас зовут?",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(RequestForm.name)
async def process_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not (2 <= len(name) <= 100):
        await message.answer(
            "Пожалуйста, введите корректное имя (от 2 до 100 символов).",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(name=name)
    await state.set_state(RequestForm.phone)
    await message.answer(
        f"Приятно познакомиться, {esc(name)}!\n\n"
        "Шаг 3 из 4. Отправьте номер телефона текстом или поделитесь контактом:",
        reply_markup=phone_request_kb(),
    )


@router.message(RequestForm.phone, F.text == "❌ Отмена")
async def cancel_from_phone_step(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Заявка отменена.", reply_markup=ReplyKeyboardRemove())
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(RequestForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await state.set_state(RequestForm.datetime_comment)
    await message.answer("Контакт получен ✅", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        "Шаг 4 из 4. Укажите удобную дату/время или добавьте комментарий к заявке:",
        reply_markup=cancel_kb(),
    )


@router.message(RequestForm.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not (10 <= len(digits) <= 15):
        await message.answer(
            "Похоже, номер указан некорректно. Введите номер телефона ещё раз "
            "или поделитесь контактом:",
            reply_markup=phone_request_kb(),
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(RequestForm.datetime_comment)
    await message.answer("Телефон получен ✅", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        "Шаг 4 из 4. Укажите удобную дату/время или добавьте комментарий к заявке:",
        reply_markup=cancel_kb(),
    )


@router.message(RequestForm.datetime_comment)
async def process_datetime_comment(message: Message, state: FSMContext):
    comment = (message.text or "").strip()
    if not comment:
        await message.answer(
            "Пожалуйста, напишите текстом удобное время или комментарий.",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(datetime_comment=comment)
    data = await state.get_data()

    summary = (
        "📋 <b>Проверьте вашу заявку:</b>\n\n"
        f"🔹 Услуга: {esc(data.get('service', '-'))}\n"
        f"🔹 Имя: {esc(data.get('name', '-'))}\n"
        f"🔹 Телефон: {esc(data.get('phone', '-'))}\n"
        f"🔹 Дата/комментарий: {esc(data.get('datetime_comment', '-'))}\n\n"
        "Всё верно?"
    )
    await message.answer(summary, reply_markup=confirm_kb())


@router.callback_query(RequestForm.datetime_comment, F.data == "restart")
async def restart_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RequestForm.service)
    await callback.message.edit_text(
        "Шаг 1 из 4. Выберите услугу:", reply_markup=services_choice_kb()
    )
    await callback.answer()


@router.callback_query(RequestForm.datetime_comment, F.data == "confirm")
async def confirm_request(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = callback.from_user

    try:
        await save_request(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            service=data.get("service", "-"),
            client_name=data.get("name", "-"),
            phone=data.get("phone", "-"),
            datetime_comment=data.get("datetime_comment", "-"),
        )
    except Exception:
        logger.exception("Ошибка при сохранении заявки в базу данных")
        await callback.message.edit_text(
            "😔 Произошла ошибка при сохранении заявки. Попробуйте, пожалуйста, позже."
        )
        await state.clear()
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(
        "✅ Ваша заявка принята! Мы свяжемся с вами в ближайшее время.\n\n"
        "Спасибо, что выбрали нас 💫",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()

    if user.username:
        profile_link = f'<a href="https://t.me/{user.username}">@{esc(user.username)}</a>'
    else:
        profile_link = f'<a href="tg://user?id={user.id}">профиль клиента</a>'

    admin_text = (
        "🆕 <b>Новая заявка!</b>\n\n"
        f"👤 Клиент: {esc(data.get('name', '-'))}\n"
        f"📞 Телефон: {esc(data.get('phone', '-'))}\n"
        f"💼 Услуга: {esc(data.get('service', '-'))}\n"
        f"🗓 Дата/комментарий: {esc(data.get('datetime_comment', '-'))}\n"
        f"🔗 Telegram: {profile_link}\n"
        f"🕐 Время заявки: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception:
        logger.exception("Не удалось отправить уведомление администратору")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        rows = await get_last_requests(10)
    except Exception:
        logger.exception("Ошибка при получении заявок из базы данных")
        await message.answer("😔 Не удалось получить список заявок.")
        return

    if not rows:
        await message.answer("Заявок пока нет.")
        return

    text_parts = ["📑 <b>Последние заявки:</b>\n"]
    for row in rows:
        username_part = f"@{esc(row['username'])}" if row["username"] else "—"
        text_parts.append(
            f"\n<b>#{row['id']}</b> | {row['created_at']}\n"
            f"👤 {esc(row['client_name'])} ({username_part})\n"
            f"📞 {esc(row['phone'])}\n"
            f"💼 {esc(row['service'])}\n"
            f"🗓 {esc(row['datetime_comment'] or '-')}\n"
        )
    await message.answer("".join(text_parts))


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "Не совсем понял вас 🤔 Воспользуйтесь меню ниже:",
            reply_markup=main_menu_kb(),
        )
