from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='manage_orders_index'),
    path('manage_orders/order/', views.order, name='manage_orders_order'),
    path('api/prices', views.api_prices, name='mo_api_prices'),
]
