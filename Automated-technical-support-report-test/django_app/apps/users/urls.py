from django.urls import path
from . import views

urlpatterns = [
    path('login/',           views.login_view,      name='login'),
    path('logout/',          views.logout_view,     name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/',         views.profile,         name='profile'),
    path('manage/',          views.manage_users,    name='manage_users'),
    path('change-role/<int:user_id>/', views.change_role, name='change_role'),
    # ✅ Notifications API
    path('notifications/', views.notifications_api, name='notifications_api'),
    # ✅ Background poll — يولّد إشعارات resolved جديدة في أي صفحة
    path('check-resolved/', views.check_resolved_api, name='check_resolved_api'),
]
