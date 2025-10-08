from django.urls import path
from .views import ForecastListView, GenerateForecastView, ExportForecastCSVView, TrainModelView

urlpatterns = [
    path('forecast/list/', ForecastListView.as_view(), name='forecast_list'),
    path('generate/', GenerateForecastView.as_view(), name='generate_forecast'),
    path('export/', ExportForecastCSVView.as_view(), name='export_forecast_csv'),
    path('forecast/train/', TrainModelView.as_view(), name='train_forecast_model'),  # rota para treinar modelo
]
