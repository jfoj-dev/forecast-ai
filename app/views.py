from django.shortcuts import render
from django.db.models import Sum, F, Q, FloatField
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
from products.models import Product
from outflows.models import Outflow

def home(request):
    # --------------------------------------------
    # 🔹 1. Filtro de período (Data Início e Fim)
    # --------------------------------------------
    data_inicio_str = request.GET.get("data_inicio")
    data_fim_str = request.GET.get("data_fim")

    if data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
        except ValueError:
            data_fim = datetime.now().date()
            data_inicio = data_fim - timedelta(days=30)
    else:
        data_fim = datetime.now().date()
        data_inicio = data_fim - timedelta(days=30)

    # --------------------------------------------
    # 🔹 2. Coleta de dados de produtos e saídas
    # --------------------------------------------
    produtos = Product.objects.all()
    outflows = Outflow.objects.filter(created_at__range=[data_inicio, data_fim])

    # --------------------------------------------
    # 🔹 3. Cálculos principais
    # --------------------------------------------
    total_produtos = produtos.count()

    custo_estoque = produtos.aggregate(
        total=Coalesce(Sum(F("quantity") * F("cost_price"), output_field=FloatField()), 0.0)
    )["total"]

    valor_estoque = produtos.aggregate(
        total=Coalesce(Sum(F("quantity") * F("selling_price"), output_field=FloatField()), 0.0)
    )["total"]

    lucro_estoque = valor_estoque - custo_estoque

    produtos_risco = produtos.annotate(
        qtd_vendida=Coalesce(
            Sum(
                "outflows__quantity",
                filter=Q(outflows__created_at__range=[data_inicio, data_fim]),
            ),
            0,
        )
    ).filter(qtd_vendida__gt=F("quantity")).count()

    promo_impact = 12.5

    last_update = outflows.order_by("-created_at").first()
    last_update = last_update.created_at.strftime("%d/%m/%Y %H:%M") if last_update else "-"

    periodo_anterior_inicio = data_inicio - (data_fim - data_inicio)
    periodo_anterior_fim = data_inicio

    vendas_atual = outflows.aggregate(total=Coalesce(Sum("quantity"), 0))["total"]
    vendas_anterior = Outflow.objects.filter(
        created_at__range=[periodo_anterior_inicio, periodo_anterior_fim]
    ).aggregate(total=Coalesce(Sum("quantity"), 0))["total"]

    monthly_growth = (
        round(((vendas_atual - vendas_anterior) / vendas_anterior) * 100, 2)
        if vendas_anterior > 0
        else 0
    )

    top_produtos = (
        produtos.annotate(
            qtd_vendida=Coalesce(
                Sum(
                    "outflows__quantity",
                    filter=Q(outflows__created_at__range=[data_inicio, data_fim]),
                ),
                0,
            ),
            lucro_estimado=Coalesce(
                (F("selling_price") - F("cost_price")) * F("quantity"),
                0,
                output_field=FloatField(),
            ),
        )
        .order_by("-qtd_vendida")[:20]
    )

    # --------------------------------------------
    # 🔹 4. Contexto para o template (corrigido)
    # --------------------------------------------
    contexto = {
        # 🔸 Envia as datas formatadas para manter nos inputs
        "data_inicio": data_inicio.strftime("%Y-%m-%d"),
        "data_fim": data_fim.strftime("%Y-%m-%d"),

        "total_produtos": total_produtos,
        "custo_estoque": custo_estoque,
        "valor_estoque": valor_estoque,
        "lucro_estoque": lucro_estoque,
        "products_risk": produtos_risco,
        "promo_impact": promo_impact,
        "last_update": last_update,
        "monthly_growth": monthly_growth,
        "top_produtos": top_produtos,
    }

    return render(request, "dashboard.html", contexto)
