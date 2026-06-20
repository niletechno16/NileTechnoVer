import os
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password, is_password_usable
from django.contrib.auth.models import User
from apps.users.models import UserProfile
from db_connection import get_connection


class Command(BaseCommand):
    help = 'إنشاء أو استعادة حسابات الـ developer والـ owner من SQL Server'

    def get_user_data(self, uid):
        """يجيب الاسم والـ password hash من users_Details_byA"""
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_name, phone FROM users_Details_byA WHERE user_id = %s",
                (uid,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                name      = row[0].strip() if row[0] else uid
                pwd_hash  = row[1].strip() if row[1] else None
                return name, pwd_hash
        except Exception as e:
            self.stdout.write(f'⚠️  خطأ في DB: {e}')
        return uid, None

    def save_hash_to_db(self, uid, pwd_hash):
        """يحفظ الـ password hash في phone"""
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users_Details_byA SET phone = %s WHERE user_id = %s",
                (pwd_hash, uid)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            self.stdout.write(f'⚠️  مش قادر يحفظ الـ hash في DB: {e}')

    def handle(self, *args, **kwargs):
        developer_id = os.getenv('DEVELOPER_ID')
        owner_id     = os.getenv('OWNER_ID')

        if not developer_id or not owner_id:
            self.stdout.write('❌ DEVELOPER_ID أو OWNER_ID مش موجودين في الـ environment')
            return

        admins = [
            {'id': developer_id.strip(), 'role': 'developer'},
            {'id': owner_id.strip(),     'role': 'owner'},
        ]

        for a in admins:
            uid       = a['id']
            full_name, pwd_hash = self.get_user_data(uid)

            # لو اليوزر موجود في Django — حدّث الباسورد منه
            try:
                profile = UserProfile.objects.get(agent_id=uid)
                if pwd_hash and is_password_usable(pwd_hash):
                    profile.user.password = pwd_hash
                    profile.user.save()
                    self.stdout.write(f'🔄 استعادة باسورد ID {uid} من SQL Server')
                else:
                    self.stdout.write(f'⚠️  ID {uid} موجود بالفعل — بدون تغيير')
                continue
            except UserProfile.DoesNotExist:
                pass

            # لو مش موجود — أنشئه
            if pwd_hash and is_password_usable(pwd_hash):
                # استخدم الـ hash المحفوظ
                new_user          = User(username=uid, first_name=full_name)
                new_user.password = pwd_hash
                new_user.save()
                is_first = False
                self.stdout.write(f'✅ تم إنشاء {a["role"]} — ID: {uid} — باسورد محفوظ من DB')
            else:
                # أول مرة — باسورد = ID وحفظ الـ hash في SQL
                new_user = User.objects.create_user(
                    username=uid, password=uid, first_name=full_name
                )
                self.save_hash_to_db(uid, new_user.password)
                is_first = True
                self.stdout.write(f'✅ تم إنشاء {a["role"]} — ID: {uid} — باسورد جديد محفوظ في SQL')

            UserProfile.objects.create(
                user=new_user,
                agent_id=uid,
                full_name=full_name,
                role=a['role'],
                is_first_login=is_first,
            )

        self.stdout.write('🎉 خلص!')
