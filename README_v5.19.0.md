# CS Platform v5.19.0 — Central de alertas operacionais

## O que foi adicionado

- sino de alertas no cabeçalho da plataforma;
- contador de pendências operacionais ativas;
- alertas de cobranças críticas;
- alertas de promessas de pagamento vencidas;
- alertas de acompanhamentos de cobrança atrasados;
- alertas de tarefas do CRM com prazo vencido;
- atalho em cada alerta para abrir a tela já filtrada;
- atualização manual dos alertas dentro da própria central;
- atualização automática após alterações em cobranças e tarefas.

## Implantação

Substitua os sete arquivos entregues no pacote, mantendo exatamente as mesmas pastas. Faça o commit e aguarde o deploy dos serviços `cs-platform-api` e `cs-platform-web`.

Esta versão não possui migração de banco de dados e não exige comando de pré-deploy adicional.

## Conferência rápida

1. Entre na plataforma e confirme que o sino aparece no cabeçalho.
2. Clique no sino e confira os alertas ativos.
3. Clique em **Cobranças críticas** e confirme a abertura da tela Cobranças com o filtro **Crítica**.
4. Volte ao sino, clique em **Tarefas do CRM atrasadas** e confirme a abertura da aba **Tarefas** com o filtro **Atrasadas**.
5. Em Configurações, confirme a versão `5.19.0` e a conexão da API.

Commit sugerido:

`feat: adicionar central de alertas operacionais v5.19.0`
