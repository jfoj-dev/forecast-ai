from django.db import models
from products.models import Product

class Forecast(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='forecasts')
    date = models.DateField()  # dia da previsão
    predicted_quantity = models.FloatField()
    mape = models.FloatField(null=True, blank=True)  # erro médio da previsão
    daily_mape = models.FloatField(null=True, blank=True)  # MAPE individual por dia
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'date')
        ordering = ['product', 'date']

    def __str__(self):
        return f"{self.product.title} - {self.date}"
