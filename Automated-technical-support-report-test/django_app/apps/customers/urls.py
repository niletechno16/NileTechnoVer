from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.customers_list,  name='customers_list'),
    path('<int:customer_id>/',  views.customer_detail, name='customer_detail'),
]
