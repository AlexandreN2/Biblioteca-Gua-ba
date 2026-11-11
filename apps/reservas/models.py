from django.conf import settings
from django.db import models

ESTADOS_ATIVOS = ('pendente', 'confirmada', 'pronta')


class Reserva(models.Model):
    class Estado(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        CONFIRMADA = 'confirmada', 'Confirmada'
        PRONTA = 'pronta', 'Pronta para retirada'
        RETIRADA = 'retirada', 'Retirada'
        CANCELADA = 'cancelada', 'Cancelada'
        EXPIRADA = 'expirada', 'Expirada'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reservas')
    exemplar = models.ForeignKey('catalogo.Exemplar', on_delete=models.PROTECT, related_name='reservas')
    solicitada_em = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDENTE)
    prazo_retirada = models.DateTimeField(null=True, blank=True)
    cancelada_em = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField('observações administrativas', blank=True)

    class Meta:
        ordering = ['-solicitada_em', '-pk']
        verbose_name = 'reserva demonstrativa'
        verbose_name_plural = 'reservas demonstrativas'
        constraints = [
            models.UniqueConstraint(fields=['exemplar'], condition=models.Q(estado__in=ESTADOS_ATIVOS), name='reserva_ativa_unica_exemplar'),
            models.CheckConstraint(condition=models.Q(estado__in=['pendente', 'confirmada', 'pronta', 'retirada', 'cancelada', 'expirada']), name='reserva_estado_valido'),
            models.CheckConstraint(condition=(models.Q(estado='cancelada', cancelada_em__isnull=False) | (~models.Q(estado='cancelada') & models.Q(cancelada_em__isnull=True))), name='reserva_cancelamento_consistente'),
        ]

    @property
    def cancelavel(self):
        return self.estado in ESTADOS_ATIVOS

    def __str__(self):
        return f'Reserva demonstrativa #{self.pk} — {self.exemplar.obra}'
