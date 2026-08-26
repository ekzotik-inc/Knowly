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


CREATE TABLE IF NOT EXISTS profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    display_name varchar(128) NOT NULL,
    avatar_url varchar(512),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title varchar(128) NOT NULL DEFAULT 'Насколько ты меня знаешь?',
    mode varchar(64) NOT NULL DEFAULT 'know_me',
    public_token varchar(32) NOT NULL UNIQUE,
    status varchar(24) NOT NULL DEFAULT 'draft',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_tests_owner_status ON tests(owner_id, status);

CREATE TABLE IF NOT EXISTS questions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text varchar(500) NOT NULL,
    options jsonb NOT NULL,
    correct_option varchar(255) NOT NULL,
    category varchar(64),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS test_questions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id uuid NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    question_id uuid NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    position integer NOT NULL,
    CONSTRAINT uq_test_question UNIQUE (test_id, question_id)
);

CREATE TABLE IF NOT EXISTS test_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id uuid NOT NULL REFERENCES tests(id) ON DELETE RESTRICT,
    participant_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status varchar(24) NOT NULL DEFAULT 'in_progress',
    current_position integer NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_test_sessions_participant ON test_sessions(participant_user_id, status);

CREATE TABLE IF NOT EXISTS test_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL UNIQUE REFERENCES test_sessions(id) ON DELETE RESTRICT,
    test_id uuid NOT NULL REFERENCES tests(id) ON DELETE RESTRICT,
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    participant_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    correct_answers integer NOT NULL,
    total_questions integer NOT NULL,
    percentage integer NOT NULL CHECK (percentage BETWEEN 0 AND 100),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS result_answers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id uuid NOT NULL REFERENCES test_results(id) ON DELETE CASCADE,
    question_id uuid NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    selected_option varchar(255) NOT NULL,
    correct_option varchar(255) NOT NULL,
    is_correct boolean NOT NULL,
    CONSTRAINT uq_result_answer UNIQUE (result_id, question_id)
);


CREATE TABLE IF NOT EXISTS session_answers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    question_id uuid NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    selected_option varchar(255) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_session_answer UNIQUE (session_id, question_id)
);
