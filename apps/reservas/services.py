"""Operações transacionais. Nenhuma função acessa sistemas da biblioteca real.

A seleção inicial é fora de atomic(): em SQLite evita promover uma transação de
leitura para escrita. O primeiro comando transacional reivindica o exemplar com
UPDATE condicional; perdedores não criam reserva. A restrição parcial oferece
uma segunda barreira contra duas reservas ativas para o mesmo exemplar.
"""
from django.db import IntegrityError, OperationalError, transaction
from django.utils import timezone

from apps.catalogo.models import Exemplar
from .models import ESTADOS_ATIVOS, Reserva


class DomainError(Exception):
    """Erro de negócio que pode ser apresentado ao cidadão."""


def listar_reservas(usuario):
    return Reserva.objects.filter(usuario=usuario).select_related('exemplar__obra')


def solicitar_reserva(usuario, obra_id):
    if not usuario.is_authenticated or not usuario.is_active:
        raise DomainError('Entre na sua conta para solicitar uma reserva demonstrativa.')
    try:
        candidatos = list(Exemplar.objects.filter(obra_id=obra_id, situacao='disponivel').values_list('pk', flat=True))
    except OperationalError as exc:
        raise DomainError('O catálogo está ocupado. Atualize a página e tente novamente.') from exc
    for exemplar_id in candidatos:
        try:
            with transaction.atomic():
                atualizado = Exemplar.objects.filter(pk=exemplar_id, situacao='disponivel').update(situacao='reservado', atualizado_em=timezone.now())
                if not atualizado:
                    continue
                return Reserva.objects.create(usuario=usuario, exemplar_id=exemplar_id)
        except (IntegrityError, OperationalError) as exc:
            raise DomainError('A disponibilidade mudou enquanto você reservava. Atualize a página e tente novamente.') from exc
    raise DomainError('Não há exemplar disponível para esta obra no momento.')


def _transicionar(reserva_id, estado, *, usuario=None, prazo_retirada=None):
    filtro = Reserva.objects.filter(pk=reserva_id)
    if usuario is not None:
        filtro = filtro.filter(usuario=usuario)
    try:
        reserva = filtro.select_related('exemplar__obra').first()
    except OperationalError as exc:
        raise DomainError('As reservas estão ocupadas. Atualize a página e tente novamente.') from exc
    if reserva is None:
        raise DomainError('Reserva não encontrada para esta conta.')
    transicoes = {
        'pendente': {'confirmada', 'cancelada', 'expirada'},
        'confirmada': {'pronta', 'cancelada', 'expirada'},
        'pronta': {'retirada', 'cancelada', 'expirada'},
    }
    if estado not in transicoes.get(reserva.estado, set()):
        raise DomainError('Essa alteração não é permitida para a situação atual da reserva.')
    agora = timezone.now()
    if estado == 'expirada' and (reserva.prazo_retirada is None or reserva.prazo_retirada > agora):
        raise DomainError('Esta reserva ainda não atingiu o prazo de retirada.')
    if estado in ('confirmada', 'pronta', 'retirada') and reserva.prazo_retirada and reserva.prazo_retirada <= agora:
        raise DomainError('O prazo desta reserva terminou. Execute a expiração antes de continuar.')
    campos = {'estado': estado, 'cancelada_em': agora if estado == 'cancelada' else None}
    if prazo_retirada is not None:
        if prazo_retirada <= agora:
            raise DomainError('O prazo de retirada deve estar no futuro.')
        campos['prazo_retirada'] = prazo_retirada
    try:
        with transaction.atomic():
            if not Reserva.objects.filter(pk=reserva.pk, estado=reserva.estado).update(**campos):
                raise DomainError('A reserva foi alterada por outra operação. Atualize a página.')
            situacao = 'emprestado' if estado == 'retirada' else 'disponivel' if estado in ('cancelada', 'expirada') else 'reservado'
            if not Exemplar.objects.filter(pk=reserva.exemplar_id, situacao='reservado').update(situacao=situacao, atualizado_em=agora):
                raise DomainError('A situação do exemplar mudou. Solicite a revisão de um funcionário.')
    except (IntegrityError, OperationalError) as exc:
        raise DomainError('Não foi possível alterar a reserva agora. Atualize e tente novamente.') from exc
    for campo, valor in campos.items():
        setattr(reserva, campo, valor)
    return reserva


def cancelar_reserva(usuario, reserva_id):
    return _transicionar(reserva_id, 'cancelada', usuario=usuario)


def alterar_estado(reserva_id, estado, prazo_retirada=None):
    """Uso exclusivo da administração, que verifica change_reserva antes da chamada."""
    return _transicionar(reserva_id, estado, prazo_retirada=prazo_retirada)


def expirar_reservas():
    ids = list(Reserva.objects.filter(estado__in=ESTADOS_ATIVOS, prazo_retirada__lte=timezone.now()).values_list('pk', flat=True))
    total = 0
    for reserva_id in ids:
        try:
            _transicionar(reserva_id, 'expirada')
            total += 1
        except DomainError:
            # Alterações concorrentes serão reavaliadas na próxima execução.
            continue
    return total
