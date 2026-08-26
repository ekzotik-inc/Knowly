from __future__ import annotations

from uuid import UUID

from aiogram import Bot
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.config import settings
from app.db.models import Entitlement
from app.db.session import get_db
from app.services.payments import PaymentError, create_invoice_link
from fastapi import Depends

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


class ProductResponse(BaseModel):
    code: str
    title: str
    description: str
    stars: int
    entitlement_key: str


class CreateInvoiceRequest(BaseModel):
    product_code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_:-]+$")


class InvoiceResponse(BaseModel):
    order_id: UUID
    product_code: str
    stars: int
    invoice_link: str


class EntitlementResponse(BaseModel):
    entitlement_key: str
    active: bool


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
) -> list[ProductResponse]:
    result = await db.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.stars))
    return [
        ProductResponse(
            code=item.code,
            title=item.title,
            description=item.description,
            stars=item.stars,
            entitlement_key=item.entitlement_key,
        )
        for item in result.scalars()
    ]


@router.post("/invoice", response_model=InvoiceResponse)
async def create_invoice(
    request: CreateInvoiceRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    try:
        async with Bot(settings.telegram_bot_token) as bot:
            order, invoice_link = await create_invoice_link(
                db,
                bot,
                current_user,
                request.product_code,
            )
        await db.commit()
    except PaymentError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to create Telegram invoice",
        )

    return InvoiceResponse(
        order_id=order.id,
        product_code=order.product.code,
        stars=order.stars,
        invoice_link=invoice_link,
    )


@router.get("/entitlements", response_model=list[EntitlementResponse])
async def list_entitlements(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[EntitlementResponse]:
    result = await db.execute(
        select(Entitlement).where(Entitlement.user_id == current_user.id)
    )
    return [
        EntitlementResponse(
            entitlement_key=item.entitlement_key,
            active=item.active,
        )
        for item in result.scalars()
    ]
