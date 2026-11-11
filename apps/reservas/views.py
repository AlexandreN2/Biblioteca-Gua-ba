from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .services import DomainError, solicitar_reserva, cancelar_reserva, listar_reservas


@login_required
def minhas(request):
    return render(request, "reservas/minhas.html", {"reservas": listar_reservas(request.user)})

@require_POST
@login_required
def solicitar(request, pk):
    try:
        solicitar_reserva(request.user, pk)
    except DomainError as error:
        messages.error(request, str(error))
        return redirect("catalogo:detalhe", pk=pk)
    messages.success(request, "Reserva demonstrativa solicitada! Acompanhe a situação em Minhas reservas.")
    return redirect("reservas:minhas")

@require_POST
@login_required
def cancelar(request, pk):
    try:
        cancelar_reserva(request.user, pk)
    except DomainError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Reserva demonstrativa cancelada. O exemplar voltou a ficar disponível.")
    return redirect("reservas:minhas")
