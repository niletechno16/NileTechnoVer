from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    label = 'dashboard'

    def ready(self):
        # شغّل الـ keep-alive thread لما Django يبدأ
        import keep_alive
        keep_alive.start()
