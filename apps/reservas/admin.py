from django import forms
from django.contrib import admin, messages
from django.utils import timezone

from apps.catalogo.admin import ContencaoAdminMixin
from .models import Reserva
from .services import DomainError, alterar_estado


class ReservaAdminForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = '__all__'

    def clean_prazo_retirada(self):
        prazo = self.cleaned_data['prazo_retirada']
        if 'prazo_retirada' in self.changed_data and prazo and prazo <= timezone.now():
            raise forms.ValidationError('Informe um prazo de retirada no futuro.')
        return prazo


@admin.register(Reserva)
class ReservaAdmin(ContencaoAdminMixin, admin.ModelAdmin):
    form = ReservaAdminForm
    list_display = ['id', 'usuario', 'obra', 'exemplar', 'estado', 'solicitada_em', 'prazo_retirada']
    list_filter = ['estado', 'solicitada_em']
    search_fields = ['usuario__username', 'exemplar__codigo', 'exemplar__obra__titulo']
    readonly_fields = ['usuario', 'exemplar', 'estado', 'solicitada_em', 'cancelada_em']
    actions = ['confirmar', 'preparar', 'retirar', 'cancelar']

    @admin.display(description='Obra')
    def obra(self, obj):
        return obj.exemplar.obra

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'exemplar__obra')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        # Metadados não podem regravar um estado lido antes de uma ação concorrente.
        campos = set(form.changed_data) & {'prazo_retirada', 'observacoes'}
        if campos:
            obj.save(update_fields=campos)

    def _acao(self, request, queryset, estado):
        sucessos = 0
        for reserva in queryset:
            try:
                alterar_estado(reserva.pk, estado)
                sucessos += 1
            except DomainError as exc:
                self.message_user(request, f'Reserva #{reserva.pk}: {exc}', messages.WARNING)
        if sucessos:
            self.message_user(request, f'{sucessos} reserva(s) demonstrativa(s) atualizada(s).', messages.SUCCESS)

    @admin.action(description='Confirmar reservas selecionadas', permissions=['change'])
    def confirmar(self, request, queryset):
        self._acao(request, queryset, 'confirmada')

    @admin.action(description='Marcar como prontas para retirada', permissions=['change'])
    def preparar(self, request, queryset):
        self._acao(request, queryset, 'pronta')

    @admin.action(description='Registrar retirada e empréstimo demonstrativo', permissions=['change'])
    def retirar(self, request, queryset):
        self._acao(request, queryset, 'retirada')

    @admin.action(description='Cancelar reservas selecionadas', permissions=['change'])
    def cancelar(self, request, queryset):
        self._acao(request, queryset, 'cancelada')
