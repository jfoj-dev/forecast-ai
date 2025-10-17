from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from .models import Product
from categories.models import Category
from brands.models import Brands
from . import forms
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# -------------------- LISTAGEM --------------------
class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 10
    permission_required = 'products.view_product'

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

# -------------------- CRIAÇÃO --------------------
class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    template_name = 'product_create.html'
    form_class = forms.ProductForm
    success_url = reverse_lazy('product_list')
    permission_required = 'products.add_product'

    def form_valid(self, form):
        # Ao criar, last_cost_price recebe o valor inicial de cost_price
        form.instance.last_cost_price = form.cleaned_data['cost_price']
        return super().form_valid(form)

# -------------------- DETALHE --------------------
class ProductDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Product
    template_name = 'product_detail.html'
    permission_required = 'products.view_product'

# -------------------- ATUALIZAÇÃO --------------------
class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    template_name = 'product_update.html'
    form_class = forms.ProductForm
    success_url = reverse_lazy('product_list')
    permission_required = 'products.add_product'

    def form_valid(self, form):
        # Se o checkbox update_cost estiver marcado
        if self.request.POST.get('update_cost'):
            # Atualiza last_cost_price com o valor antigo
            form.instance.last_cost_price = form.instance.cost_price
            # cost_price será atualizado com o valor enviado no form
            return super().form_valid(form)
        else:
            # Mantém o custo atual sem alterações
            form.instance.cost_price = form.instance.cost_price
            return super().form_valid(form)

# -------------------- EXCLUSÃO --------------------
class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = 'product_delete.html'
    success_url = reverse_lazy('product_list')
    permission_required = 'productss.delete_product'

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
                f'Não é possível excluir o produto "{self.object.title}" pois está vinculado a algum registro.'
            )
            return redirect(self.success_url)

# -------------------- EXCLUSÃO EM MASSA --------------------
class ProductBulkDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
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
