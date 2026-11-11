# Registro de verificação

Verificação automatizada executada em **11 de novembro de 2026**, com Python 3.12.14, Django 5.2.19 e SQLite, em ambiente Linux.

| Comando | Resultado |
| --- | --- |
| `python manage.py check` | Aprovado, sem problemas identificados |
| `python manage.py makemigrations --check --dry-run` | Aprovado, nenhuma alteração de modelo sem migração |
| `python manage.py test --noinput` | **42 testes aprovados**, em 37,127 segundos |

A suíte usa um banco SQLite de teste separado, criado e removido pelo Django. O teste de concorrência abre duas conexões em threads distintas para disputar o único exemplar disponível e confirma que apenas uma reserva é criada. A outra solicitação recebe um erro de domínio legível.

Os testes cobrem:

- Obras com metadados opcionais, códigos únicos de exemplares e restrições de situação.
- Busca por título, autor, gênero e ISBN sem distinção de caixa ou acentos, atualização do índice de busca, filtros combinados, contagens e paginação.
- Páginas públicas, detalhes com dados ausentes e página de erro com falha na obtenção das configurações do banco.
- Cadastro com senha protegida, login, logout por POST e exigência de autenticação para reservas.
- Bloqueio de redirecionamento de cadastro para URL externa e preservação de retorno local.
- Solicitação, indisponibilidade, repetição da disputa pelo último exemplar e cancelamento.
- Isolamento entre usuários, operações restritas a POST e rejeição de POST sem CSRF.
- Transições válidas e inválidas, retirada, prazo vencido, expiração, unicidade de reserva ativa e rollback integral em caso de inconsistência.
- Acesso ao Admin por usuários comuns e funcionários com ou sem permissões, ações de reserva e ações de situação do exemplar que preservam reservas ativas.
- Empréstimo e devolução demonstrativos e repetição da carga `seed_demo` sem duplicação ou criação de administrador com senha fixa.

Esses resultados verificam o comportamento nas condições testadas. A acessibilidade completa, a adequação institucional e a preparação para produção exigem avaliação própria. O [roteiro manual](testes-manuais.md) registra verificações adicionais de teclado, leitores de tela e compatibilidade.

## Navegador

Verificação com Playwright e Chromium local, sem adicionar dependências ao projeto Django:

- Páginas públicas e formulários responderam com HTTP 200 e sem erros de JavaScript.
- Ausência de rolagem horizontal nas páginas de início, acervo, atendimento e cadastro nas larguras de 360, 390, 768 e 1440 pixels.
- Menu móvel aberto por teclado, fechamento por Esc com retorno do foco e link de pular para o conteúdo como primeiro foco.
- Fluxo completo: obra disponível → login → cadastro com retorno à obra escolhida → reserva → acompanhamento → cancelamento → sair → entrar novamente.
- O fluxo de conta e reserva passou no desktop e em viewport móvel de 390 pixels; a lista de reservas também foi verificada quanto à rolagem horizontal.
- Conta comum redirecionada à autenticação administrativa ao tentar acessar o Admin.
- Inspeção visual de capturas da página inicial no desktop e do catálogo no celular.

A validação móvel identificou e corrigiu a interceptação de toques por decoração de capa, além de disponibilizar a saída da conta no menu móvel. Leitores de tela reais, auditoria completa de contraste, múltiplos motores de navegador e avaliação institucional não foram executados nesta sessão; veja o roteiro manual.
