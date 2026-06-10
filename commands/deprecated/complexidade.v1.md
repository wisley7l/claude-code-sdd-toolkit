---
description: Mede complexidade ciclomática APENAS nos arquivos alterados (vs base ou staged). Report inline, threshold 10 (ou CLAUDE.md do projeto). Detecta ferramenta na ordem linter do projeto → lizard → fta. Com --fix, oferece refactor via code-simplifier. Nunca commita.
model: claude-haiku-4-5-20251001
allowed-tools: Read, Glob, Grep, Agent, AskUserQuestion, Bash(git diff*), Bash(git status*), Bash(git branch*), Bash(git worktree list*), Bash(git merge-base*), Bash(lizard *), Bash(npx *), Bash(bunx *), Bash(ls *)
---

# Check de Complexidade — arquivos alterados

Atalho standalone pro mesmo gate de complexidade usado por `/sdd-review` (Etapa 1) e `/executor-plan` (Verificação Final). Mede complexidade ciclomática **apenas nos arquivos alterados**, reporta inline e termina. Não salva relatório, não commita.

## Flags

- `--staged` — mede só os arquivos staged (`git diff --cached`)
- `--threshold N` — sobrescreve o threshold (default: 10, ou o que o `CLAUDE.md` do projeto declarar)
- `--fix` — após o report, oferece correção via `code-simplifier`

## Fluxo de Execução

### Passo 1 — Resolver escopo (arquivos alterados)

**Default** (sem `--staged`): união de alterados vs base + working tree:

```bash
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main 2>/dev/null)
git diff --name-only "$BASE"...HEAD
git diff --name-only          # não staged
git diff --cached --name-only # staged
```

> Se o projeto usa outra branch base (`dev`, `develop` — ver `CLAUDE.md`), use ela. Se ambíguo, pergunte uma vez.

**Com `--staged`**: só `git diff --cached --name-only`.

Filtre pra arquivos de código (`.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.go`, `.py`, etc.). Se a lista ficar vazia:

```
Nenhum arquivo de código alterado — nada a medir.
```

### Passo 2 — Resolver threshold

Ordem: flag `--threshold` → limite declarado no `CLAUDE.md` do projeto → **10** (default).

### Passo 3 — Medir (primeira ferramenta disponível)

1. **Regra de complexidade já ativa no linter do projeto** (ESLint `complexity`, oxlint equivalente; Biome só tem `noExcessiveCognitiveComplexity` — métrica **cognitiva**, default 15: se for o caso, use o threshold do Biome e anote a métrica no report) → rode o lint restrito aos arquivos do escopo e extraia as violações
2. **`lizard`** — CCN por função, parseia TS/JS/Go/Python nativo:
   ```bash
   lizard -C <threshold> <arquivos>
   ```
3. **`npx fta-cli <diretórios>`** — score por arquivo (menos preciso; anote a limitação)

Se nenhuma disponível, informe e encerre (não invente medição):

```
Nenhuma ferramenta de medição disponível.
Sugestão: pip install lizard (métrica por função, multi-linguagem)
```

### Passo 4 — Filtrar funções tocadas pelo diff

Cruze as linhas das funções violadoras com os hunks do diff (`git diff -U0`). Função com CC alta que o diff **não tocou** sai do report principal — vai pra uma linha de rodapé ("N funções pré-existentes acima do threshold ignoradas").

### Passo 5 — Report inline

```
Complexidade ciclomática — [N] arquivos alterados (threshold: 10, ferramenta: lizard)

| Função | Arquivo | CC | Status |
|---|---|---|---|
| processOrder | src/orders/process.ts:42 | 17 | 🔴 alto (>15) |
| validateCart | src/cart/validate.ts:108 | 12 | 🟡 atenção (11–15) |

✅ [M] funções tocadas dentro do limite
(rodapé: [K] funções pré-existentes acima do threshold ignoradas — não introduzidas por você)
```

Se zero violações: report de 1 linha (`✅ Todas as [M] funções tocadas ≤ [threshold]`) e encerre.

### Passo 6 — Fix opcional (só com `--fix`, ou pergunte se houver 🔴)

Se `--fix` foi passado (ou há violações >15 e o usuário topar quando perguntado):

Lance `Agent` com `subagent_type: code-simplifier` escopado aos arquivos das violações:

```
Reduza a complexidade ciclomática das funções abaixo para <= <threshold> SEM mudar comportamento:
- <arquivo>:<função> (CC atual: N)
Técnicas: extrair helpers, early returns, substituir cadeias if/else por lookup, decompor condições.
NÃO toque em funções fora da lista. NÃO altere testes.
```

Depois: re-meça e, se o `CLAUDE.md` declarar gate (typecheck/test), rode-o. Mostre o antes → depois. **Não faça `git add` nem commit** — mudanças ficam no working tree pro usuário revisar.

## Guardrails

- **Nunca o repo inteiro**: escopo é sempre arquivos alterados. Sem exceção
- **Nunca commite nem stage**: report e (opcionalmente) fix no working tree. Git é ação do usuário
- **Não invente medição**: sem ferramenta disponível = informar e encerrar
- **CC pré-existente é rodapé, não issue**: só funções tocadas pelo diff entram no report principal
- **Fix só sob confirmação**: `--fix` explícito ou pergunta respondida com sim
