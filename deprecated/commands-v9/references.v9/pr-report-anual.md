# Reference: template do relatório anual (/pr-report)

> Carregado sob demanda pelo `/pr-report` (Modo Anual, Etapa 5 — apresentar relatorio anual inline). O anual NAO inclui bloco machine-readable.

```markdown
# Relatorio Anual de PRs — {YEAR}

**Repo**: `{REPO}` (extraido do 1o mensal)
**Periodo coberto**: {meses encontrados}
**Lacunas**: {meses faltando, se houver}

---

## Quantitativo anual

| Metrica | Total |
|---|---|
| PRs criados | {N} |
| Mergeados | {M} |
| Ainda abertos | {O} |
| Closed sem merge (desconsiderados) | {C} |
| **Taxa de merge anual** | **{XX}%** |
| PRs revisados | {R} |

## Qualitativo anual

### Lead time agregado (todos os mergeados do ano)
| Metrica | Valor |
|---|---|
| Media | {X} dias |
| Mediana | {Y} dias |
| Min / Max | {Zmin} / {Zmax} dias |

### Engajamento
| Metrica | Valor |
|---|---|
| Media de interacoes/PR | {E} |
| PR mais discutido do ano | #{NUM} — {titulo} ({total} interacoes) |

---

## Evolucao mensal

| Mes | Criados | Mergeados | Revisados | Lead time medio |
|---|---|---|---|---|
| Jan | ... | ... | ... | ... |
| Fev | ... | ... | ... | ... |
| ... | | | | |
| **Total** | {N} | {M} | {R} | {avg} |

## Por trimestre

| Trimestre | Criados | Mergeados | Taxa de merge |
|---|---|---|---|
| Q1 | ... | ... | ... |
| Q2 | ... | ... | ... |
| Q3 | ... | ... | ... |
| Q4 | ... | ... | ... |

---

## Highlights

### Top 5 mais discutidos
| # | Titulo | Interacoes |
|---|---|---|
| [#NNN](url) | titulo | N |

### Top 5 maior lead time (mergeados)
| # | Titulo | Lead time |
|---|---|---|
| [#NNN](url) | titulo | X dias |

### Top autores que voce mais revisou
| Autor | PRs revisados |
|---|---|
| @user | N |
```
