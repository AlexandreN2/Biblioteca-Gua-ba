from django.contrib import admin, messages
from django.db import DatabaseError
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Exemplar, Obra
from .services import alterar_situacao_exemplares
from apps.reservas.services import DomainError


class ContencaoAdminMixin:
    """O admin faz leitura dentro de atomic; SQLite pode recusar sua promoção.

    O catch fica fora da transação do Django, garantindo rollback completo antes
    de gerar uma mensagem e redirecionar para uma nova leitura.
    """
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except DatabaseError:
            self.message_user(request, 'Outra operação alterou os dados. Atualize e tente novamente.', messages.WARNING)
            return HttpResponseRedirect(reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_changelist'))

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context)
        except DatabaseError:
            self.message_user(request, 'O acervo está ocupado. Atualize e tente novamente.', messages.WARNING)
            return HttpResponseRedirect(reverse('admin:index'))


@admin.register(Obra)
class ObraAdmin(ContencaoAdminMixin, admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'genero', 'isbn']
    list_filter = ['genero']
    search_fields = ['titulo', 'autor', 'isbn', 'busca']
    readonly_fields = ['criado_em', 'atualizado_em']
    ordering = ['titulo']


@admin.register(Exemplar)
class ExemplarAdmin(ContencaoAdminMixin, admin.ModelAdmin):
    list_display = ['codigo', 'obra', 'situacao', 'localizacao']
    list_filter = ['situacao', 'obra__genero']
    search_fields = ['codigo', 'obra__titulo', 'obra__autor']
    autocomplete_fields = ['obra']
    readonly_fields = ['atualizado_em']
    actions = ['disponibilizar', 'emprestar', 'indisponibilizar']

    def get_readonly_fields(self, request, obj=None):
        # A situação de exemplares existentes é alterada pelas ações abaixo.
        # A obra permanece fixa para preservar o histórico bibliográfico.
        return ['atualizado_em', 'situacao', 'obra'] if obj else ['atualizado_em']

    def save_model(self, request, obj, form, change):
        if change:
            campos = set(form.changed_data) & {'codigo', 'localizacao', 'identificador_externo'}
            if campos:
                obj.save(update_fields=campos | {'atualizado_em'})
        else:
            super().save_model(request, obj, form, change)

    def _situacao(self, request, queryset, situacao):
        try:
            total = alterar_situacao_exemplares(list(queryset.values_list('pk', flat=True)), situacao)
            self.message_user(request, f'{total} exemplar(es) atualizado(s). Exemplares com reserva ativa são preservados.', messages.SUCCESS)
        except DomainError as exc:
            self.message_user(request, str(exc), messages.WARNING)

    @admin.action(description='Marcar como disponíveis (sem reserva ativa)', permissions=['change'])
    def disponibilizar(self, request, queryset):
        self._situacao(request, queryset, 'disponivel')

    @admin.action(description='Registrar empréstimo demonstrativo (sem reserva ativa)', permissions=['change'])
    def emprestar(self, request, queryset):
        self._situacao(request, queryset, 'emprestado')

    @admin.action(description='Marcar como indisponíveis (sem reserva ativa)', permissions=['change'])
    def indisponibilizar(self, request, queryset):
        self._situacao(request, queryset, 'indisponivel')
