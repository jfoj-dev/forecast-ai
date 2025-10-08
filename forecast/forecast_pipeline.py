from datetime import datetime, timedelta
import pandas as pd
import joblib
from outflows.models import Outflow
from products.models import Product
from .models import Forecast
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
import numpy as np

# -------------------------
# Pipeline de previsão
# -------------------------
def run_pipeline():
    """
    Gera previsões de demanda e salva no modelo Forecast.
    Para produtos sem histórico suficiente, gera previsões zeradas.
    """
    products = Product.objects.all()
    forecast_objects = []

    for product in products:
        outflows = Outflow.objects.filter(product=product).order_by('created_at')

        if outflows.exists():
            # Cria DataFrame
            data = pd.DataFrame(list(outflows.values('created_at', 'quantity', 'promotion')))
            data['created_at'] = pd.to_datetime(data['created_at'])
            data = data.set_index('created_at')

            # Resample diário e preencher lacunas
            data = data.resample('D').sum()
            data['promotion'] = data['promotion'].astype(int)

            # Features e target
            X = data[['promotion']]
            y = data['quantity']

            # Treina modelo se houver dados suficientes
            if len(y) > 5:
                model = XGBRegressor(n_estimators=100, random_state=42)
                model.fit(X, y)
                # Previsão para os próximos 30 dias
                future_dates = pd.date_range(datetime.today(), periods=30)
                X_future = pd.DataFrame({'promotion': [0]*30}, index=future_dates)
                y_pred = model.predict(X_future)
            else:
                # Poucos dados → gera zeros
                future_dates = pd.date_range(datetime.today(), periods=30)
                y_pred = [0]*30
        else:
            # Sem histórico → gera zeros
            future_dates = pd.date_range(datetime.today(), periods=30)
            y_pred = [0]*30

        # Cria ou atualiza previsões (evita duplicidade)
        for date, pred in zip(future_dates, y_pred):
            Forecast.objects.update_or_create(
                product=product,
                date=date,
                defaults={'predicted_quantity': max(0, round(pred))}
            )
            forecast_objects.append(1)

    return len(forecast_objects)

# -------------------------
# Treinamento do modelo
# -------------------------
def train_forecast_model():
    """
    Treina modelo global de previsão de demanda e retorna métricas.
    """
    outflows = Outflow.objects.all()
    if not outflows.exists():
        return None

    df = pd.DataFrame(list(outflows.values('product_id', 'quantity', 'promotion', 'created_at')))
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['promotion'] = df['promotion'].astype(int)

    X = df[['product_id', 'promotion']]
    y = df['quantity']

    if len(X) < 5:
        return None  # dados insuficientes

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    metrics = {
        'mae': mean_absolute_error(y_test, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
        'r2': r2_score(y_test, y_pred)
    }

    # Salva modelo
    joblib.dump(model, 'forecast/trained_model.pkl')

    return metrics
