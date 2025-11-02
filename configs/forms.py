# configs/forms.py
from django import forms
from .models import ForecastConfig

class ForecastConfigForm(forms.ModelForm):
    class Meta:
        model = ForecastConfig
        # Lista de campos que serão exibidos no formulário
        fields = [
            'start_date',
            'frequencia',
            'dia_semana',
            'dia_mes',
            'forecast_horizon'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'frequencia': forms.Select(attrs={'class': 'form-select'}),
            'dia_semana': forms.Select(attrs={'class': 'form-select'}),
            'dia_mes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'forecast_horizon': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'start_date': 'Data Inicial',
            'frequencia': 'Frequência',
            'dia_semana': 'Dia da Semana',
            'dia_mes': 'Dia do Mês',
            'forecast_horizon': 'Horizonte (dias)',
        }
        help_texts = {
            'start_date': 'Data base para início das previsões.',
            'forecast_horizon': 'Número de dias para prever.',
        }
