# Roteiro de verificação manual

Execute `migrate`, `seed_demo`, crie um administrador e inicie `runserver`, conforme o README. Use somente contas e dados fictícios. Execute os testes em uma cópia local de avaliação.

## Navegação e conteúdo

1. Abra a página inicial e confirme que a identificação de demonstração está visível.
2. Use todos os links principais: início, acervo, como reservar, sobre, atendimento e área do usuário.
3. Confira se endereço, horário e contatos não confirmados aparecem como pendentes; não devem parecer contatos oficiais validados.
4. Busque uma palavra acentuada com e sem acento e em maiúsculas. Confira título, autor, gênero e ISBN quando houver.
5. Combine filtros, avance e volte na paginação. Os filtros e o termo devem ser preservados.
6. Faça uma busca sem resultados. A página deve explicar como ajustar a pesquisa.
7. Abra uma obra sem ISBN, editora, ano ou sinopse. A página deve continuar legível e sem imagens quebradas.

## Fluxo de reserva

1. Sem autenticação, abra uma obra disponível e siga o acesso à conta. Cadastre uma conta e volte aos detalhes da obra.
2. Confirme a reserva; verifique a mensagem, a lista pessoal e a redução de disponibilidade.
3. Atualize a página e tente reservar o último exemplar novamente. Não deve haver duplicação da posse do exemplar.
4. Cancele uma reserva ativa. Confira a situação cancelada e a disponibilidade restabelecida.
5. Faça login em outra conta. A reserva da primeira conta não deve aparecer nem poder ser cancelada ao alterar a URL manualmente.
6. Abra uma obra indisponível. A interface deve explicar a situação e impedir a reserva.
7. Tente solicitar e cancelar com URL aberta diretamente (GET). Nenhum dado deve ser alterado.

## Administração

1. Com uma conta comum, tente abrir `/admin/`; não deve conseguir administrar dados.
2. Com o administrador local, crie uma obra e vários exemplares com códigos distintos.
3. Tente usar um código de exemplar repetido. Confira uma mensagem de validação.
4. Reserve um exemplar e confirme, prepare e registre sua retirada no Admin. Ele deve terminar emprestado.
5. Tente pular uma transição de reserva. A operação deve ser impedida com uma mensagem legível. Use a ação de disponibilizar um exemplar com reserva ativa; ele deve continuar reservado, conforme a mensagem da ação.
6. Configure um prazo próximo no futuro em uma reserva ativa. Quando o prazo vencer, execute `python manage.py expirar_reservas` e confira a liberação do exemplar.
7. Altere o nome e os dados de atendimento no Admin e confira o site. Publique e retire um comunicado.
8. Crie um funcionário com permissões específicas. Confira que ser membro da equipe não concede permissão para os demais modelos.

## Teclado e acessibilidade

1. Use `Tab`, `Shift+Tab`, `Enter`, `Espaço` e `Esc` sem mouse. O foco deve ser visível e seguir uma ordem coerente.
2. Acione o link **Pular para o conteúdo**. O foco deve alcançar o conteúdo principal.
3. No celular, abra e feche o menu por teclado e confira `aria-expanded` com uma ferramenta de inspeção.
4. Envie login e cadastro com campos vazios, senhas inválidas e usuário duplicado. Mensagens e rótulos devem permitir corrigir cada erro.
5. Use NVDA/Firefox, VoiceOver/Safari ou ferramenta equivalente. Confira idioma, título da página, regiões, cabeçalhos, rótulos, mensagens e situações de disponibilidade.
6. Aumente o zoom até 200% e 400%. O conteúdo deve refluir sem perda de ações; confira também espaçamento de texto aumentado.
7. Ative redução de movimento no sistema. A interface não deve exigir animação para funcionar.
8. Verifique contraste com uma ferramenta de auditoria. A cor nunca deve ser o único indicador de situação.

## Tamanhos de tela e compatibilidade

Teste pelo menos 360 × 800, 768 × 1024 e 1440 × 900, em navegadores atuais. Confira que cartões e formulários reflitam o espaço disponível, que o menu seja utilizável, que os botões tenham área de toque confortável e que não haja rolagem horizontal da página. No mínimo, percorra início → pesquisa → detalhes → login/cadastro → reserva → cancelamento em tela pequena e grande.

## Registro do resultado

Anote navegador, versão, resolução, passos, resultado esperado e observado de cada falha. Anexe captura sem dados pessoais quando ajudar. Este roteiro complementa os testes automatizados; não constitui certificação WCAG ou eMAG.
