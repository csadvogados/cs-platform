# Checklist de Deploy

- [ ] Backup ou commit do backend atual.
- [ ] Arquivos copiados sobre o backend após 02B.4.
- [ ] `alembic heads` mostra somente `0003_merge_auth_organization`.
- [ ] `alembic upgrade head` concluído.
- [ ] `pytest -q` concluído.
- [ ] Login administrativo validado.
- [ ] `/api/v1/auth/me` retorna organização e permissões.
- [ ] `ORGANIZATION_API_ENABLED=true` configurado no Railway.
- [ ] `/api/v1/organizations/current` responde com token válido.
- [ ] Deploy concluído sem erro de múltiplos heads.
