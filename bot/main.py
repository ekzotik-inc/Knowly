from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, PreCheckoutQuery
from sqlalchemy import select

from app.core.config import settings
from app.db.models import User
from app.db.session import SessionLocal
from app.services.payments import (
    PaymentError,
    find_pending_order,
    mark_successful_payment,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = Bot(settings.telegram_bot_token)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Добро пожаловать в Knowly. Откройте Mini App, чтобы создать тест "
        "или пройти тест друга."
    )


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    async with SessionLocal() as db:
        order = await find_pending_order(db, payload=query.invoice_payload)
        valid = bool(
            order
            and order.status == "pending"
            and order.currency == query.currency == "XTR"
            and order.stars == query.total_amount
            and order.user.telegram_id == query.from_user.id
        )
        if valid:
            await query.answer(ok=True)
        else:
            await query.answer(
                ok=False,
                error_message="Не удалось подтвердить заказ. Попробуйте создать счёт заново.",
            )


@dp.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment
    if payment is None:
        return

    async with SessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                raise PaymentError("user not found")

            order = await mark_successful_payment(
                db,
                payload=payment.invoice_payload,
                telegram_payment_charge_id=payment.telegram_payment_charge_id,
                total_amount=payment.total_amount,
                currency=payment.currency,
            )
            if order.user_id != user.id:
                raise PaymentError("payment user mismatch")
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
