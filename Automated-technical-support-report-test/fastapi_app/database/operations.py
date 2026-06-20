from difflib import SequenceMatcher
from fastapi_app.database.connection import get_connection
from fastapi_app.config.settings import (
    PROBLEM_TABLE, USERS_TABLE, CATEGORY_TABLE,
    CATEGORY_SIMILARITY_THRESHOLD
)


# ================================================================
# CATEGORY: جلب أو إنشاء — يرجع category_id
# ================================================================
def get_or_create_category(category_name: str) -> int:
    if not category_name or not category_name.strip():
        category_name = "غير محدد"

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"SELECT id, category_name FROM {CATEGORY_TABLE}")
        rows = cursor.fetchall()

        best_id    = None
        best_ratio = 0.0
        best_name  = ""

        for row in rows:
            ratio = SequenceMatcher(None, category_name.strip(), row[1].strip()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_id    = row[0]
                best_name  = row[1]

        if best_ratio >= CATEGORY_SIMILARITY_THRESHOLD:
            conn.close()
            print(f"🔁 Category matched: '{category_name}' → '{best_name}' (id={best_id}, ratio={best_ratio:.2f})")
            return best_id

        # كاتيجوري جديدة
        cursor.execute(
            f"INSERT INTO {CATEGORY_TABLE} (category_name) VALUES (%s)",
            (category_name,)
        )
        cursor.execute("SELECT @@IDENTITY")
        new_id = int(cursor.fetchone()[0])
        conn.commit()
        conn.close()
        print(f"🆕 New category added: '{category_name}' → id={new_id}")
        return new_id

    except Exception as e:
        print(f"❌ get_or_create_category error: {str(e)}")
        return 0


# ================================================================
# GET EXISTING CATEGORY NAMES (للبرومت)
# ================================================================
def get_existing_category_names() -> list:
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT category_name FROM {CATEGORY_TABLE}")
        names = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return names
    except Exception as e:
        print(f"⚠️ get_existing_category_names error: {str(e)}")
        return []


# ================================================================
# SAVE USER — عميل أو أيجينت (مرة واحدة بس)
# ================================================================
def save_user(user_id, user_name, phone, user_type):
    if user_id is None:
        return
    user_type_label = "Customer" if user_type == 1 else "Customer Support"
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            IF NOT EXISTS (SELECT 1 FROM {USERS_TABLE} WHERE user_id = %d)
            BEGIN
                INSERT INTO {USERS_TABLE} (user_id, user_name, phone, user_type, user_type_label)
                VALUES (%d, %s, %s, %d, %s)
            END
        """, (user_id, user_id, user_name, phone, user_type, user_type_label))
        conn.commit()
        conn.close()
        print(f"✅ User saved — id:{user_id} | {user_type_label}")
    except Exception as e:
        print(f"❌ User save failed: {str(e)}")


# ================================================================
# SAVE PROBLEM
# ================================================================
def save_problem(customer_id, prob_type, problem,
                 category_id, agent_id, conv_id,
                 start_message_date, resolve_date,
                 duration_minutes, summary):
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {PROBLEM_TABLE}
                (customer_id, type, problem,
                 category_id, agent_id, conv_id,
                 start_message_date, resolve_date, duration_minutes,
                 summary)
            VALUES (%d, %d, %s, %d, %d, %s, %d, %d, %d, %s)
        """, (
            customer_id,
            prob_type,
            problem,
            category_id,
            agent_id,
            str(conv_id),
            start_message_date,
            resolve_date,
            duration_minutes,
            summary
        ))
        conn.commit()
        conn.close()
        print(f"✅ Problem saved — conv_id:{conv_id} | type:{prob_type} | cat_id:{category_id}")
    except Exception as e:
        print(f"❌ Problem insert failed: {str(e)}")
