from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'cashup'

urlpatterns = [
    path('', views.index, name='index'),
    path('crew-login/', views.CrewLoginView.as_view(), name='crew_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('start/', views.start_shift, name='start'),
    path('do/', views.do_cashup, name='do'),
    path('close/', views.close_shift, name='close'),
    path('report/', views.report, name='report'),
]
