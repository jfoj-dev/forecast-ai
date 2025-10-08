# forecast/forecast_pipeline.py
from datetime import datetime, timedelta
import random
from .models import Forecast
from products.models import Product

def run_pipeline():
    """
    Função que simula a geração de previsões de demanda para todos os produtos
    e salva no modelo Forecast. Retorna o número de previsões geradas.
    """
    # Definir horizonte de previsão (30 dias a partir de hoje)
    today = datetime.today().date()
    horizon_days = 30

    # Obter todos os produtos
    products = Product.objects.all()
    if not products.exists():
        return 0

    total_generated = 0

    for product in products:
        for day_offset in range(horizon_days):
            forecast_date = today + timedelta(days=day_offset)

            # Simular quantidade prevista (aleatório baseado no estoque atual)
            predicted_quantity = max(0, int(product.quantity * random.uniform(0.8, 1.5)))

            # Simular MAPE aleatório
            mape = round(random.uniform(5, 20), 2)

            # Salvar ou atualizar previsão existente para o mesmo produto e data
            forecast_obj, created = Forecast.objects.update_or_create(
                product=product,
                date=forecast_date,
                defaults={
                    "predicted_quantity": predicted_quantity,
                    "mape": mape,
                }
            )
            total_generated += 1

    return total_generated
