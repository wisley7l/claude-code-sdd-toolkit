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

### Passo 6 — Verificar .gitignore

Garantir que `.worktrees/` está no `.gitignore` da raiz. Se não estiver, adicionar.

### Passo 7 — Reportar ao Usuário

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
