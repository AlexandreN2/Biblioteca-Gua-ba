"""Dados editoriais ilustrativos. Não são uma cópia do acervo institucional."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogo.models import Exemplar, Obra
from apps.core.models import Comunicado, Configuracao
from apps.reservas.models import Reserva

OBRAS = [
    ('O Tempo e o Vento', 'Erico Verissimo', 'Romance regional'),
    ('Dom Casmurro', 'Machado de Assis', 'Romance'),
    ('Contos Gauchescos', 'João Simões Lopes Neto', 'Contos'),
    ('A Rua dos Cataventos', 'Mario Quintana', 'Poesia'),
    ('Quarto de Despejo', 'Carolina Maria de Jesus', 'Memórias'),
    ('O Cortiço', 'Aluísio Azevedo', 'Romance'),
    ('Memórias Póstumas de Brás Cubas', 'Machado de Assis', 'Romance'),
    ('Vidas Secas', 'Graciliano Ramos', 'Romance'),
    ('A Hora da Estrela', 'Clarice Lispector', 'Romance'),
    ('Capitães da Areia', 'Jorge Amado', 'Romance'),
    ('O Menino Maluquinho', 'Ziraldo', 'Infantojuvenil'),
    ('Reinações de Narizinho', 'Monteiro Lobato', 'Infantojuvenil'),
    ('O Pequeno Príncipe', 'Antoine de Saint-Exupéry', 'Infantojuvenil'),
    ('A Revolução dos Bichos', 'George Orwell', 'Ficção'),
    ('Frankenstein', 'Mary Shelley', 'Ficção'),
    ('Orgulho e Preconceito', 'Jane Austen', 'Romance'),
    ('Os Sertões', 'Euclides da Cunha', 'Literatura e história'),
    ('Iracema', 'José de Alencar', 'Romance'),
    ('Cecília Meireles: seleção poética', 'Cecília Meireles', 'Poesia'),
    ('Histórias da Nossa Cidade', 'Autoria demonstrativa', 'Cultura local'),
]


class Command(BaseCommand):
    help = 'Cria dados demonstrativos sem duplicar nem substituir alterações existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        Configuracao.obter()
        usuario, criado = get_user_model().objects.get_or_create(username='leitor_demo_inativo', defaults={'is_active': False, 'first_name': 'Leitor demonstrativo'})
        if criado:
            usuario.set_unusable_password()
            usuario.save(update_fields=['password'])
        novas = 0
        for indice, (titulo, autor, genero) in enumerate(OBRAS, start=1):
            obra, criada = Obra.objects.get_or_create(
                identificador_externo=f'demo:obra:{indice:02d}',
                defaults={'titulo': titulo, 'autor': autor, 'genero': genero,
                          'sinopse': f'Registro de demonstração de “{titulo}”. A sinopse e os dados desta edição estão pendentes de curadoria. Os exemplares e sua disponibilidade são fictícios.'},
            )
            novas += criada
            situacoes = {
                1: ['disponivel', 'disponivel', 'emprestado'],
                3: ['disponivel', 'disponivel'],
                4: ['emprestado'],
                5: ['indisponivel'],
                6: ['reservado'],
                12: ['emprestado', 'emprestado'],
                15: ['indisponivel', 'emprestado'],
            }.get(indice, ['disponivel'])
            for numero, situacao in enumerate(situacoes, start=1):
                exemplar, novo = Exemplar.objects.get_or_create(codigo=f'DEMO-{indice:02d}-{numero:02d}', defaults={'obra': obra, 'situacao': situacao, 'localizacao': f'Estante demonstrativa · {genero}'})
                if novo and situacao == 'reservado':
                    Reserva.objects.create(usuario=usuario, exemplar=exemplar, observacoes='Reserva fictícia para demonstrar disponibilidade. Conta sem acesso e sem senha utilizável.')
        Comunicado.objects.get_or_create(titulo='Bem-vindo ao portal de demonstração', defaults={
            'texto': 'Explore o catálogo de teste e conheça o fluxo de reservas. Este ambiente não recebe pedidos oficiais nem altera o acervo real da biblioteca.', 'publicado': True,
        })
        Comunicado.objects.get_or_create(titulo='Informações institucionais em confirmação', defaults={
            'texto': 'Endereço, horários, contatos e regras oficiais serão publicados após validação da instituição. Os funcionários podem editar esses campos no painel administrativo.', 'publicado': True,
        })
        self.stdout.write(self.style.SUCCESS(f'Demonstração preparada: {novas} novas obras. Nenhuma senha administrativa foi criada.'))
