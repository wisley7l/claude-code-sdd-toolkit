#!/usr/bin/env bash
#
# install-structure-cache.sh — põe o `structure-cache` (+ atalho `sc`) no PATH.
#
# Cria wrappers finos em ~/.local/bin que chamam o motor build.py DESTE repo
# (o repo segue sendo a fonte — editou aqui, o comando reflete na hora). Sem sudo,
# idempotente. Os git hooks opt-in (post-commit/checkout) ficam no install-hooks.sh.
#
# Uso:
#   ./install-structure-cache.sh          # instala structure-cache + sc
#   ./install-structure-cache.sh --no-sc  # só o `structure-cache` (pula o atalho)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"          # .../scripts
BUILD="$SCRIPT_DIR/structure-cache/build.py"
BIN_DIR="$HOME/.local/bin"

say() { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$1" >&2; }

[ -f "$BUILD" ] || { warn "não achei $BUILD"; exit 1; }
mkdir -p "$BIN_DIR"

say "Instalando 'structure-cache' em $BIN_DIR/structure-cache (wrapper → $BUILD)"
cat > "$BIN_DIR/structure-cache" <<EOF
#!/bin/sh
# wrapper gerado por install-structure-cache.sh — aponta pro motor no repo
exec python3 "$BUILD" "\$@"
EOF
chmod +x "$BIN_DIR/structure-cache"

if [ "${1:-}" = "--no-sc" ]; then
  say "Atalho 'sc' pulado (--no-sc)."
elif command -v sc >/dev/null 2>&1 && [ ! -L "$BIN_DIR/sc" ]; then
  warn "'sc' já existe no PATH ($(command -v sc)) e não é nosso symlink — não criei o atalho."
  warn "Use 'structure-cache' (ou rode com --no-sc pra silenciar este aviso)."
else
  ln -sf structure-cache "$BIN_DIR/sc"
  say "Atalho 'sc' → structure-cache criado."
fi

case ":$PATH:" in
  *":$BIN_DIR:"*) say "PATH já inclui $BIN_DIR" ;;
  *)
    warn "$BIN_DIR não está no seu PATH. Adicione ao ~/.zshrc ou ~/.bashrc:"
    warn '  export PATH="$HOME/.local/bin:$PATH"'
    ;;
esac

say "Pronto. Teste:  structure-cache help   (ou:  sc help)"
