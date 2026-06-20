from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_id', models.CharField(max_length=50, unique=True)),
                ('role', models.CharField(
                    choices=[
                        ('developer', 'Developer'),
                        ('owner',     'Owner'),
                        ('admin',     'Admin'),
                        ('agent',     'Agent'),
                        ('visitor',   'Visitor'),
                    ],
                    default='agent', max_length=20
                )),
                ('is_first_login', models.BooleanField(default=True)),
                ('full_name', models.CharField(blank=True, default='', max_length=200)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to='auth.user'
                )),
            ],
        ),
    ]
