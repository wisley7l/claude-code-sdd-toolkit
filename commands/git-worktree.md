---
description: Cria uma git worktree a partir da branch default do repositório para trabalho paralelo. Use quando precisar trabalhar em múltiplas branches simultaneamente.
argument-hint: <nome-da-branch>
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# Git Worktree Creator

Cria uma worktree isolada a partir da **branch default** do repositório, permitindo trabalho paralelo em múltiplas features.

## Argumentos

- `$ARGUMENTS` — Nome da nova branch (obrigatório). Será usado como nome da branch e do diretório.

## Fluxo de Execução

### Passo 1 — Validar Argumentos

Se `$ARGUMENTS` estiver vazio, pergunte ao usuário o nome da branch usando AskUserQuestion.

### Passo 2 — Detectar Branch Default

```bash
git remote show origin | grep 'HEAD branch' | awk '{print $NF}'
```

Se falhar, verificar se `dev`, `main` ou `master` existem localmente.

### Passo 3 — Buscar Última Versão

```bash
git fetch origin <branch-default>
```

### Passo 4 — Definir Local da Worktree

Usar `.worktrees/` na **raiz do repositório**:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_DIR="$REPO_ROOT/.worktrees/$ARGUMENTS"
```

### Passo 5 — Criar a Worktree

```bash
git worktree add -b "$ARGUMENTS" "$WORKTREE_DIR" "origin/<branch-default>"
```

Se a branch já existir, usar sem `-b`:
```bash
git worktree add "$WORKTREE_DIR" "$ARGUMENTS"
```

### Passo 6 — Copiar testes TDD (thoughts/tests/)

Testes unitarios TDD nao sao commitados, entao nao existem na nova worktree. Se o root tiver testes, copiar para a worktree:

```bash
MAIN_ROOT=$(git worktree list | head -1 | awk '{print $1}')
```

Se `$MAIN_ROOT/thoughts/tests/` existir e tiver arquivos:

```bash
mkdir -p "$WORKTREE_DIR/thoughts/tests/"
cp -r "$MAIN_ROOT/thoughts/tests/"* "$WORKTREE_DIR/thoughts/tests/"
```

Avisar o usuario:
```
Testes TDD copiados de <root>/thoughts/tests/ para <worktree>/thoughts/tests/.
Imports e paths relativos podem precisar de ajuste para apontar ao worktree.
```

Se nao existir ou estiver vazio, pular silenciosamente.

### Passo 7 — Centralizar auto-memory (symlink)

Pra que o `MEMORY.md` carregado pelo harness na sessao do worktree seja o do **root** (e nao um novo vazio), crie symlink:

```bash
WORKTREE_ENC=$(echo "$WORKTREE_DIR" | sed 's|/|-|g')
ROOT_ENC=$(echo "$REPO_ROOT" | sed 's|/|-|g')
WORKTREE_MEM="$HOME/.claude/projects/$WORKTREE_ENC/memory"
ROOT_MEM="$HOME/.claude/projects/$ROOT_ENC/memory"

mkdir -p "$ROOT_MEM"
mkdir -p "$HOME/.claude/projects/$WORKTREE_ENC"
```

Casos a tratar:

- **Ja e symlink pro root** (`readlink "$WORKTREE_MEM"` = `$ROOT_MEM`) → skip (idempotente).
- **E symlink pra outro destino** → mostre o destino atual, pergunte antes de substituir. Se confirmar, `unlink` e recrie.
- **E diretorio real** (provavel: harness criou em sessao anterior do worktree) → **NAO substitua sozinho**. Avise: *"`$WORKTREE_MEM` existe como diretorio real. Rode `/memory-organize relink` pra migrar com seguranca (checa notas unicas antes de descartar)."* Continue o resto do fluxo do worktree.
- **Nao existe** → `ln -s "$ROOT_MEM" "$WORKTREE_MEM"`. Reporte: *"Auto-memory centralizado: symlink criado pro root."*

**Por que**: sem isso, o harness cria `memory/` vazio no path encoded do worktree, e `MEMORY.md` carregado no system prompt nao inclui notas salvas trabalhando no root (ou em outros worktrees do mesmo projeto). Symlink centraliza.

### Passo 8 — Verificar .gitignore

Garantir que `.worktrees/` está no `.gitignore` da raiz. Se não estiver, adicionar.

### Passo 9 — Reportar ao Usuário

Após criação, informar:
- Caminho da worktree (absoluto)
- Nome da branch
- Baseada em qual branch default + commit
- Como navegar: `cd <caminho>`
- Como abrir nova sessão Claude Code: `cd <caminho> && claude`
- Como remover depois: `git worktree remove <caminho>`
- Como listar todas: `git worktree list`

## Tratamento de Erros

- Worktree já existe naquele caminho → informar e perguntar se quer navegar até ela
- Branch já existe → perguntar se quer reusar ou escolher outro nome
- Repo sujo na branch default → avisar mas prosseguir (worktrees não exigem estado limpo)

## Importante

- **Nunca** remover worktrees existentes com force
- **Nunca** deletar branches sem consentimento explícito
- Manter o diretório de trabalho principal inalterado após criação
