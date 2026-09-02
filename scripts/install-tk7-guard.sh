#!/usr/bin/env bash
#
# install-tk7-guard.sh — põe o `tk7-guard` no PATH.
#
# Cria um wrapper fino em ~/.local/bin que chama o guard DESTE repo (o repo segue
# sendo a fonte — editou aqui, o hook reflete na hora). Sem sudo, idempotente.
#
# O guard é um hook PreToolUse: sozinho no PATH ele não protege nada. Quem o liga
# é o settings — a worktree nasce com ele (skills/worktree/permissions.json), e pro
# global a linha está no fim da saída.
#
# Uso:
#   ./install-tk7-guard.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"          # .../scripts
ENGINE="$SCRIPT_DIR/tk7-guard"
BIN_DIR="$HOME/.local/bin"

say() { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$1" >&2; }

[ -f "$ENGINE" ] || { warn "não achei $ENGINE"; exit 1; }
command -v python3 >/dev/null 2>&1 || { warn "python3 não está no PATH"; exit 1; }
mkdir -p "$BIN_DIR"

if command -v tk7-guard >/dev/null 2>&1 && [ ! -f "$BIN_DIR/tk7-guard" ]; then
  warn "já existe um 'tk7-guard' no PATH ($(command -v tk7-guard)) que não é nosso — não vou sobrescrever."
  exit 1
fi

say "Instalando 'tk7-guard' em $BIN_DIR/tk7-guard (wrapper → $ENGINE)"
cat > "$BIN_DIR/tk7-guard" <<EOF
#!/bin/sh
# wrapper gerado por install-tk7-guard.sh — aponta pro guard no repo
exec python3 "$ENGINE" "\$@"
EOF
chmod +x "$BIN_DIR/tk7-guard"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) warn "$BIN_DIR não está no seu PATH — adicione no ~/.zshrc:"
     warn '  export PATH="$HOME/.local/bin:$PATH"' ;;
esac

say "Pronto. Teste com: python3 $SCRIPT_DIR/tk7-guard.test.py"
say "Pra valer em TODOS os projetos, e não só nas worktrees, ligue em ~/.claude/settings.json:"
cat <<'EOF'
      "hooks": {
        "PreToolUse": [
          { "matcher": "Bash", "hooks": [{ "type": "command", "command": "tk7-guard" }] }
        ]
      }
EOF
