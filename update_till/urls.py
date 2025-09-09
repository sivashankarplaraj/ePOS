from django.urls import path
from . import views

urlpatterns = [
    path('', views.update_till_import, name='update_till_home'),
    path('import/', views.update_till_import, name='update_till_import'),
]