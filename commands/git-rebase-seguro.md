---
description: Atualiza a branch da feature com a base de forma segura — baseline de testes antes, conflitos resolvidos com confirmação, test count protection depois, rollback garantido. Nunca force-pusha.
model: claude-sonnet-4-6
allowed-tools: Read, Edit, Glob, Grep, AskUserQuestion, Bash(git fetch*), Bash(git rebase*), Bash(git merge*), Bash(git status*), Bash(git log*), Bash(git diff*), Bash(git stash*), Bash(git rev-list*), Bash(git rev-parse*), Bash(git branch*), Bash(git worktree list*), Bash(git add*), Bash(git checkout*), Bash(git remote*), Bash(gh *), Bash(npm *), Bash(npx *), Bash(bun *), Bash(bunx *), Bash(pnpm *), Bash(node *), Bash(go *), Bash(ls *)
---

# Git Rebase Seguro — atualizar branch longa sem comer código

Branch de feature que vive dias (worktree + PR em review) fica atrás da base. Você incorpora a base com **proteções**: baseline de testes antes, conflito nunca resolvido em silêncio, test count protection depois, e SHA de rollback anotado — porque o jeito mais comum de perder código silenciosamente é um conflito mal resolvido.

## Fluxo

### 1. Pré-checks + ponto de rollback

```bash
git branch --show-current        # ≠ branch default — senão aborte
git status --short               # working tree limpo?
git rev-parse HEAD               # SHA_ORIGINAL — ANOTE: é o rollback garantido
```

- **Working tree sujo**: pare. Ofereça `git stash` (com confirmação; lembre de `stash pop` no fim) ou abortar pra commitar antes.
- Resolva a base do projeto (CLAUDE.md → `main`/`dev`/etc.) e `git fetch origin <base>`.
- `git rev-list --count HEAD..origin/<base>` — quantos commits atrás. Zero → "branch já atualizada", encerre.

### 2. Baseline (antes de mexer)

Rode o gate do projeto (test/typecheck do CLAUDE.md) e **anote a contagem de testes**: `Baseline: X testes, gate [green/red]`.

Gate já vermelho ANTES: avise — atualizar a branch não conserta isso e vai confundir o diagnóstico depois. Pergunte se segue mesmo assim (anote no resumo).

### 3. Estratégia — rebase ou merge

Mostre o que vai entrar (`git log --oneline HEAD..origin/<base>` resumido) e recomende:

- **Rebase** (histórico linear) — quando a branch é só sua e o PR está em **draft**: ninguém baseou trabalho nela.
- **Merge da base** (`git merge origin/<base>`) — quando o PR **já tem review do time**: rebase reescreve os commits e desancora os comentários inline das threads; merge preserva.

Detecte o estado do PR (`gh pr view --json isDraft,reviews 2>/dev/null`) pra embasar a recomendação. Pergunte com a recomendação marcada. **Aviso obrigatório se rebase**: o push depois exigirá `--force-with-lease` — e push é **sempre seu, manual**.

### 4. Executar + conflitos sob confirmação

Execute a estratégia escolhida. A cada conflito, **pare e apresente por arquivo**:

```
Conflito em src/foo.ts:
  Base mudou:   [o que a base fez + por quê, se o commit disser]
  Branch mudou: [o que a sua branch fez]
  Proposta:     [resolução + justificativa em 1-2 linhas]

Aplico a proposta, você resolve manual, ou abortamos? [aplica/manual/aborta]
```

- **Nunca** resolva conflito sem mostrar os dois lados.
- Conflito em **arquivo de teste** merece atenção dobrada (é onde silent deletion nasce) — destaque.
- `aborta` → `git rebase --abort` / `git merge --abort` e encerre com estado intacto.

### 5. Pós-check — test count protection

Re-rode o gate e compare com o baseline:

- **Contagem caiu** → **PARADA DURA**. Provável conflito que comeu teste/código. Mostre: baseline X → atual Y, diff dos arquivos de teste (`git diff SHA_ORIGINAL -- <paths de teste>`). Ofereça rollback: `git reset --hard SHA_ORIGINAL` (com confirmação) ou investigação manual. Não siga.
- **Gate quebrou** (e estava green no baseline) → mostre o erro e os arquivos de conflito relacionados; ofereça corrigir agora (ajustes pequenos) ou rollback.
- **Tudo green e contagem preservada** → siga.

Se tinha stash do passo 1: `git stash pop` agora (e re-rode o gate se o stash tocava código).

### 6. Resumo

```
Branch atualizada com origin/<base> via [rebase/merge].
  Commits incorporados: [N]
  Conflitos resolvidos: [lista de arquivos, ou "nenhum"]
  Gate: green · Test count: [X → X] PRESERVADO
  Rollback disponível: git reset --hard [SHA_ORIGINAL] (enquanto não pushar)

Push é seu:
  [rebase] git push --force-with-lease
  [merge]  git push
```

## Guardrails

- **SHA de rollback anotado antes de qualquer mutação** — e informado no resumo
- **Nunca pushe, nunca force-pushe** — você prepara, o usuário publica
- **Conflito nunca é resolvido em silêncio** — sempre os dois lados + proposta + confirmação
- **Test count protection é bloqueante** — contagem caiu = parada dura com oferta de rollback
- **PR com review do time → recomende merge** (rebase desancora as threads)
- **Nunca na branch default** — este command é pra branch de feature
- **Working tree limpo antes** — sujo = stash com confirmação ou abortar
