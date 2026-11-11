from django.conf import settings
from django.db import models

class Perfil(models.Model):
    """Perfil mínimo: nenhuma informação pessoal além da conta nativa."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "perfil demonstrativo"

    def __str__(self):
        return self.usuario.get_username()
