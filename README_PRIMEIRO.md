# CS Platform v5.24.0 — LEIA PRIMEIRO

Esta versão adiciona a **Central Gerencial** com indicadores executivos da operação.

Substitua exatamente os sete arquivos presentes neste pacote, mantendo as mesmas pastas no GitHub.

Use este nome no commit:

`feat: adicionar central gerencial e indicadores executivos v5.24.0`

Não há migração de banco. Deixe **Pre-deploy Command** vazio no Railway.

## Depois do deploy

1. Aguarde `cs-platform-api` e `cs-platform-web` ficarem verdes.
2. Abra o sistema e pressione `Ctrl + F5`.
3. Em **Configurações**, confirme a versão `5.24.0`.
4. Abra **Indicadores** e confira a **Central Gerencial**.
5. Teste os períodos de 7, 30 e 90 dias.
6. Escolha duas datas, clique em **Aplicar período** e confira a atualização dos indicadores.
7. Confira a evolução diária, os riscos, o funil comercial e o desempenho da equipe.
8. Clique em **Exportar CSV** e abra o relatório.
9. Confirme que um perfil sem acesso a relatórios não enxerga a opção **Indicadores**.

O arquivo `SHA256SUMS.txt` permite conferir a integridade dos arquivos.

