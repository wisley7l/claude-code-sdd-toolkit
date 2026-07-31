#!/usr/bin/env bash
#
# install-memory-audit.sh — põe o `memory-audit` no PATH.
#
# Cria um wrapper fino em ~/.local/bin que chama o motor audit.py DESTE repo
# (o repo segue sendo a fonte — editou aqui, o comando reflete na hora). Sem sudo,
# idempotente. O comando é SOMENTE LEITURA: nunca escreve, move ou apaga memória.
#
# Uso:
#   ./install-memory-audit.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"          # .../scripts
ENGINE="$SCRIPT_DIR/memory/audit.py"
BIN_DIR="$HOME/.local/bin"

say() { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$1" >&2; }

[ -f "$ENGINE" ] || { warn "não achei $ENGINE"; exit 1; }
command -v python3 >/dev/null 2>&1 || { warn "python3 não está no PATH"; exit 1; }
mkdir -p "$BIN_DIR"

if command -v memory-audit >/dev/null 2>&1 && [ ! -f "$BIN_DIR/memory-audit" ]; then
  warn "já existe um 'memory-audit' no PATH ($(command -v memory-audit)) que não é nosso."
  warn "renomeie o outro, ou chame o motor direto: python3 $ENGINE"
  exit 1
fi

say "Instalando 'memory-audit' em $BIN_DIR/memory-audit (wrapper → $ENGINE)"
cat > "$BIN_DIR/memory-audit" <<EOF
#!/bin/sh
# wrapper gerado por install-memory-audit.sh — aponta pro motor no repo
exec python3 "$ENGINE" "\$@"
EOF
chmod +x "$BIN_DIR/memory-audit"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) warn "$BIN_DIR não está no seu PATH — adicione no ~/.zshrc:"
     warn '  export PATH="$HOME/.local/bin:$PATH"' ;;
esac

say "Pronto. Teste com: memory-audit"
say "Pra pré-autorizar sem prompt, adicione em ~/.claude/settings.json:"
printf '      "Bash(memory-audit:*)"\n'
