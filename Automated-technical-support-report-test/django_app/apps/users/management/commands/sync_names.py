from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import is_password_usable
from apps.users.models import UserProfile
from db_connection import get_connection


class Command(BaseCommand):
    help = 'يجيب أسماء وباسوردات كل اليوزرين من SQL Server ويحدّثهم'

    def handle(self, *args, **kwargs):
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, user_name, phone FROM users_Details_byA")
            rows = {
                str(row[0]).strip(): {
                    'name': row[1].strip() if row[1] else '',
                    'hash': row[2].strip() if row[2] else None,
                }
                for row in cursor.fetchall()
            }
            conn.close()
        except Exception as e:
            self.stdout.write(f'❌ فشل الاتصال بـ SQL Server: {e}')
            return

        for profile in UserProfile.objects.select_related('user').exclude(role='visitor'):
            uid  = str(profile.agent_id).strip()
            data = rows.get(uid)
            if not data:
                continue

            changed = False

            # تحديث الاسم
            if data['name'] and profile.full_name != data['name']:
                profile.full_name       = data['name']
                profile.user.first_name = data['name']
                changed = True

            # استعادة الباسورد من SQL لو موجود
            if data['hash'] and is_password_usable(data['hash']):
                profile.user.password = data['hash']
                changed = True
                self.stdout.write(f'🔑 استعادة باسورد ID {uid}')

            if changed:
                profile.save()
                profile.user.save()
                self.stdout.write(f'✅ ID {uid} → {data["name"]}')

        self.stdout.write('🎉 sync خلص!')
