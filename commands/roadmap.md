---
description: Gerenciar ROADMAP.md — adicionar entradas, importar de issues GH, mostrar estado
model: claude-haiku-4-5-20251001
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(git worktree list*), Bash(git log*), Bash(git status*), Bash(gh *), Bash(ls *), Bash(mkdir *), Bash(find *)
---

# Roadmap — Visao Multi-Feature

Voce gerencia `thoughts/ROADMAP.md` — a visao de cima dos problemas/features do projeto.

O eixo das secoes e o **estado real do trabalho (o PR)**, NAO a presenca de SPEC. Quatro secoes:

| Secao | Significado |
|---|---|
| `## 🔴 Próximos (fila priorizada)` | Fila curta, curada manualmente — o que fazer a seguir. O sync NAO mexe aqui automaticamente. |
| `## Backlog (resto)` | Tudo identificado mas sem PR aberto. Sem ordem. Pode ter SPEC ou nao. |
| `## Em progresso (PR aberto)` | Tem PR aberto e ativo. |
| `## Concluído (merged)` | PR merged. |

**Filosofia**: minimo de ceremonia. Cada entrada tem 1 linha. O detalhe vive no SPEC/IMP/PR correspondente.

**Escopo**: ver memoria de feedback do projeto sobre o que entra no roadmap (ex: backend-only) — respeitar a regra vigente. Em duvida, perguntar.

## Resolucao do diretorio root

```bash
git worktree list | head -1 | awk '{print $1}'
```

Use esse caminho como base para `thoughts/ROADMAP.md`.

## Modos de uso

| Invocacao | O que faz |
|---|---|
| `/roadmap` (sem args) | Mostra estado atual + sincroniza secoes por status de PR + sugere proximos passos |
| `/roadmap add "<descricao>"` | Adiciona entrada nova ao Backlog (resto) |
| `/roadmap add #123` | Busca issue do GH via `gh` e adiciona ao Backlog (resto) com link, titulo e corpo |

## Configuracao Inicial

### 1. Resolver caminho
```bash
ROOT=$(git worktree list | head -1 | awk '{print $1}')
ROADMAP="$ROOT/thoughts/ROADMAP.md"
```

### 2. Garantir que existe
Se nao existir, crie usando o template (final deste documento).

### 3. Identificar o modo
- Argumentos vazios → modo "sync"
- Comeca com `add "..."` → modo "add manual"
- Comeca com `add #...` → modo "add issue"
- Outro padrao → mostre help e saia

---

## Modo: Add Manual

`/roadmap add "<descricao>"`

### Passos

1. Le o ROADMAP atual
2. Decide o proximo numero (NNN) baseado em todas as entradas existentes (max + 1, com 3 digitos)
3. Adiciona ao **Backlog (resto)**:
```markdown
- [ ] NNN — <descricao> — [criado: DD-MM-YYYY]
```
4. Salva
5. Informa: `Adicionado ao Backlog: NNN — <descricao>`

---

## Modo: Add Issue

`/roadmap add #123`

### Passos

1. Busca a issue:
```bash
gh issue view 123 --json title,body,url,labels,number
```

2. Verifica se ja esta no roadmap (busca por `#123` ou pelo numero da issue). Se sim, informe e saia.

3. Le o ROADMAP atual, decide o proximo NNN

4. Adiciona ao **Backlog (resto)** com link e resumo:
```markdown
- [ ] NNN — [<titulo da issue>](<url da issue>) [#123] — [criado: DD-MM-YYYY]
```

5. Se a issue tem body relevante (>1 linha de contexto), pergunte se deve adicionar um resumo de 1 linha.

6. Salva e informa.

---

## Modo: Sync (sem args)

O sync e **PR-driven**: o que dita a secao de cada item e o status do(s) PR(s) que ele referencia, nao a existencia de arquivo SPEC/IMP.

### Passos

1. Le o ROADMAP atual e extrai cada entrada com seu NNN e qualquer `#<PR>` referenciado.

2. Para cada entrada que referencia um PR, consulta o status:
```bash
gh pr view <N> --json state,mergedAt,updatedAt,title
```
   Aplica as transicoes:
   - **merged** → mover para **Concluído (merged)**, marcar `[x]`, normalizar o link para `→ [PR #N](url)`.
   - **open com atividade recente** (updatedAt < ~4 semanas) → **Em progresso (PR aberto)**.
   - **open mas parado** (updatedAt > ~4 semanas) → NAO move sozinho: sinaliza ao usuario sugerindo rebaixar para Backlog com nota `WIP parado desde DD-MM`.
   - **closed sem merge** → sinaliza (PR morto); sugere voltar ao **Backlog (resto)** preservando o contexto.

3. **🔴 Próximos** e **Backlog (resto)** sao curados manualmente — o sync nao promove/rebaixa entre eles automaticamente. Apenas: se um item de Próximos/Backlog ganhou PR aberto, move para Em progresso; se foi concluido, para Concluído.

4. Detecta PRs abertos do autor que NAO tem entrada no roadmap:
```bash
gh pr list --author "@me" --state open --json number,title,headRefName
```
   Para cada, mostre ao usuario e pergunte se quer adicionar (respeitando o escopo vigente do roadmap — ex: backend-only).

5. Apresente resumo:
```
Roadmap sincronizado (PR-driven):

- 🔴 Próximos: [N]
- Backlog: [M]
- Em progresso: [P] (PRs abertos)
- Concluído: [R] (moveu S por merge)

Sinais: [T] PRs parados (>4 sem) · [U] PRs fechados sem merge · [V] PRs abertos sem entrada
```

6. Salva o ROADMAP atualizado.

---

## Template ROADMAP.md

Quando criar pela primeira vez:

```markdown
# Roadmap

> Visao multi-feature do projeto. O eixo das secoes e o **estado real do trabalho (o PR)**, nao a presenca de SPEC.
> 🔴 Próximos = fila priorizada · Backlog = resto (sem ordem) · Em progresso = PR aberto ativo · Concluído = merged.
> `/roadmap add "<descricao>"` ou `/roadmap add #issue` para adicionar · `/roadmap` sincroniza status via PR.

## 🔴 Próximos (fila priorizada)

[Fila curta do que fazer a seguir — curada manualmente]

## Backlog (resto)

[Tudo identificado mas sem PR aberto]

## Em progresso (PR aberto)

[Itens com PR aberto e ativo]

## Concluído (merged)

[Itens entregues — ver PR/IMP para detalhes]
```

---

## Guardrails

- **NNN sequencial**: nunca reuse numero. Sempre `max(numeros existentes) + 1`
- **Nunca duplique entradas**: antes de adicionar issue, verifique se ja existe (por numero #)
- **Migracao sem perda**: ao mover entre secoes, preserve NNN e titulo. So ajusta o link/status
- **Sync e PR-driven**: a secao segue o status do PR (merged/open/closed), nao a presenca de SPEC/IMP
- **Próximos e manual**: o sync nunca promove itens para 🔴 Próximos sozinho — isso e priorizacao humana
- **PRs parados/fechados**: o sync sinaliza mas nao rebaixa sozinho — pede confirmacao
- **GitHub via `gh` CLI**: nunca tokens manuais
- **1 linha por entrada**: detalhes vivem no SPEC/IMP/PR, nao no roadmap
- **Escopo do roadmap**: respeitar a regra vigente (ex: backend-only, via memoria de feedback do projeto)
