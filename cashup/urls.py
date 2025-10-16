from django.urls import path
from . import views

app_name = 'cashup'

urlpatterns = [
    path('', views.index, name='index'),
]
