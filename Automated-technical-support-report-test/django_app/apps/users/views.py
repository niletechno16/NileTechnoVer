from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import UserProfile, Notification
from .notifications import notify_login, notify_password_changed
from db_connection import get_connection


# ---------------- ROLES ----------------
def get_role(user):
    try:
        return user.profile.role
    except:
        return None

def is_high_level(user):
    return get_role(user) in ['developer', 'owner']

def is_manager_level(user):
    return get_role(user) in ['developer', 'owner', 'admin', 'agent']

def can_change_role(changer, target_role):
    changer_role = get_role(changer)
    protected = {'developer': ['owner'], 'owner': ['developer']}
    if changer_role in protected and target_role in protected[changer_role]:
        return False
    return True


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # دخول كزائر
        if action == 'visitor':
            visitor_user, created = User.objects.get_or_create(username='visitor')
            if created:
                visitor_user.set_password('visitor123')
                visitor_user.save()

            profile, profile_created = UserProfile.objects.get_or_create(
                user=visitor_user,
                defaults={
                    'agent_id': '0000000000',
                    'role': 'visitor',
                    'is_first_login': False,
                }
            )
            if not profile_created and profile.role != 'visitor':
                profile.role = 'visitor'
                profile.save()

            login(request, visitor_user)
            return redirect('home')

        # دخول عادي
        username = (request.POST.get('username') or request.POST.get('agent_id', '')).strip()
        password = request.POST.get('password', '').strip()

        import logging
        log = logging.getLogger(__name__)

        from django.contrib.auth.hashers import is_password_usable

        user = authenticate(request, username=username, password=password)

        if not user:
            try:
                profile = UserProfile.objects.get(agent_id=username)
                user = authenticate(request, username=profile.user.username, password=password)
            except (UserProfile.DoesNotExist, ValueError):
                pass

        # لو authenticate فشلت → دور في SQL وصلّح/أنشئ اليوزر
        if not user:
            try:
                conn   = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT user_id, user_name, phone FROM users_Details_byA WHERE user_id = %s AND user_type = 2",
                    (username,)
                )
                row = cursor.fetchone()
                conn.close()

                if row:
                    sql_id     = str(row[0]).strip()
                    sql_name   = (row[1] or '').strip()
                    saved_hash = row[2].strip() if row[2] else None

                    try:
                        dj_user = User.objects.get(username=sql_id)
                    except User.DoesNotExist:
                        dj_user = None

                    if saved_hash and is_password_usable(saved_hash):
                        if dj_user is None:
                            dj_user = User(username=sql_id, first_name=sql_name)
                        dj_user.password = saved_hash
                        dj_user.save()
                        is_first = False
                    else:
                        if dj_user is None:
                            dj_user = User.objects.create_user(
                                username=sql_id,
                                password=sql_id,
                                first_name=sql_name,
                            )
                        else:
                            dj_user.set_password(sql_id)
                            dj_user.save()
                        try:
                            conn2   = get_connection()
                            cursor2 = conn2.cursor()
                            cursor2.execute(
                                "UPDATE users_Details_byA SET phone = %s WHERE user_id = %s",
                                (dj_user.password, sql_id)
                            )
                            conn2.commit()
                            conn2.close()
                        except Exception as e:
                            log.warning("فشل حفظ الـ hash في SQL: %s", e)
                        is_first = True

                    profile, _ = UserProfile.objects.get_or_create(
                        agent_id=sql_id,
                        defaults={
                            'user':          dj_user,
                            'full_name':     sql_name,
                            'role':          'agent',
                            'is_first_login': is_first,
                        }
                    )

                    login_password = sql_id if is_first else password
                    user = authenticate(request, username=sql_id, password=login_password)
                    if user:
                        login(request, user)
                        if user.profile.role != 'visitor':
                            notify_login(user)
                        if is_first:
                            return redirect('change_password')
                        return redirect('home')
                    else:
                        log.error("authenticate فشلت للـ ID: %s", sql_id)
                        messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
                else:
                    log.info("ID %s مش موجود في SQL أو user_type مش 2", username)

            except Exception as e:
                log.error("خطأ في SQL أثناء auto-register: %s", e, exc_info=True)

        if user:
            login(request, user)
            if user.profile.role != 'visitor':
                notify_login(user)
            if user.profile.is_first_login:
                return redirect('change_password')
            return redirect('home')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')

    return render(request, 'users/login.html')


# ---------------- CHANGE PASSWORD (first login) ----------------
@login_required
def change_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm      = request.POST.get('confirm_password', '').strip()
        email        = request.POST.get('email', '').strip()

        error = False

        if new_password != confirm:
            messages.error(request, 'كلمات المرور غير متطابقة')
            error = True
        elif len(new_password) < 6:
            messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
            error = True

        if not error:
            request.user.set_password(new_password)

            if email:
                if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                    messages.error(request, 'هذا الإيميل مستخدم بالفعل')
                    error = True
                else:
                    request.user.email = email

        if not error:
            request.user.save()
            request.user.profile.is_first_login = False
            request.user.profile.save()
            update_session_auth_hash(request, request.user)

            # حفظ الـ hash الجديد في SQL Server
            try:
                conn   = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users_Details_byA SET phone = %s WHERE user_id = %s",
                    (request.user.password, request.user.profile.agent_id)
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

            # إشعار تغيير الباسورد
            notify_password_changed(request.user)

            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('home')

    return render(request, 'users/change_password.html', {
        'agent_id':  request.user.profile.agent_id,
        'full_name': request.user.profile.full_name or request.user.first_name,
    })


# ---------------- PROFILE ----------------
@login_required
def profile(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # ── تغيير الباسورد من صفحة البروفايل ──
        if action == 'change_password':
            old_password = request.POST.get('old_password', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm      = request.POST.get('confirm_password', '').strip()

            if not request.user.check_password(old_password):
                messages.error(request, 'كلمة المرور الحالية غير صحيحة')
            elif new_password != confirm:
                messages.error(request, 'كلمات المرور الجديدة غير متطابقة')
            elif len(new_password) < 6:
                messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)

                # ✅ تحديث الـ hash في SQL Server في عمود phone
                try:
                    conn   = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users_Details_byA SET phone = %s WHERE user_id = %s",
                        (request.user.password, request.user.profile.agent_id)
                    )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

                # إشعار تغيير الباسورد
                notify_password_changed(request.user)

                messages.success(request, 'تم تغيير كلمة المرور بنجاح ✅')
                return redirect('profile')

        # ── تغيير الإيميل ──
        elif action == 'change_email':
            new_email = request.POST.get('new_email', '').strip()
            if new_email:
                if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                    messages.error(request, 'هذا الإيميل مستخدم بالفعل')
                else:
                    request.user.email = new_email
                    request.user.save()
                    messages.success(request, 'تم تحديث البريد الإلكتروني ✅')
            return redirect('profile')

    return render(request, 'users/profile.html', {
        'role':       get_role(request.user),
        'is_manager': is_manager_level(request.user),
        'agent_id':   request.user.profile.agent_id,
    })


# ---------------- NOTIFICATIONS API (محمية - server side فقط) ----------------
@login_required
def notifications_api(request):
    """
    GET  → جيب الإشعارات الجديدة (مش مقروءة) للـ user الحالي
    POST → mark as read
    البيانات بتيجي من السيرفر مباشرة — مش في HTML مشفر
    """
    if request.method == 'POST':
        notif_id = request.POST.get('id')
        if notif_id:
            Notification.objects.filter(
                id=notif_id, recipient=request.user
            ).update(is_read=True)
        else:
            # mark all as read
            Notification.objects.filter(
                recipient=request.user, is_read=False
            ).update(is_read=True)
        return JsonResponse({'ok': True})

    # GET → إرجع الإشعارات للـ user ده بس
    notifs = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:30]

    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    data = []
    for n in notifs:
        data.append({
            'id':         n.id,
            'type':       n.notif_type,
            'title':      n.title,
            'body':       n.body,
            'is_read':    n.is_read,
            'agent_id':   n.agent_id,
            'conv_id':    n.conv_id,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({'notifications': data, 'unread_count': unread_count})


# ---------------- MANAGE USERS ----------------
@login_required
def manage_users(request):
    if not is_high_level(request.user):
        return redirect('home')

    sql_users = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name
            FROM users_Details_byA
            WHERE user_type = 2
        """)
        rows = cursor.fetchall()
        conn.close()

        registered_ids = set(
            UserProfile.objects.exclude(role='visitor')
                               .values_list('agent_id', flat=True)
        )

        for row in rows:
            uid  = str(row[0]).strip()
            name = row[1].strip() if row[1] else uid
            sql_users.append({
                'id':           uid,
                'name':         name,
                'is_registered': uid in registered_ids,
            })

    except Exception as e:
        messages.error(request, f'خطأ في الاتصال بقاعدة البيانات: {e}')

    if request.method == 'POST':
        agent_id  = request.POST.get('agent_id', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        role      = request.POST.get('role', 'agent')

        if not agent_id:
            messages.error(request, 'الـ ID مطلوب')
        elif UserProfile.objects.filter(agent_id=agent_id).exists():
            messages.error(request, 'هذا الـ ID مسجل بالفعل')
        else:
            new_user = User.objects.create_user(
                username=str(agent_id),
                password=str(agent_id),
                first_name=full_name,
            )
            UserProfile.objects.create(
                user=new_user,
                agent_id=agent_id,
                full_name=full_name,
                role=role,
                is_first_login=True,
            )
            messages.success(request, f'✅ تم تسجيل {full_name} — ID: {agent_id} — الباسورد المؤقت: {agent_id}')
            return redirect('manage_users')

    profiles = UserProfile.objects.select_related('user').exclude(role='visitor')

    return render(request, 'users/manage.html', {
        'profiles':     profiles,
        'sql_users':    sql_users,
        'is_manager':   True,
        'role_choices': UserProfile.ROLE_CHOICES,
    })


# ---------------- CHANGE ROLE ----------------
@login_required
def change_role(request, user_id):
    if not is_high_level(request.user):
        return redirect('home')

    if request.method == 'POST':
        new_role = request.POST.get('role')
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            if can_change_role(request.user, profile.role):
                profile.role = new_role
                profile.save()
                messages.success(request, 'تم تغيير الصلاحية')
            else:
                messages.error(request, 'غير مسموح بتغيير صلاحية هذا المستخدم')
        except UserProfile.DoesNotExist:
            messages.error(request, 'المستخدم غير موجود')

    return redirect('manage_users')


# ---------------- CHECK RESOLVED (background poll) ----------------
@login_required
def check_resolved_api(request):
    """
    GET → يتحقق من تقارير الأيجنت الحالي ويولّد إشعارات resolved جديدة لو مش موجودة
    بيتعمله poll من base.html كل 60 ثانية — مش مرتبط بصفحة معينة

    المنطق:
    - أول استدعاء في الـ session → نسجّل الـ baseline (conv_ids الموجودة حالياً) ومنعملش إشعارات
    - الاستدعاءات اللي بعدها → بس لو conv_id جديد مش في الـ baseline ومش في الـ DB
    """
    from .notifications import notify_resolved
    import datetime
    import calendar as cal

    user = request.user
    try:
        agent_id = str(user.profile.agent_id)
    except Exception:
        return JsonResponse({'ok': False})

    # نجيب تقارير الشهر الحالي فقط
    today      = datetime.date.today()
    date_from  = today.replace(day=1).strftime('%Y-%m-%d')
    last_day   = cal.monthrange(today.year, today.month)[1]
    date_to    = today.replace(day=last_day).strftime('%Y-%m-%d')

    session_key = f'resolved_baseline_{agent_id}'

    new_count = 0
    try:
        conn   = get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            "EXEC Get_Reports_byA @FromDate = %s, @ToDate = %s",
            (date_from, date_to)
        )
        raw = cursor.fetchall() or []
        conn.close()

        # جيب كل conv_ids المحلولة حالياً
        current_resolved = set()
        agent_name = None
        names_map  = {}
        for r in raw:
            if str(r.get('agent_id', '')) != agent_id:
                continue
            if not r.get('classification', '').startswith('تم حل'):
                continue
            cid = str(r.get('conv_id', ''))
            if cid:
                current_resolved.add(cid)
            if not agent_name:
                agent_name = r.get('agent_name', agent_id)
            names_map[cid] = r.get('agent_name', agent_id)

        # أول استدعاء في الـ session → سجّل الـ baseline بس
        if session_key not in request.session:
            request.session[session_key] = list(current_resolved)
            request.session.modified = True
            return JsonResponse({'ok': True, 'new': 0, 'baseline': True})

        baseline = set(request.session[session_key])

        for conv_id in current_resolved:
            # لو كان موجود في الـ baseline → قديم، تجاهل
            if conv_id in baseline:
                continue

            # لو اتبعت إشعار قبل كده في الـ DB → تجاهل
            already = Notification.objects.filter(
                notif_type='resolved',
                agent_id=agent_id,
                body__contains=conv_id,
            ).exists()

            if not already:
                notify_resolved(agent_id, names_map.get(conv_id, agent_id), conv_id)
                new_count += 1

        # حدّث الـ baseline بالجديد عشان المرة الجاية
        request.session[session_key] = list(current_resolved)
        request.session.modified = True

    except Exception:
        pass

    return JsonResponse({'ok': True, 'new': new_count})


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect('login')
