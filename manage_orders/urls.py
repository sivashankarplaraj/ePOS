from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='manage_orders_index'),
    path('manage_orders/order/', views.order, name='manage_orders_order'),
    path('manage_orders/dashboard/', views.dashboard, name='manage_orders_dashboard'),
    path('api/prices', views.api_prices, name='mo_api_prices'),
    # add path to manage_orders/app_prod_order.html
    path('manage_orders/app_prod_order/', views.app_prod_order, name='manage_orders_app_prod_order'),
    # API: menu structure (categories + items) for a given price band
    path('api/menu', views.api_menu, name='mo_api_menu'),
    # API: options for a given product (P_CHOICE relationships)
    path('api/product/<int:prod_code>/options', views.api_product_options, name='mo_api_product_options'),
    # Unified item detail (product or combo)
    path('api/item/<str:item_type>/<int:code>/detail', views.api_item_detail, name='mo_api_item_detail'),
    # API: submit order
    path('api/order/submit', views.api_submit_order, name='mo_api_submit_order'),
    path('api/orders/summary', views.api_orders_summary, name='mo_api_orders_summary'),
    path('api/orders/pending', views.api_orders_pending, name='mo_api_orders_pending'),
    path('api/order/<int:order_id>/complete', views.api_order_complete, name='mo_api_order_complete'),
]
