# Reference: symlink de auto-memory entre worktree e root

Protocolo completo de gestão do symlink de auto-memory usado por `/git-worktree` (criação) e `/git-remove-worktree` (remoção). Objetivo: centralizar a memória no root via symlink, pra que o `MEMORY.md` carregado pelo harness na sessão do worktree seja o do **root** (e não um novo vazio).

**Por que**: sem o symlink, o harness cria `memory/` vazio no path encoded do worktree, e o `MEMORY.md` carregado no system prompt não inclui notas salvas trabalhando no root (ou em outros worktrees do mesmo projeto). Symlink centraliza.

## Resolução dos paths

```bash
WORKTREE_ENC=$(echo "$WORKTREE_DIR" | sed 's|/|-|g')
ROOT_ENC=$(echo "$REPO_ROOT" | sed 's|/|-|g')
WORKTREE_MEM="$HOME/.claude/projects/$WORKTREE_ENC/memory"
ROOT_MEM="$HOME/.claude/projects/$ROOT_ENC/memory"
```

## Na criação da worktree (/git-worktree)

Antes de tratar os casos, garantir que os diretórios base existem:

```bash
mkdir -p "$ROOT_MEM"
mkdir -p "$HOME/.claude/projects/$WORKTREE_ENC"
```

Casos a tratar:

- **Já é symlink pro root** (`readlink "$WORKTREE_MEM"` = `$ROOT_MEM`) → skip (idempotente).
- **É symlink pra outro destino** → mostre o destino atual, pergunte antes de substituir. Se confirmar, `unlink` e recrie.
- **É diretorio real** (provável: harness criou em sessão anterior do worktree) → **NÃO substitua sozinho**. Avise: *"`$WORKTREE_MEM` existe como diretorio real. Rode `/memory-organize relink` pra migrar com seguranca (checa notas unicas antes de descartar)."* Continue o resto do fluxo do worktree.
- **Não existe** → `ln -s "$ROOT_MEM" "$WORKTREE_MEM"`. Reporte: *"Auto-memory centralizado: symlink criado pro root."*

## Na remoção (/git-remove-worktree)

Antes de remover a worktree do git, limpe o symlink de auto-memory criado por `/git-worktree`. **Crucial**: use `unlink` (ou `rm` sem `-r`) pra remover apenas o symlink. **Nunca** `rm -rf` — seguir o symlink apagaria o `memory/` do root.

Casos a tratar:

- **É symlink pro root** (caso normal, criado por `/git-worktree`): `unlink "$WORKTREE_MEM"`. Reporte: *"Symlink de auto-memory removido."*
- **É symlink pra outro destino**: mostre `readlink "$WORKTREE_MEM"`. Pergunte antes de remover. Confirmacao → `unlink`.
- **É diretorio real** (raro: harness criou antes do relink, ou symlink foi sobrescrito): liste conteudo. Pergunte:
  - `(m)` Mover notas pro root antes de descartar
  - `(d)` Descartar (assume que ja tem copia no root)
  - `(c)` Cancelar a remocao do worktree
- **Não existe**: skip silenciosamente.

**Importante**: **NÃO remova o diretorio pai inteiro** `~/.claude/projects/<worktree-encoded>/`. O harness guarda historico de sessoes e outros artefatos la — perda silenciosa. User limpa manualmente se quiser.
