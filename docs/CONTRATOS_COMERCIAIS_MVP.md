# Gestão de propostas e contratos — MVP

## Escopo entregue

- geração de contrato a partir de proposta aceita e lead convertido;
- vínculo obrigatório com organização, lead, proposta e cliente;
- numeração por organização e conteúdo inicial editável pela API;
- fluxo `RASCUNHO → EM_REVISAO → APROVADO → ENVIADO → ASSINADO`;
- aprovação restrita a administrador, supervisor do sistema ou advogado;
- referência obrigatória para registrar assinatura manual;
- documento HTML pronto para impressão ou salvamento em PDF;
- timeline do lead, auditoria e exclusão lógica preparadas no modelo.

Assinatura eletrônica automática e integração com provedores externos continuam fora do escopo.

## Migration

Aplicar `alembic upgrade head`. A revision `0026_commercial_contracts` cria a tabela `commercial_contracts` e seus índices multitenant.

## Endpoints

- `POST /api/v1/leads/{lead_id}/proposals/{proposal_id}/contract`
- `PATCH /api/v1/leads/{lead_id}/contracts/{contract_id}/status`
- `GET /api/v1/leads/{lead_id}/contracts/{contract_id}/document`
- `GET /api/v1/leads/{lead_id}/timeline` passa a incluir `contracts`.

## Teste manual

1. Crie uma proposta e marque-a como aceita.
2. Converta o lead em cliente.
3. Abra novamente o lead e clique em **Gerar contrato**.
4. Abra o documento e revise o conteúdo gerado.
5. Avance por revisão, aprovação e registro de envio.
6. Registre a assinatura informando onde ou como o documento assinado foi arquivado.
7. Confirme todos os eventos na timeline e no histórico de auditoria.
# Arquivamento administrativo

Na Central de contratos, administrador/superadministrador pode usar **Arquivar contrato**, com confirmação. `DELETE /api/v1/contracts/{contract_id}` retorna 204 e faz exclusão lógica por `deleted_at`, sem migration. Repetir a operação não duplica o histórico. O contrato deve pertencer à organização atual, inclusive para superadministrador.

Conteúdo, assinatura e situação são preservados no banco. O documento arquivado deixa de ser acessível pelas telas ativas; esta entrega não inclui tela de arquivo/restauração. A operação gera auditoria e interação na timeline do lead. Não cancela juridicamente o contrato, nem arquiva cliente, lead ou proposta. Indicadores de propostas/receita comercial podem continuar incluindo a proposta até tratamento separado do lead.

Teste: administrador arquiva contrato de teste, lista e resumo de contratos deixam de contá-lo; timeline registra uma única ação; outros perfis recebem 403, outra organização recebe 404. Nunca usar limpeza de testes em contratos reais sem decisão administrativa específica.
