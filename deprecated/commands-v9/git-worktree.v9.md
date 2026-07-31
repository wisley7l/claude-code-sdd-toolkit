---
description: Cria uma git worktree a partir da branch default e, por default, ativa MODO LIVRE nela (a sessão nova aberta na worktree já nasce autônoma — sem rodar /modo-livre on nem reload). `--ml-off` cria a worktree sem modo-livre. Trabalho paralelo em múltiplas branches.
model: claude-haiku-4-5-20251001
argument-hint: <nome-da-branch> [--ml-off]
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# Git Worktree Creator

Cria uma worktree isolada a partir da **branch default** do repositório, permitindo trabalho paralelo em múltiplas features.

## Argumentos

- `$ARGUMENTS` — Nome da nova branch (obrigatório). Será usado como nome da branch e do diretório.
- `--ml-off` — (opcional) NÃO ativa o modo-livre na worktree. Sem essa flag, o modo-livre é ativado por default (ver Passo 9).

## Fluxo de Execução

### Passo 1 — Validar Argumentos

Separe a flag `--ml-off` do restante: `MODO_LIVRE=on` por default; se `--ml-off` aparecer em `$ARGUMENTS`, `MODO_LIVRE=off` e **remova a flag** antes de usar o resto como nome da branch.

O que sobrar de `$ARGUMENTS` é o nome da branch. Se estiver vazio, pergunte ao usuário usando AskUserQuestion.

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

```bash
WORKTREE_MEM="$HOME/.claude/projects/$(echo "$WORKTREE_DIR" | sed 's|/|-|g')/memory"
ROOT_MEM="$HOME/.claude/projects/$(echo "$REPO_ROOT" | sed 's|/|-|g')/memory"
mkdir -p "$ROOT_MEM" "$(dirname "$WORKTREE_MEM")"
```

Objetivo: centralizar a memoria no root via symlink, pra que o `MEMORY.md` carregado na sessao do worktree seja o do root.

Protocolo completo (casos symlink válido/quebrado/diretório real/não existe) no reference `memoria-symlink.md` — procure em `.claude/sdd-references/` do projeto, senao em `~/.claude/sdd-references/`. **Fallback** (reference ausente): garanta que `~/.claude/projects/<worktree-encoded>/memory` seja symlink pro `memory/` do root; na remoção, desfaça o symlink (unlink) sem apagar o destino.

### Passo 8 — Verificar .gitignore

Garantir que `.worktrees/` está no `.gitignore` da raiz. Se não estiver, adicionar.

### Passo 9 — Ativar MODO LIVRE na worktree (default; pula se `--ml-off`)

Se `MODO_LIVRE=off` (flag `--ml-off` foi passada): pule este passo e registre no reporte "modo-livre: não ativado (--ml-off)".

Se `MODO_LIVRE=on` (default): aplique o protocolo **ATIVAR** do `/modo-livre` **apontando pra worktree recém-criada** (`$WORKTREE_DIR`), NÃO pro root. A sessão que o usuário abrir com `cd $WORKTREE_DIR && claude` é nova — o harness lê o settings ao iniciar, então **não há reload a fazer**.

**1. Ler o JSON canônico de permissões** (fonte única — nunca reconstruir de memória):
   - Procure o reference `modo-livre-settings.json` em `$REPO_ROOT/.claude/sdd-references/`, senão em `~/.claude/sdd-references/`.
   - **Se o reference NÃO existir**: NÃO invente nem improvise o JSON (é segurança). Pule a ativação, deixe a worktree criada e avise no reporte: "modo-livre NÃO ativado — reference `modo-livre-settings.json` ausente. Rode `/modo-livre on` dentro da worktree ou instale o reference." Siga pro Passo 10.

**2. Backup (raro numa worktree nova)**: se `$WORKTREE_DIR/.claude/settings.local.json` já existir (settings commitado na branch default), copie pra `$WORKTREE_DIR/thoughts/modo-livre/settings.local.json.bak` antes de sobrescrever. Se não existir, sem backup.

**3. Escrever settings + marker na worktree**:
   ```bash
   mkdir -p "$WORKTREE_DIR/.claude" "$WORKTREE_DIR/thoughts/modo-livre"
   ```
   - Escreva o conteúdo **integral** do reference em `$WORKTREE_DIR/.claude/settings.local.json` (cópia fiel, sem editar).
   - Crie o marker:
     ```bash
     date -Iseconds > "$WORKTREE_DIR/thoughts/modo-livre/active"
     ```

Observações: `thoughts/` é gitignored por convenção (marker/backup não poluem o repo). O `.claude/settings.local.json` da worktree pode aparecer no `git status` da branch — o usuário decide se ignora. **Não** ative modo-livre no root — só na worktree.

### Passo 10 — Reportar ao Usuário

Após criação, informar:
- Caminho da worktree (absoluto)
- Nome da branch
- Baseada em qual branch default + commit
- **Modo-livre**: `<ativado (a sessão na worktree já nasce autônoma) | não ativado (--ml-off) | não ativado (reference ausente)>`
- Como navegar: `cd <caminho>`
- Como abrir nova sessão Claude Code: `cd <caminho> && claude` — se modo-livre ativado, já vale nessa sessão (sem reload)
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
