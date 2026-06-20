"""
Session backend يخزن الـ sessions في SQL Server مباشرة.
بيخلي الـ sessions تعيش حتى لو Vercel عمل cold start.
"""

import json
import logging
from datetime import datetime, timezone
from django.contrib.sessions.backends.base import SessionBase, CreateError
from db_connection import get_connection

log = logging.getLogger(__name__)


def _now_utc():
    return datetime.now(timezone.utc)


class SessionStore(SessionBase):
    """
    يحتاج جدول في SQL Server:

    CREATE TABLE django_sessions (
        session_key  VARCHAR(40)   NOT NULL PRIMARY KEY,
        session_data NVARCHAR(MAX) NOT NULL,
        expire_date  DATETIME2     NOT NULL
    );
    CREATE INDEX idx_django_sessions_expire ON django_sessions(expire_date);
    """

    def __init__(self, session_key=None):
        super().__init__(session_key)

    def _get_session_from_db(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT session_data FROM django_sessions WHERE session_key = %s AND expire_date > %s",
                (self.session_key, _now_utc())
            )
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            log.error("Session load error: %s", e)
            return None

    def load(self):
        data = self._get_session_from_db()
        if data is None:
            self._session_key = None
            return {}
        try:
            return self.decode(data)
        except Exception:
            self._session_key = None
            return {}

    def exists(self, session_key):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM django_sessions WHERE session_key = %s",
                (session_key,)
            )
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            log.error("Session exists error: %s", e)
            return False

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        data = self.encode(self._get_session(no_load=must_create))
        expiry = self.get_expiry_date()
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if must_create:
                try:
                    cursor.execute(
                        "INSERT INTO django_sessions (session_key, session_data, expire_date) VALUES (%s, %s, %s)",
                        (self._session_key, data, expiry)
                    )
                except Exception:
                    conn.close()
                    raise CreateError
            else:
                cursor.execute(
                    """
                    IF EXISTS (SELECT 1 FROM django_sessions WHERE session_key = %s)
                        UPDATE django_sessions SET session_data = %s, expire_date = %s WHERE session_key = %s
                    ELSE
                        INSERT INTO django_sessions (session_key, session_data, expire_date) VALUES (%s, %s, %s)
                    """,
                    (self._session_key, data, expiry, self._session_key,
                     self._session_key, data, expiry)
                )
            conn.commit()
            conn.close()
        except CreateError:
            raise
        except Exception as e:
            log.error("Session save error: %s", e)

    def delete(self, session_key=None):
        key = session_key or self._session_key
        if not key:
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM django_sessions WHERE session_key = %s", (key,))
            conn.commit()
            conn.close()
        except Exception as e:
            log.error("Session delete error: %s", e)

    @classmethod
    def clear_expired(cls):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM django_sessions WHERE expire_date < %s", (_now_utc(),))
            conn.commit()
            conn.close()
        except Exception as e:
            log.error("Session clear_expired error: %s", e)
