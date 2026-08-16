"""Initial schema migration for PayGuard prototype models.

Revision ID: 0001_initial_models
"""

from sqlalchemy import create_engine, text


def upgrade(database_url: str = "sqlite:///./payguard.db") -> None:
    """Create initial tables for customers, orders, payment submissions, SMS, and results."""
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    ddl = """
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        phone VARCHAR(32) NOT NULL UNIQUE,
        created_at DATETIME NOT NULL
    );
    CREATE INDEX IF NOT EXISTS ix_customers_phone ON customers (phone);

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        external_order_id VARCHAR(64) NOT NULL UNIQUE,
        customer_id INTEGER NOT NULL,
        expected_amount_lkr NUMERIC(12,2) NOT NULL,
        business_account_no VARCHAR(32) NOT NULL,
        status VARCHAR(20) NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    );
    CREATE INDEX IF NOT EXISTS ix_orders_external_order_id ON orders (external_order_id);
    CREATE INDEX IF NOT EXISTS ix_orders_customer_id ON orders (customer_id);

    CREATE TABLE IF NOT EXISTS payment_submissions (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        image_path VARCHAR(500) NOT NULL,
        image_sha256 VARCHAR(64) NOT NULL,
        image_phash VARCHAR(32) NOT NULL,
        submitted_amount_lkr NUMERIC(12,2),
        submitted_account_no VARCHAR(32),
        submitted_reference VARCHAR(64),
        submitted_paid_at DATETIME,
        status VARCHAR(24) NOT NULL,
        flags_json TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    );
    CREATE INDEX IF NOT EXISTS ix_payment_submissions_order_id ON payment_submissions (order_id);
    CREATE INDEX IF NOT EXISTS ix_payment_submissions_customer_id ON payment_submissions (customer_id);
    CREATE INDEX IF NOT EXISTS ix_payment_submissions_image_sha256 ON payment_submissions (image_sha256);
    CREATE INDEX IF NOT EXISTS ix_payment_submissions_image_phash ON payment_submissions (image_phash);

    CREATE TABLE IF NOT EXISTS bank_sms (
        id INTEGER PRIMARY KEY,
        raw_text TEXT NOT NULL,
        parsed_amount_lkr NUMERIC(12,2),
        parsed_reference VARCHAR(64),
        parsed_account_no VARCHAR(32),
        received_at DATETIME NOT NULL,
        sender VARCHAR(32)
    );
    CREATE INDEX IF NOT EXISTS ix_bank_sms_parsed_amount_lkr ON bank_sms (parsed_amount_lkr);
    CREATE INDEX IF NOT EXISTS ix_bank_sms_parsed_reference ON bank_sms (parsed_reference);
    CREATE INDEX IF NOT EXISTS ix_bank_sms_parsed_account_no ON bank_sms (parsed_account_no);
    CREATE INDEX IF NOT EXISTS ix_bank_sms_received_at ON bank_sms (received_at);

    CREATE TABLE IF NOT EXISTS verification_results (
        id INTEGER PRIMARY KEY,
        payment_submission_id INTEGER NOT NULL UNIQUE,
        decision VARCHAR(32) NOT NULL,
        internal_reason TEXT NOT NULL,
        customer_message TEXT NOT NULL,
        confidence_score FLOAT NOT NULL,
        evidence_json TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(payment_submission_id) REFERENCES payment_submissions(id)
    );
    CREATE INDEX IF NOT EXISTS ix_verification_results_decision ON verification_results (decision);
    CREATE INDEX IF NOT EXISTS ix_verification_results_payment_submission_id ON verification_results (payment_submission_id);
    """
    with engine.begin() as conn:
        for statement in ddl.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))


def downgrade(database_url: str = "sqlite:///./payguard.db") -> None:
    """Drop all initial tables in reverse dependency order."""
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS verification_results"))
        conn.execute(text("DROP TABLE IF EXISTS bank_sms"))
        conn.execute(text("DROP TABLE IF EXISTS payment_submissions"))
        conn.execute(text("DROP TABLE IF EXISTS orders"))
        conn.execute(text("DROP TABLE IF EXISTS customers"))
