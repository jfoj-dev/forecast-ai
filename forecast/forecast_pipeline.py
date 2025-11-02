import os
import numpy as np
import pandas as pd
from datetime import timedelta
from django.conf import settings
from joblib import dump, load
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from products.models import Product
from outflows.models import Outflow
from django.db.models import Sum
from .models import Forecast

MODEL_PATH = os.path.join(settings.BASE_DIR, "forecast", "trained_model.pkl")


# -------------------------
# Treina o modelo de previsão diária
# -------------------------
def train_forecast_model(include_promotions=True):
    products = Product.objects.all()
    if not products.exists():
        return None

    data = []
    for product in products:
        total_outflow = Outflow.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
        promo_outflow = 0
        if include_promotions:
            promo_outflow = Outflow.objects.filter(product=product, promotion=True).aggregate(total=Sum('quantity'))['total'] or 0

        days = max(Outflow.objects.filter(product=product).count(), 1)
        daily_target = total_outflow / days  # target diário

        data.append({
            'quantity': product.quantity or 0,
            'cost_price': product.cost_price or 0,
            'selling_price': product.selling_price or 0,
            'total_outflow': total_outflow,
            'promo_outflow': promo_outflow,
            'target': daily_target
        })

    df = pd.DataFrame(data)
    if df.empty:
        return None

    features = ['quantity', 'cost_price', 'selling_price', 'total_outflow']
    if include_promotions:
        features.append('promo_outflow')
    else:
        df['promo_outflow'] = 0
        features.append('promo_outflow')

    X = df[features]
    y = df['target']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / np.where(y_test != 0, y_test, 1))) * 100

    dump({"model": model, "scaler": scaler}, MODEL_PATH)

    return {"r2": r2, "rmse": rmse, "mae": mae, "mape": mape}


# -------------------------
# Executa pipeline de previsão considerando configuração
# -------------------------
def run_pipeline(config):
    """
    Executa a previsão com base na configuração passada.
    """
    if not config:
        return 0

    # Treina modelo se não existir
    if not os.path.exists(MODEL_PATH):
        train_forecast_model(include_promotions=config.include_promotions)

    model_data = load(MODEL_PATH)
    model = model_data['model']
    scaler = model_data['scaler']

    products = Product.objects.all()
    if not products.exists():
        return 0

    data_list = []
    for product in products:
        total_outflow = Outflow.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
        promo_outflow = 0
        if config.include_promotions:
            promo_outflow = Outflow.objects.filter(product=product, promotion=True).aggregate(total=Sum('quantity'))['total'] or 0

        data_list.append({
            'product_id': product.id,
            'quantity': product.quantity or 0,
            'cost_price': product.cost_price or 0,
            'selling_price': product.selling_price or 0,
            'total_outflow': total_outflow,
            'promo_outflow': promo_outflow
        })

    df = pd.DataFrame(data_list)

    # Seleção de features
    features = ['quantity', 'cost_price', 'selling_price', 'total_outflow']
    if config.include_promotions:
        features.append('promo_outflow')
    else:
        df['promo_outflow'] = 0
        features.append('promo_outflow')

    X_scaled = scaler.transform(df[features])
    df['predicted_quantity'] = model.predict(X_scaled)

    forecast_count = 0
    start_date = config.start_date
    horizon_days = config.forecast_horizon

    # Map dias da semana
    dia_map = {
        'segunda': 0, 'terca': 1, 'quarta': 2, 'quinta': 3,
        'sexta': 4, 'sabado': 5, 'domingo': 6
    }

    # Cria ou atualiza previsões
    for _, row in df.iterrows():
        for day_offset in range(horizon_days):
            date = start_date + timedelta(days=day_offset)

            # Lógica de frequência
            if config.frequencia == 'diaria':
                pass
            elif config.frequencia == 'semanal':
                if date.weekday() != dia_map.get(config.dia_semana, 0):
                    continue
            elif config.frequencia == 'mensal':
                if config.dia_mes and date.day != config.dia_mes:
                    continue
            else:
                continue

            Forecast.objects.update_or_create(
                product_id=row['product_id'],
                date=date,
                defaults={'predicted_quantity': max(0, int(row['predicted_quantity']))}
            )
            forecast_count += 1

    return forecast_count
