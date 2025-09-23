from django.db import models
from products.models import Product
from suppliers.models import Supplier

class Inflow(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='inflows')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='inflows')
    quantity = models.IntegerField()
    cost_price = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Atualiza o preço de custo e salva o último custo
        self.product.last_cost_price = self.product.cost_price
        self.product.cost_price = self.cost_price
        self.product.save()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.product)
