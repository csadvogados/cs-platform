# Publicação no Render

1. Crie um repositório privado no GitHub chamado `cs-platform`.
2. Envie o conteúdo desta pasta para a raiz do repositório.
3. No Render, escolha **New > Blueprint** e selecione o repositório.
4. O Render detectará o arquivo `render.yaml` e criará a API e o PostgreSQL.
5. Quando solicitado, defina `INITIAL_ADMIN_PASSWORD` com uma senha forte.
6. Após o deploy, abra `https://<servico>.onrender.com/docs`.
7. Em Settings > Custom Domains, adicione `api.rdsconsultoria.com.br`.
8. Na HostGator, crie o registro DNS indicado pelo Render.

Não envie arquivos `.env`, senhas ou bancos SQLite ao GitHub.
