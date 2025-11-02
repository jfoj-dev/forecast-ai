from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from app import views  # importa a view home corretamente

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('api/v1/', include('authentication.urls')),
    
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
    path('configs/', include('configs.urls')),
]
