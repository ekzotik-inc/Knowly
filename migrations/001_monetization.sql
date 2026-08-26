CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id bigint NOT NULL UNIQUE,
    first_name varchar(128) NOT NULL,
    last_name varchar(128),
    username varchar(64),
    language_code varchar(16),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(64) NOT NULL UNIQUE,
    title varchar(128) NOT NULL,
    description varchar(255) NOT NULL,
    stars integer NOT NULL CHECK (stars > 0),
    entitlement_key varchar(128) NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    product_id uuid NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    payload varchar(128) NOT NULL UNIQUE,
    currency varchar(3) NOT NULL DEFAULT 'XTR',
    stars integer NOT NULL CHECK (stars > 0),
    status varchar(24) NOT NULL DEFAULT 'pending',
    telegram_payment_charge_id varchar(128) UNIQUE,
    telegram_invoice_payload text,
    paid_at timestamptz,
    refunded_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_orders_user_status ON orders(user_id, status);

CREATE TABLE IF NOT EXISTS entitlements (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id uuid NOT NULL UNIQUE REFERENCES orders(id) ON DELETE RESTRICT,
    entitlement_key varchar(128) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    granted_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz,
    CONSTRAINT uq_entitlements_user_key UNIQUE (user_id, entitlement_key)
);

INSERT INTO products (code, title, description, stars, entitlement_key)
VALUES
    ('premium_results', 'Premium-разбор результатов', 'Подробный разбор ответов и дополнительные игровые показатели', 49, 'premium_results'),
    ('extra_questions', 'Дополнительные вопросы', 'Расширенный тест с дополнительными вопросами', 39, 'extra_questions'),
    ('profile_themes', 'Премиум-темы профиля', 'Набор романтичных тем оформления персонального теста', 29, 'profile_themes')
ON CONFLICT (code) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    stars = EXCLUDED.stars,
    entitlement_key = EXCLUDED.entitlement_key;
