import unicodedata

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.casefold()) if not unicodedata.combining(c))


class Obra(models.Model):
    titulo = models.CharField('título', max_length=240)
    autor = models.CharField(max_length=200, blank=True)
    genero = models.CharField('gênero', max_length=80, blank=True)
    isbn = models.CharField('ISBN', max_length=20, blank=True)
    editora = models.CharField(max_length=160, blank=True)
    ano_publicacao = models.PositiveSmallIntegerField('ano de publicação', null=True, blank=True)
    sinopse = models.TextField(blank=True)
    identificador_externo = models.CharField(max_length=120, null=True, blank=True, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    busca = models.TextField(editable=False)

    class Meta:
        ordering = ['titulo', 'pk']
        verbose_name = 'obra'
        verbose_name_plural = 'obras'

    def save(self, *args, **kwargs):
        self.busca = normalizar(f'{self.titulo} {self.autor} {self.genero} {self.isbn}')
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'busca'}
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('catalogo:detalhe', args=[self.pk])


class Exemplar(models.Model):
    class Situacao(models.TextChoices):
        DISPONIVEL = 'disponivel', 'Disponível'
        EMPRESTADO = 'emprestado', 'Emprestado'
        RESERVADO = 'reservado', 'Reservado'
        INDISPONIVEL = 'indisponivel', 'Indisponível'

    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='exemplares')
    codigo = models.CharField('código de patrimônio', max_length=80, unique=True)
    situacao = models.CharField('situação', max_length=20, choices=Situacao.choices, default=Situacao.DISPONIVEL)
    localizacao = models.CharField('localização física', max_length=160, blank=True)
    identificador_externo = models.CharField(max_length=120, null=True, blank=True, unique=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['codigo']
        verbose_name = 'exemplar'
        verbose_name_plural = 'exemplares'
        constraints = [models.CheckConstraint(condition=models.Q(situacao__in=['disponivel', 'emprestado', 'reservado', 'indisponivel']), name='exemplar_situacao_valida')]

    def clean(self):
        super().clean()
        if self.pk and self.reservas.filter(estado__in=['pendente', 'confirmada', 'pronta']).exists():
            original = type(self).objects.get(pk=self.pk)
            if self.situacao != 'reservado' or self.obra_id != original.obra_id:
                raise ValidationError('Este exemplar possui reserva ativa. Gerencie a reserva antes de alterar a situação ou a obra.')

    def __str__(self):
        return f'{self.codigo} — {self.obra}'
