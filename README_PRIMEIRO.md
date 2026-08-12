# CS Platform v5.6.9 — gestão da equipe

Este pacote completa a área **Equipe** com controles seguros para administrar o acesso dos usuários da organização.

Ele permite ao administrador:

- cadastrar um novo membro com nome, e-mail, senha temporária e perfil de acesso;
- editar o nome e o perfil de um membro;
- desativar e reativar acessos;
- visualizar o estado ativo ou inativo de cada usuário;
- identificar a própria conta, que fica protegida contra desativação pela tela;
- informar que o novo membro deverá trocar a senha temporária no primeiro acesso.

Os demais perfis podem consultar a equipe quando autorizados pela API, mas não veem os botões de administração.

## Como aplicar no GitHub

Substitua exatamente estes três arquivos no repositório `csadvogados/cs-platform`:

1. `frontend/index.html`
2. `frontend/assets/app.js`
3. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar gestão da equipe v5.6.9`

O commit deverá gerar o deployment do serviço `cs-platform-web` no Railway. Se a API aparecer como **Skipped / No changes to watched files**, isso é normal.

Aguarde o `cs-platform-web` ficar verde. Depois, abra o sistema e pressione `Ctrl + F5`.

Não altere banco, migrations, variáveis, `railway.json`, `Dockerfile`, `docker-entrypoint.sh` ou `nginx.conf`. Esta versão não exige migration.

## Teste depois do deploy

1. Entre com uma conta de administrador e abra **Equipe**.
2. Clique em **Novo membro**.
3. Cadastre um usuário de teste com uma senha temporária de pelo menos 12 caracteres.
4. Confirme que o usuário aparece na lista como ativo e com a troca de senha pendente.
5. Clique em **Editar**, altere o nome ou o perfil e salve.
6. Desative o usuário de teste e confirme que o estado muda para **Inativo**.
7. Reative o mesmo usuário e confirme que o estado retorna para **Ativo**.
8. Confirme que a sua própria linha mostra **Conta atual** e não oferece os botões de alteração de acesso.
9. Entre com um perfil não administrador e confirme que os botões **Novo membro**, **Editar**, **Ativar** e **Desativar** não aparecem.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos três arquivos substituídos e deste README.
