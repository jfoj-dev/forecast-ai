from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from outflows.models import Outflow
from forecast.models import Forecast
from django.db import models

# -------------------------
# Atualiza quantidade do produto
# -------------------------
@receiver(post_save, sender=Outflow)
def update_product_quantity(sender, instance, created, **kwargs):
    if created:
        if instance.quantity > 0:
            product = instance.product
            product.quantity -= instance.quantity
            product.save()


# -------------------------
# Atualiza MAPE diário da Forecast
# -------------------------
@receiver([post_save, post_delete], sender=Outflow)
def update_forecast_mape(sender, instance, **kwargs):
    """
    Atualiza o daily_mape da Forecast relacionada ao produto e data
    sempre que um Outflow é criado, atualizado ou deletado.
    """
    product = instance.product
    date = instance.created_at.date()  # assume que created_at é DateTimeField

    try:
        forecast = Forecast.objects.get(product=product, date=date)
    except Forecast.DoesNotExist:
        return  # não existe previsão para essa data, nada a fazer

    # Soma total de saídas reais do produto na data da previsão
    real_qty = Outflow.objects.filter(
        product=product,
        created_at__date=date
    ).aggregate(total=models.Sum('quantity'))['total'] or 0

    # Calcula MAPE se houver vendas reais
    if real_qty > 0:
        forecast.daily_mape = abs((real_qty - forecast.predicted_quantity) / real_qty) * 100
    else:
        forecast.daily_mape = None

    forecast.save()
