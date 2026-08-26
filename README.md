# Knowly

Knowly — Telegram Mini App для игровых тестов «Насколько хорошо ты меня знаешь?». Репозиторий содержит foundation проекта и первую интеграцию платных функций через **Telegram Stars**.

## Архитектура

| Компонент | Технологии | Назначение |
|---|---|---|
| Mini App | React, TypeScript, Vite | Каталог premium-функций и запуск Telegram invoice |
| API | FastAPI, Python 3.12+, SQLAlchemy async | Telegram auth, каталог, заказы и entitlements |
| Bot worker | aiogram 3.x | `/start`, pre-checkout и successful payment updates |
| Database | PostgreSQL | Users, products, orders, entitlements |
| Hosting | Render | API, worker, static frontend и PostgreSQL |

## Монетизация через Telegram Stars

Приложение продаёт цифровые функции только в Telegram. Backend создаёт invoice link с `currency="XTR"`, `provider_token=""` и server-generated payload. Telegram присылает `pre_checkout_query`; worker проверяет пользователя, payload, цену, валюту и статус заказа, после чего отвечает на query. Доступ выдаётся только после update с `successful_payment`.

В текущем каталоге предусмотрены три продукта:

| Код | Функция | Цена |
|---|---|---:|
| `premium_results` | Подробный разбор результатов | 49 Stars |
| `extra_questions` | Расширенный тест | 39 Stars |
| `profile_themes` | Премиум-темы профиля | 29 Stars |

Цены находятся в PostgreSQL, а не во frontend. Frontend получает каталог через `GET /api/v1/payments/products`.

## Локальный запуск

Скопируйте `.env.example` в `.env`, задайте реальный токен бота только локально и сгенерируйте длинный `SESSION_SECRET`:

```bash
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Создайте PostgreSQL и примените миграцию:

```bash
psql "$DATABASE_URL" -f migrations/001_monetization.sql
```

Запустите API:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

В другом терминале запустите bot worker:

```bash
cd /path/to/Knowly
. backend/.venv/bin/activate
python -m bot.main
```

Запустите Mini App:

```bash
cd frontend
npm install
npm run dev
```

Для работы внутри Telegram настройте URL Mini App в BotFather. Для локальной разработки используйте Telegram test environment или публичный HTTPS-туннель; обычный `localhost` не будет доступен Telegram-клиенту как production Mini App URL.

## API

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/health` | Проверка API |
| `POST` | `/api/v1/auth/telegram` | Проверка `Telegram.WebApp.initData` и выдача собственного Bearer token |
| `GET` | `/api/v1/payments/products` | Каталог активных Stars-продуктов |
| `POST` | `/api/v1/payments/invoice` | Создание pending order и invoice link |
| `GET` | `/api/v1/payments/entitlements` | Доступные функции текущего пользователя |
| `POST` | `/api/v1/tests` | Создать и опубликовать тест с вопросами |
| `GET` | `/api/v1/tests` | Получить свои тесты |
| `GET` | `/api/v1/public/tests/{public_token}` | Получить публичную версию теста без правильных ответов |
| `POST` | `/api/v1/public/tests/{public_token}/sessions` | Начать игровую сессию |
| `POST` | `/api/v1/sessions/{session_id}/answers` | Сохранить выбранный вариант |
| `POST` | `/api/v1/sessions/{session_id}/complete` | Рассчитать и зафиксировать результат |
| `GET` | `/api/v1/results/{result_id}` | Просмотреть результат и разбор ответов |

Первичный запрос авторизации передаёт исходную строку Mini App так:

```http
Authorization: TWA <window.Telegram.WebApp.initData>
```

После успешной авторизации frontend хранит access token только в памяти и передаёт:

```http
Authorization: Bearer <access_token>
```

## Безопасность

Backend проверяет HMAC-SHA-256 hash по алгоритму Telegram, срок действия `auth_date`, размер payload, дубликаты ключей и структуру `user`. Bot token хранится только в environment variables. Клиентский `score`, цена, Telegram ID и готовый entitlement не считаются доверенными.

Обработка успешной оплаты идемпотентна. `payload` и `telegram_payment_charge_id` имеют уникальные ограничения, а заказ переходит из `pending` в `paid` только один раз. При возврате сначала нужно отозвать entitlement по принятой политике продукта, затем вызвать `refundStarPayment` и записать `refunded_at`.

## Render

Blueprint содержит отдельные сервисы для API, bot worker и static Mini App, а также PostgreSQL. После создания сервисов задайте `TELEGRAM_BOT_TOKEN`, `SESSION_SECRET`, `WEBAPP_URL`, `ALLOWED_ORIGINS` и `VITE_API_URL` в Render Dashboard. Секреты не добавляйте в Git.

## Статус

Сейчас реализованы Telegram auth exchange, каталог продуктов, создание invoice link в XTR, pre-checkout validation, successful payment processing, entitlements и рабочий игровой MVP: создание теста, публикация deep link, прохождение по вопросам, сохранение ответов, серверный подсчёт результата и базовый premium UI.
