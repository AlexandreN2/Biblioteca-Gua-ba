# Arquitetura

## Visão geral

O portal é uma aplicação Django renderizada no servidor. O navegador recebe HTML dos templates; CSS e JavaScript locais cuidam da apresentação e do menu. A lógica de catálogo e reservas funciona em Python e persiste no SQLite pelo ORM. Não há chamadas ao banco institucional nem serviços externos necessários à navegação.

```text
Navegador
   │ GET de páginas / POST de ações com CSRF
   ▼
URLs → Views e formulários → Serviços → Modelos / ORM → SQLite
             │
             ▼
         Templates + arquivos estáticos locais
```

## Responsabilidades

| Diretório | Responsabilidade |
| --- | --- |
| `config/` | Configurações, URLs principais e pontos de entrada WSGI/ASGI |
| `apps/core/` | Conteúdo institucional, comunicados e páginas informativas |
| `apps/catalogo/` | Obras, exemplares, consultas e administração bibliográfica |
| `apps/reservas/` | Reserva de exemplares, estados, cancelamento e expiração |
| `apps/usuarios/` | Cadastro e perfil mínimo, apoiados na autenticação Django |
| `apps/integracoes/` | Contrato para uma futura implementação de acesso ao acervo |
| `templates/` e `static/` | Apresentação HTML, CSS, SVG e JavaScript |
| `tests/` | Verificação automatizada de comportamento e integridade |

As views interpretam a requisição, validam formulários e escolhem a resposta. Os serviços decidem quais dados consultar e como executar as operações de domínio. Os templates exibem os resultados. Essa separação evita que reservar um exemplar dependa do desenho de uma página.

## Dados

**Obra** representa o conteúdo bibliográfico: título, autoria, gênero e metadados opcionais. **Exemplar** representa cada cópia física e possui código único, localização e situação. Uma obra pode ter vários exemplares, cada um com disponibilidade independente.

**Reserva** vincula um usuário a um exemplar. Não armazena CPF ou endereço residencial. O usuário é autenticado pelo sistema nativo do Django; senhas são armazenadas com os mecanismos do framework. O perfil complementa apenas os dados mínimos usados no protótipo.

**Configuração** centraliza a identificação provisória, atendimento e regras. **Comunicado** permite publicar conteúdo na página inicial. Dados pendentes permanecem identificados como não confirmados.

Relacionamentos preservam registros com histórico: apagar uma obra, exemplar ou usuário referenciado não deve remover reservas silenciosamente. Restrições de integridade complementam as validações da aplicação.

## Catálogo

A consulta é feita pelos serviços do catálogo, combinando termo, gênero, autor e disponibilidade. Um campo de busca normalizado remove diferenças de acentos e de maiúsculas, inclusive no SQLite. As contagens são calculadas a partir dos exemplares, e a view pagina os resultados. As capas são representações gráficas locais; não correspondem a capas editoriais oficiais.

O campo normalizado é mantido no salvamento das obras. Uma futura importação em lote deve passar pelo mesmo mecanismo ou reconstruir esse campo; escrever diretamente no banco contorna essa manutenção.

## Reserva e concorrência

1. A view exige usuário autenticado, método POST e proteção CSRF.
2. O serviço confirma a disponibilidade dentro da transação.
3. Uma atualização condicional muda somente um exemplar ainda disponível para reservado. O número de linhas alteradas indica se a disputa foi vencida.
4. O serviço cria a reserva pendente na mesma transação.
5. Restrições do banco impedem mais de uma reserva ativa para o mesmo exemplar.
6. Um erro desfaz a transação; a view devolve uma mensagem de domínio compreensível.

SQLite não oferece os mesmos bloqueios de linha de PostgreSQL. Por isso a atualização condicional e a restrição de unicidade são necessárias. Em concorrência, o serviço também trata bloqueios do SQLite como indisponibilidade temporária, sem expor mensagens do banco ao cidadão. Essa proteção não transforma SQLite em um banco apropriado para tráfego público intenso.

## Estados

O fluxo normal é:

```text
pendente → confirmada → pronta → retirada
    │           │         │
    └───────────┴─────────┴──→ cancelada ou expirada
```

Reservas ativas mantêm o exemplar reservado. Cancelamento ou expiração liberam o exemplar. A retirada o torna emprestado, demonstrando a saída física. Estados terminais não devem ser reabertos por edição direta. A devolução é feita pelo funcionário pela ação de disponibilizar um exemplar emprestado; um módulo completo de empréstimos não faz parte desta etapa.

O Admin usa os mesmos serviços nas mudanças de reserva. Isso evita que confirmar, retirar ou cancelar pela administração deixe o exemplar em uma situação incompatível. A situação de exemplares já existentes é alterada por ações condicionais na listagem do Admin; essas ações preservam exemplares com reservas ativas. A obra vinculada não é editável após o cadastro. As permissões nativas do Django limitam as operações de funcionários. Um usuário comum só consulta e cancela suas próprias reservas.

`expirar_reservas` busca reservas ativas com prazo vencido e executa a transição apropriada. É um comando manual: não existe serviço periódico em execução.

## Demonstração e instalação

As migrações criam a estrutura do banco. `seed_demo` insere dados identificados para demonstração e pode ser repetido sem duplicação. Não cria senhas administrativas fixas. O banco local e as configurações privadas não pertencem aos arquivos distribuídos.

O funcionamento usa arquivos locais após a instalação das dependências. O `.env` separa configurações da instalação do código. O servidor de desenvolvimento atende apenas à avaliação local e não substitui uma configuração de produção.

## Contrato para integração futura

O contrato agrupa as operações esperadas: listar obras, obter obra por identificador, consultar disponibilidade, solicitar reserva, listar reservas de um usuário e cancelar reserva. A implementação inicial utiliza os serviços e o ORM locais.

Para integrar futuramente:

1. Identificar software, SGBD, tabelas ou API, permissões e regras reais.
2. Definir a fonte oficial de disponibilidade, empréstimos e reservas e os limites de escrita.
3. Mapear identificadores externos e estados, evitando duplicação de obras e exemplares.
4. Implementar um adaptador autorizado com os mesmos resultados e erros de domínio.
5. Definir comportamento diante de falhas, repetição de chamadas, sincronização e conflitos.
6. Verificar autenticação, proteção de dados, auditoria e testes de contrato antes de habilitar acesso real.

Migrar o banco local para PostgreSQL é uma decisão separada da integração. A estrutura Django permite alterar a configuração e instalar o driver, mas esquema, credenciais, migrações e testes precisam de validação. Nenhuma decisão sobre o banco existente é presumida.

Assistente virtual, notificações e recomendações podem consumir os serviços no futuro. Não estão implementados nem são necessários ao fluxo atual.
