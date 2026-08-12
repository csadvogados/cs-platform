# CS Platform v5.7.0 — configurações e segurança

Este pacote completa a área **Configurações** e corrige a revogação das sessões no backend.

Ele permite:

- consultar e atualizar razão social, nome de apresentação, e-mail e telefone da organização;
- restringir a alteração dos dados institucionais aos perfis autorizados;
- alterar a senha da conta conectada;
- exigir confirmação da nova senha no frontend;
- direcionar usuários com senha temporária para a área de troca de senha;
- visualizar as sessões ativas com navegador, sistema, IP e datas;
- encerrar uma sessão específica;
- encerrar todas as sessões e sair da plataforma;
- revogar corretamente o token de renovação associado à sessão encerrada;
- revogar todas as sessões e tokens após a alteração da senha;
- registrar navegador e IP nos novos acessos.

Sessões criadas antes desta atualização podem aparecer como **Dispositivo não identificado**. Os dados do navegador e do IP passam a ser gravados nos novos logins.

## Como aplicar no GitHub

Substitua exatamente estes seis arquivos no repositório `csadvogados/cs-platform`:

1. `backend/app/api/routes/auth.py`
2. `backend/app/api/routes/access_control.py`
3. `backend/app/core/config.py`
4. `frontend/index.html`
5. `frontend/assets/app.js`
6. `frontend/assets/styles.css`

Use este nome no commit:

`feat: adicionar configurações e segurança v5.7.0`

O commit deverá gerar deployments dos serviços `cs-platform-api` e `cs-platform-web` no Railway.

Aguarde os dois serviços ficarem verdes. Depois, abra o sistema e pressione `Ctrl + F5`.

Esta versão não exige migration e não altera `railway.json`, `Dockerfile`, `docker-entrypoint.sh`, `nginx.conf` ou as variáveis do Railway.

## Teste depois do deploy

1. Entre na plataforma e abra **Configurações**.
2. Confirme que os dados da organização foram carregados.
3. Altere o nome de apresentação ou o telefone e clique em **Salvar organização**.
4. Abra o sistema em outro navegador ou janela anônima e faça um segundo login.
5. Volte para **Configurações** e confirme que existem duas sessões ativas.
6. Encerre apenas a segunda sessão e confirme que ela desaparece da lista.
7. Altere a senha usando a senha atual e uma nova senha de pelo menos 12 caracteres.
8. Confirme que a plataforma encerra todas as sessões e solicita um novo login.
9. Entre novamente usando a nova senha.
10. Opcionalmente, entre com um usuário que não seja administrador e confirme que os dados da organização ficam somente para leitura.

## Conferência

O arquivo `SHA256SUMS.txt` contém os códigos SHA-256 dos seis arquivos substituídos e deste README.
