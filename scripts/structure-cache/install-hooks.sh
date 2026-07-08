#!/usr/bin/env sh
# Instala (ou remove) os git hooks opt-in do structure-cache que mantêm o cache
# MORNO: após cada commit/checkout, dispara um build incremental DESTACADO.
#
# Worktree-safe por construção: os hooks vivem no hooks-dir COMUM
# (git rev-parse --git-common-dir), compartilhado por todos os worktrees, então
# instala UMA vez e vale pra todos. O hook roda com cwd = o worktree que disparou,
# e `structure-cache build` auto-detecta esse worktree via git — cada um atualiza
# só o próprio cache.
#
# Garantias: NUNCA bloqueia o commit/checkout (processo destacado, saída
# descartada); idempotente (marcadores); reversível (--uninstall).
#
# Uso:
#   ./install-hooks.sh              # instala post-commit e post-checkout
#   ./install-hooks.sh --uninstall  # remove só o bloco do structure-cache
set -eu

MARK_START="# structure-cache-hook-start"
MARK_END="# structure-cache-hook-end"

if ! command -v git >/dev/null 2>&1; then
  echo "structure-cache: git não encontrado" >&2
  exit 1
fi
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "structure-cache: rode de dentro de um repo git" >&2
  exit 1
fi

# hooks-dir COMUM (compartilhado entre worktrees). Respeita core.hooksPath se setado.
HOOKS_PATH="$(git config --get core.hooksPath || true)"
if [ -n "$HOOKS_PATH" ]; then
  HOOKS_DIR="$HOOKS_PATH"
else
  HOOKS_DIR="$(git rev-parse --git-common-dir)/hooks"
fi
mkdir -p "$HOOKS_DIR"

# path absoluto do build.py, cravado no hook (funciona mesmo sem PATH configurado).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_PY="$SCRIPT_DIR/build.py"

strip_block() {
  # remove o bloco marcado de um arquivo de hook, se existir
  target="$1"
  [ -f "$target" ] || return 0
  awk -v s="$MARK_START" -v e="$MARK_END" '
    $0 ~ s {skip=1; next}
    $0 ~ e {skip=0; next}
    !skip {print}
  ' "$target" > "$target.tmp"
  mv "$target.tmp" "$target"
  chmod +x "$target" 2>/dev/null || true
}

install_hook() {
  target="$HOOKS_DIR/$1"
  strip_block "$target"                       # evita duplicar em reinstalação
  if [ ! -f "$target" ]; then
    printf '#!/bin/sh\n' > "$target"
  fi
  {
    echo "$MARK_START"
    echo 'if command -v structure-cache >/dev/null 2>&1; then _sc="structure-cache";'
    echo "else _sc=\"python3 $BUILD_PY\"; fi"
    echo '# destacado: nunca bloqueia o git; saída descartada'
    echo 'if command -v setsid >/dev/null 2>&1; then'
    echo '  ( setsid $_sc build >/dev/null 2>&1 & ) >/dev/null 2>&1 || true'
    echo 'else'
    echo '  ( nohup $_sc build >/dev/null 2>&1 & ) >/dev/null 2>&1 || true'
    echo 'fi'
    echo "$MARK_END"
  } >> "$target"
  chmod +x "$target"
  echo "  ✓ $1"
}

if [ "${1:-}" = "--uninstall" ]; then
  echo "structure-cache: removendo hooks de $HOOKS_DIR"
  strip_block "$HOOKS_DIR/post-commit"
  strip_block "$HOOKS_DIR/post-checkout"
  echo "  ✓ removido (bloco structure-cache). Outros hooks preservados."
  exit 0
fi

echo "structure-cache: instalando hooks em $HOOKS_DIR (compartilhado entre worktrees)"
install_hook post-commit
install_hook post-checkout
echo "Pronto. O cache é mantido morno após commit/checkout (build incremental destacado)."
echo "Correção ainda vem do 'structure-cache check'/'query' (revalida por hash — pega rebase/stash)."
