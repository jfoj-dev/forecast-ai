from django.urls import path
from . import views

urlpatterns = [
    path('', views.config_list_view, name='config_list'),
]
