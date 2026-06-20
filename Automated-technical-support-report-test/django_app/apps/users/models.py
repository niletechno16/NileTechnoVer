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
