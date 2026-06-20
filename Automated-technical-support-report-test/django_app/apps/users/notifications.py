"""
مساعد الإشعارات — كل الـ logic في ملف واحد
"""
from django.contrib.auth.models import User
from .models import Notification


def _get_high_level_users():
    """جيب Owner و Developer"""
    return User.objects.filter(
        profile__role__in=['owner', 'developer']
    ).select_related('profile')


def notify_login(user):
    """إشعار تسجيل الدخول → لليوزر نفسه + Owner + Developer"""
    name = user.profile.full_name or user.first_name or user.username
    title = f"تسجيل دخول: {name}"
    body  = f"تم تسجيل الدخول بـ ID: {user.profile.agent_id}"

    recipients = set()
    recipients.add(user)
    for u in _get_high_level_users():
        recipients.add(u)

    for recipient in recipients:
        # لو مش owner/developer → بس يشوف إشعار نفسه
        if recipient == user or recipient.profile.role in ['owner', 'developer']:
            Notification.objects.create(
                recipient=recipient,
                notif_type='login',
                title=title,
                body=body,
            )


def notify_password_changed(user):
    """إشعار تغيير الباسورد → لليوزر نفسه + Owner + Developer"""
    name = user.profile.full_name or user.first_name or user.username
    title = f"تغيير كلمة المرور: {name}"
    body  = f"تم تغيير كلمة المرور بنجاح للحساب: {user.profile.agent_id}"

    recipients = set()
    recipients.add(user)
    for u in _get_high_level_users():
        recipients.add(u)

    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            notif_type='password_changed',
            title=title,
            body=body,
        )


def notify_resolved(agent_id, agent_name, conv_id=''):
    """
    إشعار resolved → للأيجنت نفسه + Owner + Developer
    agent_id: string مثل '1234567890'
    conv_id:  رقم التقرير للـ link
    """
    title = f"تم حل تقرير: {agent_name}"
    body  = f"تم تصنيف تقريرك كـ (تم حل) — رقم المحادثة: {conv_id}" if conv_id else "تم تصنيف تقريرك كـ (تم حل)"

    recipients = set()

    # الأيجنت نفسه
    try:
        agent_user = User.objects.get(profile__agent_id=str(agent_id))
        recipients.add(agent_user)
    except User.DoesNotExist:
        pass

    # Owner + Developer
    for u in _get_high_level_users():
        recipients.add(u)

    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            notif_type='resolved',
            title=title,
            body=body,
            agent_id=str(agent_id),
            conv_id=str(conv_id) if conv_id else '',
        )
