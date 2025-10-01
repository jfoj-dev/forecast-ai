from django import forms
from . import models

class OutflowForm(forms.ModelForm):
    class Meta:
        model = models.Outflow
        fields = ['product', 'quantity', 'promotion', 'description']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'promotion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'produto': 'Produto',
            'quantidade': 'Quantidade',
            'promotion': 'Promoção',
            'description': 'Descrição',
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        product = self.cleaned_data.get('product')

        if quantity > product.quantity:
            raise forms.ValidationError(
                f'A quantidade disponível em estoque para o produto {product.title} é de {product.quantity} unidades.'
            )
        return quantity    