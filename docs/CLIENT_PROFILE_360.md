# Perfil 360 do Cliente — primeira entrega

O Perfil 360 amplia a ficha já existente do cliente e reúne, sem duplicar cadastros, as informações comerciais, jurídicas e financeiras produzidas pelos módulos da CS Platform.

## API

`GET /api/v1/clients/{client_id}/profile`

A resposta respeita a organização do usuário autenticado e apresenta:

- lead convertido mais recente, origem, serviço e responsável;
- contrato comercial mais recente e sua situação;
- caso do CS Recupera mais recente, etapa e responsável;
- próxima ação comercial pendente;
- diagnóstico financeiro mais recente;
- quantidades de documentos, negociações e acordos;
- histórico cronológico unificado da jornada comercial, do contrato, do caso e do diagnóstico.

## Interface

Na área **Clientes**, abra **Ver detalhes**. A seção **Perfil 360 — Visão unificada do cliente** aparece logo após os dados cadastrais e antes das informações financeiras detalhadas.

Registros ainda inexistentes são mostrados com uma indicação clara, sem impedir o carregamento dos demais dados.

## Teste rápido

1. Abra um cliente originado de um lead convertido.
2. Confira origem comercial, contrato, caso e próxima ação.
3. Compare as quantidades de documentos, negociações e acordos com as seções detalhadas da mesma página.
4. Confirme que o histórico está em ordem do registro mais recente para o mais antigo.
