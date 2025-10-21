from django.urls import path
from . import views

app_name = 'cashup'

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_shift, name='start'),
    path('do/', views.do_cashup, name='do'),
    path('close/', views.close_shift, name='close'),
]
