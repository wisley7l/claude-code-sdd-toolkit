---
description: Remove uma git worktree de forma segura, verificando mudanças não commitadas.
argument-hint: <nome-da-worktree>
allowed-tools: Bash, Read, AskUserQuestion
---

# Git Worktree Remover

Remove uma worktree existente de forma segura, verificando mudanças não commitadas antes de prosseguir.

## Argumentos

- `$ARGUMENTS` — Nome da worktree a remover (opcional). Se vazio, listar worktrees disponíveis e perguntar qual remover.

## Fluxo de Execução

### Passo 1 — Listar Worktrees

```bash
git worktree list
```

Se `$ARGUMENTS` estiver vazio, listar as worktrees disponíveis em `.worktrees/` e perguntar ao usuário qual remover usando AskUserQuestion.

### Passo 2 — Verificar se Estamos Dentro da Worktree

Verificar se o diretório de trabalho atual (`pwd`) está dentro da worktree que será removida. Se estiver, **parar imediatamente** e avisar:

```
⚠️ Você está dentro da worktree que será removida.
Saia primeiro com: cd <repo-root>
Depois execute este comando novamente.
```

**Não prosseguir** — remover a worktree atual invalida a sessão do Claude.

### Passo 3 — Resolver Caminho

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_DIR="$REPO_ROOT/.worktrees/$ARGUMENTS"
```

Verificar que a worktree existe. Se não existir, informar e listar as disponíveis.

### Passo 4 — Verificar Mudanças Não Commitadas

```bash
git -C "$WORKTREE_DIR" status --porcelain
```

Se houver mudanças, **avisar o usuário** e perguntar se deseja:
- Continuar removendo (perde mudanças)
- Cancelar para commitar antes

### Passo 5 — Migrar testes TDD (thoughts/tests/)

Se a worktree tiver `thoughts/tests/` com arquivos:

1. Resolver o root do repo principal:
```bash
MAIN_ROOT=$(git worktree list | head -1 | awk '{print $1}')
```

2. Copiar testes para o root:
```bash
mkdir -p "$MAIN_ROOT/thoughts/tests/"
cp -r "$WORKTREE_DIR/thoughts/tests/"* "$MAIN_ROOT/thoughts/tests/"
```

3. Avisar o usuario:
```
Testes TDD migrados de <worktree>/thoughts/tests/ para <root>/thoughts/tests/.
Imports e paths relativos podem precisar de ajuste manual para apontar ao root.
```

Se `thoughts/tests/` nao existir ou estiver vazio, pular este passo silenciosamente.

### Passo 6 — Verificar Branch Remota

Detectar a branch associada e verificar se já foi enviada ao remote:

```bash
BRANCH=$(git -C "$WORKTREE_DIR" branch --show-current)
git branch -vv | grep "$BRANCH"
```

Se a branch não tiver tracking remoto, avisar o usuário antes de prosseguir.

### Passo 7 — Remover Worktree

```bash
git worktree remove "$WORKTREE_DIR"
```

Se falhar por mudanças pendentes e o usuário confirmou que quer prosseguir:

```bash
git worktree remove --force "$WORKTREE_DIR"
```

### Passo 8 — Reportar ao Usuário

Informar:
- Worktree removida com sucesso
- Branch local mantida (informar nome)
- Listar worktrees restantes: `git worktree list`

## Tratamento de Erros

- Worktree não existe → listar disponíveis e perguntar
- Mudanças não commitadas → avisar e pedir confirmação antes de forçar
- Usuário está dentro da worktree → avisar que precisa sair antes de remover

## Importante

- **Nunca** forçar remoção sem consentimento explícito
- **Nunca** deletar a branch local (apenas a worktree)
- **Nunca** remover a worktree principal (bare)
- Sempre verificar mudanças pendentes antes de qualquer ação destrutiva
