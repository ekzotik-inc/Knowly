from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import LabeledPrice
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Entitlement, Order, Product, User


class PaymentError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PaymentDecision:
    accepted: bool
    reason: str | None = None


def validate_pre_checkout(
    *,
    order: Order | None,
    telegram_user_id: int,
    currency: str,
    total_amount: int,
) -> PaymentDecision:
    if order is None:
        return PaymentDecision(False, "unknown order")
    if order.status != "pending":
        return PaymentDecision(False, "order is not pending")
    if order.user.telegram_id != telegram_user_id:
        return PaymentDecision(False, "payment user mismatch")
    if currency != "XTR" or order.currency != currency:
        return PaymentDecision(False, "currency mismatch")
    if total_amount != order.stars:
        return PaymentDecision(False, "amount mismatch")
    return PaymentDecision(True)


def validate_successful_payment(
    *,
    order: Order | None,
    telegram_user_id: int,
    telegram_payment_charge_id: str,
    total_amount: int,
    currency: str,
) -> PaymentDecision:
    if order is None:
        return PaymentDecision(False, "unknown order")
    if order.user.telegram_id != telegram_user_id:
        return PaymentDecision(False, "payment user mismatch")
    if currency != "XTR" or total_amount != order.stars:
        return PaymentDecision(False, "payment amount or currency mismatch")
    if order.status == "paid":
        if order.telegram_payment_charge_id == telegram_payment_charge_id:
            return PaymentDecision(True, "already processed")
        return PaymentDecision(False, "payment charge mismatch")
    if order.status != "pending":
        return PaymentDecision(False, "order is not payable")
    if order.telegram_payment_charge_id not in (None, telegram_payment_charge_id):
        return PaymentDecision(False, "payment charge mismatch")
    return PaymentDecision(True)


async def get_product(db: AsyncSession, product_code: str) -> Product:
    result = await db.execute(
        select(Product).where(Product.code == product_code, Product.is_active.is_(True))
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise PaymentError("product unavailable")
    if product.stars <= 0:
        raise PaymentError("invalid product price")
    return product


def make_payload(order_id: uuid.UUID) -> str:
    # The order UUID is not secret; the random suffix prevents guessing and
    # makes payloads safe to correlate without exposing user data.
    return f"knowly:{order_id}:{secrets.token_urlsafe(12)}"[:128]


async def create_invoice_link(
    db: AsyncSession,
    bot: Bot,
    user: User,
    product_code: str,
) -> tuple[Order, str]:
    product = await get_product(db, product_code)
    order_id = uuid.uuid4()
    order = Order(
        id=order_id,
        user_id=user.id,
        product_id=product.id,
        payload=make_payload(order_id),
        currency="XTR",
        stars=product.stars,
        status="pending",
    )
    db.add(order)
    await db.flush()

    invoice_link = await bot.create_invoice_link(
        title=product.title,
        description=product.description,
        payload=order.payload,
        currency="XTR",
        prices=[LabeledPrice(label=product.title, amount=product.stars)],
        provider_token="",
    )
    await db.flush()
    return order, invoice_link


async def find_pending_order(
    db: AsyncSession,
    *,
    payload: str,
) -> Order | None:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.product), selectinload(Order.user))
        .where(Order.payload == payload)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def mark_successful_payment(
    db: AsyncSession,
    *,
    payload: str,
    telegram_user_id: int,
    telegram_payment_charge_id: str,
    total_amount: int,
    currency: str,
) -> Order:
    order = await find_pending_order(db, payload=payload)
    if order is None:
        raise PaymentError("unknown payment payload")

    decision = validate_successful_payment(
        order=order,
        telegram_user_id=telegram_user_id,
        telegram_payment_charge_id=telegram_payment_charge_id,
        total_amount=total_amount,
        currency=currency,
    )
    if not decision.accepted:
        raise PaymentError(decision.reason or "invalid payment")
    if order.status == "paid":
        # Idempotent update delivery: do not issue a second entitlement.
        return order

    order.status = "paid"
    order.telegram_payment_charge_id = telegram_payment_charge_id
    order.paid_at = datetime.now(timezone.utc)
    db.add(
        Entitlement(
            user_id=order.user_id,
            order_id=order.id,
            entitlement_key=order.product.entitlement_key,
            active=True,
        )
    )
    return order


async def user_has_entitlement(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    entitlement_key: str,
) -> bool:
    result = await db.execute(
        select(Entitlement.id).where(
            Entitlement.user_id == user_id,
            Entitlement.entitlement_key == entitlement_key,
            Entitlement.active.is_(True),
        )
    )
    return result.scalar_one_or_none() is not None


async def refund_order(
    db: AsyncSession,
    bot: Bot,
    *,
    order_id: uuid.UUID,
) -> Order:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.entitlement))
        .where(Order.id == order_id)
        .with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None or order.status != "paid" or not order.telegram_payment_charge_id:
        raise PaymentError("order cannot be refunded")

    await bot.refund_star_payment(
        user_id=(await _telegram_id_for_order(db, order.user_id)),
        telegram_payment_charge_id=order.telegram_payment_charge_id,
    )
    order.status = "refunded"
    order.refunded_at = datetime.now(timezone.utc)
    if order.entitlement:
        order.entitlement.active = False
        order.entitlement.revoked_at = order.refunded_at
    return order


async def _telegram_id_for_order(db: AsyncSession, user_id: uuid.UUID) -> int:
    telegram_id = await db.scalar(select(User.telegram_id).where(User.id == user_id))
    if telegram_id is None:
        raise PaymentError("user not found")
    return telegram_id
