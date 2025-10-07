from django.views.generic import ListView
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Forecast

class ForecastListView(ListView):
    model = Forecast
    template_name = 'forecast_list.html'
    context_object_name = 'forecasts'
    paginate_by = 10

    def get_queryset(self):
        """
        Retorna as previsões filtradas por data inicial e final (caso informadas).
        Caso não sejam informadas, retorna previsões dos últimos 30 dias.
        """
        queryset = super().get_queryset()

        # Captura os parâmetros GET
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        # Define o intervalo de filtro
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(date__range=(start_date, end_date))
            except ValueError:
                pass  # Caso o formato de data seja inválido, ignora e usa o padrão
        else:
            # Padrão: últimos 30 dias
            today = timezone.now().date()
            thirty_days_ago = today - timedelta(days=30)
            queryset = queryset.filter(date__range=(thirty_days_ago, today))

        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        """
        Adiciona as datas ao contexto para reaparecerem no formulário e mostra estatísticas.
        """
        context = super().get_context_data(**kwargs)
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')

        # KPIs básicos de exemplo
        forecasts = context['forecasts']
        if forecasts.exists():
            context['avg_mape'] = round(forecasts.aggregate_avg('mape') or 0, 2)
            context['total_predicted'] = sum(f.value for f in forecasts)
        else:
            context['avg_mape'] = 0
            context['total_predicted'] = 0

        return context
