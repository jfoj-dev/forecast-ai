from django import forms
from . import models

class InflowForm(forms.ModelForm):
    class Meta:
        model = models.Inflow
        fields = ['supplier', 'product', 'quantity', 'cost_price', 'description']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'supplier': 'Fornecedor',
            'produto': 'Produto',
            'quantidade': 'Quantidade',
            'cost_price': 'Preço de Custo',
            'description': 'Descrição',
        }