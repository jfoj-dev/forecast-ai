from django.shortcuts import render, redirect
from django.urls import reverse
from .models import ForecastConfig
from .forms import ForecastConfigForm
from forecast.forecast_pipeline import run_pipeline

def config_list_view(request):
    """
    Exibe a tela de configuração e salva alterações.
    """
    # Busca a última configuração ou cria um objeto vazio
    config = ForecastConfig.objects.order_by('-created_at').first()

    if request.method == 'POST':
        form = ForecastConfigForm(request.POST, instance=config)
        
        if form.is_valid():
            # Não salva ainda para ajustar campos manualmente
            config = form.save(commit=False)
            
            # Corrige o checkbox: True se marcado, False se não
            config.include_promotions = 'include_promotions' in request.POST
            
            config.save()  # Salva no banco
            
            # Roda o pipeline passando a config atualizada
            run_pipeline(config)
            
            # Redireciona para a mesma página para evitar reenvio do POST
            return redirect(reverse('config_list'))
    
    else:
        form = ForecastConfigForm(instance=config)

    return render(request, 'configs/config_list.html', {'form': form, 'config': config})
