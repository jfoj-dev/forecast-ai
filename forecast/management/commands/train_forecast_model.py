from django.core.management.base import BaseCommand
from forecast.forecast_pipeline import load_outflows_to_df, train_model, save_model

class Command(BaseCommand):
    help = 'Treina o modelo de previsão e salva em disco'

    def handle(self, *args, **kwargs):
        print("Carregando dados...")
        df = load_outflows_to_df()
        print("Treinando modelo...")
        model, df_clean, mape = train_model(df)
        print(f"Salvando modelo em disco (MAPE={mape:.2f}%)")
        save_model(model)
        print("Modelo treinado e salvo com sucesso!")
