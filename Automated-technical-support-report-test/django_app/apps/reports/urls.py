from django.urls import path
from . import views

urlpatterns = [
    path('',         views.reports_list, name='reports_list'),
    path('monthly/', views.monthly,      name='monthly'),
]