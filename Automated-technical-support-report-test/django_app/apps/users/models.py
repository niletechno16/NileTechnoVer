from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('owner',     'Owner'),
        ('admin',     'Admin'),
        ('agent',     'Agent'),
        ('visitor',   'Visitor'),
    ]

    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    agent_id       = models.CharField(max_length=50, unique=True)
    role           = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    is_first_login = models.BooleanField(default=True)
    full_name      = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return f"{self.user.username} — {self.role} — ID: {self.agent_id}"


# ─────────────────────────────────────────────
#  Notification Model
# ─────────────────────────────────────────────
class Notification(models.Model):

    TYPE_CHOICES = [
        ('login',            'تسجيل دخول'),
        ('password_changed', 'تغيير كلمة المرور'),
        ('resolved',         'تم حل'),
    ]

    recipient   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type  = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title       = models.CharField(max_length=200)
    body        = models.TextField(blank=True, default='')
    is_read     = models.BooleanField(default=False)
    # لو النوع resolved → بنحفظ agent_id و conv_id عشان نعمل link للتقرير
    agent_id    = models.CharField(max_length=50, blank=True, default='')
    conv_id     = models.CharField(max_length=100, blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] → {self.recipient.username}"
