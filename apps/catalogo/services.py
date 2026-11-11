"""Consultas do catálogo local. Toda busca textual usa conteúdo normalizado."""
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from .models import Exemplar, Obra, normalizar


def listar_obras(query='', genero='', autor='', disponibilidade=''):
    obras = Obra.objects.annotate(
        total_exemplares=Count('exemplares'),
        disponiveis=Count('exemplares', filter=Q(exemplares__situacao='disponivel')),
    )
    for termo in normalizar(query.strip()).split():
        obras = obras.filter(busca__contains=termo)
    if genero:
        obras = obras.filter(genero=genero)
    if autor:
        obras = obras.filter(autor=autor)
    if disponibilidade in ('disponivel', 'disponiveis'):
        obras = obras.filter(disponiveis__gt=0)
    elif disponibilidade in ('indisponivel', 'indisponiveis'):
        obras = obras.filter(disponiveis=0)
    return obras.order_by('titulo', 'pk')


def obter_obra(pk):
    return get_object_or_404(listar_obras(), pk=pk)


def opcoes_filtros():
    return {
        'generos': Obra.objects.exclude(genero='').values_list('genero', flat=True).distinct().order_by('genero'),
        'autores': Obra.objects.exclude(autor='').values_list('autor', flat=True).distinct().order_by('autor'),
    }


def alterar_situacao_exemplares(ids, situacao):
    """Alteração administrativa por comparação atômica e ausência de reserva ativa.

    Não produz uma reserva ao marcar manualmente um exemplar. Estados reservados
    são controlados exclusivamente pelo serviço de reservas.
    """
    from django.db import OperationalError
    from django.utils import timezone
    from apps.reservas.services import DomainError
    if situacao not in ('disponivel', 'emprestado', 'indisponivel'):
        raise DomainError('Escolha uma situação administrativa válida.')
    try:
        return Exemplar.objects.filter(pk__in=ids).exclude(
            reservas__estado__in=['pendente', 'confirmada', 'pronta'],
        ).update(situacao=situacao, atualizado_em=timezone.now())
    except OperationalError as exc:
        raise DomainError('O acervo está ocupado. Atualize a página e tente novamente.') from exc
