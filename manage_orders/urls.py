from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='manage_orders_index'),
    path('manage_orders/order/', views.order, name='manage_orders_order'),
    path('manage_orders/dashboard/', views.dashboard, name='manage_orders_dashboard'),
    path('api/prices', views.api_prices, name='mo_api_prices'),
    path('api/channels', views.api_channel_mappings, name='mo_api_channels'),
    # add path to manage_orders/app_prod_order.html
    path('manage_orders/app_prod_order/', views.app_prod_order, name='manage_orders_app_prod_order'),
    path('manage_orders/reports/', views.reports, name='manage_orders_reports'),
    path('manage_orders/kitchen/', views.kitchen_monitor, name='manage_orders_kitchen'),
    path('manage_orders/customer_basket/', views.customer_basket, name='manage_orders_customer_basket'),
    # API: menu structure (categories + items) for a given price band
    path('api/menu', views.api_menu, name='mo_api_menu'),
    # Lightweight APIs to reduce payloads
    path('api/menu/categories', views.api_menu_categories, name='mo_api_menu_categories'),
    path('api/menu/category/<int:group_id>/items', views.api_category_items, name='mo_api_category_items'),
    # API: options for a given product (P_CHOICE relationships)
    path('api/product/<int:prod_code>/options', views.api_product_options, name='mo_api_product_options'),
    path('api/product/<int:prod_code>/toppings', views.api_product_toppings, name='mo_api_product_toppings'),
    # Unified item detail (product or combo)
    path('api/item/<str:item_type>/<int:code>/detail', views.api_item_detail, name='mo_api_item_detail'),
    # API: submit order
    path('api/order/submit', views.api_submit_order, name='mo_api_submit_order'),
    path('api/paid-out', views.api_paid_out, name='mo_api_paid_out'),
    path('api/orders/summary', views.api_orders_summary, name='mo_api_orders_summary'),
    path('api/orders/pending', views.api_orders_pending, name='mo_api_orders_pending'),
    path('api/order/<int:order_id>/complete', views.api_order_complete, name='mo_api_order_complete'),
    path('api/order/<int:order_id>/pack', views.api_order_pack, name='mo_api_order_pack'),
    path('api/orders/completed', views.api_orders_completed, name='mo_api_orders_completed'),
    path('api/daily-sales', views.api_daily_sales, name='mo_api_daily_sales'),
    path('api/daily-sales-hourly', views.api_daily_sales_hourly, name='mo_api_daily_sales_hourly'),
    path('reports/export-daily-csvs', views.export_daily_csvs_zip, name='mo_export_daily_csvs_zip'),
]
