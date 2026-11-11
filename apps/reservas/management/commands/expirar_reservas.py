from django.core.management.base import BaseCommand
from apps.reservas.services import expirar_reservas


class Command(BaseCommand):
    help = 'Expira reservas demonstrativas ativas com prazo vencido e libera os exemplares.'

    def handle(self, *args, **options):
        total = expirar_reservas()
        self.stdout.write(self.style.SUCCESS(f'{total} reserva(s) demonstrativa(s) expirada(s).'))
