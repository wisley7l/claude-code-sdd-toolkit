# Reference: template do relatório mensal (/pr-report)

> Carregado sob demanda pelo `/pr-report` (fluxo mensal): template na Etapa 5 (apresentar inline) e bloco YAML na Etapa 7 (ao salvar em `thoughts/reports/`).

## Template do relatorio

```markdown
# Relatorio de PRs — {LABEL}

**Repo**: `{REPO}`
**Periodo**: {FROM} a {TO}
**Usuario**: @{USER}

---

## Quantitativo

### PRs criados por mim

| Metrica | Valor |
|---|---|
| Total criados no periodo | {N} |
| Mergeados | {M} |
| Ainda abertos | {O} |
| Closed sem merge (desconsiderados) | {C} |
| **Taxa de merge** | **{M/(M+O+C) * 100}%** |

### PRs revisados por mim

| Metrica | Valor |
|---|---|
| Total | {R} |
| Mergeados (do que revisei) | {RM} |
| Ainda abertos | {RO} |

> Limitacao: filtro por `created` no periodo, nao pela data do review.

---

## Qualitativo

### Lead time (so PRs mergeados, criados por mim)

| Metrica | Valor |
|---|---|
| Media | {X} dias |
| Mediana | {Y} dias |
| Min / Max | {Zmin} / {Zmax} dias |

### Engajamento (so PRs mergeados, criados por mim)

| Metrica | Valor |
|---|---|
| Media de comentarios + reviews por PR | {E} |
| PR mais discutido | #{NUM} — {titulo} ({total} interacoes) |

### Distribuicao temporal (PRs criados)

| Semana | Criados | Mergeados |
|---|---|---|
| Sem {N1} ({date}) | {X} | {Y} |
| ... | ... | ... |

---

## Lista detalhada

### Mergeados ({M})

| # | Titulo | Lead time | Interacoes |
|---|---|---|---|
| [#NNN](url) | titulo | X dias | N |

### Ainda abertos ({O})

| # | Titulo | Idade | Interacoes |
|---|---|---|---|
| [#NNN](url) | titulo | X dias | N |

### Revisados por mim ({R})

| # | Autor | Titulo | Estado |
|---|---|---|---|
| [#NNN](url) | @user | titulo | merged/open |
```

## Bloco de dados machine-readable (so no arquivo salvo, consumido pelo modo `anual`)

````markdown
## Dados (machine-readable)

```yaml
type: pr-report-monthly
generated: YYYY-MM-DD HH:MM
repo: owner/repo
user: username
period:
  from: YYYY-MM-DD
  to: YYYY-MM-DD
  label: "MM/YYYY" # ou range
created:
  total: N
  merged: M
  open: O
  closed_no_merge: C
  merge_rate: 0.XX
reviewed:
  total: R
  merged: RM
  open: RO
lead_time_days:
  avg: X.X
  median: Y.Y
  min: Zmin
  max: Zmax
engagement:
  avg_interactions: E.E
  most_discussed_pr: NNN
prs_merged:
  - { number: NNN, title: "...", url: "...", lead_time_days: X, interactions: N }
prs_open:
  - { number: NNN, title: "...", url: "...", age_days: X, interactions: N }
prs_reviewed:
  - { number: NNN, author: "@user", title: "...", url: "...", state: "merged|open" }
```
````
