from django.shortcuts import render
from apps.catalogo.services import listar_obras
from .services import listar_comunicados


def inicio(request):
    return render(request, "core/inicio.html", {"destaques": listar_obras()[:4], "comunicados": listar_comunicados()[:3]})

def sobre(request):
    return render(request, "core/sobre.html")

def atendimento(request):
    return render(request, "core/atendimento.html")

def como_reservar(request):
    return render(request, "core/como_reservar.html")

def erro_400(request, exception):
    return render(request, "erro.html", {"codigo": 400, "mensagem": "Não foi possível entender esta solicitação."}, status=400)

def erro_403(request, exception):
    return render(request, "erro.html", {"codigo": 403, "mensagem": "Você não tem permissão para realizar esta operação. Recarregue a página caso o formulário tenha expirado."}, status=403)

def erro_404(request, exception):
    return render(request, "erro.html", {"codigo": 404, "mensagem": "A página que você procura não foi encontrada."}, status=404)

def erro_500(request):
    return render(request, "erro.html", {"codigo": 500, "mensagem": "Não foi possível concluir agora. Tente novamente em instantes."}, status=500)

def csrf_failure(request, reason=""):
    return erro_403(request, None)
