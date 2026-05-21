---
description: Confirma drafts de decision/blocker/lesson/idea (em thoughts/decisions-draft/) e move pro auto-memory apenas se o PR relacionado estiver mergeado. Pergunta caso a caso. Drafts cancelados (PR fechado sem merge) sao removidos com confirmacao.
model: claude-sonnet-4-6
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Agent, Bash(ls *), Bash(cat *), Bash(mkdir *), Bash(mv *), Bash(rm *), Bash(date *), Bash(git *), Bash(gh *), Bash(realpath *), Bash(pwd), Bash(find *), Bash(stat *), Bash(basename *), Bash(dirname *)
# Complementa /sdd-learning. Enquanto sdd-learning extrai aprendizado novo de IMPs/reviews,
# este command resolve o ciclo "registrar agora → validar com PR → confirmar/cancelar".
---

# SDD Confirm — Confirmar drafts de memoria apos merge de PR

Voce confirma drafts de memoria local (em `thoughts/decisions-draft/`) e os move pro **auto-memory do Claude Code** APENAS se o PR relacionado foi mergeado. Drafts cuja PR foi fechada sem merge sao removidos com confirmacao do user.

**Filosofia**: auto-memory so contem decisoes definitivas. Durante dev/PR review, decisoes ficam como draft local — preservando contexto sem poluir a memoria com entradas que podem ser canceladas/superadas pelo review.

A persistencia final segue a skill `memory-keeper`: arquivo `<tipo>_<slug>.md` na raiz de `~/.claude/projects/<projeto>/memory/`, com entrada correspondente no `MEMORY.md`.

## Pre-cheques

1. **Auto-memory existe** (resolve via root do worktree pra centralizar memorias):
   ```bash
   ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
   PROJ_ENC=$(echo "${ROOT:-$(pwd)}" | sed 's|/|-|g')
   MEM_DIR="$HOME/.claude/projects/$PROJ_ENC/memory"
   test -d "$MEM_DIR"
   ```
   Se nao: diga "Auto-memory nao existe em $MEM_DIR. Rode `/sdd-plan` ou `/quick-task` antes — o diretorio e criado pelo harness na primeira sessao do projeto." e saia.

2. **Drafts**: `thoughts/decisions-draft/` existe e tem pelo menos 1 `.md`. Se nao: diga "Sem drafts pendentes neste projeto" e saia.

3. **gh**: `gh auth status` ok. Se nao: peca ao user rodar `gh auth login` e saia.

## Mapeamento de tipos legados

Drafts antigos podem usar tipos em pt-BR. Faca o mapping no momento do confirm:

| Draft (legado) | Auto-memory (canonico) |
|---|---|
| `decisao` | `decision` |
| `blocker` | `blocker` |
| `licao` | `lesson` |
| `ideia` | `idea` |
| `preferencia` | `preference` |

## Workflow

### Passo 1 — Listar drafts

Liste todos os `.md` em `thoughts/decisions-draft/`. Para cada um, leia o frontmatter:

```
---
type: decision | blocker | lesson | idea | preference   # (ou legado em pt-BR)
title: <titulo>
date: <YYYY-MM-DD>
branch: <branch onde foi criado>
pr: <numero opcional>
---
```

Mostre o resumo:

```
Drafts pendentes em thoughts/decisions-draft/ (N):
  1. <YYYY-MM-DD>-<slug>.md — <type> — "<title>" — branch: <branch> — PR: <#N | "?">
  2. ...
```

### Passo 2 — Para cada draft, descobrir status do PR

**Caso A: PR no frontmatter**

```bash
gh pr view <numero> --json state,mergedAt,reviews,commits,changedFiles,additions,deletions
```

Estados:
- `state: "MERGED"` → vai pro Passo 3 (PROPOR MOVIMENTACAO)
- `state: "OPEN"` → skip, mostre "PR #<N> ainda aberto, draft preservado"
- `state: "CLOSED"` (sem `mergedAt`) → vai pro Passo 4 (PROPOR REMOCAO)

**Caso B: Sem PR no frontmatter**

Tente descobrir pela branch:
```bash
gh pr list --head <branch> --state all --json number,state,mergedAt,title --limit 5
```

- 1 resultado: atualize o frontmatter do draft com o `pr: <numero>` e siga como Caso A.
- 0 resultados: pergunte ao user "Sem PR encontrado pra branch `<branch>`. Como proceder?"
  - `(n) Numero do PR` — user informa, atualiza frontmatter e segue como Caso A
  - `(p) Promover sem PR` — vai pro Passo 3 (sem dados de review)
  - `(s) Skip` — preserva o draft, segue pro proximo
- >1 resultados: liste os PRs e peca pra user escolher.

### Passo 3 — PROPOR MOVIMENTACAO (PR mergeado)

Mostre o conteudo COMPLETO do draft + contexto do PR:

```
Draft: <title>
Tipo: <type-canonico>   # ja convertido pelo mapping acima
Branch: <branch>  PR: #<N> (mergeado em <data>, +<adds>/-<dels> linhas, <files> arquivos)

Conteudo do draft:
---
<conteudo do draft, completo>
---

Atividade no review (resumido):
- <N> reviews, <M> commits durante review
- Comentarios chave (se houver): "<quote breve>"

A decisao continua valida como foi escrita?
  (s) Sim, mover para a memoria como esta
  (e) Editar antes de mover (eu mostro o conteudo no Edit pra voce ajustar)
  (n) Nao, remover o draft (decisao foi superada/cancelada pelo review)
  (k) Skip (decidir depois)
```

Se `(s)`:
1. Construa slug a partir do nome do draft (tira a data — vai pro frontmatter): `<YYYY-MM-DD>-<slug>.md` → `<slug>`
2. Path final: `$MEM_DIR/<type-canonico>_<slug>.md`
3. **Verifique colisao**: se ja existir nota com esse slug, vai pro caso de borda "Memory tem nota com mesmo slug".
4. Construa o conteudo no formato da skill `memory-keeper`:
   ```yaml
   ---
   name: <type-canonico>-<slug-kebab>
   description: <copia do title ou hook curto>
   metadata:
     type: <type-canonico>
     created: <date do draft>
     updated: <data ISO do PR merge>
     pr: <numero>
     branch: <branch>
   ---

   <corpo do draft, sem a linha "**Draft — sera proposto..." se existir>

   **Why:** <extrair do draft se houver, senao deixar placeholder>

   **How to apply:** <extrair do draft se houver, senao deixar placeholder>
   ```
5. Escreva o arquivo em `$MEM_DIR/<type-canonico>_<slug>.md`.
6. **Atualize o `MEMORY.md`** seguindo a skill `memory-keeper`:
   - Adicione linha na tabela da secao `## <Type-canonico capitalizado>`
   - Se a secao nao existir, crie respeitando a ordem canonica (user → feedback → project → reference → decision → blocker → lesson → idea → preference)
7. Remova o arquivo de draft em `thoughts/decisions-draft/`.
8. Sumarize: "✅ Movido para `$MEM_DIR/<type-canonico>_<slug>.md`"

Se `(e)`:
- Mostre o conteudo
- Pergunte o que ajustar (ou abra Edit no draft)
- Apos ajustes, volte e pergunte `(s)` ou `(n)` de novo

Se `(n)`:
- Confirme: "Remover draft `<slug>` permanentemente?"
- Remova o arquivo
- Sumarize: "🗑️ Removido"

Se `(k)`:
- Preserve o draft, va pro proximo

### Passo 4 — PROPOR REMOCAO (PR fechado sem merge)

```
Draft: <title>
PR #<N> foi FECHADO sem merge em <data>.

Conteudo do draft:
---
<conteudo>
---

  (r) Remover o draft (decisao nao se aplicou)
  (m) Manter como draft (PR pode ser reaberto / ainda relevante)
  (p) Promover pra memoria mesmo assim (decisao valida fora do PR)
```

Aplique conforme escolha. `(p)` segue mesma logica do `(s)` do Passo 3.

### Passo 5 — Sumario final

```
/sdd-confirm concluido:
  ✅ Movidos pra memoria:    N
  🗑️ Removidos:              M
  ⏸️ Skipped (PR aberto):    K
  ⏸️ Skipped (manual):       J

Drafts remanescentes em thoughts/decisions-draft/: <count>
```

## Casos de borda

- **Memory tem nota com mesmo slug**: mostre as duas versoes lado-a-lado e pergunte (atualizar nota existente acrescentando o que falta, salvar com `_v2` no slug, cancelar).
- **PR foi `reopened` depois de `merged`**: trate como MERGED (codigo entrou na main).
- **Multiplos PRs na mesma branch**: o mais recente MERGED ganha. Se houver multiplos MERGED, pergunte.
- **`gh` falha (network, rate limit)**: nao remova nada. Peca pra user rodar de novo mais tarde.
- **Frontmatter malformado num draft**: avise e pule esse draft. Nao tente "corrigir" sem permissao.
- **Tipo legado nao mapeavel** (ex: draft com `type: foo`): pergunte ao user qual tipo canonico aplicar antes de mover.

## Boas praticas

- **Sempre mostre o conteudo do draft antes de pedir confirmacao** — o user precisa lembrar do que se trata. Nao confie que ele lembra de 1 semana atras.
- **Cite o que mudou no PR review** quando relevante (ex: "review pediu pra mudar de X pra Y") — isso ajuda o user a decidir se a decisao do draft ainda vale.
- **Confirmacao individual, nao batch**. Tentacao de "confirmar todos pendentes de uma vez" e erro.
- **Em duvida, preserve o draft**. No harm em manter. Pior caso: rodar de novo depois.
- **MEMORY.md sempre atualizado**: nota sem linha no `MEMORY.md` vira orfa — depois `/memory-organize` arruma, mas evite criar problema desnecessario.

## Relacao com outros commands

- `/sdd-plan` / `/quick-task` / `/executor-plan` / `/sdd-review` **CRIAM** drafts em `thoughts/decisions-draft/` quando registram memoria durante um trabalho que vai pra PR
- `/sdd-confirm` **MOVE** drafts pro auto-memory apos merge (via skill `memory-keeper`)
- `/sdd-learning` **EXTRAI** aprendizado novo de IMPs/reviews ja escritos (input diferente, complementar)
- `/memory-organize` **ARRUMA** a memoria periodicamente (sub-sumarios, orfaos, links quebrados)

Drafts em `thoughts/decisions-draft/` ficam gitignored (convencao `thoughts/`) — sao locais ao projeto.
