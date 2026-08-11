# CS Platform v5.6.3 — edição do cliente

Este pacote acrescenta **Editar cadastro** na página de detalhes do cliente.

É possível alterar:

- nome;
- profissão;
- e-mail;
- telefone;
- cidade e estado;
- observações;
- status do atendimento.

O CPF fica protegido durante a edição. Receitas, despesas, dívidas, CRM e diagnósticos não são apagados nem recriados.

## Como aplicar no GitHub

Esta é uma atualização incremental sobre a v5.6.2. Substitua somente estes dois arquivos no repositório `csadvogados/cs-platform`:

1. `frontend/index.html`
2. `frontend/assets/app.js`

Use este nome no commit:

`feat: adicionar edição do cliente v5.6.3`

Somente o deployment `cs-platform-web` deverá ser iniciado no Railway. Aguarde-o ficar verde e pressione `Ctrl + F5` no sistema.

Não altere backend, banco, migrations, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`.

## Teste depois do deploy

1. Entre em **Clientes** e clique em **Ver detalhes**.
2. Clique em **Editar cadastro**.
3. Confira se os campos aparecem preenchidos e se o CPF está bloqueado.
4. Altere um campo, como profissão ou status, e clique em **Salvar alterações**.
5. Confirme que o novo dado aparece na página.
6. Confira se receitas, despesas, dívidas e diagnóstico continuam iguais.
7. Abra a edição novamente e teste os botões **Cancelar** e **X**.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos dois arquivos substituídos.
