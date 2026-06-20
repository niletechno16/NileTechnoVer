from fastapi_app.database.connection import get_connection
from fastapi_app.config.settings import PROBLEM_TABLE, USERS_TABLE, CATEGORY_TABLE


def init_db():
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # ─── 1) جدول الكاتيجوريز ───
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = '{CATEGORY_TABLE}'
            )
            BEGIN
                CREATE TABLE {CATEGORY_TABLE} (
                    id            INT IDENTITY(1,1) PRIMARY KEY,
                    category_name NVARCHAR(500) NOT NULL
                )
            END
        """)

        # ─── 2) جدول المشاكل ───
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = '{PROBLEM_TABLE}'
            )
            BEGIN
                CREATE TABLE {PROBLEM_TABLE} (
                    id                  INT IDENTITY(1,1) PRIMARY KEY,
                    customer_id         INT,
                    type                INT,              -- 1=resolved | 0=not_resolved
                    problem             NVARCHAR(MAX),
                    category_id         INT,
                    agent_id            INT,
                    conv_id             NVARCHAR(50),
                    start_message_date  BIGINT,
                    resolve_date        BIGINT,
                    duration_minutes    INT,
                    summary             NVARCHAR(MAX),
                    created_at          DATETIME DEFAULT GETDATE(),
                    status              INT DEFAULT 1  -- 1=active (not archived) | 0=archived
                )
            END
        """)

        # ─── 3) جدول المستخدمين ───
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = '{USERS_TABLE}'
            )
            BEGIN
                CREATE TABLE {USERS_TABLE} (
                    user_id         INT PRIMARY KEY,
                    user_name       NVARCHAR(255),
                    phone           NVARCHAR(50),
                    user_type       INT,
                    user_type_label NVARCHAR(20)
                )
            END
        """)

        conn.commit()
        conn.close()
        print(f"✅ DB ready — '{CATEGORY_TABLE}', '{PROBLEM_TABLE}', '{USERS_TABLE}' exist or created")
    except Exception as e:
        print(f"❌ DB init failed: {str(e)}")
