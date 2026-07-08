#!/usr/bin/env python3
"""Hook PreToolUse do Claude Code: lembra o modelo de consultar o structure-cache
ANTES de grepar/ler código, quando o projeto tem cache. Não bloqueia o Grep/Glob
(permissionDecision=allow) e não prompta o usuário — só injeta um lembrete.

Guardado por cache: se não há `thoughts/cache/structure/index.json` sob o git root
do cwd, sai 0 sem output (fluxo normal, custo zero). Assim é seguro global.

Registrado em settings.json:
  hooks.PreToolUse[].matcher = "Grep|Glob"  → hooks[].command = este script
"""
import json
import subprocess
import sys
from pathlib import Path

NUDGE = (
    "[structure-cache] Este projeto tem um cache de estrutura. Para perguntas de "
    "DEPENDÊNCIA/IMPACTO (quem importa X, o que Y importa, quem define algo, módulos "
    "mais acoplados), rode `structure-cache query --importers/--imports/--defs/--hotspots` "
    "ANTES de grepar/ler o código — é mais rápido e preciso. Se vier vazio/stale, "
    "`structure-cache build` (incremental automático) e reconsulte. Para busca textual "
    "geral (strings, TODOs, etc.), o Grep segue sendo o certo."
)


def _git_root(cwd: str) -> Path:
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, ValueError):
        pass
    return Path(cwd)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    cwd = payload.get("cwd") or "."
    cache = _git_root(cwd) / "thoughts" / "cache" / "structure" / "index.json"
    if not cache.is_file():
        return 0
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": NUDGE,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
