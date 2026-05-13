---
description: Gerenciar ROADMAP.md — adicionar entradas, importar de issues GH, mostrar estado
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(git worktree list*), Bash(git log*), Bash(git status*), Bash(gh *), Bash(ls *), Bash(mkdir *), Bash(find *)
---

# Roadmap — Visao Multi-Feature

Voce gerencia `thoughts/ROADMAP.md` — a visao de cima dos problemas/features do projeto. Mantem 4 secoes: Backlog, Em planejamento (tem PRD), Em andamento (tem SPEC), Concluido.

**Filosofia**: minimo de ceremonia. Cada entrada tem 1 linha. O detalhe vive no PRD/SPEC/IMP correspondente.

## Resolucao do diretorio root

```bash
git worktree list | head -1 | awk '{print $1}'
```

Use esse caminho como base para `thoughts/ROADMAP.md`.

## Modos de uso

| Invocacao | O que faz |
|---|---|
| `/roadmap` (sem args) | Mostra estado atual + atualiza secoes (migra entre status) + sugere proximos passos |
| `/roadmap add "<descricao>"` | Adiciona entrada nova ao Backlog |
| `/roadmap add #123` | Busca issue do GH via `gh` e adiciona ao Backlog com link, titulo e corpo |

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
3. Adiciona ao **Backlog**:
```markdown
- [ ] NNN — <descricao> — [criado: DD-MM-YYYY]
```
4. Salva
5. Informa:
```
Adicionado ao Backlog:
NNN — <descricao>

Total Backlog: [N]
```

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

4. Adiciona ao **Backlog** com link e resumo:
```markdown
- [ ] NNN — [<titulo da issue>](<url da issue>) [#123] — [criado: DD-MM-YYYY]
```

5. Se a issue tem body relevante (>1 linha de contexto), pergunte:
```
Issue #123 tem contexto extenso. Quer que eu adicione um resumo de 1 linha?
```

6. Se aprovado, complemente a entrada com `— <resumo>`.

7. Salva e informa.

---

## Modo: Sync (sem args)

### Passos

1. Le o ROADMAP atual e extrai todas entradas com seu NNN/slug.

2. Para cada entrada do **Backlog**, verifica se ha um PRD em `thoughts/research/`:
   - Padrao: `PRD-*-<slug>.md` (slug derivado da descricao)
   - Se encontrar: move a entrada para **Em planejamento (tem PRD)** com link
```markdown
- [ ] NNN — [titulo] → [PRD-DD-MM-YYYY-slug.md](research/PRD-DD-MM-YYYY-slug.md)
```

3. Para cada entrada de **Em planejamento**, verifica se ha SPEC em `thoughts/plans/`:
   - Padrao: `SPEC-*-<slug>.md`
   - Se encontrar: move para **Em andamento (tem SPEC)**
```markdown
- [ ] NNN — [titulo] → [SPEC-DD-MM-YYYY-slug.md](plans/SPEC-DD-MM-YYYY-slug.md)
```

4. Para cada entrada de **Em andamento**, verifica se ha IMP em `thoughts/history/`:
   - Padrao: `IMP-*-<slug>.md`
   - Se encontrar: move para **Concluido** (marca `[x]`)
```markdown
- [x] NNN — [titulo] → [IMP-DD-MM-YYYY-slug.md](history/IMP-DD-MM-YYYY-slug.md)
```

5. Detecta arquivos PRD/SPEC/IMP que NAO tem entrada correspondente no roadmap. Para cada:
   - Mostre ao usuario:
```
Encontrei [PRD/SPEC/IMP] sem entrada no roadmap:
- thoughts/research/PRD-DD-MM-YYYY-foo.md

Quer adicionar como entrada nova? (s/n)
```

6. Apresente resumo:
```
Roadmap sincronizado:

- Backlog: [N]
- Em planejamento: [M] (moveu K do Backlog)
- Em andamento: [P] (moveu Q de Em planejamento)
- Concluido: [R] (moveu S de Em andamento)

Itens sem entrada detectados: [T] (perguntei sobre cada)
Sugestao: itens em Backlog ha >14 dias podem precisar revisao
```

7. Salva o ROADMAP atualizado.

---

## Template ROADMAP.md

Quando criar pela primeira vez:

```markdown
# Roadmap

> Visao multi-feature do projeto. Cada linha aponta para PRD/SPEC/IMP correspondente quando existir.
> Use `/roadmap add "<descricao>"` ou `/roadmap add #issue` para adicionar.
> Use `/roadmap` para sincronizar status com arquivos existentes.

## Backlog

[Itens identificados mas sem pesquisa ainda]

## Em planejamento (tem PRD)

[Itens com pesquisa concluida, aguardando spec]

## Em andamento (tem SPEC)

[Itens com plano aprovado, sendo executados]

## Concluido

[Itens entregues — ver IMP para detalhes]
```

---

## Guardrails

- **NNN sequencial**: nunca reuse numero. Sempre `max(numeros existentes) + 1`
- **Slug consistente**: o slug usado no roadmap deve bater com o slug do PRD/SPEC/IMP para a migracao automatica funcionar
- **Nunca duplique entradas**: antes de adicionar issue, verifique se ja existe (por numero #)
- **Migracao sem perda**: ao mover entre secoes, preserve NNN e titulo. So adiciona o link do artefato
- **Sync nao deleta**: itens sem PRD/SPEC/IMP correspondente ficam onde estao (nao move para tras)
- **Itens orfaos**: PRD/SPEC/IMP sem entrada no roadmap perguntam ao usuario, nao adicionam automaticamente
- **GitHub via `gh` CLI**: nunca tokens manuais
- **1 linha por entrada**: detalhes vivem no PRD/SPEC/IMP, nao no roadmap
