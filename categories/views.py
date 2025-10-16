from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from . import models, forms
from django.contrib.auth.mixins import LoginRequiredMixin


class CategoryListView(LoginRequiredMixin, ListView):
    model = models.Category
    template_name = 'category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = models.Category
    template_name = 'category_create.html'
    form_class = forms.CategoryForm
    success_url = reverse_lazy('category_list')


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = models.Category
    template_name = 'category_detail.html'


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Category
    template_name = 'category_update.html'
    form_class = forms.CategoryForm
    success_url = reverse_lazy('category_list')


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Category
    template_name = 'category_delete.html'
    success_url = reverse_lazy('category_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(
                request,
                f'A categoria "{self.object.name}" foi excluída com sucesso!'
            )
            return redirect(self.success_url)
        except ProtectedError:
            messages.error(
                request,
                f'Não é possível excluir a categoria "{self.object.name}" pois está vinculada a algum produto/evento.'
            )
            return redirect(self.success_url)


# Exclusão em massa de categorias
@require_POST
def category_bulk_delete(request):
    selected_ids = request.POST.getlist('selected_categories')
    if not selected_ids:
        messages.warning(request, "Nenhuma categoria foi selecionada para exclusão.")
        return redirect('category_list')

    deleted_count = 0
    failed = []

    for category_id in selected_ids:
        try:
            category = models.Category.objects.get(id=category_id)
            category.delete()  # <- Corrigido: chamar método delete()
            deleted_count += 1
        except ProtectedError:
            failed.append(category.name)
        except models.Category.DoesNotExist:
            continue

    if deleted_count:
        messages.success(request, f"{deleted_count} categoria(s) excluída(s) com sucesso.")
    if failed:
        messages.error(
            request,
            f"Não foi possível excluir as categorias: {', '.join(failed)} pois estão vinculadas a produtos/eventos."
        )

    return redirect('category_list')
