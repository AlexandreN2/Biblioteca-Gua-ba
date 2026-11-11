"""Adaptador explícito para o protótipo local, sem chamadas de rede."""
from apps.catalogo import services as catalogo
from apps.reservas import services as reservas


class ProvedorLocal:
    listar_obras = staticmethod(catalogo.listar_obras)
    obter_obra = staticmethod(catalogo.obter_obra)
    solicitar_reserva = staticmethod(reservas.solicitar_reserva)
    listar_reservas = staticmethod(reservas.listar_reservas)
    cancelar_reserva = staticmethod(reservas.cancelar_reserva)

    @staticmethod
    def disponibilidade(obra_id):
        return catalogo.obter_obra(obra_id).disponiveis
