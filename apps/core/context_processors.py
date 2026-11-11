from django.db import DatabaseError
from .models import Configuracao
from .services import obter_configuracao


def institucional(request):
    try:
        instituicao = obter_configuracao()
    except DatabaseError:
        # Permite renderizar inclusive a página de erro durante falha do banco.
        instituicao = Configuracao()
    return {"instituicao": instituicao}
