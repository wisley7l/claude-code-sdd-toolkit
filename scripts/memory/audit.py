#!/usr/bin/env python3
"""memory-audit — diagnóstico do auto-memory de um projeto. Determinístico, sem LLM.

Responde três perguntas que não dá pra responder de olho:

1. **Estou lendo a memória certa?** O diretório vem de `CLAUDE_CONFIG_DIR` (ou `~/.claude`),
   e quem usa mais de uma config acumula memória do MESMO projeto em lugares diferentes —
   sem nunca ver as outras. Fragmentação é a primeira coisa reportada.
2. **O índice cabe?** Só o `MEMORY.md` carrega, e só até 200 linhas / 25KB. O que passa
   disso é silenciosamente descartado. Frontmatter e comentários HTML não contam (o harness
   os remove antes de carregar).
3. **As notas são alcançáveis?** Nota que não é citada no índice nem num sub-sumário só é
   lida se alguém adivinhar o nome. Escrever é barato; ser encontrado é o que importa.

Leitura por default. A única escrita possível é `migrate --apply`, que renomeia notas de
tipo aposentado e reescreve os links que apontavam pra elas — com backup, e nunca apagando.

Uso:
  memory-audit [--root <dir>] [--json] [--all-configs]
  memory-audit migrate [--apply]     # v9 → v10: blocker→bug, preference→decision
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

LIMIT_LINES = 200
LIMIT_BYTES = 25 * 1024
INDEX = "MEMORY.md"

# Tipos que o v10 oferece. `blocker` e `preference` seguem legíveis (dado existente),
# mas convergiram: blocker → bug, preference → decision. `idea` foi aposentado sem uso.
TYPES_ACTIVE = {"user", "feedback", "project", "reference", "decision", "lesson", "bug", "win"}
TYPES_RETIRED = {"blocker": "bug", "preference": "decision", "idea": None}

_FM_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_LINK_RE = re.compile(r"\]\(\.?/?([^)]+\.md)\)")


def git_root() -> Path | None:
    try:
        out = subprocess.run(["git", "worktree", "list"], capture_output=True,
                             text=True, check=True).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    lines = [l for l in out if l.strip()]
    bare = next((l for l in lines if l.rstrip().endswith("(bare)")), None)
    trees = [Path(l.split()[0]).resolve() for l in lines if l is not bare]
    if bare and not trees:
        return Path(bare.split()[0]).resolve().parent
    if bare:
        anchor = Path(bare.split()[0]).resolve().parent
        return anchor if any(anchor in t.parents or anchor == t for t in trees) else trees[0]
    return trees[0] if trees else None


def encoded(root: Path) -> str:
    """O harness deriva o nome do diretório do path do repo, com `/` virando `-`."""
    return str(root).replace("/", "-")


def find_memory_dirs(root: Path) -> list[Path]:
    """Todos os candidatos que existem, em qualquer config — é assim que a fragmentação aparece."""
    enc = encoded(root)
    found: list[Path] = []
    active = os.environ.get("CLAUDE_CONFIG_DIR")
    if active:
        p = Path(active) / "projects" / enc / "memory"
        if p.is_dir():
            found.append(p)
    for cfg in sorted(Path.home().glob(".claude*")):
        p = cfg / "projects" / enc / "memory"
        if p.is_dir() and p not in found:
            found.append(p)
    return found


def loaded_size(path: Path) -> tuple[int, int]:
    """O que o harness realmente carrega: sem frontmatter, sem comentário HTML."""
    if not path.is_file():
        return 0, 0
    text = path.read_text(encoding="utf-8", errors="replace")
    text = _FM_RE.sub("", text)
    text = _HTML_COMMENT_RE.sub("", text)
    return len(text.splitlines()), len(text.encode("utf-8"))


_TYPE_RE = re.compile(r"^\s*type:\s*(\S+)\s*$", re.M)


def note_type(mem: Path, name: str) -> str:
    """`metadata.type` manda; o prefixo do nome é só fallback.

    As duas convenções convivem: o v9 codificava o tipo no nome (`feedback_x.md`), e nota
    escrita direto pelo harness costuma vir sem prefixo. Ler o frontmatter evita contar
    como "sem tipo" uma nota perfeitamente tipada.
    """
    fm = _FM_RE.match((mem / name).read_text(encoding="utf-8", errors="replace"))
    if fm:
        hit = _TYPE_RE.search(fm.group(0))
        if hit:
            return hit.group(1)
    return name.split("_", 1)[0] if "_" in name else "(sem tipo)"


def audit(mem: Path) -> dict:
    index = mem / INDEX
    notes = sorted(p.name for p in mem.glob("*.md")
                   if p.name != INDEX and not p.name.startswith("_summary"))
    summaries = sorted(p.name for p in mem.glob("_summary*.md"))

    idx_text = index.read_text(encoding="utf-8", errors="replace") if index.is_file() else ""
    sum_text = "\n".join((mem / s).read_text(encoding="utf-8", errors="replace") for s in summaries)
    linked_index = set(_LINK_RE.findall(idx_text))
    linked_sum = set(_LINK_RE.findall(sum_text))

    direct = [n for n in notes if n in linked_index]
    via_sum = [n for n in notes if n not in linked_index and n in linked_sum]
    orphan = [n for n in notes if n not in linked_index and n not in linked_sum]

    by_type: dict[str, int] = {}
    mismatched = []
    for n in notes:
        t = note_type(mem, n)
        by_type[t] = by_type.get(t, 0) + 1
        prefix = n.split("_", 1)[0] if "_" in n else None
        if prefix and prefix != t and (prefix in TYPES_ACTIVE or prefix in TYPES_RETIRED):
            mismatched.append({"nota": n, "nome_diz": prefix, "frontmatter_diz": t})

    retired = {t: c for t, c in by_type.items() if t in TYPES_RETIRED}
    unknown = {t: c for t, c in by_type.items()
               if t not in TYPES_ACTIVE and t not in TYPES_RETIRED}

    # Symlink quebrado é resíduo de relink antigo: atrapalha cópia e backup, e ninguém vê.
    broken = sorted(x.name for x in mem.iterdir() if x.is_symlink() and not x.exists())

    lines, size = loaded_size(index)
    # Linha de índice que cita um arquivo mas não diz nada além do nome: sem gancho, o
    # arquivo nunca vai ser aberto — a linha ocupa espaço e não recupera nada.
    weak = []
    for raw in idx_text.splitlines():
        if ".md)" not in raw:
            continue
        prose = _LINK_RE.sub("", raw)
        prose = re.sub(r"[|\-*\[\]`#>·—]", " ", prose).strip()
        if len(prose) < 25:
            weak.append(raw.strip()[:100])

    return {
        "dir": str(mem),
        "indice": {
            "existe": index.is_file(),
            "linhas_carregadas": lines,
            "bytes_carregados": size,
            "limite_linhas": LIMIT_LINES,
            "limite_bytes": LIMIT_BYTES,
            "estourou": lines > LIMIT_LINES or size > LIMIT_BYTES,
            "perto_do_limite": lines > LIMIT_LINES * 0.85 or size > LIMIT_BYTES * 0.85,
            "linhas_sem_gancho": weak,
        },
        "notas": {
            "total": len(notes),
            "linkadas_no_indice": len(direct),
            "so_via_sub_sumario": len(via_sum),
            "orfas": orphan,
            "por_tipo": dict(sorted(by_type.items(), key=lambda kv: -kv[1])),
            "tipos_aposentados": retired,
            "tipos_desconhecidos": unknown,
            "nome_diverge_do_tipo": mismatched,
        },
        "symlinks_quebrados": broken,
        "sub_sumarios": summaries,
        "volume_bytes": sum((mem / n).stat().st_size for n in notes) if notes else 0,
    }


def human(root: Path, dirs: list[Path], reports: list[dict]) -> None:
    print(f"Projeto: {root}\n")

    if len(dirs) > 1:
        print("⚠️  MEMÓRIA FRAGMENTADA — o mesmo projeto tem memória em mais de uma config.")
        print("   Só a config ativa é carregada; o resto está invisível na sessão.\n")
        active = os.environ.get("CLAUDE_CONFIG_DIR")
        for d, r in zip(dirs, reports):
            cfg = d.parents[2]
            mark = "  ← ATIVA" if active and str(cfg) == active else ""
            print(f"   {cfg.name:20} {r['notas']['total']:>4} notas{mark}")
        print()

    r = reports[0]
    i, n = r["indice"], r["notas"]
    print(f"Diretório carregado: {r['dir']}\n")

    if not i["existe"]:
        print("  ⚠ não existe MEMORY.md — nada é carregado nesta sessão.")
        return

    status = "ESTOUROU" if i["estourou"] else ("perto do limite" if i["perto_do_limite"] else "ok")
    print(f"  Índice:  {i['linhas_carregadas']}/{LIMIT_LINES} linhas · "
          f"{i['bytes_carregados'] // 1024}/{LIMIT_BYTES // 1024} KB   [{status}]")
    if i["estourou"]:
        print("    ⚠ o que passa do limite é descartado na próxima sessão — encurte o índice.")

    total = n["total"] or 1
    print(f"\n  Notas:   {n['total']} · volume {r['volume_bytes'] // 1024} KB "
          f"(carrega {i['bytes_carregados'] // 1024} KB)")
    print(f"    linkadas no índice:   {n['linkadas_no_indice']:>4}  "
          f"({n['linkadas_no_indice'] * 100 // total}%) — agem em toda sessão")
    print(f"    só via sub-sumário:   {n['so_via_sub_sumario']:>4}  "
          f"({n['so_via_sub_sumario'] * 100 // total}%) — 2 leituras pra chegar")
    print(f"    órfãs:                {len(n['orfas']):>4}  — só se alguém adivinhar o nome")
    for o in n["orfas"][:5]:
        print(f"      · {o}")

    print("\n  Por tipo: " + " · ".join(f"{t} {c}" for t, c in n["por_tipo"].items()))
    if n["tipos_aposentados"]:
        print("\n  Tipos aposentados no v10 (nada foi apagado; migração é decisão sua):")
        for t, c in n["tipos_aposentados"].items():
            dest = TYPES_RETIRED[t]
            print(f"    {t}: {c} nota(s) → {dest or 'sem destino (era pra não existir)'}")
    if n["tipos_desconhecidos"]:
        print(f"\n  ⚠ prefixos fora da convenção: {n['tipos_desconhecidos']}")
    if r["symlinks_quebrados"]:
        print(f"\n  ⚠ symlink(s) quebrado(s): {', '.join(r['symlinks_quebrados'])}")
        print("      resíduo de relink antigo — atrapalha backup e cópia; remova com `unlink`, "
              "nunca `rm -r`")
    if n["nome_diverge_do_tipo"]:
        print(f"\n  ⚠ {len(n['nome_diverge_do_tipo'])} nota(s) com nome mentindo sobre o tipo "
              f"(atrapalha quem procura por `ls`):")
        for m in n["nome_diverge_do_tipo"][:5]:
            print(f"      · {m['nota']}  nome diz '{m['nome_diz']}', "
                  f"frontmatter diz '{m['frontmatter_diz']}'")

    if i["linhas_sem_gancho"]:
        print(f"\n  ⚠ {len(i['linhas_sem_gancho'])} linha(s) do índice citam arquivo sem dizer "
              f"quando ele importa:")
        for w in i["linhas_sem_gancho"][:5]:
            print(f"      · {w}")


def plan_migration(mem: Path) -> list[dict]:
    """O que o v10 renomearia. Só tipo aposentado — nome divergente do type é decisão caso a caso."""
    plan = []
    for path in sorted(mem.glob("*.md")):
        if path.name == INDEX or path.name.startswith("_summary"):
            continue
        t = note_type(mem, path.name)
        dest = TYPES_RETIRED.get(t)
        if not dest:
            continue
        prefix = path.name.split("_", 1)[0] if "_" in path.name else None
        novo = f"{dest}_{path.name.split('_', 1)[1]}" if prefix == t else path.name
        plan.append({"de": path.name, "para": novo, "tipo_de": t, "tipo_para": dest,
                     "renomeia_arquivo": novo != path.name})
    return plan


def apply_migration(mem: Path, plan: list[dict]) -> None:
    """Renomeia, corrige `type:`/`name:`, e reescreve os links que apontavam pro nome antigo."""
    backup = mem.parent / f"memory.bak-{__import__('time').strftime('%Y%m%d%H%M%S')}"
    # symlinks=True: copia o link, não o alvo. O diretório de memória costuma ter symlink
    # de worktree apontando pro root — segui-lo duplicaria o acervo inteiro, e um link
    # quebrado abortaria o backup (e, sem backup, não há migração).
    __import__("shutil").copytree(mem, backup, symlinks=True)
    print(f"  backup: {backup}")

    for item in plan:
        src = mem / item["de"]
        text = src.read_text(encoding="utf-8")
        text = re.sub(r"^(\s*)type:\s*\S+\s*$",
                      lambda m: f"{m.group(1)}type: {item['tipo_para']}", text, count=1, flags=re.M)
        # `name:` interno é kebab (`blocker-lint-staged`), o arquivo é snake
        # (`blocker_lint_staged.md`) — trocar só o prefixo cobre as duas convenções.
        text = re.sub(rf"^(name:\s*){re.escape(item['tipo_de'])}([-_])",
                      rf"\g<1>{item['tipo_para']}\g<2>", text, count=1, flags=re.M)
        dst = mem / item["para"]
        dst.write_text(text, encoding="utf-8")
        if item["renomeia_arquivo"]:
            src.unlink()

    # Link que aponta pro nome antigo vira link morto — e nota inalcançável é nota que não existe.
    renamed = {i["de"]: i["para"] for i in plan if i["renomeia_arquivo"]}
    if renamed:
        for f in list(mem.glob("*.md")):
            text = original = f.read_text(encoding="utf-8")
            for old, new in renamed.items():
                text = text.replace(old, new).replace(old[:-3], new[:-3])
            if text != original:
                f.write_text(text, encoding="utf-8")
                print(f"  links atualizados em {f.name}")


def cmd_migrate(mem: Path, apply: bool) -> int:
    plan = plan_migration(mem)
    if not plan:
        print("Nada a migrar — nenhuma nota com tipo aposentado.")
        return 0

    print(f"Migração v9 → v10 · {mem}\n")
    for i in plan:
        arrow = f"{i['de']}  →  {i['para']}" if i["renomeia_arquivo"] else f"{i['de']}  (só o frontmatter)"
        print(f"  {i['tipo_de']} → {i['tipo_para']}   {arrow}")
    print(f"\n  {len(plan)} nota(s). Nada é apagado; links são reescritos junto.")

    if not apply:
        print("\n  Isto é uma prévia. Para aplicar:  memory-audit migrate --apply")
        return 0
    print()
    apply_migration(mem, plan)
    print(f"\n  ✓ {len(plan)} nota(s) migrada(s). Confira com: memory-audit")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="memory-audit", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=None, help="raiz do projeto (default: repositório principal)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--all-configs", action="store_true",
                   help="detalha cada config, não só a ativa")
    sub = p.add_subparsers(dest="cmd")
    pm = sub.add_parser("migrate", help="v9 → v10: blocker→bug, preference→decision")
    pm.add_argument("--apply", action="store_true", help="escreve (default é só a prévia)")
    pm.add_argument("--root", default=None)
    a = p.parse_args(argv)

    root = Path(a.root).resolve() if a.root else git_root()
    if root is None:
        print("erro: não estou num repositório git (use --root)", file=sys.stderr)
        return 1

    dirs = find_memory_dirs(root)
    if not dirs:
        print(f"nenhuma memória encontrada para {root}", file=sys.stderr)
        print(f"  procurei em ~/.claude*/projects/{encoded(root)}/memory", file=sys.stderr)
        return 1

    if getattr(a, "cmd", None) == "migrate":
        return cmd_migrate(dirs[0], a.apply)

    reports = [audit(d) for d in dirs]
    if a.json:
        print(json.dumps({"root": str(root), "fragmentado": len(dirs) > 1,
                          "configs": reports if a.all_configs else reports[:1]},
                         ensure_ascii=False, indent=2))
        return 0
    human(root, dirs, reports)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
