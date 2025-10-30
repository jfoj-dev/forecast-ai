from django.views.generic import TemplateView
from django.views import View
from django.db.models import Sum, F
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from collections import defaultdict
import csv

from .models import Forecast
from outflows.models import Outflow
from .forecast_pipeline import run_pipeline, train_forecast_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


# -------------------------
# LISTA DE PREVISÕES
# -------------------------
class ForecastListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "forecast_list.html"
    permission_required = 'forecasts.view_forecast'

    def get(self, request, *args, **kwargs):
        # -------------------------
        # Filtros de período
        # -------------------------
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        today = datetime.today().date()

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today + timedelta(days=30)

        forecasts = Forecast.objects.filter(date__range=(start_date, end_date)).select_related('product')

        # -------------------------
        # Calcular MAPE individual e agrupar por data
        # -------------------------
        forecasts_by_date = defaultdict(list)
        mape_list = []

        for f in forecasts:
            real_qty = Outflow.objects.filter(
                product=f.product,
                created_at__date=f.date
            ).aggregate(total=Sum('quantity'))['total'] or 0

            # 🔹 MAPE seguro
            if real_qty == 0 and f.predicted_quantity == 0:
                f.daily_mape = 0.0
            elif real_qty == 0:
                f.daily_mape = None
            else:
                diff = abs(f.predicted_quantity - real_qty)
                f.daily_mape = round((diff / real_qty) * 100, 2) if diff >= 0.01 else 0.0
                mape_list.append(f.daily_mape)

            forecasts_by_date[f.date].append(f)

        forecasts_by_date = dict(sorted(forecasts_by_date.items()))

        # -------------------------
        # KPIs principais
        # -------------------------
        total_predicted = forecasts.aggregate(total=Sum('predicted_quantity'))['total'] or 0
        avg_mape = round(sum(mape_list) / len(mape_list), 2) if mape_list else 0
        products_risk = forecasts.filter(product__quantity__lt=F('predicted_quantity')).count()
        last_update = forecasts.order_by('-date').first().date if forecasts.exists() else None

        # -------------------------
        # Impacto de promoções
        # -------------------------
        product_ids = forecasts.values_list('product', flat=True)
        promo_qty = Outflow.objects.filter(product_id__in=product_ids, promotion=True).aggregate(total=Sum('quantity'))['total'] or 0
        normal_qty = Outflow.objects.filter(product_id__in=product_ids, promotion=False).aggregate(total=Sum('quantity'))['total'] or 0

        if promo_qty + normal_qty > 0:
            promo_impact = round(promo_qty / (promo_qty + normal_qty) * 100, 2)
        else:
            promo_impact = 0

        # -------------------------
        # Dados para gráfico de barras (Top produtos previstos)
        # -------------------------
        top_forecasts = forecasts.values('product__title') \
                                 .annotate(total_pred=Sum('predicted_quantity')) \
                                 .order_by('-total_pred')[:10]
        chart_labels = [f['product__title'] for f in top_forecasts]
        chart_data = [f['total_pred'] for f in top_forecasts]

        # -------------------------
        # Histórico vs Previsão (gráfico de linha)
        # -------------------------
        line_labels, line_real, line_forecast = [], [], []
        date_cursor = start_date
        while date_cursor <= end_date:
            daily_forecasts = forecasts.filter(date=date_cursor)
            line_labels.append(date_cursor.strftime("%d/%m"))

            daily_real = sum(
                Outflow.objects.filter(
                    product=f.product,
                    created_at__date=date_cursor
                ).aggregate(total=Sum('quantity'))['total'] or 0
                for f in daily_forecasts
            )

            daily_pred = daily_forecasts.aggregate(total=Sum('predicted_quantity'))['total'] or 0
            line_real.append(daily_real)
            line_forecast.append(daily_pred)
            date_cursor += timedelta(days=1)

        # -------------------------
        # Heatmap (total previsto por mês)
        # -------------------------
        heatmap = []
        for month in range(1, 13):
            month_sum = forecasts.filter(date__month=month).aggregate(total=Sum('predicted_quantity'))['total'] or 0
            heatmap.append(month_sum)

        # -------------------------
        # Contexto final
        # -------------------------
        context = {
            'forecasts_by_date': forecasts_by_date,
            'start_date': start_date,
            'end_date': end_date,
            'total_predicted': total_predicted,
            'avg_mape': avg_mape,
            'products_risk': products_risk,
            'last_update': last_update,
            'promo_impact': promo_impact,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'line_labels': line_labels,
            'line_real': line_real,
            'line_forecast': line_forecast,
            'heatmap': heatmap,
            'promo_count': promo_qty,
            'normal_count': normal_qty,
        }

        return self.render_to_response(context)


# -------------------------
# GERAR PREVISÕES
# -------------------------
class GenerateForecastView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            result = run_pipeline()
            return JsonResponse({"success": True, "message": f"{result} previsões geradas com sucesso!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


# -------------------------
# EXPORTAR CSV
# -------------------------
class ExportForecastCSVView(LoginRequiredMixin, View):
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

            # 🔹 MAPE seguro para CSV
            if real_qty == 0 and f.predicted_quantity == 0:
                mape_val = 0.0
            elif real_qty == 0:
                mape_val = None
            else:
                diff = abs(f.predicted_quantity - real_qty)
                mape_val = round((diff / real_qty) * 100, 2) if diff >= 0.01 else 0.0

            writer.writerow([
                f.product.title,
                f.date,
                f.predicted_quantity,
                f.product.quantity,
                mape_val if mape_val is not None else '-'
            ])

        return response


# -------------------------
# TREINAR MODELO VIA AJAX
# -------------------------
@method_decorator(csrf_exempt, name='dispatch')
class TrainModelView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            metrics = train_forecast_model()
            if metrics:
                message = (
                    f"Modelo treinado! R²: {metrics['r2']:.2f}, "
                    f"RMSE: {metrics['rmse']:.2f}, "
                    f"MAE: {metrics['mae']:.2f}, "
                    f"MAPE: {metrics['mape']:.2f}%"
                )
            else:
                message = "Treinamento não foi executado (dados insuficientes)."
            return JsonResponse({"success": True, "message": message})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
