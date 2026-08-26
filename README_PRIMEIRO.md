# CS Platform v5.25.0 — Metas e desempenho

Esta versão adiciona planejamento mensal e acompanhamento automático de resultados à plataforma.

## Novidades

- Metas mensais para novos clientes, atendimentos, tarefas concluídas, recebimentos e oportunidades ganhas.
- Metas gerais da organização e metas individuais por integrante.
- Comparação entre meta, resultado realizado e projeção de fechamento.
- Alertas automáticos de metas atingidas ou abaixo da projeção.
- Ranking da equipe pelo cumprimento das metas.
- Histórico mensal: basta alterar o mês de referência para consultar outro período.
- Exportação do relatório de metas em CSV.
- Registro no Histórico das inclusões, alterações e exclusões de metas.
- Controle de acesso: administradores e supervisores gerenciam metas; demais perfis autorizados consultam os resultados.

## Banco de dados

A versão inclui a migração `0014_performance_goals.py`. Ela cria automaticamente a tabela `performance_goals` durante o deploy da API.

Não execute comandos manualmente no banco. O `docker-entrypoint.sh` aplica a migração antes de iniciar a API.

## Instalação

Substitua ou adicione os 12 arquivos do pacote mantendo exatamente as pastas indicadas. Depois faça um único commit no GitHub.

Mensagem sugerida:

`feat: adicionar metas e desempenho da equipe v5.25.0`

O Railway deverá fazer o deploy da API e do site. Aguarde os dois serviços ficarem com a indicação de sucesso.

## Como testar

1. Atualize a plataforma com `Ctrl + F5` e entre novamente.
2. Abra **Metas** no menu lateral.
3. Escolha o mês atual e clique em **Nova meta**.
4. Cadastre uma meta para **Toda a organização**.
5. Cadastre outra meta selecionando um integrante da equipe.
6. Confirme os cartões de realizado, percentual e projeção.
7. Confira os alertas e o ranking da equipe.
8. Cadastre novamente o mesmo indicador para confirmar que o valor é atualizado.
9. Use **Exportar CSV**.
10. Apague uma meta de teste e confirme que somente a meta desapareceu; os dados realizados permanecem.

## Validação técnica realizada

- Sintaxe do frontend e backend conferida.
- Cadeia de 15 migrações validada com uma única versão final.
- Fluxo de cadastro e atualização testado no navegador.
- Layout validado em desktop, tablet e celular.
- Nenhum erro de console encontrado.
