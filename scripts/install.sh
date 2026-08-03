#!/usr/bin/env bash
#
# install.sh — instala tudo que o toolkit precisa fora do plugin.
#
# O plugin em si (as skills) você instala pelo Claude Code. Este script cuida do resto:
# os comandos que as skills chamam por Bash, e as permissões que evitam um prompt a cada uso.
#
#   1. `roadmap`         — motor do vault de roadmap        (skill roadmap, plan, pr-draft, pr-close)
#   2. `memory-audit`    — diagnóstico do auto-memory       (skill memory)
#   3. `structure-cache` — índice de estrutura + atalho `sc` (skill plan, code-review, pr-audit)
#   4. pré-autorização desses comandos no settings.json
#
# Sem sudo, idempotente, e nunca sobrescreve binário que não seja nosso.
#
# Uso:
#   ./install.sh                 # instala e pergunta antes de mexer no settings.json
#   ./install.sh --check         # só relata o que está instalado, não altera nada
#   ./install.sh --yes           # não pergunta (para uso não-interativo)
#   ./install.sh --no-perms      # instala os comandos e não toca no settings.json
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
CHECK_ONLY=0; ASSUME_YES=0; SKIP_PERMS=0

for arg in "$@"; do
  case "$arg" in
    --check)    CHECK_ONLY=1 ;;
    --yes|-y)   ASSUME_YES=1 ;;
    --no-perms) SKIP_PERMS=1 ;;
    --help|-h)  sed -n '2,20p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) printf 'argumento desconhecido: %s (use --help)\n' "$arg" >&2; exit 2 ;;
  esac
done

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
say()  { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
ok()   { printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[1;33m!\033[0m %s\n' "$1" >&2; }
bad()  { printf '  \033[1;31m✗\033[0m %s\n' "$1" >&2; }

# ---------------------------------------------------------------- pré-requisitos

bold "claude-code-sdd-toolkit — instalação"
echo

say "Pré-requisitos"
missing=0
for cmd in python3 git; do
  if command -v "$cmd" >/dev/null 2>&1; then ok "$cmd"; else bad "$cmd — obrigatório"; missing=1; fi
done
command -v gh >/dev/null 2>&1 && ok "gh (GitHub CLI)" \
  || warn "gh ausente — pr-draft, pr-ready, pr-close e pr-audit dependem dele"
[ "$missing" -eq 0 ] || { echo; bad "instale o que falta e rode de novo"; exit 1; }
echo

# ---------------------------------------------------------------- comandos

# nosso = wrapper que criamos em ~/.local/bin. Qualquer outro binário de mesmo nome
# no PATH é de terceiro e não se toca.
install_one() {
  local name="$1" installer="$2" desc="$3"
  local existing; existing="$(command -v "$name" 2>/dev/null || true)"

  if [ -n "$existing" ] && [ "$existing" != "$BIN_DIR/$name" ]; then
    warn "$name: já existe em $existing e não é nosso — pulando ($desc)"
    return 0
  fi
  if [ "$CHECK_ONLY" -eq 1 ]; then
    [ -n "$existing" ] && ok "$name — instalado" || warn "$name — ausente ($desc)"
    return 0
  fi
  if bash "$SCRIPT_DIR/$installer" >/dev/null 2>&1; then
    ok "$name — $([ -n "$existing" ] && echo 'atualizado' || echo 'instalado')"
  else
    bad "$name — o installer falhou; rode ./scripts/$installer pra ver o erro"
  fi
}

say "Comandos"
install_one roadmap         install-roadmap.sh        "vault de roadmap"
install_one memory-audit    install-memory-audit.sh   "diagnóstico da memória"
install_one structure-cache install-structure-cache.sh "índice de estrutura"
echo

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) warn "$BIN_DIR não está no PATH — os comandos não vão ser encontrados."
     warn 'adicione no ~/.zshrc:  export PATH="$HOME/.local/bin:$PATH"'
     echo ;;
esac

# ---------------------------------------------------------------- permissões

# Respeita CLAUDE_CONFIG_DIR: quem usa mais de uma config precisa das permissões
# na config ativa, não numa qualquer.
CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SETTINGS="$CONFIG_DIR/settings.json"
PERMS='Bash(roadmap:*) Bash(memory-audit:*) Bash(structure-cache:*) Bash(sc:*)'

if [ "$SKIP_PERMS" -eq 1 ]; then
  say "Permissões — puladas (--no-perms)"
elif [ "$CHECK_ONLY" -eq 1 ]; then
  say "Permissões em $SETTINGS"
  for p in $PERMS; do
    grep -qF "$p" "$SETTINGS" 2>/dev/null && ok "$p" || warn "$p — ausente"
  done
else
  say "Permissões em $SETTINGS"
  echo "  Sem isso, cada chamada desses comandos pede confirmação."
  echo "  Vou adicionar em permissions.allow (backup antes, entradas existentes preservadas):"
  for p in $PERMS; do echo "      $p"; done
  echo

  reply=s
  if [ "$ASSUME_YES" -eq 0 ]; then
    printf '  Aplicar? [s/N] '
    read -r reply </dev/tty || reply=n
  fi

  case "$reply" in
    s|S|y|Y)
      mkdir -p "$CONFIG_DIR"
      [ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak-$(date +%Y%m%d%H%M%S)"
      SETTINGS="$SETTINGS" PERMS="$PERMS" python3 - <<'PY'
import json, os, pathlib
path = pathlib.Path(os.environ["SETTINGS"])
try:
    data = json.loads(path.read_text()) if path.is_file() and path.read_text().strip() else {}
except json.JSONDecodeError:
    raise SystemExit(f"  ✗ {path} não é JSON válido — corrija à mão; nada foi alterado")
allow = data.setdefault("permissions", {}).setdefault("allow", [])
added = [p for p in os.environ["PERMS"].split() if p not in allow]
allow.extend(added)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(f"  ✓ {len(added)} adicionada(s), {len(allow) - len(added)} já existiam")
PY
      ;;
    *) warn "pulado — adicione à mão em permissions.allow quando quiser" ;;
  esac
fi
echo

# ---------------------------------------------------------------- o que falta

say "O que este script NÃO faz"
cat <<EOF
  • O plugin com as skills. No Claude Code:
        claude --plugin-dir $(cd "$SCRIPT_DIR/.." && pwd)      # só esta sessão
        ln -s $(cd "$SCRIPT_DIR/.." && pwd) ~/.claude/skills/tk7   # permanente (já clonado)
  • O code-simplifier (opcional, usado pelo implement depois do verde):
        /plugin install code-simplifier@claude-plugins-official
  • gh auth login, se o gh ainda não estiver autenticado.
EOF
echo
[ "$CHECK_ONLY" -eq 1 ] && bold "Verificação concluída." || bold "Pronto. Teste com: roadmap status"
