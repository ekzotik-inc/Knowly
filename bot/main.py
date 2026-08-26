import asyncio
import logging
from urllib.parse import quote

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, PreCheckoutQuery, WebAppInfo
from sqlalchemy import select

from app.core.config import settings
from app.db.models import User
from app.db.session import SessionLocal
from app.services.payments import (
    PaymentError,
    find_pending_order,
    mark_successful_payment,
    validate_pre_checkout,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = Bot(settings.telegram_bot_token)
dp = Dispatcher()


def app_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Открыть Knowly ↗", web_app=WebAppInfo(url=url))]])


def start_app_url(message: Message) -> str:
    base_url = settings.webapp_url.rstrip("/")
    payload = (message.text or "").split(maxsplit=1)
    if len(payload) == 2 and payload[1].strip():
        return f"{base_url}/?startapp={quote(payload[1].strip())}"
    return base_url


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Привет! Я Knowly — маленькая игра, которая показывает, кто действительно тебя знает.\n\n"
        "Создай свой тест, настрой двух Knowly companion или открой игру друга. Ответы сохранятся, а результат можно сразу отправить в чат.",
        reply_markup=app_keyboard(start_app_url(message)),
    )


@dp.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "В Knowly можно создать тест о себе, поделиться им с друзьями и пройти чужую игру.\n\n"
        "Нажми кнопку ниже, чтобы открыть Mini App.",
        reply_markup=app_keyboard(settings.webapp_url.rstrip("/")),
    )


@dp.message(Command("characters"))
async def characters_command(message: Message) -> None:
    await message.answer(
        "Создай своего личного Knowly companion: выбери образ, настрой волосы, одежду и аксессуары. Изменить персонажа можно в любой момент.",
        reply_markup=app_keyboard(f"{settings.webapp_url.rstrip('/')}/?startapp=characters"),
    )


@dp.message(Command("terms"))
async def terms(message: Message) -> None:
    await message.answer("Knowly использует Telegram-авторизацию и хранит только данные, необходимые для работы профиля, игр и результатов.")


@dp.message(Command("paysupport"))
async def pay_support(message: Message) -> None:
    await message.answer("Платные функции пока отключены: Knowly работает в бесплатном тестовом режиме.")


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    async with SessionLocal() as db:
        order = await find_pending_order(db, payload=query.invoice_payload)
        decision = validate_pre_checkout(
            order=order,
            telegram_user_id=query.from_user.id,
            currency=query.currency,
            total_amount=query.total_amount,
        )
        if decision.accepted:
            await query.answer(ok=True)
        else:
            await query.answer(ok=False, error_message="Не удалось подтвердить заказ. Попробуйте создать счёт заново.")


@dp.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment
    if payment is None:
        return

    async with SessionLocal() as db:
        try:
            result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
            user = result.scalar_one_or_none()
            if user is None:
                raise PaymentError("user not found")

            await mark_successful_payment(
                db,
                payload=payment.invoice_payload,
                telegram_user_id=message.from_user.id,
                telegram_payment_charge_id=payment.telegram_payment_charge_id,
                total_amount=payment.total_amount,
                currency=payment.currency,
            )
            await db.commit()
        except PaymentError:
            await db.rollback()
            log.exception("Payment update rejected")
            return

    await message.answer("Оплата подтверждена. Платная функция уже доступна в Mini App.")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
