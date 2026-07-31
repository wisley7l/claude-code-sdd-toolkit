# Reference: template do output semanal (/pr-report)

> Carregado sob demanda pelo `/pr-report` (Modo Semanal, Etapa 4 — apresentar inline). Semanal nunca salva arquivo.

```markdown
# Semana — {LABEL}

**Repo**: `{REPO}` · **Usuario**: @{USER}

---

## Resumo

| Atividade | Quantidade |
|---|---|
| PRs que abri | {A} |
| PRs que mergeei | {M} |
| PRs que revisei | {R} |

---

## PRs que abri ({A})

| # | Titulo | Estado atual | Idade |
|---|---|---|---|
| [#NNN](url) | titulo | merged/open | X dias |

## PRs que mergeei ({M})

> Inclui PRs criados antes desta semana — lead time mostra a diferenca.

| # | Titulo | Aberto em | Lead time |
|---|---|---|---|
| [#NNN](url) | titulo | YYYY-MM-DD | X dias |

## PRs que revisei ({R})

> Aproximacao por `updated` na semana — pode incluir reviews antigos com atividade nova.

| # | Autor | Titulo | Estado atual |
|---|---|---|---|
| [#NNN](url) | @user | titulo | merged/open |
```
