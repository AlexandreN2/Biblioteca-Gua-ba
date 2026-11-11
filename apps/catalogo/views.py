from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from .models import Obra
from .services import listar_obras, obter_obra, opcoes_filtros


def lista(request):
    filtros = {"query": request.GET.get("q", "").strip()[:200], "genero": request.GET.get("genero", "")[:100], "autor": request.GET.get("autor", "")[:180], "disponibilidade": request.GET.get("disponibilidade", "")}
    obras = listar_obras(**filtros)
    opcoes = opcoes_filtros()
    return render(request, "catalogo/lista.html", {**filtros, **opcoes, "page_obj": Paginator(obras, 12).get_page(request.GET.get("page"))})

def detalhe(request, pk):
    try:
        obra = obter_obra(pk)
    except Obra.DoesNotExist:
        raise Http404("Obra não encontrada.")
    return render(request, "catalogo/detalhe.html", {"obra": obra})
