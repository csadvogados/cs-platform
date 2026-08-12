# CS Platform v5.7.4 — Segurança da importação e exclusão de clientes

Este pacote corrige o fluxo de importação e adiciona a exclusão segura de clientes.

## O que foi corrigido

- o botão **Conferir arquivo** apenas apresenta a prévia e não grava clientes;
- o botão de importação permanece bloqueado até a caixa de autorização ser marcada;
- depois da autorização, uma segunda janela informa a quantidade e o nome do arquivo;
- os clientes só são gravados ao clicar em **Confirmar e gravar**;
- botão **Apagar cliente** disponível somente para administrador ou superadministrador;
- a exclusão exige confirmação mostrando o nome do cliente;
- clientes com registros vinculados não podem ser apagados;
- exclusões concluídas ficam registradas no **Histórico de atividades**.

## Arquivos que devem ser substituídos

Substitua somente estes quatro arquivos no repositório `csadvogados/cs-platform`:

1. `backend/app/api/routes/clients.py`
2. `frontend/index.html`
3. `frontend/assets/app.js`
4. `frontend/assets/styles.css`

Os arquivos já estão nas pastas corretas dentro deste ZIP.

## Aplicação pelo GitHub

1. Extraia este ZIP no computador.
2. Abra o repositório `csadvogados/cs-platform` no GitHub.
3. Substitua os quatro arquivos acima, mantendo exatamente os mesmos caminhos.
4. Faça todos os arquivos no mesmo commit.
5. Use este nome no commit:

   `fix: proteger importação e exclusão de clientes v5.7.4`

6. Confirme o commit na branch `main`.
7. Aguarde os deployments de `cs-platform-api` e `cs-platform-web` ficarem **Successful** no Railway.

## Não altere no Railway

Esta versão não exige:

- migration do banco de dados;
- variável nova;
- mudança em `railway.json`;
- mudança em `Dockerfile`;
- comando manual no Console.

## Teste da importação

1. Abra `https://cs-platform-web-production.up.railway.app/`.
2. Pressione `Ctrl + F5`.
3. Entre com a conta de administrador.
4. Abra **Clientes → Importar CSV**.
5. Selecione um arquivo e clique em **Conferir arquivo**.
6. Feche a janela, atualize a lista e confirme que nenhum cliente foi gravado.
7. Abra a importação novamente, confira o arquivo e marque **Revisei os dados acima e autorizo a gravação**.
8. Clique em **Importar clientes**.
9. Confira a segunda janela. A base ainda não foi alterada nesse momento.
10. Clique em **Confirmar e gravar** para concluir.

## Como apagar o cliente Teste

Depois do deployment:

1. Abra **Clientes**.
2. Pesquise `Teste`.
3. Clique em **Ver detalhes**.
4. Clique em **Apagar cliente**.
5. Confira o nome e confirme.

Se o cliente não possuir registros vinculados, será apagado. Caso tenha histórico, o sistema impedirá a exclusão e informará quais registros precisam ser tratados primeiro.

## Registros que bloqueiam a exclusão

- receitas;
- despesas;
- dívidas;
- diagnósticos;
- contatos do CRM;
- atendimentos;
- oportunidades;
- tarefas.

## Validações realizadas

- sintaxe Python e JavaScript;
- isolamento do cliente por organização;
- permissão `client.delete` restrita ao administrador;
- bloqueio de todos os vínculos financeiros e do CRM;
- trava do registro durante a verificação de exclusão;
- auditoria da exclusão;
- conferência do CSV sem gravação;
- botão de importação inicialmente bloqueado;
- caixa de autorização obrigatória;
- segunda janela de confirmação antes da gravação;
- exclusão real de cliente sem histórico em ambiente local isolado;
- bloqueio real de cliente com receita vinculada;
- estrutura e hashes SHA-256 do ZIP.
