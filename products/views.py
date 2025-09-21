from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from products.models import Product
from categories.models import Category
from brands.models import Brands
from . import forms

class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.GET.get('title')
        serie_number = self.request.GET.get('serie_number')
        category = self.request.GET.get('category')
        brand = self.request.GET.get('brand')

        if title:
            queryset = queryset.filter(title__icontains=title)
        if serie_number:
            queryset = queryset.filter(serie_number__icontains=serie_number)
        if category:
            queryset = queryset.filter(category_id=category)
        if brand:
            queryset = queryset.filter(brand_id=brand)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['brands'] = Brands.objects.all()
        return context

class ProductCreateView(CreateView):
    model = Product
    template_name = 'product_create.html'
    form_class = forms.ProductForm
    success_url = reverse_lazy('product_list')

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'

class ProductUpdateView(UpdateView):
    model = Product
    template_name = 'product_update.html'
    form_class = forms.ProductForm
    success_url = reverse_lazy('product_list')

class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product_delete.html'
    success_url = reverse_lazy('product_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(
                request,
                f'O produto "{self.object.title}" foi excluído com sucesso!'
            )
            return redirect(self.success_url)
        except ProtectedError:
            messages.error(
                request,
                f'Não é possível excluir o produto "{self.object.title}" pois ele está vinculado a algum evento ou registro.'
            )
            return redirect(self.success_url)

# --- Exclusão em massa ---
class ProductBulkDeleteView(View):
    def post(self, request, *args, **kwargs):
        selected_ids = request.POST.getlist('selected_products')
        if not selected_ids:
            messages.error(request, "Selecione pelo menos um produto para excluir.")
            return redirect(reverse_lazy('product_list'))

        products = Product.objects.filter(id__in=selected_ids)
        failed = []
        for product in products:
            try:
                product.delete()
            except ProtectedError:
                failed.append(product.title)

        if failed:
            messages.warning(
                request,
                f'Não foi possível excluir os seguintes produtos pois estão vinculados a algum registro: {", ".join(failed)}'
            )

        deleted_count = products.count() - len(failed)
        if deleted_count > 0:
            messages.success(request, f'{deleted_count} produto(s) excluído(s) com sucesso.')

        return redirect(reverse_lazy('product_list'))
