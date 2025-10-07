from django.urls import path
from . import views

urlpatterns = [
    path('forecast/list/', views.ForecastListView.as_view(), name='forecast_list'),
    
]
