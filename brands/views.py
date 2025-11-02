from rest_framework import generics
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from . import models, forms, serializers
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class BrandListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = models.Brands
    template_name = 'brand_list.html'
    context_object_name = 'brands'
    paginate_by = 10
    permission_required = 'brands.view_brands'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class BrandCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = models.Brands
    template_name = 'brand_create.html'
    form_class = forms.BrandForm
    success_url = reverse_lazy('brand_list')
    permission_required = 'brands.add_brand'


class BrandDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = models.Brands
    template_name = 'brand_detail.html'
    permission_required = 'brands.view_brand'


class BrandUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = models.Brands
    template_name = 'brand_update.html'
    form_class = forms.BrandForm
    success_url = reverse_lazy('brand_list')
    permission_required = 'brands.change_brand'


class BrandDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = models.Brands
    template_name = 'brand_delete.html'
    success_url = reverse_lazy('brand_list')
    permission_required = 'brands.delete_brand'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(
                request,
                f'A marca "{self.object.name}" foi excluída com sucesso!'
            )
            return redirect(self.success_url)
        except ProtectedError:
            messages.error(
                request,
                f'Não é possível excluir a marca "{self.object.name}" pois ela está vinculada a um evento/produto.'
            )
            return redirect(self.success_url)

class BrandCreateListAPIView(generics.ListCreateAPIView):
    queryset = models.Brands.objects.all()
    serializer_class = serializers.BrandSerializer


class BrandRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Brands.objects.all()
    serializer_class = serializers.BrandSerializer



# Função para exclusão em massa de marcas
@require_POST
def brand_bulk_delete(request):
    selected_ids = request.POST.getlist('selected_brands')
    if not selected_ids:
        messages.warning(request, "Nenhuma marca foi selecionada para exclusão.")
        return redirect('brand_list')

    failed = []
    deleted_count = 0

    for brand_id in selected_ids:
        try:
            brand = models.Brands.objects.get(id=brand_id)
            brand.delete()
            deleted_count += 1
        except ProtectedError:
            failed.append(brand.name)
        except models.Brands.DoesNotExist:
            continue

    if deleted_count > 0:
        messages.success(request, f"{deleted_count} marca(s) excluída(s) com sucesso!")
    if failed:
        messages.error(
            request,
            f"Não foi possível excluir as seguintes marcas pois estão vinculadas: {', '.join(failed)}"
        )

    return redirect('brand_list')
