from types import SimpleNamespace

import pytest

from app.services.payments import validate_pre_checkout, validate_successful_payment


@pytest.fixture
def pending_order():
    return SimpleNamespace(
        status="pending",
        currency="XTR",
        stars=49,
        telegram_payment_charge_id=None,
        user=SimpleNamespace(telegram_id=1001),
    )


def test_pre_checkout_accepts_matching_pending_order(pending_order):
    decision = validate_pre_checkout(
        order=pending_order,
        telegram_user_id=1001,
        currency="XTR",
        total_amount=49,
    )
    assert decision.accepted is True
    assert decision.reason is None


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"order": None}, "unknown order"),
        ({"telegram_user_id": 9999}, "payment user mismatch"),
        ({"currency": "USD"}, "currency mismatch"),
        ({"total_amount": 50}, "amount mismatch"),
    ],
)
def test_pre_checkout_rejects_invalid_order(pending_order, kwargs, reason):
    values = {
        "order": pending_order,
        "telegram_user_id": 1001,
        "currency": "XTR",
        "total_amount": 49,
    }
    values.update(kwargs)
    decision = validate_pre_checkout(**values)
    assert decision.accepted is False
    assert decision.reason == reason


def test_pre_checkout_rejects_already_paid_order(pending_order):
    pending_order.status = "paid"
    decision = validate_pre_checkout(
        order=pending_order,
        telegram_user_id=1001,
        currency="XTR",
        total_amount=49,
    )
    assert decision.accepted is False
    assert decision.reason == "order is not pending"


def test_successful_payment_accepts_valid_pending_payment(pending_order):
    decision = validate_successful_payment(
        order=pending_order,
        telegram_user_id=1001,
        telegram_payment_charge_id="charge-1",
        total_amount=49,
        currency="XTR",
    )
    assert decision.accepted is True


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"order": None}, "unknown order"),
        ({"telegram_user_id": 9999}, "payment user mismatch"),
        ({"currency": "USD"}, "payment amount or currency mismatch"),
        ({"total_amount": 1}, "payment amount or currency mismatch"),
    ],
)
def test_successful_payment_rejects_tampering(pending_order, kwargs, reason):
    values = {
        "order": pending_order,
        "telegram_user_id": 1001,
        "telegram_payment_charge_id": "charge-1",
        "total_amount": 49,
        "currency": "XTR",
    }
    values.update(kwargs)
    decision = validate_successful_payment(**values)
    assert decision.accepted is False
    assert decision.reason == reason


def test_successful_payment_allows_same_update_to_be_replayed_idempotently(pending_order):
    pending_order.status = "paid"
    pending_order.telegram_payment_charge_id = "charge-1"
    decision = validate_successful_payment(
        order=pending_order,
        telegram_user_id=1001,
        telegram_payment_charge_id="charge-1",
        total_amount=49,
        currency="XTR",
    )
    assert decision.accepted is True
    assert decision.reason == "already processed"


def test_successful_payment_rejects_different_charge_on_paid_order(pending_order):
    pending_order.status = "paid"
    pending_order.telegram_payment_charge_id = "charge-1"
    decision = validate_successful_payment(
        order=pending_order,
        telegram_user_id=1001,
        telegram_payment_charge_id="charge-attacker",
        total_amount=49,
        currency="XTR",
    )
    assert decision.accepted is False
    assert decision.reason == "payment charge mismatch"
