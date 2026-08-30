# CS Platform v5.24.0 — Central Gerencial

Esta versão reúne os principais indicadores comerciais, financeiros e operacionais em um painel gerencial único.

## O que foi incluído

- nova opção **Indicadores** no menu;
- períodos rápidos de 7, 30 e 90 dias, além de período personalizado;
- comparação automática com o período anterior equivalente;
- indicadores de novos clientes, atendimentos, tarefas concluídas e recebimentos;
- taxas de conversão comercial e recuperação financeira;
- evolução diária visual da operação;
- funil completo do CRM com quantidade e valor por etapa;
- painel de riscos com tarefas e cobranças atrasadas;
- recomendações gerenciais automáticas;
- produtividade individual da equipe;
- exportação CSV do relatório gerencial;
- acesso protegido pelas permissões `report.read` e `report.export`;
- layout responsivo para computador, tablet e celular.

Não possui migração de banco.

Commit: `feat: adicionar central gerencial e indicadores executivos v5.24.0`

## Como testar

1. Entre com um perfil administrador, supervisor, advogado ou financeiro e abra **Indicadores**.
2. Confira os seis indicadores principais e as comparações com o período anterior.
3. Troque entre 7, 30 e 90 dias.
4. Informe um período personalizado e clique em **Aplicar período**.
5. Confira a evolução diária, os riscos atuais e o funil comercial.
6. Confira a tabela **Desempenho da equipe**.
7. Clique em **Exportar CSV** e abra o arquivo.
8. Entre com um perfil sem `report.read` e confirme que **Indicadores** não aparece no menu.

