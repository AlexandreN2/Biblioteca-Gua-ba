"""Contrato inicial para um futuro adaptador autorizado.

O contrato é síncrono. Identificadores locais não devem ser confundidos com os
identificadores externos opcionais. O projeto não define o SGBD institucional,
nem qual sistema será fonte oficial de disponibilidade e reservas.
"""
from typing import Protocol, TYPE_CHECKING
from collections.abc import Iterable

if TYPE_CHECKING:
    from apps.catalogo.models import Obra
    from apps.reservas.models import Reserva


class ProvedorBiblioteca(Protocol):
    def listar_obras(self, query: str = '', genero: str = '', autor: str = '', disponibilidade: str = '') -> Iterable['Obra']: ...
    def obter_obra(self, pk: int) -> 'Obra': ...
    def disponibilidade(self, obra_id: int) -> int: ...
    def solicitar_reserva(self, usuario, obra_id: int) -> 'Reserva': ...
    def listar_reservas(self, usuario) -> Iterable['Reserva']: ...
    def cancelar_reserva(self, usuario, reserva_id: int) -> 'Reserva': ...
