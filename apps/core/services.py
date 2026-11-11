from .models import Comunicado, Configuracao


def obter_configuracao():
    return Configuracao.obter()


def listar_comunicados():
    return Comunicado.objects.filter(publicado=True)
