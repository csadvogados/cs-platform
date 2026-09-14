# Restauração após substituição do backend

Esta correção recupera os arquivos de backend e configuração Render do commit `2d478c0`, que contém o backend homologado e a primeira entrega do Perfil 360. Os pacotes v5.5.0/v5.5.1 baseados no snapshot antigo não representam o conjunto atual de funcionalidades.

São recuperados os módulos de leads, contratos, documentos, negociações, RecoveryCase, notificações, financeiro, permissões e a rota `/api/v1/clients/{client_id}/profile`.

A cadeia original possui uma única cabeça: `0028_contract_deliveries`. O arquivo divergente `0007_cs_captacao_mvp` foi removido do código; nenhum downgrade, stamp, exclusão de dados ou comando contra o banco de produção foi executado. Todos os arquivos removidos permanecem recuperáveis no histórico Git.

Antes de publicar, conferir a revisão do banco no Railway com `alembic current`. Se contiver `0007_cs_captacao_mvp`, interromper a publicação e comparar o esquema: não executar stamp nem downgrade para ocultar a divergência. A restauração não desfaz transformações eventualmente já aplicadas aos dados por essa migration.

O Perfil 360 foi preservado em seu escopo inicial. Ampliações de histórico e navegação serão tratadas após a recuperação e homologação da plataforma.
