#!/usr/bin/env bash
#
# install-roadmap.sh — põe o `roadmap` no PATH.
#
# Cria um wrapper fino em ~/.local/bin que chama o motor roadmap.py DESTE repo
# (o repo segue sendo a fonte — editou aqui, o comando reflete na hora). Sem sudo,
# idempotente.
#
# Uso:
#   ./install-roadmap.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"          # .../scripts
ENGINE="$SCRIPT_DIR/roadmap/roadmap.py"
BIN_DIR="$HOME/.local/bin"

say() { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$1" >&2; }

[ -f "$ENGINE" ] || { warn "não achei $ENGINE"; exit 1; }
command -v python3 >/dev/null 2>&1 || { warn "python3 não está no PATH"; exit 1; }
mkdir -p "$BIN_DIR"

if command -v roadmap >/dev/null 2>&1 && [ ! -f "$BIN_DIR/roadmap" ]; then
  warn "já existe um 'roadmap' no PATH ($(command -v roadmap)) que não é nosso — não vou sobrescrever."
  warn "renomeie o outro, ou chame o motor direto: python3 $ENGINE"
  exit 1
fi

say "Instalando 'roadmap' em $BIN_DIR/roadmap (wrapper → $ENGINE)"
cat > "$BIN_DIR/roadmap" <<EOF
#!/bin/sh
# wrapper gerado por install-roadmap.sh — aponta pro motor no repo
exec python3 "$ENGINE" "\$@"
EOF
chmod +x "$BIN_DIR/roadmap"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) warn "$BIN_DIR não está no seu PATH — adicione no ~/.zshrc:"
     warn '  export PATH="$HOME/.local/bin:$PATH"' ;;
esac

say "Pronto. Teste com: roadmap status"
say "Pro board no navegador (por projeto): roadmap board -a"
say "Pra pré-autorizar sem prompt, adicione em ~/.claude/settings.json:"
printf '      "Bash(roadmap:*)"\n'
