# CS Platform v5.12.0 — Central de cobranças

Este pacote deve ser aplicado sobre a versão v5.11.0.

## Novidades

- Anulação segura de ações de cobrança por administrador.
- Justificativa obrigatória para cada anulação.
- Registro original preservado e identificado como anulado.
- Administrador, data e motivo da anulação exibidos no histórico.
- Registros anulados deixam de contar nos indicadores.
- Filtros por acompanhamento atrasado, para hoje, futuro ou não agendado.
- Filtros por promessa vencida, para hoje, futura ou inexistente.
- Indicadores de acompanhamentos futuros e promessas abertas ou vencidas.
- Promessa e valor exibidos diretamente na agenda.
- Auditoria da anulação no Histórico de atividades.

## Arquivos

Substitua ou adicione os 9 arquivos exatamente nos mesmos caminhos do repositório.

Arquivo novo:

`backend/alembic/versions/0012_collection_action_cancellation.py`

## Commit sugerido

`feat: ampliar central e anulação de cobranças v5.12.0`

## Deploy

1. Envie os 9 arquivos no mesmo commit.
2. Aguarde o deploy da API e do site.
3. A API executará automaticamente a migração `0012_collection_action_cancellation`.
4. Não configure nem altere o campo Pre-deploy Command do Railway.

## Teste após o deploy

1. Atualize com `Ctrl + F5` e entre novamente.
2. Abra **Cobranças** e confirme os novos filtros de acompanhamento e promessa.
3. Abra o histórico de uma parcela que tenha contato registrado.
4. Como administrador, clique em **Anular registro**.
5. Informe uma justificativa e confirme.
6. Verifique se o registro permanece visível como **Anulado**.
7. Confirme que ele deixou de contar nos indicadores e filtros.
8. Abra **Histórico** no menu e confirme a atividade **Anulou — Ação de cobrança**.

## Revisão do banco

Nos logs da API, a revisão final deve aparecer como:

`0012_collection_action_cancellation (head)`
