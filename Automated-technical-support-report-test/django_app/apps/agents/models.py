# from django.db import models
# from django.contrib.auth.models import User


# class UserProfile(models.Model):

#     ROLE_CHOICES = [
#         ('developer', 'Developer'),
#         ('owner',     'Owner'),
#         ('admin',     'Admin'),
#         ('agent',     'Agent'),
#         ('visitor',   'Visitor'),
#     ]

#     user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
#     phone_number   = models.CharField(max_length=20, unique=True)
#     role           = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
#     is_first_login = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.user.username} — {self.role}"

from django.db import models

# No models here