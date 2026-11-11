from django.contrib import admin
from .models import Comunicado, Configuracao


@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Identidade provisória', {'fields': ['nome', 'sobre']}),
        ('Atendimento — confirmar com a instituição', {'fields': ['endereco', 'horarios', 'telefone', 'email', 'como_chegar_url']}),
        ('Orientações ao cidadão', {'fields': ['orientacoes_cadastro', 'regras_emprestimo', 'orientacoes_reserva']}),
    ]

    def has_add_permission(self, request):
        return not Configuracao.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'publicado', 'criado_em']
    list_filter = ['publicado']
    search_fields = ['titulo', 'texto']
    readonly_fields = ['criado_em']
