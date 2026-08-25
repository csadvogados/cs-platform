# Correção de implantação da v5.12.0

O log mostrou que o identificador da migração `0012_collection_action_cancellation` excedia o limite de 32 caracteres da tabela do Alembic.

## Arquivo que deve ser substituído

Envie o arquivo desta pasta para o mesmo caminho do repositório:

`backend/alembic/versions/0012_collection_action_cancellation.py`

Confirme a substituição do arquivo existente e faça o commit. O nome do arquivo permanece igual; apenas o identificador interno foi encurtado para `0012_action_cancellation`.

Depois, aguarde o novo deploy da API. A migração anterior foi executada em uma transação e falhou ao registrar a versão, portanto o novo deploy pode reaplicá-la com segurança.

## Resultado esperado no log

`0012_action_cancellation (head)`

seguido da conclusão das migrações e da inicialização da API.
