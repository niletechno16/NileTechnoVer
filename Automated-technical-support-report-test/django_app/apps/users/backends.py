"""
Custom authentication backend.
يتحقق من اليوزر والباسورد مباشرة من SQL Server — بدون SQLite أو Django User model.
"""

import logging
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password, make_password, is_password_usable
from db_connection import get_connection

log = logging.getLogger(__name__)


class MSSQLUser:
    """
    كائن يمثل اليوزر في الـ session — بيحاكي Django User interface
    بدون ما يلمس قاعدة بيانات محلية.
    """
    is_anonymous = False
    is_authenticated = True

    def __init__(self, user_id, full_name, role, is_first_login=False):
        self.id = user_id          # required by Django session
        self.pk = user_id
        self.username = user_id
        self.agent_id = user_id
        self.first_name = full_name
        self.full_name = full_name
        self.role = role
        self.is_first_login = is_first_login
        self.is_staff = False
        self.is_superuser = False
        self.is_active = True

    # Django middleware/session يحتاج الميثودين دول
    def get_username(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.role in ('developer', 'owner')

    def has_module_perms(self, app_label):
        return self.role in ('developer', 'owner')

    # Django session بيحاول يعمل str(user)
    def __str__(self):
        return self.username


class MSSQLAuthBackend(BaseBackend):
    """
    Backend يتحقق من user_id + password مقابل جدول users_Details_byA في SQL Server.
    الباسورد مخزن في عمود phone كـ Django hash (pbkdf2_sha256$...).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, user_name, phone, role
                FROM users_Details_byA
                WHERE user_id = %s AND user_type = 2
                """,
                (username,)
            )
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            log.error("SQL auth error: %s", e)
            return None

        if not row:
            return None

        sql_id     = str(row[0]).strip()
        sql_name   = (row[1] or '').strip()
        saved_hash = (row[2] or '').strip()
        role       = (row[3] or 'agent').strip()

        # ── أول مرة: لا يوجد hash → الباسورد المؤقت هو نفس الـ ID ──
        if not saved_hash or not is_password_usable(saved_hash):
            if password != sql_id:
                return None
            # احفظ hash في SQL عشان المرة الجاية
            new_hash = make_password(password)
            self._save_hash(sql_id, new_hash)
            return MSSQLUser(sql_id, sql_name, role, is_first_login=True)

        # ── تحقق عادي ──
        if not check_password(password, saved_hash):
            return None

        return MSSQLUser(sql_id, sql_name, role, is_first_login=False)

    def get_user(self, user_id):
        """Django session بتستدعي ده عشان تسترجع اليوزر من الـ session."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, user_name, role
                FROM users_Details_byA
                WHERE user_id = %s AND user_type = 2
                """,
                (user_id,)
            )
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            log.error("get_user SQL error: %s", e)
            return None

        if not row:
            return None

        return MSSQLUser(
            user_id  = str(row[0]).strip(),
            full_name= (row[1] or '').strip(),
            role     = (row[2] or 'agent').strip(),
        )

    def _save_hash(self, user_id, hashed_password):
        """يحفظ Django hash في عمود phone في SQL Server."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users_Details_byA SET phone = %s WHERE user_id = %s",
                (hashed_password, user_id)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.warning("Failed to save hash: %s", e)
