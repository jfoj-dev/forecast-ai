# forecast/train_forecast_model.py
import os
import numpy as np
import pandas as pd
from django.conf import settings
from joblib import dump
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from products.models import Product
from outflows.models import Outflow

MODEL_PATH = os.path.join(settings.BASE_DIR, "forecast", "trained_model.pkl")

def train_forecast_model():
    print("Iniciando treinamento do modelo de previsão de demanda...")

    products = Product.objects.all()
    if not products.exists():
        print("Nenhum produto encontrado.")
        return

    # Preparar DataFrame com features
    data = []
    for product in products:
        total_outflow = Outflow.objects.filter(product=product).aggregate(
            total=pd.NamedAgg(column='quantity', aggfunc='sum')
        )['total'] or 0

        promo_outflow = Outflow.objects.filter(product=product, promotion=True).aggregate(
            total=pd.NamedAgg(column='quantity', aggfunc='sum')
        )['total'] or 0

        data.append({
            'quantity': product.quantity or 0,
            'cost_price': product.cost_price or 0,
            'selling_price': product.selling_price or 0,
            'total_outflow': total_outflow,
            'promo_outflow': promo_outflow,
            # Aqui podemos colocar a variável alvo; para exemplo, vamos usar `total_outflow`
            'target': total_outflow
        })

    df = pd.DataFrame(data)
    X = df[['quantity', 'cost_price', 'selling_price', 'total_outflow', 'promo_outflow']]
    y = df['target']

    # Normalização
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Divisão treino/teste
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    # Treinar modelo
    model = XGBRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Avaliação
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    r2 = r2_score(y_test, y_pred)

    print(f"Modelo treinado com sucesso!")
    print(f"MAE: {mae:.2f},RMSE: {rmse:.2f},R²: {r2:.2f}")

    # Salvar modelo + scaler
    dump({"model": model, "scaler": scaler}, MODEL_PATH)
    print(f"Modelo salvo em: {MODEL_PATH}")

if __name__ == "__main__":
    train_forecast_model()
