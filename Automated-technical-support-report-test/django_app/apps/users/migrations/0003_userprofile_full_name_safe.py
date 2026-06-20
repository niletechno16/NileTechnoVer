from django.db import migrations, models


def add_full_name_if_missing(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'users_userprofile'
                      AND COLUMN_NAME = 'full_name'
                )
                ALTER TABLE users_userprofile ADD full_name NVARCHAR(200) NOT NULL DEFAULT ''
            """)
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_full_name_if_missing, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='userprofile',
                    name='full_name',
                    field=models.CharField(blank=True, default='', max_length=200),
                ),
            ],
            database_operations=[],
        ),
    ]
