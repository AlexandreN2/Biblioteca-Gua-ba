from django.contrib import messages
from django.contrib.auth import login
from django.db import IntegrityError, OperationalError, transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import CadastroForm
from .models import Perfil


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("reservas:minhas")
    form = CadastroForm(request.POST or None)
    proxima = request.POST.get("next", request.GET.get("next", ""))
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                usuario = form.save()
                Perfil.objects.create(usuario=usuario)
        except IntegrityError:
            form.add_error(None, "Não foi possível criar esta conta. Tente outro nome de usuário.")
            return render(request, "usuarios/cadastro.html", {"form": form, "next": proxima})
        except OperationalError:
            form.add_error(None, "O cadastro está ocupado. Aguarde um instante e tente novamente.")
            return render(request, "usuarios/cadastro.html", {"form": form, "next": proxima})
        login(request, usuario)
        messages.success(request, "Conta demonstrativa criada. Você já pode solicitar reservas.")
        if url_has_allowed_host_and_scheme(proxima, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(proxima)
        return redirect("catalogo:lista")
    return render(request, "usuarios/cadastro.html", {"form": form, "next": proxima})
