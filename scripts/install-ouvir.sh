#!/usr/bin/env bash
#
# install-ouvir.sh — instala o comando `ouvir` + TTS local (piper, voz pt-BR), sem sudo.
#
# Tudo vai pra ~/.local (binário, modelo e o próprio script). Não toca em diretórios
# de sistema e não precisa de root. Idempotente: pula o que já existe.
#
# Uso:
#   ./install-ouvir.sh            # instala ouvir + piper + modelo pt_BR-faber-medium
#   OUVIR_MODEL=pt_BR-edresson-low ./install-ouvir.sh   # outro modelo (ver piper-voices)
#   ./install-ouvir.sh --skip-tts # só instala o script (você cuida do TTS)
#
set -euo pipefail

PIPER_VERSION="2023.11.14-2"
MODEL="${OUVIR_MODEL:-pt_BR-faber-medium}"          # <lang>_<REGION>-<voz>-<qualidade>
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
PIPER_DIR="$HOME/.local/share/piper-bin"
MODEL_DIR="$HOME/.local/share/piper"

say() { printf '\033[1;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$1" >&2; }

mkdir -p "$BIN_DIR" "$PIPER_DIR" "$MODEL_DIR"

# 1. O script `ouvir`
say "Instalando o comando 'ouvir' em $BIN_DIR/ouvir"
install -m 0755 "$SCRIPT_DIR/ouvir" "$BIN_DIR/ouvir"

if [ "${1:-}" = "--skip-tts" ]; then
  say "TTS pulado (--skip-tts). Instale piper ou 'sudo apt install espeak-ng' depois."
else
  # 2. Binário do piper (por arquitetura)
  arch="$(uname -m)"
  case "$arch" in
    x86_64)  asset="piper_linux_x86_64.tar.gz" ;;
    aarch64) asset="piper_linux_aarch64.tar.gz" ;;
    armv7l)  asset="piper_linux_armv7l.tar.gz" ;;
    *) warn "Arquitetura '$arch' sem binário piper pré-compilado conhecido."
       warn "Use o fallback espeak-ng (sudo apt install espeak-ng) ou compile o piper."
       asset="" ;;
  esac

  if [ -n "$asset" ] && [ ! -x "$PIPER_DIR/piper/piper" ]; then
    say "Baixando piper ($asset)"
    url="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/${asset}"
    curl -fsSL -o /tmp/piper.tar.gz "$url"
    tar -xzf /tmp/piper.tar.gz -C "$PIPER_DIR"
    rm -f /tmp/piper.tar.gz
  elif [ -x "$PIPER_DIR/piper/piper" ]; then
    say "piper já instalado, pulando download"
  fi

  # wrapper no PATH (garante que o binário rode do diretório dele, com as libs ao lado)
  if [ -x "$PIPER_DIR/piper/piper" ]; then
    cat > "$BIN_DIR/piper" <<'EOF'
#!/bin/sh
exec "$HOME/.local/share/piper-bin/piper/piper" "$@"
EOF
    chmod +x "$BIN_DIR/piper"
  fi

  # 3. Modelo de voz pt-BR (.onnx + .onnx.json)
  if [ ! -f "$MODEL_DIR/$MODEL.onnx" ]; then
    # caminho no HuggingFace: pt/pt_BR/<voz>/<qualidade>/<modelo>
    region="${MODEL%%-*}"                 # pt_BR
    lang="${region%%_*}"                  # pt
    rest="${MODEL#*-}"; voice="${rest%-*}"; quality="${rest#*-}"
    base="https://huggingface.co/rhasspy/piper-voices/resolve/main/${lang}/${region}/${voice}/${quality}"
    say "Baixando modelo de voz $MODEL (~60MB)"
    curl -fsSL -o "$MODEL_DIR/$MODEL.onnx"      "$base/$MODEL.onnx"
    curl -fsSL -o "$MODEL_DIR/$MODEL.onnx.json" "$base/$MODEL.onnx.json"
  else
    say "Modelo $MODEL já presente, pulando download"
  fi
fi

# 4. PATH
case ":$PATH:" in
  *":$BIN_DIR:"*) say "PATH já inclui $BIN_DIR" ;;
  *)
    warn "$BIN_DIR não está no seu PATH."
    warn "Adicione ao seu ~/.zshrc ou ~/.bashrc:"
    warn '  export PATH="$HOME/.local/bin:$PATH"'
    ;;
esac

say "Pronto. Dentro de um projeto com sessão do Claude Code, rode:  ouvir"
say "Pra ver o texto sem tocar áudio:  ouvir --text-only"
