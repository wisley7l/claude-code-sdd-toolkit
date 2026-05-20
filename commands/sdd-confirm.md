---
description: Confirma drafts de decisao/blocker/licao/ideia (em thoughts/decisions-draft/) e move pro vault apenas se o PR relacionado estiver mergeado. Pergunta caso a caso. Drafts cancelados (PR fechado sem merge) sao removidos com confirmacao.
model: claude-sonnet-4-6
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Bash(ls *), Bash(cat *), Bash(mkdir *), Bash(mv *), Bash(rm *), Bash(date *), Bash(git *), Bash(gh *), Bash(realpath *), Bash(pwd), Bash(find *), Bash(stat *), Bash(basename *), Bash(dirname *)
# Complementa /sdd-learning. Enquanto sdd-learning extrai aprendizado novo de IMPs/reviews,
# este command resolve o ciclo "registrar agora → validar com PR → confirmar/cancelar".
---

# SDD Confirm — Confirmar drafts de memoria apos merge de PR

Voce confirma drafts de memoria local (em `thoughts/decisions-draft/`) e os move pro vault Obsidian central APENAS se o PR relacionado foi mergeado. Drafts cuja PR foi fechada sem merge sao removidos com confirmacao do user.

**Filosofia**: vault central so contem decisoes definitivas. Durante dev/PR review, decisoes ficam como draft local — preservando contexto sem poluir o vault com entradas que podem ser canceladas/superadas pelo review.

## Pre-cheques

1. **Detectar org/projeto**: heuristica padrao `~/codigos/<org>/<projeto>/`. Se nao bater, pergunte ao user.
2. **Vault**: `$CLAUDE_VAULT_PATH` setado e diretorio existe. Se nao: diga "Configure CLAUDE_VAULT_PATH primeiro (ou use modo legacy via STATE.md)" e saia.
3. **Drafts**: `thoughts/decisions-draft/` existe e tem pelo menos 1 `.md`. Se nao: diga "Sem drafts pendentes neste projeto" e saia.
4. **gh**: `gh auth status` ok. Se nao: pe ao user rodar `gh auth login` e saia.

## Workflow

### Passo 1 — Listar drafts

Liste todos os `.md` em `thoughts/decisions-draft/`. Para cada um, leia o frontmatter:

```
---
type: decisao | blocker | licao | ideia | preferencia
title: <titulo>
date: <YYYY-MM-DD>
branch: <branch onde foi criado>
pr: <numero opcional>
projeto: <opcional>
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
Tipo: <type>
Branch: <branch>  PR: #<N> (mergeado em <data>, +<adds>/-<dels> linhas, <files> arquivos)

Conteudo do draft:
---
<conteudo do draft, completo>
---

Atividade no review (resumido):
- <N> reviews, <M> commits durante review
- Comentarios chave (se houver): "<quote breve>"

A decisao continua valida como foi escrita?
  (s) Sim, mover para o vault como esta
  (e) Editar antes de mover (eu mostro o conteudo no Edit pra voce ajustar)
  (n) Nao, remover o draft (decisao foi superada/cancelada pelo review)
  (k) Skip (decidir depois)
```

Se `(s)`:
1. Construa o path final: `$CLAUDE_VAULT_PATH/<org>/<projeto>/state/<type>s/<YYYY-MM-DD>-<slug>.md`
   - `type` no plural: `decisao` → `decisoes/`, `blocker` → `blockers/`, `licao` → `licoes/`, `ideia` → `ideias/`, `preferencia` → `preferencias/`
2. `mkdir -p` do diretorio pai se necessario
3. Copie o conteudo do draft pro destino, atualizando o frontmatter:
   - Adicione: `status: confirmed`
   - Adicione: `merged_at: <data ISO do PR>`
   - Garanta: `pr: <numero>`
4. Remova do corpo qualquer linha tipo "**Draft — sera proposto ao vault apos merge**"
5. Remova o arquivo de draft em `thoughts/decisions-draft/`
6. Sumarize: "✅ Movido para `<path>`"

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
  (p) Promover pro vault mesmo assim (decisao valida fora do PR)
```

Aplique conforme escolha. `(p)` segue mesma logica do `(s)` do Passo 3.

### Passo 5 — Sumario final

```
/sdd-confirm concluido:
  ✅ Movidos pro vault:     N
  🗑️ Removidos:             M
  ⏸️ Skipped (PR aberto):    K
  ⏸️ Skipped (manual):       J

Drafts remanescentes em thoughts/decisions-draft/: <count>
```

## Casos de borda

- **Vault tem nota com mesmo slug**: mostre as duas versoes lado-a-lado e pergunte (sobrescrever, criar com `-v2`, cancelar).
- **PR foi `reopened` depois de `merged`**: trate como MERGED (codigo entrou na main).
- **Multiplos PRs na mesma branch**: o mais recente MERGED ganha. Se houver multiplos MERGED, pergunte.
- **`gh` falha (network, rate limit)**: nao remova nada. Peca pra user rodar de novo mais tarde.
- **Frontmatter malformado num draft**: avise e pule esse draft. Nao tente "corrigir" sem permissao.

## Boas praticas

- **Sempre mostre o conteudo do draft antes de pedir confirmacao** — o user precisa lembrar do que se trata. Nao confie que ele lembra de 1 semana atras.
- **Cite o que mudou no PR review** quando relevante (ex: "review pediu pra mudar de X pra Y") — isso ajuda o user a decidir se a decisao do draft ainda vale.
- **Confirmacao individual, nao batch**. Tentacao de "confirmar todos pendentes de uma vez" e erro.
- **Em duvida, preserve o draft**. No harm em manter. Pior caso: rodar de novo depois.

## Relacao com outros commands

- `/sdd-plan` / `/quick-task` / `/executor-plan` / `/sdd-review` **CRIAM** drafts em `thoughts/decisions-draft/` quando registram memoria durante um trabalho que vai pra PR
- `/sdd-confirm` **MOVE** drafts pro vault apos merge
- `/sdd-learning` **EXTRAI** aprendizado novo de IMPs/reviews ja escritos (input diferente, complementar)

Drafts em `thoughts/decisions-draft/` ficam gitignored (convencao `thoughts/`) — sao locais ao projeto.
