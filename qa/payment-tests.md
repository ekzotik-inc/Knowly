# Unit-тесты платежной логики Knowly

## Зачем выносить проверки из handlers

Aiogram handler должен отвечать за интеграцию с Telegram: получить update, вызвать бизнес-логику и вернуть `query.answer()` или сообщение. Проверка заказа не должна быть спрятана внутри handler, потому что тогда для обычного теста придётся создавать сложные объекты Telegram и имитировать сеть.

В Knowly чистые функции `validate_pre_checkout()` и `validate_successful_payment()` получают обычные данные заказа и возвращают `PaymentDecision`. Поэтому unit-тесты запускаются быстро, не требуют Bot API и не зависят от PostgreSQL.

## Что проверяется

| Сценарий | Ожидаемый результат |
|---|---|
| Pending order, пользователь, XTR и сумма совпадают | `accepted=True` |
| Payload не найден | Отклонение |
| Telegram ID не совпадает с владельцем заказа | Отклонение |
| Валюта не `XTR` | Отклонение |
| Сумма отличается от цены заказа | Отклонение |
| Pre-checkout для уже оплаченного заказа | Отклонение |
| Повторный successful payment с тем же charge ID | Разрешён как idempotent replay |
| Paid order с другим charge ID | Отклонение |

## Запуск

Из корня репозитория:

```bash
PYTHONPATH=backend \
TELEGRAM_BOT_TOKEN='123456:TEST_TOKEN' \
SESSION_SECRET='0123456789abcdef0123456789abcdef' \
DATABASE_URL='sqlite+aiosqlite:///./test.db' \
pytest -q tests
```

Тесты не используют настоящий bot token. Вызовы к Telegram API также не выполняются: это зона integration-тестов, а не unit-тестов.

## Важный принцип successful_payment

Один и тот же update может быть доставлен повторно. Повтор нужно считать безопасным только если одновременно совпадают владелец заказа, валюта, сумма и `telegram_payment_charge_id`. Если заказ уже `paid`, но charge ID другой, событие нужно отклонить. Именно это отдельно проверяет `test_successful_payment_rejects_different_charge_on_paid_order`.

## Где находятся тесты

Основные тесты находятся в `tests/test_payment_validation.py`. Тесты криптографической проверки Telegram находятся в `tests/test_telegram_auth.py`.
