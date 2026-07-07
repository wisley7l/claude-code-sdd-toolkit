#!/usr/bin/env python3
"""structure-cache — índice shallow de estrutura de código, invalidado por hash.

Protótipo (MVP): TypeScript/TSX. A extração usa regex como STAND-IN do tree-sitter
(a fidelidade do parser é secundária pro protótipo; o que estamos validando é o
mecanismo de manifest + hash + build incremental). `extract_ts()` é isolada de
propósito pra ser trocada por tree-sitter depois sem mexer no resto.

Determinístico, sem LLM. Worktree-safe: opera SEMPRE relativo a --root (o caller
passa `git rev-parse --show-toplevel`), e escreve o cache DENTRO daquele worktree
(thoughts/cache/structure/), nunca num lugar compartilhado.

Uso (rode de QUALQUER lugar dentro do repo/worktree — --root é auto-detectado via git):
  build.py build [--incremental] [--root <dir>]   # constrói/atualiza o cache
  build.py check [--root <dir>]                    # relata fresh/stale (exit 0=fresh, 1=stale)
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CACHE_SUBDIR = Path("thoughts") / "cache" / "structure"
INDEX_NAME = "index.json"
MANIFEST_NAME = "manifest.json"
HOTSPOTS_NAME = "HOTSPOTS.md"
SCHEMA_VERSION = 1
CODE_SUFFIXES = {".ts", ".tsx"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "coverage", "thoughts"}

_IMPORT_RE = re.compile(r"""(?:import\b[^'"]*?from\s*|import\s*|require\s*\(\s*)['"]([^'"]+)['"]""")
_FUNC_RE = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", re.M)
_CLASS_RE = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)", re.M)
_CONST_FN_RE = re.compile(r"^\s*(?:export\s+)?(?:const|let)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]+)?=\s*(?:async\s*)?\(?[^;=]*=>", re.M)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def iter_source_files(root: Path) -> list[Path]:
    """Lista arquivos de código sob root, pulando dirs de build/deps. Ordenado
    pra saída byte-estável."""
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in CODE_SUFFIXES:
            continue
        if path.name.endswith(".d.ts"):
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        out.append(path)
    out.sort()
    return out


def _resolve_import(from_rel: str, spec: str, known: set[str]) -> str | None:
    """Resolve um import relativo ('./x', '../y') pra um path conhecido do repo.
    Bare imports (pacotes npm) retornam None — viram nó 'module', não edge de arquivo."""
    if not spec.startswith("."):
        return None
    base = (Path(from_rel).parent / spec).as_posix()
    base = re.sub(r"/\./", "/", base)
    while "/../" in base:
        base = re.sub(r"/[^/]+/\.\./", "/", base)
    candidates = [base, base + ".ts", base + ".tsx", base + "/index.ts", base + "/index.tsx"]
    for cand in candidates:
        norm = cand.lstrip("./")
        if norm in known:
            return norm
    return None


def extract_ts(rel: str, text: str) -> dict:
    """STAND-IN do tree-sitter: extrai defs (function/class/arrow const) e imports.
    Retorna nós e edges brutos de UM arquivo (imports resolvidos depois, quando
    o conjunto de arquivos conhecidos existe)."""
    nodes: list[dict] = []
    for m in _FUNC_RE.finditer(text):
        nodes.append({"id": f"{rel}::{m.group(1)}", "kind": "func", "file": rel})
    for m in _CLASS_RE.finditer(text):
        nodes.append({"id": f"{rel}::{m.group(1)}", "kind": "class", "file": rel})
    for m in _CONST_FN_RE.finditer(text):
        nodes.append({"id": f"{rel}::{m.group(1)}", "kind": "func", "file": rel})
    imports = sorted({m.group(1) for m in _IMPORT_RE.finditer(text)})
    return {"nodes": nodes, "imports": imports}


def build(root: Path, incremental: bool) -> int:
    cache_dir = root / CACHE_SUBDIR
    manifest_path = cache_dir / MANIFEST_NAME
    index_path = cache_dir / INDEX_NAME
    files = iter_source_files(root)
    current_hashes = {p.relative_to(root).as_posix(): sha256_file(p) for p in files}
    prev_manifest = _load_json(manifest_path) if incremental else None
    prev_index = _load_json(index_path) if incremental else None
    per_file: dict[str, dict] = {}
    reused = 0
    parsed = 0
    if incremental and prev_manifest and prev_index and "per_file" in prev_index:
        prev_hashes = prev_manifest.get("files", {})
        prev_per_file = prev_index["per_file"]
        for rel, digest in current_hashes.items():
            if rel in prev_per_file and prev_hashes.get(rel) == digest:
                per_file[rel] = prev_per_file[rel]
                reused += 1
            else:
                per_file[rel] = extract_ts(rel, (root / rel).read_text(encoding="utf-8", errors="replace"))
                parsed += 1
    else:
        for rel in current_hashes:
            per_file[rel] = extract_ts(rel, (root / rel).read_text(encoding="utf-8", errors="replace"))
            parsed += 1
    known = set(current_hashes.keys())
    nodes, edges = _assemble(per_file, known)
    index = {
        "schema_version": SCHEMA_VERSION,
        "root_name": root.name,
        "counts": {"files": len(known), "nodes": len(nodes), "edges": len(edges)},
        "nodes": nodes,
        "edges": edges,
        "per_file": per_file,
    }
    manifest = {"schema_version": SCHEMA_VERSION, "files": current_hashes}
    cache_dir.mkdir(parents=True, exist_ok=True)
    _write_json(index_path, index)
    _write_json(manifest_path, manifest)
    _write_hotspots(cache_dir / HOTSPOTS_NAME, nodes, edges, known)
    removed = 0
    if incremental and prev_manifest:
        removed = len(set(prev_manifest.get("files", {})) - known)
    print(f"structure-cache: {len(known)} arquivos | parseados={parsed} reaproveitados={reused} removidos={removed}")
    print(f"  → {index_path.relative_to(root)} ({len(nodes)} nós, {len(edges)} edges)")
    return 0


def _assemble(per_file: dict, known: set[str]) -> tuple[list[dict], list[dict]]:
    """Junta nós de todos os arquivos e resolve imports em edges (dedup + ordenação
    estável)."""
    nodes: list[dict] = []
    for rel in sorted(per_file):
        nodes.extend(per_file[rel]["nodes"])
    nodes.sort(key=lambda n: n["id"])
    edges_set: set[tuple] = set()
    for rel in sorted(per_file):
        for spec in per_file[rel]["imports"]:
            target = _resolve_import(rel, spec, known)
            if target:
                edges_set.add((rel, target, "imports", "EXTRACTED"))
            else:
                edges_set.add((rel, f"pkg:{spec}", "imports", "EXTRACTED"))
    edges = [{"from": a, "to": b, "rel": r, "conf": c} for (a, b, r, c) in sorted(edges_set)]
    return nodes, edges


def _write_hotspots(path: Path, nodes: list[dict], edges: list[dict], known: set[str]) -> None:
    """Deriva god-nodes (arquivos por grau de edge) — é ISTO que o /sdd-learning leria
    pra propor lesson/blocker na memória durável."""
    degree: dict[str, int] = {rel: 0 for rel in known}
    for e in edges:
        if e["from"] in degree:
            degree[e["from"]] += 1
        if e["to"] in degree:
            degree[e["to"]] += 1
    ranked = sorted(degree.items(), key=lambda kv: (-kv[1], kv[0]))
    lines = ["# HOTSPOTS (derivado — NÃO é memória durável)", ""]
    lines.append(f"Arquivos: {len(known)} · nós: {len(nodes)} · edges: {len(edges)}")
    lines += ["", "## God-nodes (maior acoplamento por grau de import)", ""]
    for rel, deg in ranked[:10]:
        if deg == 0:
            continue
        lines.append(f"- `{rel}` — grau {deg}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check(root: Path) -> int:
    """Compara hash atual vs manifest. Este é o BACKSTOP de correção: pega
    rebase/checkout/stash que os hooks perderam. exit 0=fresh, 1=stale/ausente."""
    manifest_path = root / CACHE_SUBDIR / MANIFEST_NAME
    prev = _load_json(manifest_path)
    if not prev:
        print("structure-cache: SEM cache — build frio necessário (ou fallback pra reler código)")
        return 1
    prev_hashes = prev.get("files", {})
    current = {p.relative_to(root).as_posix(): sha256_file(p) for p in iter_source_files(root)}
    changed = [r for r in current if prev_hashes.get(r) != current[r]]
    removed = [r for r in prev_hashes if r not in current]
    if not changed and not removed:
        print(f"structure-cache: FRESCO ({len(current)} arquivos batem com o manifest)")
        return 0
    print(f"structure-cache: STALE — {len(changed)} mudados, {len(removed)} removidos")
    for r in (changed + removed)[:10]:
        print(f"  ~ {r}")
    return 1


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")


def detect_root() -> Path | None:
    """Descobre o topo do worktree ATUAL via git. Rodado de dentro de um worktree
    linkado, o git devolve o root DAQUELE worktree — é isto que torna o cache
    worktree-safe sem o usuário passar path nenhum."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
    except (OSError, ValueError):
        return None
    if out.returncode != 0:
        return None
    top = out.stdout.strip()
    return Path(top).resolve() if top else None


def _is_stale(root: Path) -> bool:
    """True se o cache não bate mais com os hashes atuais (ou não existe)."""
    manifest = _load_json(root / CACHE_SUBDIR / MANIFEST_NAME)
    if not manifest:
        return True
    prev = manifest.get("files", {})
    current = {p.relative_to(root).as_posix(): sha256_file(p) for p in iter_source_files(root)}
    return prev != current


def query(root: Path, kind: str, target: str | None, top: int, as_json: bool) -> int:
    """Consulta o cache SEM reler código. É o que /sdd-plan e /sdd-spec chamam na
    pesquisa. exit: 0=respondeu, 3=sem cache (caller deve cair no fallback de reler
    código). Se o cache está stale, responde mesmo assim mas avisa no stderr — quem
    decide re-buildar é o caller."""
    index = _load_json(root / CACHE_SUBDIR / INDEX_NAME)
    if index is None:
        print("structure-cache: SEM cache — caller deve reler código (fallback)", file=sys.stderr)
        return 3
    if _is_stale(root):
        print("structure-cache: aviso — cache STALE; rode 'structure-cache build --incremental'", file=sys.stderr)
    edges = index.get("edges", [])
    nodes = index.get("nodes", [])
    if kind == "importers":
        result = sorted({e["from"] for e in edges if e["to"] == target})
    elif kind == "imports":
        result = sorted({e["to"] for e in edges if e["from"] == target})
    elif kind == "defs":
        result = [{"id": n["id"], "kind": n["kind"]} for n in nodes if n["file"] == target]
    elif kind == "hotspots":
        degree: dict[str, int] = {}
        for e in edges:
            for endpoint in (e["from"], e["to"]):
                if not endpoint.startswith("pkg:"):
                    degree[endpoint] = degree.get(endpoint, 0) + 1
        ranked = sorted(degree.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
        result = [{"file": f, "degree": d} for f, d in ranked]
    else:
        print(f"structure-cache: query desconhecida: {kind}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for item in result:
            print(item if isinstance(item, str) else json.dumps(item, ensure_ascii=False))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="structure-cache", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    pb = sub.add_parser("build", help="constrói/atualiza o cache")
    pb.add_argument("--root", default=None, help="raiz do projeto (default: git toplevel do dir atual)")
    pb.add_argument("--incremental", action="store_true")
    pc = sub.add_parser("check", help="relata fresh/stale")
    pc.add_argument("--root", default=None, help="raiz do projeto (default: git toplevel do dir atual)")
    pq = sub.add_parser("query", help="consulta o cache sem reler código")
    pq.add_argument("--root", default=None, help="raiz do projeto (default: git toplevel do dir atual)")
    pq.add_argument("--importers", metavar="FILE", help="arquivos que importam FILE")
    pq.add_argument("--imports", metavar="FILE", help="o que FILE importa")
    pq.add_argument("--defs", metavar="FILE", help="definições em FILE")
    pq.add_argument("--hotspots", action="store_true", help="god-nodes por acoplamento")
    pq.add_argument("--top", type=int, default=10, help="limite p/ --hotspots (default 10)")
    pq.add_argument("--json", action="store_true", help="saída JSON (p/ consumo por comando)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else detect_root()
    if root is None:
        print("structure-cache: fora de um repo git — passe --root <dir> explicitamente", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"structure-cache: root inválido: {root}", file=sys.stderr)
        return 2
    if args.cmd == "build":
        return build(root, args.incremental)
    if args.cmd == "check":
        return check(root)
    if args.cmd == "query":
        if args.importers:
            return query(root, "importers", args.importers, args.top, args.json)
        if args.imports:
            return query(root, "imports", args.imports, args.top, args.json)
        if args.defs:
            return query(root, "defs", args.defs, args.top, args.json)
        if args.hotspots:
            return query(root, "hotspots", None, args.top, args.json)
        print("structure-cache query: escolha --importers/--imports/--defs/--hotspots", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
