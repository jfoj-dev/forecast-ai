from django.contrib import admin
from django.urls import path, include
from app import views  # importa a view home corretamente

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Dashboard / página inicial
    path('', views.home, name='home'),

    # Rotas dos apps com prefixos
    path('brands/', include('brands.urls')),
    path('categories/', include('categories.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('inflows/', include('inflows.urls')),
    path('outflows/', include('outflows.urls')),
    path('products/', include('products.urls')),
    path('forecast/', include('forecast.urls')),
]
