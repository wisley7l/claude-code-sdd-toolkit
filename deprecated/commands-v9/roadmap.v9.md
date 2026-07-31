---
description: Gerenciar o roadmap (vault Obsidian) — adicionar itens, ligar dependências, sincronizar por PR, migrar do formato antigo
model: claude-haiku-4-5-20251001
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(git worktree list*), Bash(git log*), Bash(git status*), Bash(gh *), Bash(ls *), Bash(mkdir *), Bash(mv *), Bash(find *), Bash(basename *)
---

# Roadmap — Visao Multi-Feature (vault Obsidian)

Voce gerencia o roadmap do projeto em `thoughts/roadmap/` — a visao de cima dos problemas/features.

O roadmap e um **vault Obsidian**: cada item e um arquivo `.md`, cada dependencia e um wikilink `[[...]]`, e o **grafo e nativo** (o Obsidian desenha as arestas a partir dos links — nao se gera mermaid). O contrato completo do arquivo de item, dos algoritmos e da migracao esta na reference `roadmap-item.md` — procure em `.claude/sdd-references/` do projeto, senao em `~/.claude/sdd-references/`. **Fallback** (reference ausente): item = `thoughts/roadmap/<status>/NNN-slug.md` com frontmatter (`id`, `titulo`, `pr`, `criado`, `plan`, `next`) + corpo com `**Depende de:** [[MMM-slug]]` e `**Docs:** [[SPEC]] · [[PLAN]]`; status = a pasta (`backlog/` · `em-progresso/` · `concluido/`); dependencia = wikilink; sem ciclos; NNN sequencial nunca reusado.

O eixo do status e o **estado real do trabalho (o PR)**, NAO a presenca de PLAN. Tres pastas de status + duas visoes derivadas no hub:

| Onde | Significado |
|---|---|
| `backlog/` | Tudo identificado mas sem PR aberto. Pode ter PLAN ou nao. |
| `em-progresso/` | Tem PR aberto e ativo. |
| `concluido/` | PR merged. |
| Hub: `## 🔴 Próximos` | Itens com `next: true` — fila curta curada **manualmente**. O sync NAO liga isso sozinho. |
| Hub: `## 🔓 Desbloqueados agora` | **Derivado** — itens de `backlog/` cujas dependencias estao todas em `concluido/`. E daqui que sai "o proximo passo apos um merge". |

**Filosofia**: minimo de ceremonia. Cada item e um arquivo enxuto (frontmatter + 2-3 linhas). O detalhe vive no PLAN/IMP/PR linkado.

**Dependencia entre PRs (`Depende de:`)**: quando a ordem importa (item-B so comeca depois do item-A mergear), o corpo de B carrega `**Depende de:** [[A-slug]]`. E dai que o grafo do Obsidian desenha a seta, e e dai que o `## 🔓 Desbloqueados agora` se calcula. Contrato completo: reference `roadmap-item.md`.

**Quem alimenta o roadmap** (alem do `add` manual/issue deste command):
- `/sdd-plan` (e `/sdd-plan-eco`) cria **1 item por PR previsto** em `backlog/` ao escrever um PLAN (PLAN multi-PR = N itens com `Depende de:` entre slices sequenciais).
- `/pr-draft` **move** o item do slice de `backlog/` pra `em-progresso/` (+ preenche `pr:`) ao abrir o draft.
- `/roadmap` sync e `/sdd-close` movem pra `concluido/` no merge.
Ou seja: o sync deste command reconcilia por status de PR, mas os itens ja chegam populados pelo fluxo SDD.

**Escopo**: ver memoria de feedback do projeto sobre o que entra no roadmap (ex: backend-only) — respeitar a regra vigente. Em duvida, perguntar.

## Resolucao do diretorio root

```bash
ROOT=$(git worktree list | head -1 | awk '{print $1}')
ROADMAP_DIR="$ROOT/thoughts/roadmap"
HUB="$ROADMAP_DIR/ROADMAP.md"
```

Use `$ROADMAP_DIR` como base do vault.

## Deteccao de formato (rode SEMPRE antes de operar)

- Existe `$ROADMAP_DIR/` com itens (`backlog/`, `em-progresso/` ou `concluido/`) → **formato novo**, siga o modo pedido.
- Existe `$ROOT/thoughts/ROADMAP.md` (arquivo unico antigo) e **nao** existe `$ROADMAP_DIR/` → **formato antigo**: avise e ofereca **migrar** (`/roadmap migrar`) antes de qualquer outra operacao. Nao opere no arquivo antigo.
- Nao existe nenhum → primeiro `add`/`sdd-plan` cria o vault do zero (template do hub na reference).

## Modos de uso

| Invocacao | O que faz |
|---|---|
| `/roadmap` (sem args) | Sincroniza status por PR (move itens entre pastas) + recalcula 🔓 Desbloqueados + regenera o hub + mostra estado |
| `/roadmap add "<descricao>"` | Cria item novo em `backlog/`. Aceita ` dep: NNN[, MMM]` no fim pra ja ligar dependencia |
| `/roadmap add #123` | Busca issue do GH via `gh` e cria item em `backlog/` com link, titulo e corpo |
| `/roadmap dep NNN <- MMM[, PPP]` | Liga/atualiza a(s) dependencia(s) do item NNN (passa a depender de MMM, PPP) |
| `/roadmap dep NNN clear` | Remove todas as dependencias de NNN |
| `/roadmap migrar` | Converte o `thoughts/ROADMAP.md` antigo (arquivo unico) pro vault `thoughts/roadmap/` |

## Configuracao Inicial

Se `$ROADMAP_DIR/` nao existir, crie a estrutura ao primeiro item:
```bash
mkdir -p "$ROADMAP_DIR/backlog" "$ROADMAP_DIR/em-progresso" "$ROADMAP_DIR/concluido"
```
E gere o hub `ROADMAP.md` com o template da reference.

Identificar o modo:
- Argumentos vazios → **sync**
- Comeca com `add "..."` → **add manual**
- Comeca com `add #...` → **add issue**
- Comeca com `dep ` → **dependencia**
- `migrar` → **migracao**
- Outro → mostre help e saia

---

## Modo: Add Manual

`/roadmap add "<descricao>"`

### Passos

1. Le todos os itens existentes (varre as 3 pastas) pra achar o proximo NNN.
2. Decide o NNN: `max(NNN de todas as pastas) + 1`, 3 digitos. Gera o `slug` (3-6 palavras kebab-case do titulo).
3. Se a descricao termina com ` dep: MMM[, PPP]`, separe: o resto e o titulo; cada NNN vira dependencia (valide que existe como item — ignore+sinalize os inexistentes).
4. Cria `$ROADMAP_DIR/backlog/NNN-slug.md` com o frontmatter + corpo (reference `roadmap-item.md`). Inclui `**Depende de:** [[MMM-slug]]` so se houver dependencia.
5. **Regenera o hub** (`ROADMAP.md`) e salva.
6. Informa: `Adicionado ao Backlog: NNN — <titulo>` (+ `· depende de MMM` se houver).

---

## Modo: Add Issue

`/roadmap add #123`

### Passos

1. Busca a issue:
```bash
gh issue view 123 --json title,body,url,labels,number
```
2. Verifica se ja existe item que referencia `#123` (varre as pastas). Se sim, informe e saia.
3. Decide o proximo NNN, gera o slug do titulo da issue.
4. Cria `$ROADMAP_DIR/backlog/NNN-slug.md`. No corpo, linke a issue: `**Issue:** [#123](<url>)`. Se o body da issue tem contexto relevante (>1 linha), pergunte se deve incluir 1 linha de resumo.
5. **Regenera o hub** e salva. Informa.

---

## Modo: Dependencia

`/roadmap dep NNN <- MMM[, PPP]` (ligar) ou `/roadmap dep NNN clear` (desligar).

Define **a ordem entre PRs**: NNN so comeca depois que MMM (e PPP) mergearem. E dai que o grafo desenha as setas e o 🔓 Desbloqueados se calcula.

### Passos

1. Localize o item NNN (varra as pastas). Se nao existir, informe e saia.
2. **`clear`**: remova a linha `**Depende de:** ...` do corpo de NNN, se houver.
   **`<- MMM[, PPP]`**: valide que cada MMM/PPP existe (os inexistentes sao ignorados+sinalizados). Rejeite auto-dependencia (`NNN <- NNN`). Escreva/substitua a linha `**Depende de:** [[MMM-slug]], [[PPP-slug]]` no corpo de NNN.
3. **Guarda de ciclo**: seguindo os `Depende de:` a partir de NNN, se alcancar NNN de volta, a nova aresta fecha um ciclo — **nao aplique** e avise (ordem impossivel).
4. **Regenera o hub** e salva.
5. Informe: `NNN agora depende de: MMM, PPP` (ou `NNN sem dependencias`).

---

## Modo: Sync (sem args)

O sync e **PR-driven**: o que dita a pasta de cada item e o status do(s) PR(s) que ele referencia (`pr:` no frontmatter), nao a existencia de PLAN/IMP.

### Passos

1. Varre as 3 pastas e extrai cada item (NNN, `pr:`, `Depende de:`).

2. Para cada item com `pr:` preenchido, consulta o status:
```bash
gh pr view <N> --json state,mergedAt,updatedAt,title
```
   Aplica as transicoes (movendo o **arquivo** entre pastas com `mv`):
   - **merged** → `mv` pra `concluido/`.
   - **open com atividade recente** (updatedAt < ~4 semanas) → garantir em `em-progresso/`.
   - **open mas parado** (updatedAt > ~4 semanas) → NAO move sozinho: sinaliza sugerindo voltar pra `backlog/` (com nota `WIP parado desde DD-MM`).
   - **closed sem merge** → sinaliza (PR morto); sugere voltar pra `backlog/` preservando contexto.

   Mover entre pastas nao quebra wikilink (Obsidian resolve por nome). Nao e `git mv` (`thoughts/` e gitignored).

3. **🔴 Próximos** (`next: true`) e o conteudo de `backlog/` sao curados manualmente — o sync nao liga `next:` sozinho.

4. Detecta PRs abertos do autor que NAO tem item no roadmap:
```bash
gh pr list --author "@me" --state open --json number,title,headRefName
```
   Para cada, mostre e pergunte se quer adicionar (respeitando o escopo vigente — ex: backend-only).

5. **Recalcula 🔓 Desbloqueados agora**: item de `backlog/` com `Depende de:` cujas deps estao **todas** em `concluido/` (reference `roadmap-item.md`, algoritmo). E o "proximo passo" apos os merges desta rodada.

6. **Regenera o hub** `ROADMAP.md` (linka todos, agrupa por pasta, lista 🔴 Próximos e 🔓 Desbloqueados). Sinalize links orfaos (`[[...]]` apontando pra item inexistente) e ciclos.

7. Apresente resumo:
```
Roadmap sincronizado (PR-driven):

- 🔴 Próximos: [N]
- 🔓 Desbloqueados agora: [D]
- Backlog: [M]
- Em progresso: [P] (PRs abertos)
- Concluído: [R] (moveu S por merge)

Sinais: [T] PRs parados (>4 sem) · [U] PRs fechados sem merge · [V] PRs abertos sem item · [W] links órfãos
```

8. Salva.

---

## Modo: Migracao

`/roadmap migrar` — converte o `thoughts/ROADMAP.md` antigo (arquivo unico) pro vault `thoughts/roadmap/`.

### Passos

1. **Confirme o gatilho**: existe `$ROOT/thoughts/ROADMAP.md` e **nao** existe `$ROADMAP_DIR/` com itens. Se `$ROADMAP_DIR/` ja tem itens → avise "ja migrado" e saia (idempotente).
2. Siga o **algoritmo de migracao** da reference `roadmap-item.md` (parse das entradas → pasta por secao → 1 arquivo por entrada com frontmatter → `dep:` vira `**Depende de:** [[...]]` → `PLAN:` vira `**Docs:** [[...]]` → descarta o bloco mermaid → gera hub → backup do antigo).
3. **Mostre o de-para ANTES de escrever** e peca confirmacao:
```
Migração do ROADMAP (antigo → vault Obsidian):

  Backlog:      [M] itens → backlog/
  Em progresso: [P] itens → em-progresso/
  Concluído:    [R] itens → concluido/
  🔴 Próximos:  [N] itens marcados next: true
  Dependências: [D] arestas [[...]] preservadas

  Antigo ROADMAP.md → backup em roadmap/_migrado-de-ROADMAP.md.bak

  (s) Migrar    (n) Cancelar
```
4. Se `(s)`: cria as pastas, escreve os itens, gera o hub, move o antigo pro `.bak`. Sinalize links orfaos/ciclos encontrados.
5. Sumarize: "✅ Migrado: [K] itens → `thoughts/roadmap/` · hub regenerado · antigo em `.bak`".

---

## Guardrails

- **NNN sequencial**: nunca reuse numero. Sempre `max(NNN de todas as pastas) + 1`. E o id estavel do no no grafo.
- **Nunca duplique itens**: antes de adicionar issue, verifique se ja existe (por `#N`).
- **Migracao sem perda**: ao mover item entre pastas, preserve o arquivo inteiro (NNN, titulo, `Depende de:`, `Docs:`); so muda a pasta (status) e o `pr:` quando aplicavel.
- **Sync e PR-driven**: a pasta segue o status do PR (merged/open/closed), nao a presenca de PLAN/IMP.
- **🔴 Próximos e manual**: o sync nunca liga `next: true` sozinho — isso e priorizacao humana.
- **PRs parados/fechados**: o sync sinaliza mas nao rebaixa sozinho — pede confirmacao.
- **GitHub via `gh` CLI**: nunca tokens manuais.
- **1 item = 1 arquivo enxuto**: detalhes vivem no PLAN/IMP/PR linkado, nao no item.
- **Escopo do roadmap**: respeitar a regra vigente (ex: backend-only, via memoria de feedback do projeto).
- **O grafo e nativo, nunca se edita a mao**: as arestas saem dos `[[links]]` do `Depende de:`/`Docs:`. Pra mudar o desenho, mude o `Depende de:` (via `/roadmap dep`). Nao existe mais bloco mermaid.
- **`Depende de:` = ordem entre PRs**: NNN depende de MMM significa "NNN nao comeca antes de MMM mergear". Sem ciclos; NNN referenciado tem que existir (senao vira no fantasma no grafo — sinalize).
- **Vault sob `thoughts/` (gitignored)**: `mv`/`Write` simples, nunca `git mv`, nunca commit/push.
