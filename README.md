# Biblioteca Guaíba

Protótipo local de um portal para a **Biblioteca Pública Municipal Darcy Azambuja — Guaíba/RS**. A identificação é provisória e pode ser alterada no Django Admin. O portal permite consultar o acervo, criar uma conta e reservar exemplares para uma retirada presencial demonstrativa.

**Ambiente de demonstração:** os dados não representam o acervo real e nenhuma reserva chega à biblioteca ou à prefeitura. Endereço, contatos, horários e regras oficiais estão pendentes de confirmação. Não há deploy nem integração com sistemas institucionais.

## O que foi implementado

- Página inicial, orientações de reserva, apresentação e atendimento.
- Catálogo com busca por título, autor, gênero e ISBN, sem distinção de maiúsculas ou acentos; filtros combináveis e paginação.
- Detalhes das obras, distinguindo obra bibliográfica de exemplares físicos.
- Cadastro, login, logout e acompanhamento das reservas do próprio usuário.
- Reserva e cancelamento por POST, com CSRF e operações transacionais.
- Administração de obras, exemplares, reservas, comunicados e informações institucionais pelo Django Admin.
- Carga idempotente de 20 obras demonstrativas e comando manual de expiração.
- Fontes de sistema, CSS, JavaScript e elementos gráficos locais, sem dependências visuais externas.

## Tecnologias

| Tecnologia | Responsabilidade |
| --- | --- |
| Python 3.12+ | Execução da aplicação |
| Django 5.2 LTS | ORM, migrações, autenticação, formulários, templates e Admin |
| SQLite | Banco local, criado pelas migrações |
| HTML, CSS e JavaScript | Interface responsiva e navegação acessível |
| python-dotenv | Leitura das configurações locais de `.env` |

Não é necessário Node.js, Docker, serviço pago ou conta externa para executar o projeto. A instalação inicial das dependências exige internet; o funcionamento posterior é local.

## Instalação local

Abra um terminal na pasta que contém `manage.py`. Instale Python 3.12 ou posterior compatível antes de começar.

### Linux e macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se a ativação estiver bloqueada pela política local do PowerShell, use diretamente `.venv\Scripts\python.exe` no lugar de `python` nos comandos seguintes.

Edite `.env` conforme os comentários de `.env.example`. `DJANGO_DEBUG=True` e `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]` mantêm a configuração local. Se `DJANGO_SECRET_KEY` ficar vazio, uma chave aleatória será criada em `.local-secret` na primeira execução. Você também pode gerar uma chave e copiá-la para `DJANGO_SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

A chave é exclusiva da sua instalação. Não envie `.env`, `.local-secret`, o banco SQLite ou senhas para o repositório. Mantenha o modo de desenvolvimento e os hosts locais previstos no exemplo.

Prepare o banco e inicie o servidor:

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

O comando `createsuperuser` pede os dados e a senha no terminal; não existe administrador ou senha compartilhada no código. `seed_demo` pode ser executado novamente sem duplicar os registros de demonstração. Ele não deve ser usado como importador de um acervo real.

Abra **http://127.0.0.1:8000/**. Encerre o servidor com `Ctrl+C`.

## Como usar

1. Pesquise na página inicial ou abra **Acervo**. Combine termo, autor, gênero e disponibilidade.
2. Abra os detalhes de uma obra. A disponibilidade é recalculada ao solicitar a reserva.
3. Crie uma conta demonstrativa na área do usuário, usando apenas dados fictícios. Faça login e confirme a reserva.
4. Acompanhe a solicitação em **Minhas reservas**. O cancelamento é permitido enquanto a reserva está ativa.
5. Quando não houver exemplar disponível, a interface informa a indisponibilidade; duas solicitações não podem ficar com o mesmo exemplar.

### Administração

Acesse **http://127.0.0.1:8000/admin/** com o superusuário criado localmente.

- Em **Obras**, cadastre título, autor, gênero e os dados bibliográficos conhecidos. Campos opcionais podem ficar em branco.
- Em **Exemplares**, relacione cada cópia física à obra e informe um código único de patrimônio. Ajuste a localização no formulário. Para exemplares já cadastrados, use as ações da listagem para disponibilizar, emprestar ou tornar indisponível; exemplares com reserva ativa são preservados. A obra vinculada permanece fixa para preservar o histórico.
- Em **Reservas**, consulte as solicitações e use as ações administrativas para confirmar, preparar, registrar retirada ou cancelar. A retirada deixa o exemplar emprestado nesta demonstração.
- Em **Configuração**, atualize nome, apresentação, contatos, endereço, horários, regras e o endereço do botão **Como chegar**, depois de validar essas informações oficialmente.
- Em **Comunicados**, publique os avisos exibidos na página inicial.
- Em **Usuários** e **Grupos**, conceda a funcionários somente as permissões necessárias. Marcar alguém como membro da equipe permite entrar no Admin, mas não concede automaticamente acesso a todos os modelos.

Para processar reservas vencidas, execute manualmente:

```bash
python manage.py expirar_reservas
```

O protótipo não contém agendador. Enquanto o comando não for executado, a expiração não é um serviço automático em segundo plano.

## Verificações

Com o ambiente virtual ativo:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Os testes abrangem modelos, busca, filtros, autenticação, reservas, cancelamento, permissões, acesso entre usuários, transições de estado e concorrência pelo último exemplar. A base de testes é isolada da base utilizada na demonstração.

O resultado da execução está em [docs/verificacao.md](docs/verificacao.md). Veja também o [roteiro de testes manuais](docs/testes-manuais.md) para teclado, leitores de tela e diferentes tamanhos de tela. As práticas implementadas buscam WCAG 2.2 AA e recomendações eMAG; uma auditoria formal de acessibilidade ainda é necessária.

## Arquitetura e integração futura

A organização e os fluxos estão descritos em [docs/arquitetura.md](docs/arquitetura.md). Views e templates utilizam serviços de catálogo e reservas; o contrato de integração mantém a implementação local separada de uma futura fonte autorizada.

Antes de integrar o sistema institucional, será necessário conhecer o software em uso, SGBD e esquema, APIs disponíveis, regras de empréstimo e reserva, identificadores de obras/exemplares, autenticação e autorização técnica, política de dados e qual sistema será a fonte oficial da disponibilidade. Nenhum SGBD é presumido. Uma migração futura para PostgreSQL exige configurar o banco e instalar o driver adequado; não torna essa integração automática.

## Limites e próximos passos

Este projeto serve para avaliação local. Não está preparado para operação pública: publicação exige revisão de segurança, HTTPS, configuração de produção, backups, observabilidade, política de privacidade, gestão de contas e validação institucional. Os exemplares e metadados de demonstração não devem ser tratados como registros oficiais.

Não há integração legada, empréstimos completos, notificações, recomendações ou assistente de IA nesta etapa. A devolução demonstrativa é registrada pelo funcionário pela ação **Marcar como disponíveis** em um exemplar emprestado. Os próximos passos são validar nome e atendimento, testar com cidadãos e funcionários, auditar acessibilidade e investigar a integração autorizada.
