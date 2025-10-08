from django.urls import path
from .views import ForecastListView, GenerateForecastView, ExportForecastCSVView

urlpatterns = [
    path('forecast/list/', ForecastListView.as_view(), name='forecast_list'),
    path('generate/', GenerateForecastView.as_view(), name='generate_forecast'),
    path('export/', ExportForecastCSVView.as_view(), name='export_forecast_csv'),
]
