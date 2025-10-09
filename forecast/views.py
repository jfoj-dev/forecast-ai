# forecast/views.py
from django.views.generic import TemplateView
from django.views import View
from django.db.models import Sum, F
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import csv

from .models import Forecast
from outflows.models import Outflow
from .forecast_pipeline import run_pipeline, train_forecast_model


# -------------------------
# Lista de previsões
# -------------------------
class ForecastListView(TemplateView):
    template_name = "forecast_list.html"

    def get(self, request, *args, **kwargs):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        today = datetime.today().date()

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today + timedelta(days=30)

        forecasts = Forecast.objects.filter(date__range=(start_date, end_date)).select_related('product')

        # KPIs
        total_predicted = forecasts.aggregate(total=Sum('predicted_quantity'))['total'] or 0

        # MAPE médio (considera todos os produtos/dias, usa 0 se não houver vendas)
        mape_list = []
        for f in forecasts:
            real_qty = Outflow.objects.filter(
                product=f.product,
                created_at__date=f.date
            ).aggregate(total=Sum('quantity'))['total'] or 0

            mape_val = abs((real_qty - f.predicted_quantity) / real_qty) * 100 if real_qty > 0 else 0
            mape_list.append(mape_val)

        avg_mape = sum(mape_list) / len(mape_list) if mape_list else 0

        products_risk = forecasts.filter(product__quantity__lt=F('predicted_quantity')).count()
        last_update = forecasts.order_by('-date').first().date if forecasts.exists() else None

        # Promoções
        product_ids = forecasts.values_list('product', flat=True)
        promo_count = Outflow.objects.filter(product_id__in=product_ids, promotion=True).count()
        normal_count = Outflow.objects.filter(product_id__in=product_ids, promotion=False).count()

        # Dados para gráficos
        top_forecasts = forecasts.values('product__title') \
                                 .annotate(total_pred=Sum('predicted_quantity')) \
                                 .order_by('-total_pred')[:10]
        chart_labels = [f['product__title'] for f in top_forecasts]
        chart_data = [f['total_pred'] for f in top_forecasts]

        # Histórico vs previsão
        line_labels, line_real, line_forecast = [], [], []
        date_cursor = start_date
        while date_cursor <= end_date:
            daily_forecasts = forecasts.filter(date=date_cursor)
            line_labels.append(date_cursor.strftime("%d/%m"))

            daily_real = sum(
                Outflow.objects.filter(product=f.product, created_at__date=date_cursor).aggregate(total=Sum('quantity'))['total'] or 0
                for f in daily_forecasts
            )
            daily_pred = daily_forecasts.aggregate(total=Sum('predicted_quantity'))['total'] or 0

            line_real.append(daily_real)
            line_forecast.append(daily_pred)

            date_cursor += timedelta(days=1)

        # Heatmap
        heatmap = []
        for month in range(1, 13):
            month_sum = forecasts.filter(date__month=month).aggregate(total=Sum('predicted_quantity'))['total'] or 0
            heatmap.append(month_sum)

        context = {
            'forecasts': forecasts,
            'start_date': start_date,
            'end_date': end_date,
            'total_predicted': total_predicted,
            'avg_mape': round(avg_mape, 2),
            'products_risk': products_risk,
            'last_update': last_update,
            'promo_impact': 0,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'line_labels': line_labels,
            'line_real': line_real,
            'line_forecast': line_forecast,
            'heatmap': heatmap,
            'promo_count': promo_count,
            'normal_count': normal_count,
        }

        return self.render_to_response(context)


# -------------------------
# Gerar previsões
# -------------------------
class GenerateForecastView(View):
    def post(self, request, *args, **kwargs):
        try:
            result = run_pipeline()  # função que gera e salva previsões
            return JsonResponse({"success": True, "message": f"{result} previsões geradas com sucesso!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


# -------------------------
# Exportar CSV
# -------------------------
class ExportForecastCSVView(View):
    def get(self, request, *args, **kwargs):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        today = datetime.today().date()
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today + timedelta(days=30)

        forecasts = Forecast.objects.filter(date__range=(start_date, end_date)).select_related('product')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="forecast_{start_date}_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Produto', 'Data', 'Previsto', 'Estoque', 'MAPE'])
        for f in forecasts:
            real_qty = Outflow.objects.filter(
                product=f.product,
                created_at__date=f.date
            ).aggregate(total=Sum('quantity'))['total'] or 0
            mape_val = abs((real_qty - f.predicted_quantity) / real_qty * 100) if real_qty > 0 else 0
            writer.writerow([
                f.product.title,
                f.date,
                f.predicted_quantity,
                f.product.quantity,
                round(mape_val, 2)
            ])

        return response


# -------------------------
# Treinar modelo via AJAX
# -------------------------
@method_decorator(csrf_exempt, name='dispatch')
class TrainModelView(View):
    def post(self, request, *args, **kwargs):
        try:
            metrics = train_forecast_model()
            if metrics:
                message = (f"Modelo treinado! R²: {metrics['r2']:.2f}, "
                           f"RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}, "
                           f"MAPE: {metrics['mape']:.2f}%")
            else:
                message = "Treinamento não foi executado (dados insuficientes)."
            return JsonResponse({"success": True, "message": message})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
