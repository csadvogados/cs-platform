# Continuidade CS Platform — 21/09/2026

## Base e limites da revisão

Base atual conferida: `origin/main`, commit `62132b7`. Preservadas as correções manuais posteriores ao PR32. Não reutilizar snapshots v5.4/v5.5 sobre esta base. Consultadas as conversas acessíveis abaixo, suas entregas recentes e o código; conversas longas têm páginas anteriores não esgotadas. Isto não é uma auditoria integral de todas as mensagens nem uma nova homologação de produção.

## Conversas localizadas

- Implementar MVP de captação CRM — entrega do funil, propostas, contratos, notificações, Perfil 360 e homologações do usuário.
- Continuar Clientes.py no Chat — correções manuais de permissões, Novo lead e arquivamento; última pendência: limpeza controlada de testes.
- Continuar CRM manualmente — incidente de snapshot antigo e migrations incompatíveis; superado pela restauração documentada no PR31.
- Organizar ações CS Recupera — CRM transversal como Prioridade 2; aproveitar o Recupera com clientes reais.
- Consolidar Kit CS Recupera — entrega relatada de 30 arquivos operacionais; revisar campos profissionais antes do uso.
- Mapear API CS Recupera 1.0 — diagnóstico/negociação e roadmap de acordos/documentos. Conferir cada pendência antiga no código antes de implementá-la.
- Implementar Sprint 1 da CS Platform — base organizacional e comercial; também contém materiais da CS Consultores.
- Corrigir e validar v5.4.2 — evolução posterior até indicadores/metas; propostas antigas não equivalem a pendências atuais.
- Estratégias Lucrativas na Advocacia — histórico da base antiga e correções de empacotamento.
- Explicar limite de créditos — escopo inicial do Sprint 1.
- Análise de concorrentes da API — arquitetura modular e roadmap.
- Como atuar na captação — CS Capta Recursos é produto futuro, distinto do CRM de leads.
- CS Recupera Perfil — produto jurídico de contas digitais; NÃO confundir com Perfil 360 do Cliente.
- Divulgação do CS Recupera — materiais e links de atendimento por origem; sem nova integração autorizada.
- Criar redes da CS Platform — presença institucional e contato; não comprova publicação das etapas sugeridas.

## Estado consolidado

Implementados no repositório e com homologações relatadas: CRM, conversão cliente/caso, propostas, contratos e registro manual de assinatura, modelos, notificações, Perfil 360 e arquivamento de leads. Permissões de criação/edição de clientes já migraram para CLIENT_CREATE/CLIENT_UPDATE. CRM já usa CRM_READ/CREATE/UPDATE/DELETE/CONVERT.

Lacuna confirmada nesta retomada: Perfil 360 exigia apenas CLIENT_READ, expondo resumo comercial a perfil sem CRM_READ. Correção desta entrega: exigir ambas as permissões, sem alterar a matriz de perfis ou o banco.

## Próximas ações, em ordem

1. Validar automaticamente a matriz comercial, o bloqueio do Perfil 360 e o acesso cruzado por organização; revisar o diff antes de publicar.
2. Conferir permissões da interface por ação (não só acesso ao CRM), incluindo financeiro somente leitura e negociador sem conversão. Ampliar testes de contratos e vínculos entre organizações.
3. Revisar proteção do formulário de login se JavaScript falhar. O histórico registra senha aparecendo em URL; não reproduzir senha, não redefinir credenciais automaticamente. O titular deve confirmar que a senha exposta foi trocada.
4. Inventariar registros de teste e seus derivados antes de qualquer limpeza. O histórico relata TESTE DELETE arquivado; TESTE RBAC e os convertidos exigem conferência. Não realizar exclusão automática nem presumir que arquivar lead arquiva cliente, caso ou contrato.
5. Piloto operacional com cliente real, acompanhado de checklist e kit documental. Registrar falhas antes de expandir módulos.
6. Só depois priorizar CS Recupera Perfil e CS Capta Recursos mediante escopo próprio.

Continuam fora desta entrega: chatbot, IA, anúncios, scraping, assinatura/cobrança automática e integrações externas. Nenhuma migration ou alteração de produção necessária nesta correção.

## Verificação desta entrega

- 10 testes existentes de clientes/CRM passaram.
- Novo teste de permissões passou após corrigir o CPF obrigatório da fixture: criação por administrador/advogado/atendimento, bloqueio de criação por financeiro, leitura do resumo por equipe comercial, bloqueio do perfil cliente, bloqueios de arquivamento/conversão e 404 para outra organização.
- 23 testes de interface passaram após substituir duas expectativas obsoletas do cache-buster por conferência de script versionado. Sintaxe JavaScript válida.
- Teste de papéis usa identidade controlada por override; não substitui testes de autenticação real nem demonstra isolamento completo de todos os endpoints.
- Pendência adicional: perfil `cliente` possui CLIENT_READ; revisar vínculo a cliente específico nas rotas gerais antes de disponibilizar portal externo. A correção atual protege apenas o resumo comercial.
