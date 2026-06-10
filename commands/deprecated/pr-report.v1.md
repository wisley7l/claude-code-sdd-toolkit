---
description: Relatorio de PRs do usuario no repo atual — semanal/mensal/anual. Modos mensal e anual salvam; semanal so inline. Desconsidera fechados sem merge.
model: claude-haiku-4-5-20251001
argument-hint: [--mes YYYY-MM | --de YYYY-MM-DD --ate YYYY-MM-DD | --semana atual|ultima|YYYY-Www | --mes YYYY-MM --semana N | anual YYYY]
allowed-tools: Bash(gh *), Bash(git *), Bash(date *), Bash(mkdir *), Bash(ls *), Bash(jq *), Read, Glob, Write, AskUserQuestion
---

# /pr-report — Relatorio semanal/mensal/anual de PRs

Voce gera relatorio quantitativo + qualitativo dos PRs do usuario no repo atual (cwd). Default: ultimos 30 dias. Aceita filtro por mes ou range custom.

**Regra dura**: PRs `closed` sem merge sao SEMPRE desconsiderados. So entram `open` e `merged`.

## Parse de $ARGUMENTS

Aceita 5 formatos:

| Invocacao | Modo | Janela temporal |
|---|---|---|
| `/pr-report` (sem args) | Mensal | Ultimos 30 dias (hoje - 30d ate hoje) |
| `/pr-report --mes 2026-04` | Mensal | Mes inteiro de Abril/2026 (2026-04-01 a 2026-04-30) |
| `/pr-report --de 2026-03-15 --ate 2026-04-15` | Mensal | Range custom |
| `/pr-report --semana atual` | Semanal | Semana corrente (segunda 00:00 a domingo 23:59 UTC) |
| `/pr-report --semana ultima` | Semanal | Semana anterior |
| `/pr-report --semana 2026-W17` | Semanal | Semana ISO especifica |
| `/pr-report --mes 2026-04 --semana 2` | Semanal | Semana N do mes (1=dias 1-7, 2=8-14, 3=15-21, 4=22-28, 5=29-fim) |
| `/pr-report anual 2026` | Anual | Consolida relatorios mensais ja salvos do ano (le `thoughts/reports/prs-YYYY-MM.md`) |

Se receber argumento invalido, pare e mostre os formatos validos.

> Modo **anual** nao busca PRs no GitHub — apenas le e consolida relatorios mensais ja gerados.
> Modo **semanal** so exibe inline, NUNCA salva (janela curta demais pra valer arquivo).

**Roteamento**:
- 1o token = `anual` → va pra secao "Modo Anual"
- contem `--semana` → va pra secao "Modo Semanal"
- caso contrario → fluxo mensal abaixo

## Fluxo

### 1. Resolver janela temporal

```bash
# Default: ultimos 30 dias
FROM=$(date -d '30 days ago' +%Y-%m-%d)
TO=$(date +%Y-%m-%d)

# Se --mes YYYY-MM
FROM="${MES}-01"
TO=$(date -d "${MES}-01 +1 month -1 day" +%Y-%m-%d)

# Se --de X --ate Y
FROM=$DE
TO=$ATE
```

Guarde `LABEL` pra titulo do relatorio:
- Default → `ultimos 30 dias (FROM a TO)`
- `--mes YYYY-MM` → `MM/YYYY` (ex: `04/2026`)
- Range custom → `FROM a TO`

### 2. Resolver repo atual

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
```

Se vazio (nao eh repo GH ou `gh` sem auth), pare com mensagem clara: `Nao consegui resolver o repo. Confirme que esta num repo com remote GitHub e que 'gh auth status' esta OK.`

### 3. Buscar PRs (3 queries)

#### 3a. PRs criados pelo user no periodo (open OR merged)

```bash
gh search prs \
  --repo "$REPO" \
  --author=@me \
  --created="$FROM..$TO" \
  --state=open \
  --json number,title,url,createdAt,state,isDraft \
  --limit 200 > /tmp/pr-report-open.json

gh search prs \
  --repo "$REPO" \
  --author=@me \
  --created="$FROM..$TO" \
  --state=closed \
  --json number,title,url,createdAt,closedAt,state \
  --limit 200 > /tmp/pr-report-closed.json
```

> `gh search prs --state=closed` retorna closed-sem-merge E merged. Voce filtra mergeados no proximo passo via `gh pr view`.

#### 3b. Filtrar mergeados (descarta closed-sem-merge)

Pra cada PR em `/tmp/pr-report-closed.json`, rode:

```bash
gh pr view <NUMBER> --repo "$REPO" --json number,title,url,createdAt,mergedAt,state,additions,deletions,changedFiles,comments,reviews
```

Se `mergedAt != null` e `state == "MERGED"` → entra como **mergeado**. Caso contrario → **descarte**.

Pra reduzir latencia, processe em paralelo (max 5 em paralelo via `xargs -P 5` OU loop bash em background com `wait`).

#### 3c. PRs revisados pelo user no periodo

```bash
gh search prs \
  --repo "$REPO" \
  --reviewed-by=@me \
  --created="$FROM..$TO" \
  --json number,title,url,createdAt,state,author \
  --limit 200 > /tmp/pr-report-reviewed.json
```

> Aproximacao: filtramos por `created` no periodo, nao pela data do review. Isso eh limitacao do `gh search`. Mencione no relatorio.

Filtre os com `state == "CLOSED"` E sem merge (precisa checar via `gh pr view` se `mergedAt == null` → descarta). Mantenha `OPEN` e `MERGED`.

### 4. Agregar metricas

Pra **PRs criados por mim**:
- Total = `open + merged`
- Taxa de merge = `merged / (merged + open + descartados-closed-sem-merge)` ⚠️ inclua descartados no denominador pra refletir realidade
- Lead time medio (so merged): `avg(mergedAt - createdAt)` em dias/horas
- Lead time mediano (so merged): mediana
- Engajamento medio (so merged): `avg(comments.totalCount + reviews.totalCount)` por PR

Pra **PRs revisados por mim**:
- Total
- Distribuicao por autor (top 5)
- Estado atual (open vs merged)

Pra **distribuicao temporal**:
- PRs criados por semana do periodo (bucket por ISO week)

### 5. Apresentar relatorio inline

Use este template (pt-BR, markdown):

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

### 6. Perguntar se salvar

Use `AskUserQuestion`:

```
Pergunta: Salvar relatorio em thoughts/reports/?
Header: Salvar
Opcoes:
- "Salvar (sobrescreve se existir)" → grava em thoughts/reports/prs-{SUFIXO}.md
- "Nao salvar" → encerra
```

Onde `SUFIXO`:
- `--mes YYYY-MM` → `YYYY-MM`
- Range custom ou default → `YYYY-MM-DD_a_YYYY-MM-DD` (FROM_a_TO)

### 7. Se salvar

```bash
ROOT=$(git worktree list | head -1 | awk '{print $1}')
mkdir -p "$ROOT/thoughts/reports"
```

Grave em `$ROOT/thoughts/reports/prs-{SUFIXO}.md` com:
- Header com data de geracao (`generated: YYYY-MM-DD HH:MM`)
- Todo o conteudo do relatorio inline
- Secao final `## Destaques` vazia (campo manual pro user preencher contexto qualitativo subjetivo)
- **Bloco de dados machine-readable** ao final (consumido pelo modo `anual`):

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

**Sobrescreve sem perguntar de novo** (usuario ja autorizou ao escolher "Salvar").

Informe path absoluto no final: `Salvo em: <path>`.

---

---

## Modo Anual

Invocacao: `/pr-report anual YYYY` (ex: `/pr-report anual 2026`).

Consolida relatorios mensais ja salvos em `thoughts/reports/`. **Nao toca no GitHub.**

### 1. Resolver ano e localizar arquivos

```bash
ROOT=$(git worktree list | head -1 | awk '{print $1}')
YEAR=2026  # do argumento
ls "$ROOT/thoughts/reports/prs-${YEAR}-"??.md 2>/dev/null
```

Filtre apenas arquivos no padrao `prs-YYYY-MM.md` (ignore range custom tipo `prs-YYYY-MM-DD_a_YYYY-MM-DD.md` e `prs-YYYY-anual.md`).

Se nenhum encontrado:
```
Nenhum relatorio mensal encontrado pra YYYY em thoughts/reports/.
Gere os mensais primeiro: /pr-report --mes YYYY-MM
```

### 2. Ler e extrair bloco machine-readable

Pra cada arquivo:
1. `Read` o conteudo
2. Localize o bloco `## Dados (machine-readable)` e o YAML dentro de \`\`\`yaml ... \`\`\`
3. Parse os campos: `period.label`, `created.*`, `reviewed.*`, `lead_time_days.*`, `engagement.*`, `prs_merged`, `prs_open`, `prs_reviewed`

**Falha de parse**: se algum arquivo nao tem o bloco (relatorio gerado antes desta versao), avise o user listando quais e ofereca:
- Continuar com os arquivos validos
- Cancelar e regenerar os antigos

### 3. Avisar lacunas

Verifique meses faltando. Se ano em curso, considere ate o mes atual; se ano passado, considere todos 12 meses.

```
Encontrados: Jan, Fev, Mar, Abr (4 meses)
Faltando: Mai, Jun, Jul, Ago, Set, Out, Nov, Dez (8 meses)
Gerar ate o mes atual mesmo assim? [yes/no]
```

(Use `AskUserQuestion` com opcoes "Continuar com o que tem" / "Cancelar".)

### 4. Consolidar metricas

**Somas**:
- `created.total` = soma de todos os meses
- `created.merged`, `created.open`, `created.closed_no_merge` = somas
- `reviewed.total` = soma

**Taxas recalculadas no total** (nao media de taxas):
- `merge_rate = merged / (merged + open + closed_no_merge)`

**Lead time anual**:
- Idealmente: media ponderada dos PRs mergeados (precisa de `prs_merged[].lead_time_days`)
- Concatene todos `prs_merged` dos meses → calcule `avg`, `median`, `min`, `max` do conjunto unificado

**Engajamento anual**:
- Media ponderada via `prs_merged[].interactions`

**Top 5 PRs do ano**:
- Mais discutidos (maior `interactions`)
- Maior lead time (mergeados, indicador de PR que ficou parado)
- Top autores que voce mais revisou (count em `prs_reviewed[].author`)

**Distribuicao temporal**:
- Mensal: tabela com 12 linhas (Jan-Dez) mostrando criados/mergeados/revisados por mes
- Trimestre: agregar Q1/Q2/Q3/Q4

### 5. Apresentar relatorio anual inline

Template (pt-BR):

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

### 6. Perguntar se salva

`AskUserQuestion`:
- "Salvar (sobrescreve se existir)" → grava em `thoughts/reports/prs-{YEAR}-anual.md`
- "Nao salvar"

### 7. Se salvar

Mesma logica do mensal — header com `generated:`, conteudo completo, `## Destaques` vazia no fim.

**Nao inclua bloco machine-readable** no anual (anual nao consome outro anual).

Informe path absoluto: `Salvo em: <path>`.

---

---

## Modo Semanal

Invocacoes:
- `/pr-report --semana atual` — semana corrente
- `/pr-report --semana ultima` — semana passada
- `/pr-report --semana YYYY-Www` — ISO week (ex: `2026-W17`)
- `/pr-report --mes YYYY-MM --semana N` — semana N do mes (N=1..5, dias fixos)

**Sempre inline. Nunca salva.** Sem prompt de "salvar?".

### Diferenca conceitual vs mensal

Em janela de 7 dias, PR aberto na semana pode ainda nao ter mergeado, e PR mergeado na semana pode ter sido aberto semanas antes. Por isso o relatorio semanal **separa as 3 visoes** sem misturar:

1. **PRs que ABRI nessa semana** (criados no periodo, estado atual qualquer — exceto closed-sem-merge)
2. **PRs que MERGEEI nessa semana** (mergedAt no periodo, criados quando for)
3. **PRs que REVISEI nessa semana** (aproximacao via `updated` no periodo — limitacao do `gh search`)

Nao ha "taxa de merge da semana" — denominador pequeno demais pra fazer sentido.

### 1. Resolver janela semanal

```bash
# --semana atual: segunda dessa semana ate domingo
FROM=$(date -d 'monday this week' +%Y-%m-%d)
TO=$(date -d 'sunday this week' +%Y-%m-%d)
LABEL="Semana atual ($FROM a $TO)"

# --semana ultima
FROM=$(date -d 'monday last week' +%Y-%m-%d)
TO=$(date -d 'sunday last week' +%Y-%m-%d)
LABEL="Semana passada ($FROM a $TO)"

# --semana YYYY-Www (ISO week)
# Ex: 2026-W17. Use `date -d` com formato ISO ou calcule via Python/awk se preciso.
# GNU date: date -d "YYYY-Www-1" → segunda da ISO week
FROM=$(date -d "${YEAR}-W${WEEK}-1" +%Y-%m-%d)
TO=$(date -d "${YEAR}-W${WEEK}-7" +%Y-%m-%d)
LABEL="Semana ISO ${YEAR}-W${WEEK} ($FROM a $TO)"

# --mes YYYY-MM --semana N (semana fixa do mes)
# N=1 → dias 01-07, N=2 → 08-14, N=3 → 15-21, N=4 → 22-28, N=5 → 29-fim
case "$N" in
  1) FROM="${MES}-01"; TO="${MES}-07" ;;
  2) FROM="${MES}-08"; TO="${MES}-14" ;;
  3) FROM="${MES}-15"; TO="${MES}-21" ;;
  4) FROM="${MES}-22"; TO="${MES}-28" ;;
  5) FROM="${MES}-29"; TO=$(date -d "${MES}-01 +1 month -1 day" +%Y-%m-%d) ;;
esac
LABEL="Semana ${N} de ${MES} ($FROM a $TO)"
```

### 2. Resolver repo (identico ao mensal)

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
```

### 3. Buscar PRs (3 queries independentes)

#### 3a. PRs que abri na semana

```bash
gh search prs --repo "$REPO" --author=@me --created="$FROM..$TO" \
  --json number,title,url,createdAt,state --limit 100
```

Pra cada um, `gh pr view N --json mergedAt,state` pra distinguir merged/open/closed-sem-merge. Descarte closed-sem-merge.

#### 3b. PRs que mergeei na semana

```bash
gh search prs --repo "$REPO" --author=@me --merged --merged-at="$FROM..$TO" \
  --json number,title,url,createdAt,closedAt --limit 100
```

> Nota: `--merged-at` filtra pela data de merge (nao de criacao). Eh esse o ponto do modo semanal.

Pra cada um, calcule lead time = `mergedAt - createdAt` (pode ser dias ou ate semanas — eh esperado).

#### 3c. PRs que revisei na semana (aproximacao)

```bash
gh search prs --repo "$REPO" --reviewed-by=@me --updated="$FROM..$TO" \
  --json number,title,url,author,state --limit 100
```

> **Limitacao explicita**: `gh search` nao filtra por "data do review", entao usamos `--updated` (PR teve qualquer atividade no periodo). Pode incluir PRs onde o review foi anterior mas houve novo comentario na semana. Avise o user no relatorio.

Filtre estado: mantenha `OPEN` e `MERGED`, descarte `CLOSED` sem merge.

### 4. Apresentar inline

Template:

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

### 5. Nao salvar

Encerre apos exibir. Nao pergunte sobre salvar. Se o user pedir explicitamente "salva isso", explique que modo semanal nao gera arquivo (janela curta demais) e sugira:
- `/pr-report --mes YYYY-MM` pra ter o agregado mensal
- Copiar manualmente se quiser registro pontual

---

## Notas tecnicas

- **Performance**: pra periodos com >50 PRs, o passo 3b (gh pr view por PR) pode demorar. Use paralelismo `xargs -P 5` ou loop com `&` + `wait`.
- **Rate limit**: `gh` respeita rate limit do GitHub (5000 req/h autenticado). Pra periodos muito longos (>3 meses, >200 PRs), avise o user.
- **Drafts**: PRs em draft ainda aparecem em "abertos". Sinalize com `[draft]` no titulo da tabela.
- **Lead time em horas**: se `mergedAt - createdAt < 24h`, mostre em horas em vez de dias.
- **Timezone**: `gh` retorna ISO8601 UTC. Use UTC consistentemente — nao tente converter pra local.
