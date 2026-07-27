---
description: Arquiva SPEC+PLAN concluídos (PR mergeado) — move o par pra thoughts/specs/closed/ e thoughts/plans/closed/ e move o item do roadmap pra concluido/. Distinto de `old/` (descartadas). Só age sob PR MERGED; confirmação individual; nunca commita.
model: claude-sonnet-5
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls *), Bash(mkdir *), Bash(mv *), Bash(git worktree list*), Bash(git status*), Bash(gh *), Bash(realpath *), Bash(pwd), Bash(find *), Bash(basename *), Bash(dirname *), Bash(grep *), Bash(head *), Bash(cat *)
---

# SDD Close — Arquivar SPEC+PLAN concluídos após merge

Você move o **par SPEC+PLAN de um trabalho concluído** (PR mergeado) das pastas vivas
`thoughts/specs/` e `thoughts/plans/` para `thoughts/specs/closed/` e `thoughts/plans/closed/`,
e **move o item correspondente do roadmap pra `concluido/`** (+ mostra o que isso desbloqueou).

**Filosofia**: `thoughts/specs/` e `thoughts/plans/` guardam os docs **vivos** (em fila,
em progresso). Quando o PR entra na main, o par vira histórico — sai da raiz pra `closed/`,
mantendo a raiz enxuta sem perder o rastro.

**`closed/` ≠ `old/`**:
- `closed/` = trabalho **usado e concluído** (PR MERGED). É o que este command gerencia.
- `old/` = spec/plano **descartado** (abandonado, superado sem entrega). NÃO é escopo daqui.

Se um par não foi mergeado (PR fechado sem merge ou nunca existiu), este command **não** o
arquiva em `closed/` — ele sinaliza e sugere `old/`, mas deixa a mudança pro usuário.

## Guardrails (não-negociáveis)

- **Só MERGED vai pra `closed/`.** PR aberto → skip. PR fechado sem merge / sem PR → não move; sinaliza.
- **Confirmação individual, nunca batch.** Um par por vez, mostrando SPEC + PLAN + PR antes.
- **Par junto.** Não arquive a SPEC sem o(s) PLAN(s) dela nem vice-versa (salvo caso de borda explícito).
- **Nunca commita nem pusha.** `thoughts/` é gitignored por convenção — `mv` simples basta.
- **ROADMAP: migração sem perda.** Ao concluir, `mv` o item pra `concluido/` preservando o arquivo inteiro (NNN, título, `Depende de:`, `Docs:`); o wikilink não quebra. Depois regenere o hub e recalcule os 🔓 Desbloqueados.
- **Em dúvida, preserve.** Não mover é reversível; mover errado gera confusão. Rode de novo depois.

## Pré-cheques

1. **Root do projeto** (centraliza mesmo rodando em worktree):
   ```bash
   ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
   ROOT=${ROOT:-$(pwd)}
   ```
   Use `$ROOT/thoughts/` como base.

2. **Pastas vivas existem**: `thoughts/specs/` e `thoughts/plans/`. Se nenhuma existir, diga
   "Sem `thoughts/specs/` ou `thoughts/plans/` neste projeto — nada a arquivar." e saia.

3. **`gh`**: `gh auth status`. Se falhar, peça `gh auth login` e saia (o gatilho depende do status do PR).

## Argumentos

| Invocação | O que faz |
|---|---|
| `/sdd-close` (sem args) | Varre todos os pares vivos, filtra os com PR MERGED, propõe arquivar um a um |
| `/sdd-close <slug \| path-do-PLAN \| path-da-SPEC>` | Foca num par só (resolve o par a partir do que você passou) |
| `/sdd-close --pr <N>` | Foca no par cujo PR é `#N` |

## Workflow

### Passo 1 — Coletar pares vivos

Liste os PLANs na **raiz** de `thoughts/plans/` (ignore `closed/` e `old/`):
```bash
find "$ROOT/thoughts/plans" -maxdepth 1 -name 'PLAN-*.md' -type f
```

O **PLAN é a unidade** — ele referencia a SPEC no topo (linha `SPEC: \`thoughts/specs/spec-...\``).
Para cada PLAN:
- Extraia o path da SPEC dessa linha (`grep -i 'SPEC:' <plan> | head -1`). Resolva pra path absoluto sob `$ROOT`.
- Extraia o **NNN** e o **slug** do nome do PLAN (`PLAN-<DD-MM-YYYY>-<NNN>-<slug>.md`).

Trate os casos:
- **PLANs com mesma SPEC** (multi-PR): agrupe — a SPEC só vai pra `closed/` quando **todos** os PLANs dela estiverem mergeados.
- **SPEC viva sem PLAN** (`spec-*.md` na raiz sem PLAN apontando): liste como candidata órfã → caso de borda (Passo 5).

Se argumento foi passado, restrinja a coleta ao par correspondente antes de seguir.

### Passo 2 — Descobrir o PR de cada par

Ordem de resolução (pare no primeiro que resolver):

1. **ROADMAP** (vault `thoughts/roadmap/`, se existir): ache o item com o mesmo **NNN** (ou slug/`plan:`) e leia o `pr:` dele. Se só existir o `thoughts/ROADMAP.md` antigo, avise que precisa migrar (`/roadmap migrar`) e siga pela busca no GitHub.
2. **Busca no GitHub** pelo slug:
   ```bash
   gh pr list --search "<slug em palavras>" --state all --json number,title,state,mergedAt,headRefName --limit 5
   ```
3. **Pergunte** ao usuário o número do PR (opção `(n)`), ou `(k)` skip.

### Passo 3 — Filtrar por status do PR

```bash
gh pr view <N> --json state,mergedAt,title,url
```
- `state: "MERGED"` → **candidato a arquivar** (Passo 4).
- `state: "OPEN"` → skip: "PR #N ainda aberto — par preservado em specs/plans/".
- `state: "CLOSED"` (sem `mergedAt`) → **não arquiva em `closed/`**. Sinalize: "PR #N fechado sem merge — isto é descarte, não conclusão. Considere mover pra `old/` (fora do escopo do /sdd-close)." Não mova.

### Passo 4 — Propor e arquivar (só MERGED)

Para cada par MERGED, mostre e confirme individualmente:
```
Par concluído:
  SPEC:  thoughts/specs/spec-<TS>-<slug>.md
  PLAN:  thoughts/plans/PLAN-<...>-<slug>.md   (+ outros PLANs do mesmo grupo, se houver)
  PR:    #N "<título>" — MERGED em <data>
  ROADMAP: item NNN <"encontrado em <pasta>" | "não encontrado">

Ao confirmar:
  1. move SPEC → thoughts/specs/closed/
  2. move PLAN(s) → thoughts/plans/closed/
  3. move o item NNN → thoughts/roadmap/concluido/  [se existir]

  (s) Arquivar    (k) Skip    (a) Abortar tudo
```

Se `(s)`:
1. Crie as pastas destino se faltarem:
   ```bash
   mkdir -p "$ROOT/thoughts/specs/closed" "$ROOT/thoughts/plans/closed"
   ```
2. Mova (não é `git mv` — `thoughts/` é gitignored):
   ```bash
   mv "$ROOT/thoughts/specs/spec-<...>.md"  "$ROOT/thoughts/specs/closed/"
   mv "$ROOT/thoughts/plans/PLAN-<...>.md"  "$ROOT/thoughts/plans/closed/"   # cada PLAN do grupo
   ```
   Se um destino já tiver arquivo de mesmo nome, PARE nesse par e avise (não sobrescreva).
3. **ROADMAP** (se o item existe): `mv` o arquivo do item pra `thoughts/roadmap/concluido/`, **preservando
   o arquivo inteiro** (NNN, título, `Depende de:`, `Docs:`) — o wikilink não quebra. Se o item já estava
   em `concluido/`, apenas confirme. Se **não há** item no roadmap, não invente um — apenas registre no sumário.
   Depois **regenere o hub** `thoughts/roadmap/ROADMAP.md` e **recalcule os 🔓 Desbloqueados agora** — itens de
   `backlog/` cujas dependências ficaram todas em `concluido/` com este merge (reference `roadmap-item.md`, algoritmo).
   O grafo do Obsidian se atualiza sozinho a partir dos links — não há mermaid a regenerar.
4. Sumarize: "✅ Arquivado: `<slug>` (SPEC + N PLAN(s)) → closed/ · ROADMAP: `<item → concluido/ | sem item>` · 🔓 Desbloqueou: `<NNN[, MMM] | nada>`".

Se `(k)`: preserve, siga pro próximo. Se `(a)`: pare a varredura, vá pro sumário.

### Passo 5 — Sumário

```
/sdd-close concluído:
  ✅ Arquivados (SPEC+PLAN → closed/):   N
  📋 ROADMAP (itens → concluido/):       M
  🔓 Desbloqueados agora:                D
  ⏸️ Skip (PR aberto):                   K
  ⚠️ PR fechado sem merge (sugerir old/): J
  ❓ Sem PR resolvido:                    P

Pares vivos remanescentes em thoughts/{specs,plans}/: <count>
```

## Casos de borda

- **SPEC órfã (sem PLAN)**: pergunte se deve arquivar sozinha (às vezes a spec virou quick-task sem PLAN). Só mova sob confirmação; use `--pr` ou peça o PR pra validar o merge.
- **Multi-PR na mesma SPEC**: a SPEC só vai pra `closed/` quando **todos** os PLANs dela estiverem mergeados. Se um ainda está aberto, arquive só os PLANs já mergeados e deixe a SPEC na raiz; avise no sumário.
- **Colisão de nome em `closed/`**: não sobrescreva. Pare nesse par e avise (provavelmente já foi arquivado).
- **PR `reopened` após `merged`**: trate como MERGED (o código entrou na main).
- **Múltiplos PRs MERGED pro mesmo slug**: liste e peça pro usuário escolher qual item do roadmap referenciar.
- **`gh` falha (rede/rate limit)**: não mova nada. Peça pra rodar de novo mais tarde.
- **Sem vault `thoughts/roadmap/`**: arquive os arquivos normalmente; só pule a etapa de ROADMAP e diga isso no sumário. Se houver o `thoughts/ROADMAP.md` antigo, sugira `/roadmap migrar`.

## Relação com outros commands

- `/sdd-spec` / `/sdd-plan` **criam** os docs vivos em `thoughts/specs/` e `thoughts/plans/`.
- `/roadmap` (sync) **move o item** pra `concluido/` por PR merged — `/sdd-close` aplica a mesma transição e **adiciona** o arquivamento dos docs SPEC/PLAN. Rodar `/roadmap` depois é idempotente.
- `/sdd-learning` **extrai aprendizado** do PR mergeado (input complementar; não move arquivos).
- `old/` (descartadas) é gerenciado manualmente — `/sdd-close` só **sinaliza** candidatos, nunca move pra lá.
