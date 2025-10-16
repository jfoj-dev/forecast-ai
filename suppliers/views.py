from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from . import models, forms
from django.contrib.auth.mixins import LoginRequiredMixin


class SupplierListView(LoginRequiredMixin, ListView):
    model = models.Supplier
    template_name = 'supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')

        if name:
            queryset = queryset.filter(name__icontains=name)
        
        return queryset


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = models.Supplier
    template_name = 'supplier_create.html'
    form_class = forms.SupplierForm
    success_url = reverse_lazy('supplier_list')


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = models.Supplier
    template_name = 'supplier_detail.html'


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Supplier
    template_name = 'supplier_update.html'
    form_class = forms.SupplierForm
    success_url = reverse_lazy('supplier_list')


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Supplier
    template_name = 'supplier_delete.html'
    success_url = reverse_lazy('supplier_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(
                request,
                f'O fornecedor "{self.object.name}" foi excluído com sucesso!'
            )
            return redirect(self.success_url)
        except ProtectedError:
            messages.error(
                request,
                f'Não é possível excluir o fornecedor "{self.object.name}" pois ele está sendo utilizado em um evento.'
            )
            return redirect(self.success_url)


# ===============================================
# VIEW PARA EXCLUSÃO EM MASSA
# ===============================================
@require_POST
def supplier_bulk_delete(request):
    ids = request.POST.getlist('selected_suppliers')  # IDs selecionados na checkbox
    if not ids:
        messages.warning(request, 'Nenhum fornecedor foi selecionado para exclusão.')
        return redirect('supplier_list')

    suppliers = models.Supplier.objects.filter(id__in=ids)
    deleted = []
    protected = []

    for supplier in suppliers:
        try:
            supplier.delete()
            deleted.append(supplier.name)
        except ProtectedError:
            protected.append(supplier.name)

    if deleted:
        messages.success(
            request,
            f'Fornecedores excluídos com sucesso: {", ".join(deleted)}.'
        )
    if protected:
        messages.error(
            request,
            f'Não foi possível excluir os fornecedores: {", ".join(protected)} pois estão sendo utilizados em algum evento.'
        )

    return redirect('supplier_list')
