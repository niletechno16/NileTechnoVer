"""
views.py — تسجيل الدخول والخروج وتغيير الباسورد.
كل التحقق من الهوية يمشي عبر MSSQLAuthBackend — لا SQLite، لا User.objects.
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from db_connection import get_connection

log = logging.getLogger(__name__)


# ──────────────── helpers للصلاحيات ────────────────

def get_role(user):
    return getattr(user, 'role', None)

def is_high_level(user):
    return get_role(user) in ('developer', 'owner')

def is_manager_level(user):
    return get_role(user) in ('developer', 'owner', 'admin', 'agent')


# ──────────────── LOGIN ────────────────

def login_view(request):
    if request.method == 'POST':
        username = (request.POST.get('username') or request.POST.get('agent_id', '')).strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user, backend='apps.users.backends.MSSQLAuthBackend')
            if getattr(user, 'is_first_login', False):
                return redirect('change_password')
            return redirect('home')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')

    return render(request, 'users/login.html')


# ──────────────── CHANGE PASSWORD ────────────────

@login_required
def change_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm      = request.POST.get('confirm_password', '').strip()

        if new_password != confirm:
            messages.error(request, 'كلمات المرور غير متطابقة')
        elif len(new_password) < 6:
            messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
        else:
            new_hash = make_password(new_password)
            try:
                conn   = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users_Details_byA SET phone = %s WHERE user_id = %s",
                    (new_hash, request.user.agent_id)
                )
                conn.commit()
                conn.close()
                messages.success(request, 'تم تغيير كلمة المرور بنجاح ✅')
                return redirect('home')
            except Exception as e:
                log.error("Change password SQL error: %s", e)
                messages.error(request, 'حدث خطأ أثناء حفظ كلمة المرور')

    return render(request, 'users/change_password.html', {
        'agent_id':  getattr(request.user, 'agent_id', ''),
        'full_name': getattr(request.user, 'full_name', ''),
    })


# ──────────────── PROFILE ────────────────

@login_required
def profile(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'change_password':
            old_password = request.POST.get('old_password', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm      = request.POST.get('confirm_password', '').strip()

            # تحقق من الباسورد القديم
            check_user = authenticate(request, username=request.user.agent_id, password=old_password)
            if not check_user:
                messages.error(request, 'كلمة المرور الحالية غير صحيحة')
            elif new_password != confirm:
                messages.error(request, 'كلمات المرور الجديدة غير متطابقة')
            elif len(new_password) < 6:
                messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
            else:
                new_hash = make_password(new_password)
                try:
                    conn   = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users_Details_byA SET phone = %s WHERE user_id = %s",
                        (new_hash, request.user.agent_id)
                    )
                    conn.commit()
                    conn.close()
                    messages.success(request, 'تم تغيير كلمة المرور بنجاح ✅')
                except Exception as e:
                    log.error("Profile change password SQL error: %s", e)
                    messages.error(request, 'حدث خطأ أثناء الحفظ')
            return redirect('profile')

    return render(request, 'users/profile.html', {
        'role':       get_role(request.user),
        'is_manager': is_manager_level(request.user),
        'agent_id':   getattr(request.user, 'agent_id', ''),
    })


# ──────────────── MANAGE USERS ────────────────

@login_required
def manage_users(request):
    if not is_high_level(request.user):
        return redirect('home')

    sql_users = []
    registered_ids = set()

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # كل اليوزرين من SQL
        cursor.execute("SELECT user_id, user_name FROM users_Details_byA WHERE user_type = 2")
        all_rows = cursor.fetchall()

        # اللي عندهم hash (يعني سجّلوا) 
        cursor.execute(
            "SELECT user_id FROM users_Details_byA WHERE user_type = 2 AND phone IS NOT NULL AND phone != ''"
        )
        registered_ids = {str(r[0]).strip() for r in cursor.fetchall()}
        conn.close()

        for row in all_rows:
            uid  = str(row[0]).strip()
            name = (row[1] or uid).strip()
            sql_users.append({
                'id':            uid,
                'name':          name,
                'is_registered': uid in registered_ids,
            })

    except Exception as e:
        messages.error(request, f'خطأ في الاتصال بقاعدة البيانات: {e}')

    if request.method == 'POST':
        agent_id = request.POST.get('agent_id', '').strip()
        role     = request.POST.get('role', 'agent')

        if not agent_id:
            messages.error(request, 'الـ ID مطلوب')
        else:
            try:
                conn   = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users_Details_byA SET role = %s WHERE user_id = %s",
                    (role, agent_id)
                )
                conn.commit()
                conn.close()
                messages.success(request, f'✅ تم تحديث الصلاحية للـ ID: {agent_id}')
            except Exception as e:
                messages.error(request, f'خطأ: {e}')
        return redirect('manage_users')

    return render(request, 'users/manage.html', {
        'sql_users':    sql_users,
        'is_manager':   True,
    })


# ──────────────── CHANGE ROLE ────────────────

@login_required
def change_role(request, user_id):
    if not is_high_level(request.user):
        return redirect('home')

    if request.method == 'POST':
        new_role = request.POST.get('role')
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users_Details_byA SET role = %s WHERE user_id = %s",
                (new_role, str(user_id))
            )
            conn.commit()
            conn.close()
            messages.success(request, 'تم تغيير الصلاحية')
        except Exception as e:
            messages.error(request, f'خطأ: {e}')

    return redirect('manage_users')


# ──────────────── LOGOUT ────────────────

def logout_view(request):
    logout(request)
    return redirect('login')
