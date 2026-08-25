# CS Platform v5.11.0 — Ações de cobrança

Este pacote deve ser aplicado sobre a versão v5.10.0.

## O que foi adicionado

- Registro de contatos de cobrança por parcela.
- Canais: ligação, WhatsApp, e-mail, negociação e outros.
- Resultados do contato, incluindo promessa de pagamento.
- Data e valor prometidos.
- Programação do próximo acompanhamento.
- Histórico completo por parcela, com responsável e data.
- Alertas de acompanhamentos para hoje e atrasados.
- Registro das ações no Histórico de atividades.

## Arquivos

Substitua ou adicione os 10 arquivos deste pacote exatamente nos mesmos caminhos do repositório.

O arquivo novo abaixo deve ser criado no GitHub:

`backend/alembic/versions/0011_collection_actions.py`

## Commit sugerido

`feat: adicionar ações e lembretes de cobrança v5.11.0`

## Deploy

1. Envie todos os arquivos no mesmo commit.
2. Aguarde o deploy da API e do site.
3. A API executará automaticamente a migração `0011_collection_actions` ao iniciar.
4. Não configure nem altere o campo Pre-deploy Command do Railway.

## Teste após o deploy

1. Atualize o sistema com `Ctrl + F5` e entre novamente.
2. Abra **Cobranças**.
3. Clique em **Registrar contato** em uma parcela aberta.
4. Escolha **Promessa de pagamento**, informe data, valor, próximo acompanhamento e observações.
5. Salve e confirme que o registro aparece no histórico da parcela.
6. Confirme que a coluna **Último contato** e os alertas de acompanhamento foram atualizados.
7. Abra **Histórico** no menu e confirme o registro da ação de cobrança.

## Verificação do banco

Nos logs da API, a revisão final deve aparecer como:

`0011_collection_actions (head)`
