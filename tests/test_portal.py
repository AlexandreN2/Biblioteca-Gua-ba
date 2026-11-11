"""Testes de comportamento do portal e de integridade do domínio."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, OperationalError, close_old_connections, connections, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalogo.models import Exemplar, Obra
from apps.catalogo.services import listar_obras, obter_obra
from apps.reservas.models import Reserva
from apps.reservas.services import (
    DomainError, alterar_estado, cancelar_reserva, expirar_reservas,
    listar_reservas, solicitar_reserva,
)

User = get_user_model()


class CenarioMixin:
    def criar_cenario(self):
        self.usuario = User.objects.create_user(username='leitora', password='SenhaLocalForte2026!')
        self.outro = User.objects.create_user(username='outroleitor', password='OutraSenhaForte2026!')
        self.obra = Obra.objects.create(titulo='A canção das águas', autor='Érica da Silva', genero='Ficção', isbn='9781234567890')
        self.exemplar = Exemplar.objects.create(obra=self.obra, codigo='T-001')
        self.indisponivel = Obra.objects.create(titulo='Memórias do rio', autor='João de Souza', genero='Poesia')
        Exemplar.objects.create(obra=self.indisponivel, codigo='T-002', situacao='emprestado')


class CatalogoTests(CenarioMixin, TestCase):
    def setUp(self):
        self.criar_cenario()

    def test_obra_preserva_metadados_opcionais(self):
        obra = Obra.objects.create(titulo='Obra sem metadados')
        obra.full_clean()
        self.assertEqual(obra.autor, '')
        self.assertIsNone(obra.ano_publicacao)

    def test_exemplar_relaciona_obra_e_codigo_unico(self):
        self.assertEqual(self.exemplar.obra, self.obra)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exemplar.objects.create(obra=self.indisponivel, codigo=self.exemplar.codigo)

    def test_situacao_invalida_e_impedida_pelo_banco(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exemplar.objects.filter(pk=self.exemplar.pk).update(situacao='inexistente')

    def test_pesquisa_titulo_autor_genero_isbn_ignora_acentos_e_caixa(self):
        for termo in ('CANCAO', 'aguas', 'ERICA', 'ficcao', '9781234567890'):
            with self.subTest(termo=termo):
                self.assertEqual(list(listar_obras(query=termo)), [self.obra])

    def test_atualizacao_reconstroi_busca(self):
        self.obra.titulo = 'Horizontes de Guaíba'
        self.obra.save(update_fields=['titulo'])
        self.assertEqual(list(listar_obras(query='GUAIBA')), [self.obra])
        self.assertFalse(listar_obras(query='cancao').exists())

    def test_filtros_combinados_com_busca_e_disponibilidade(self):
        resultado = listar_obras(query='aguas', genero='Ficção', autor='Érica da Silva', disponibilidade='disponivel')
        self.assertEqual(list(resultado), [self.obra])
        self.assertFalse(listar_obras(query='aguas', genero='Poesia').exists())
        self.assertEqual(list(listar_obras(disponibilidade='indisponivel')), [self.indisponivel])

    def test_contagens_de_exemplares(self):
        Exemplar.objects.create(obra=self.obra, codigo='T-003', situacao='indisponivel')
        dados = obter_obra(self.obra.pk)
        self.assertEqual(dados.total_exemplares, 2)
        self.assertEqual(dados.disponiveis, 1)

    def test_paginas_publicas_e_detalhe_sem_metadados(self):
        obra = Obra.objects.create(titulo='Somente um título')
        for nome in ('core:inicio', 'core:sobre', 'core:atendimento', 'core:como_reservar', 'catalogo:lista'):
            with self.subTest(nome=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)
        self.assertEqual(self.client.get(reverse('catalogo:detalhe', args=[obra.pk])).status_code, 200)

    def test_catalogo_pagina_resultados(self):
        for indice in range(25):
            Obra.objects.create(titulo=f'Livro {indice:02d}')
        resposta = self.client.get(reverse('catalogo:lista'))
        self.assertTrue(resposta.context['page_obj'].has_next())
        segunda = self.client.get(reverse('catalogo:lista'), {'page': 2})
        self.assertEqual(segunda.context['page_obj'].number, 2)
        self.assertFalse(set(resposta.context['page_obj']) & set(segunda.context['page_obj']))


    @override_settings(DEBUG=False)
    def test_pagina_de_erro_funciona_sem_configuracao_no_banco(self):
        with patch('apps.core.context_processors.obter_configuracao', side_effect=OperationalError('detalhe interno do banco')):
            resposta = self.client.get('/pagina-inexistente-para-teste/')
        self.assertEqual(resposta.status_code, 404)
        self.assertNotContains(resposta, 'detalhe interno do banco', status_code=404)
        self.assertContains(resposta, '404', status_code=404)


class UsuariosTests(CenarioMixin, TestCase):
    def setUp(self):
        self.criar_cenario()

    def test_login_e_logout_por_post(self):
        resposta = self.client.post(reverse('login'), {'username': 'leitora', 'password': 'SenhaLocalForte2026!'})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.usuario.pk)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.client.post(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_senha_incorreta_nao_autentica(self):
        resposta = self.client.post(reverse('login'), {'username': 'leitora', 'password': 'incorreta'})
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cadastro_cria_conta_com_senha_protegida(self):
        resposta = self.client.post(reverse('usuarios:cadastro'), {
            'username': 'nova_leitora', 'password1': 'SegredoLocalLongo!2026', 'password2': 'SegredoLocalLongo!2026',
        })
        self.assertEqual(resposta.status_code, 302)
        usuario = User.objects.get(username='nova_leitora')
        self.assertTrue(usuario.check_password('SegredoLocalLongo!2026'))
        self.assertNotEqual(usuario.password, 'SegredoLocalLongo!2026')
        self.assertFalse(usuario.is_staff)

    def test_cadastro_nao_redireciona_para_endereco_externo(self):
        resposta = self.client.post(reverse('usuarios:cadastro'), {
            'username': 'nova_conta', 'password1': 'SegredoLocalLongo!2026',
            'password2': 'SegredoLocalLongo!2026', 'next': 'https://externo.example/receber',
        })
        self.assertRedirects(resposta, reverse('catalogo:lista'))

    def test_cadastro_preserva_retorno_local_para_a_obra(self):
        destino = reverse('catalogo:detalhe', args=[self.obra.pk])
        resposta = self.client.post(reverse('usuarios:cadastro'), {
            'username': 'nova_conta', 'password1': 'SegredoLocalLongo!2026',
            'password2': 'SegredoLocalLongo!2026', 'next': destino,
        })
        self.assertRedirects(resposta, destino)

    def test_reservas_exigem_autenticacao(self):
        self.assertRedirects(self.client.get(reverse('reservas:minhas')), reverse('login') + '?next=' + reverse('reservas:minhas'))
        resposta = self.client.post(reverse('reservas:solicitar', args=[self.obra.pk]))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Reserva.objects.count(), 0)


class ReservasTests(CenarioMixin, TestCase):
    def setUp(self):
        self.criar_cenario()

    def test_solicitacao_reserva_exemplar_e_reduz_disponibilidade(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        self.exemplar.refresh_from_db()
        self.assertEqual(reserva.estado, 'pendente')
        self.assertEqual(self.exemplar.situacao, 'reservado')
        self.assertEqual(obter_obra(self.obra.pk).disponiveis, 0)

    def test_indisponibilidade_nao_cria_reserva(self):
        with self.assertRaises(DomainError):
            solicitar_reserva(self.usuario, self.indisponivel.pk)
        self.assertEqual(Reserva.objects.count(), 0)

    def test_usuario_anonimo_nao_reserva(self):
        with self.assertRaises(DomainError):
            solicitar_reserva(AnonymousUser(), self.obra.pk)
        self.assertEqual(Reserva.objects.count(), 0)

    def test_repeticao_nao_reserva_ultimo_exemplar_duas_vezes(self):
        solicitar_reserva(self.usuario, self.obra.pk)
        with self.assertRaises(DomainError):
            solicitar_reserva(self.outro, self.obra.pk)
        self.assertEqual(Reserva.objects.count(), 1)

    def test_cancelamento_libera_exemplar_e_registra_data(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        cancelada = cancelar_reserva(self.usuario, reserva.pk)
        self.exemplar.refresh_from_db()
        self.assertEqual(cancelada.estado, 'cancelada')
        self.assertIsNotNone(cancelada.cancelada_em)
        self.assertEqual(self.exemplar.situacao, 'disponivel')
        nova = solicitar_reserva(self.outro, self.obra.pk)
        self.assertNotEqual(nova.pk, reserva.pk)

    def test_terceiro_nao_cancela_nem_lista_reserva_alheia(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        with self.assertRaises(DomainError):
            cancelar_reserva(self.outro, reserva.pk)
        self.assertFalse(listar_reservas(self.outro).exists())
        self.client.force_login(self.outro)
        self.client.post(reverse('reservas:cancelar', args=[reserva.pk]))
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'pendente')
        self.assertNotIn(reserva, self.client.get(reverse('reservas:minhas')).context['reservas'])

    def test_get_nao_altera_reservas(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('reservas:solicitar', args=[self.obra.pk])).status_code, 405)
        self.assertEqual(Reserva.objects.count(), 0)
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        self.assertEqual(self.client.get(reverse('reservas:cancelar', args=[reserva.pk])).status_code, 405)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'pendente')

    def test_post_sem_csrf_e_rejeitado(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        resposta = cliente.post(reverse('reservas:solicitar', args=[self.obra.pk]))
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Reserva.objects.count(), 0)

    def test_fluxo_http_de_reserva_e_cancelamento(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(reverse('reservas:solicitar', args=[self.obra.pk]))
        self.assertRedirects(resposta, reverse('reservas:minhas'))
        reserva = Reserva.objects.get(usuario=self.usuario)
        resposta = self.client.post(reverse('reservas:cancelar', args=[reserva.pk]))
        self.assertRedirects(resposta, reverse('reservas:minhas'))
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'cancelada')

    def test_fluxo_de_retirada_atualiza_exemplar(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        for estado in ('confirmada', 'pronta', 'retirada'):
            reserva = alterar_estado(reserva.pk, estado)
            self.exemplar.refresh_from_db()
            self.assertEqual(self.exemplar.situacao, 'emprestado' if estado == 'retirada' else 'reservado')
        with self.assertRaises(DomainError):
            cancelar_reserva(self.usuario, reserva.pk)

    def test_transicao_invalida_nao_altera_dados(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        with self.assertRaises(DomainError):
            alterar_estado(reserva.pk, 'retirada')
        reserva.refresh_from_db()
        self.exemplar.refresh_from_db()
        self.assertEqual(reserva.estado, 'pendente')
        self.assertEqual(self.exemplar.situacao, 'reservado')

    def test_expiracao_libera_somente_reserva_vencida(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        Reserva.objects.filter(pk=reserva.pk).update(prazo_retirada=timezone.now() - timedelta(minutes=1))
        self.assertEqual(expirar_reservas(), 1)
        self.assertEqual(expirar_reservas(), 0)
        reserva.refresh_from_db()
        self.exemplar.refresh_from_db()
        self.assertEqual(reserva.estado, 'expirada')
        self.assertEqual(self.exemplar.situacao, 'disponivel')

    def test_reserva_futura_nao_expira(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        Reserva.objects.filter(pk=reserva.pk).update(prazo_retirada=timezone.now() + timedelta(days=1))
        self.assertEqual(expirar_reservas(), 0)

    def test_inconsistencia_do_exemplar_desfaz_transicao_inteira(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        # Simula escrita legada fora dos serviços para verificar rollback.
        Exemplar.objects.filter(pk=self.exemplar.pk).update(situacao='indisponivel')
        with self.assertRaises(DomainError):
            cancelar_reserva(self.usuario, reserva.pk)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'pendente')
        self.assertIsNone(reserva.cancelada_em)

    def test_prazo_vencido_impede_retirada_antes_da_expiracao(self):
        reserva = solicitar_reserva(self.usuario, self.obra.pk)
        alterar_estado(reserva.pk, 'confirmada')
        alterar_estado(reserva.pk, 'pronta')
        Reserva.objects.filter(pk=reserva.pk).update(prazo_retirada=timezone.now() - timedelta(seconds=1))
        with self.assertRaises(DomainError):
            alterar_estado(reserva.pk, 'retirada')
        reserva.refresh_from_db()
        self.exemplar.refresh_from_db()
        self.assertEqual(reserva.estado, 'pronta')
        self.assertEqual(self.exemplar.situacao, 'reservado')

    def test_restricao_impede_duas_reservas_ativas_do_mesmo_exemplar(self):
        solicitar_reserva(self.usuario, self.obra.pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reserva.objects.create(usuario=self.outro, exemplar=self.exemplar)

    def test_validacao_impede_disponibilizar_exemplar_com_reserva_ativa(self):
        solicitar_reserva(self.usuario, self.obra.pk)
        self.exemplar.refresh_from_db()
        self.exemplar.situacao = 'disponivel'
        with self.assertRaises(ValidationError):
            self.exemplar.full_clean()


class AdministracaoTests(CenarioMixin, TestCase):
    def setUp(self):
        self.criar_cenario()
        self.reserva = solicitar_reserva(self.usuario, self.obra.pk)

    def test_usuario_comum_nao_acessa_administracao(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse('admin:reservas_reserva_changelist'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('admin:login'), resposta.url)

    def test_funcionario_sem_permissao_nao_administra_reservas(self):
        self.usuario.is_staff = True
        self.usuario.save(update_fields=['is_staff'])
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('admin:reservas_reserva_changelist')).status_code, 403)
        self.client.post(reverse('admin:reservas_reserva_changelist'), {'action': 'confirmar', '_selected_action': [self.reserva.pk]})
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, 'pendente')

    def test_permissao_so_de_visualizacao_nao_executa_acao(self):
        self.usuario.is_staff = True
        self.usuario.save(update_fields=['is_staff'])
        self.usuario.user_permissions.add(Permission.objects.get(content_type__app_label='reservas', codename='view_reserva'))
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('admin:reservas_reserva_changelist')).status_code, 200)
        self.client.post(reverse('admin:reservas_reserva_changelist'), {'action': 'confirmar', '_selected_action': [self.reserva.pk]})
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, 'pendente')

    def test_funcionario_com_permissao_altera_estado_por_acao(self):
        self.usuario.is_staff = True
        self.usuario.save(update_fields=['is_staff'])
        self.usuario.user_permissions.add(Permission.objects.get(content_type__app_label='reservas', codename='change_reserva'))
        self.client.force_login(self.usuario)
        self.client.post(reverse('admin:reservas_reserva_changelist'), {'action': 'confirmar', '_selected_action': [self.reserva.pk]})
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, 'confirmada')
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.situacao, 'reservado')


    def test_acao_de_exemplar_exige_permissao(self):
        self.usuario.is_staff = True
        self.usuario.save(update_fields=['is_staff'])
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.post(reverse('admin:catalogo_exemplar_changelist'), {
            'action': 'disponibilizar', '_selected_action': [self.exemplar.pk],
        }).status_code, 403)
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.situacao, 'reservado')

    def test_acao_de_exemplar_preserva_reserva_ativa(self):
        self.usuario.is_staff = True
        self.usuario.save(update_fields=['is_staff'])
        self.usuario.user_permissions.add(Permission.objects.get(content_type__app_label='catalogo', codename='change_exemplar'))
        self.client.force_login(self.usuario)
        self.client.post(reverse('admin:catalogo_exemplar_changelist'), {
            'action': 'disponibilizar', '_selected_action': [self.exemplar.pk],
        })
        self.exemplar.refresh_from_db()
        self.reserva.refresh_from_db()
        self.assertEqual(self.exemplar.situacao, 'reservado')
        self.assertEqual(self.reserva.estado, 'pendente')

    def test_acao_de_exemplar_permite_devolucao_apos_emprestimo(self):
        cancelar_reserva(self.usuario, self.reserva.pk)
        self.usuario.is_staff = True
        self.usuario.save(update_fields=['is_staff'])
        self.usuario.user_permissions.add(Permission.objects.get(content_type__app_label='catalogo', codename='change_exemplar'))
        self.client.force_login(self.usuario)
        for acao, esperado in [('emprestar', 'emprestado'), ('disponibilizar', 'disponivel')]:
            self.client.post(reverse('admin:catalogo_exemplar_changelist'), {
                'action': acao, '_selected_action': [self.exemplar.pk],
            })
            self.exemplar.refresh_from_db()
            self.assertEqual(self.exemplar.situacao, esperado)


class DemonstracaoTests(TestCase):
    def test_seed_pode_ser_reexecutado_sem_duplicar(self):
        call_command('seed_demo', stdout=StringIO())
        obras = Obra.objects.count()
        exemplares = Exemplar.objects.count()
        usuarios = User.objects.count()
        self.assertGreaterEqual(obras, 20)
        self.assertGreater(exemplares, obras)
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(Obra.objects.count(), obras)
        self.assertEqual(Exemplar.objects.count(), exemplares)
        self.assertEqual(User.objects.count(), usuarios)
        self.assertFalse(User.objects.filter(is_superuser=True).exists())


class ConcorrenciaTests(CenarioMixin, TransactionTestCase):
    """Duas conexões reais disputam o único exemplar, em banco de teste isolado."""
    def setUp(self):
        self.criar_cenario()

    def test_duas_solicitacoes_disputam_ultimo_exemplar(self):
        barreira = Barrier(2)
        obra_id = self.obra.pk

        def tentar(usuario_id):
            close_old_connections()
            try:
                usuario = User.objects.get(pk=usuario_id)
                barreira.wait(timeout=10)
                try:
                    reserva = solicitar_reserva(usuario, obra_id)
                    return ('reservada', reserva.pk)
                except DomainError as exc:
                    return ('recusada', str(exc))
            finally:
                connections['default'].close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(tentar, [self.usuario.pk, self.outro.pk]))
        self.assertEqual(sum(estado == 'reservada' for estado, _ in resultados), 1, resultados)
        self.assertEqual(sum(estado == 'recusada' for estado, _ in resultados), 1, resultados)
        self.assertEqual(Reserva.objects.filter(estado='pendente').count(), 1)
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.situacao, 'reservado')
