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
import os
import posixpath
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
SKIP_DIRS = {"node_modules", "dist", "build", "coverage", "thoughts", "vendor",
             "tmp", "out", "target", "__pycache__"}

_IMPORT_RE = re.compile(r"""(?:import\b[^'"]*?from\s*|import\s*|require\s*\(\s*)['"]([^'"]+)['"]""")
_FUNC_RE = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", re.M)
_CLASS_RE = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)", re.M)
_CONST_FN_RE = re.compile(r"^\s*(?:export\s+)?(?:const|let)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]+)?=\s*(?:async\s*)?\(?[^;=]*=>", re.M)

# Viz local self-contained (sem CDN). Dados injetados em /*__DATA__*/.
_GRAPH_HTML_TEMPLATE = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>structure-cache — grafo de estrutura</title>
<style>
  html,body{margin:0;height:100%;background:#0b0e14;color:#c9d1d9;font:13px/1.4 system-ui,sans-serif;overflow:hidden}
  canvas{display:block;cursor:grab}
  canvas.drag{cursor:grabbing}
  #hud{position:fixed;top:10px;left:10px;z-index:3;background:rgba(22,27,34,.85);border:1px solid #30363d;border-radius:8px;padding:10px 12px;max-width:260px}
  #hud b{color:#e6edf3}
  #hud input{width:100%;margin-top:6px;background:#0d1117;border:1px solid #30363d;color:#c9d1d9;border-radius:5px;padding:4px 6px;box-sizing:border-box}
  #legend{margin-top:8px;max-height:34vh;overflow:auto}
  #legend div{display:flex;align-items:center;gap:6px;margin:2px 0;cursor:pointer;opacity:.9}
  #legend span.sw{width:10px;height:10px;border-radius:2px;flex:0 0 auto}
  #legend small{color:#8b949e}
  .tip{position:fixed;pointer-events:none;background:#161b22;border:1px solid #30363d;padding:5px 9px;border-radius:5px;font-size:12px;display:none;z-index:4;max-width:40vw;word-break:break-all}
  .muted{color:#8b949e}
</style></head><body>
<div id="hud">
  <b>structure-cache</b> · <span id="counts" class="muted"></span><br>
  <span class="muted">scroll: zoom · arraste fundo: pan · arraste nó: fixar · hover: detalhe</span>
  <input id="q" placeholder="filtrar arquivo…" autocomplete="off">
  <div id="legend"></div>
</div>
<div class="tip" id="tip"></div>
<canvas id="c"></canvas>
<script>const DATA=/*__DATA__*/;</script>
<script>
const cv=document.getElementById('c'),ctx=cv.getContext('2d'),tip=document.getElementById('tip');
let W,H,DPR;
function resize(){DPR=devicePixelRatio||1;W=innerWidth;H=innerHeight;cv.width=W*DPR;cv.height=H*DPR;cv.style.width=W+'px';cv.style.height=H+'px';ctx.setTransform(DPR,0,0,DPR,0,0);}
addEventListener('resize',resize);resize();
// cor por diretório (hash → hue)
const dirs=[...new Set(DATA.nodes.map(n=>n.dir))].sort();
function hue(s){let h=0;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))>>>0;return h%360;}
const color={};dirs.forEach(d=>color[d]=`hsl(${hue(d)},65%,60%)`);
// nós e índice
const idx=new Map();
const nodes=DATA.nodes.map((n,i)=>{idx.set(n.id,i);const a=Math.random()*6.28,r=Math.min(W,H)*0.35*Math.sqrt(Math.random());return{...n,x:W/2+Math.cos(a)*r,y:H/2+Math.sin(a)*r,vx:0,vy:0,rad:4+Math.sqrt(n.deg)*2.2};});
const links=DATA.links.map(l=>({s:idx.get(l.s),t:idx.get(l.t)})).filter(l=>l.s!=null&&l.t!=null);
document.getElementById('counts').textContent=nodes.length+' arquivos · '+links.length+' imports';
// legenda
const leg=document.getElementById('legend');const deg=dirs.map(d=>[d,DATA.nodes.filter(n=>n.dir===d).length]).sort((a,b)=>b[1]-a[1]);
let hideDir=new Set();
deg.forEach(([d,c])=>{const row=document.createElement('div');row.innerHTML=`<span class="sw" style="background:${color[d]}"></span>${d} <small>(${c})</small>`;row.onclick=()=>{hideDir.has(d)?hideDir.delete(d):hideDir.add(d);row.style.opacity=hideDir.has(d)?.35:.9;heat();};leg.appendChild(row);});
// view transform
let tx=0,ty=0,scale=1;
// força
let alpha=1;function heat(){alpha=Math.max(alpha,.6);}
function vis(n){return !hideDir.has(n.dir);}
function tick(){
  if(alpha>0.005){
    const k=alpha;
    for(let i=0;i<nodes.length;i++){const a=nodes[i];if(!vis(a))continue;
      for(let j=i+1;j<nodes.length;j++){const b=nodes[j];if(!vis(b))continue;
        let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+0.01;if(d2>90000)continue;
        let f=1400/d2;dx*=f;dy*=f;a.vx+=dx*k;a.vy+=dy*k;b.vx-=dx*k;b.vy-=dy*k;}}
    for(const l of links){const a=nodes[l.s],b=nodes[l.t];if(!vis(a)||!vis(b))continue;
      let dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1,f=(d-70)*0.02*k;dx=dx/d*f;dy=dy/d*f;a.vx+=dx;a.vy+=dy;b.vx-=dx;b.vy-=dy;}
    for(const n of nodes){if(!vis(n))continue;n.vx+=(W/2-n.x)*0.0009*k;n.vy+=(H/2-n.y)*0.0009*k;
      if(n.fx==null){n.x+=n.vx;n.y+=n.vy;}n.vx*=.86;n.vy*=.86;}
    alpha*=.985;
  }
  draw();requestAnimationFrame(tick);
}
function draw(){
  ctx.clearRect(0,0,W,H);ctx.save();ctx.translate(tx,ty);ctx.scale(scale,scale);
  ctx.lineWidth=0.5/scale;ctx.strokeStyle='rgba(139,148,158,.22)';ctx.beginPath();
  for(const l of links){const a=nodes[l.s],b=nodes[l.t];if(!vis(a)||!vis(b))continue;ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);}
  ctx.stroke();
  for(const n of nodes){if(!vis(n))continue;ctx.beginPath();ctx.arc(n.x,n.y,n.rad,0,6.2832);ctx.fillStyle=color[n.dir];ctx.globalAlpha=n._hi?1:.9;ctx.fill();
    if(n._hi){ctx.lineWidth=2/scale;ctx.strokeStyle='#e6edf3';ctx.stroke();}}
  ctx.globalAlpha=1;ctx.restore();
}
// interações
function toWorld(px,py){return{x:(px-tx)/scale,y:(py-ty)/scale};}
function pick(px,py){const w=toWorld(px,py);let best=null,bd=1e9;for(const n of nodes){if(!vis(n))continue;const dx=n.x-w.x,dy=n.y-w.y,d=dx*dx+dy*dy;if(d<bd&&d<(n.rad+4)**2){bd=d;best=n;}}return best;}
let drag=null,pan=null;
cv.addEventListener('mousedown',e=>{const n=pick(e.clientX,e.clientY);if(n){drag=n;n.fx=n.x;n.fy=n.y;}else{pan={x:e.clientX-tx,y:e.clientY-ty};cv.classList.add('drag');}});
addEventListener('mousemove',e=>{
  if(drag){const w=toWorld(e.clientX,e.clientY);drag.x=drag.fx=w.x;drag.y=drag.fy=w.y;heat();}
  else if(pan){tx=e.clientX-pan.x;ty=e.clientY-pan.y;}
  else{const n=pick(e.clientX,e.clientY);nodes.forEach(m=>m._hi=false);if(n){n._hi=true;tip.style.display='block';tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px';tip.innerHTML='<b>'+n.id+'</b><br>grau '+n.deg+' · '+n.dir;}else{tip.style.display='none';}}
});
addEventListener('mouseup',()=>{if(drag){drag.fx=drag.fy=null;drag=null;}pan=null;cv.classList.remove('drag');});
cv.addEventListener('wheel',e=>{e.preventDefault();const f=e.deltaY<0?1.1:1/1.1;const wx=(e.clientX-tx)/scale,wy=(e.clientY-ty)/scale;scale*=f;tx=e.clientX-wx*scale;ty=e.clientY-wy*scale;},{passive:false});
document.getElementById('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();nodes.forEach(n=>n._hi=v&&n.id.toLowerCase().includes(v));});
tick();
</script></body></html>"""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def iter_source_files(root: Path) -> list[Path]:
    """Lista arquivos de código sob root, PODANDO dirs pesados durante a varredura.
    Usa os.walk e remove os dirs a ignorar de `dirnames` in-place — assim NUNCA
    desce em node_modules/.git/vendor/etc. (num projeto real esses têm centenas de
    milhares de arquivos; filtrar depois faria a varredura parecer travada).
    Ordenado pra saída byte-estável."""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if not name.endswith(tuple(CODE_SUFFIXES)):
                continue
            if name.endswith(".d.ts"):
                continue
            out.append(Path(dirpath) / name)
    out.sort()
    return out


def _resolve_import(from_rel: str, spec: str, known: set[str]) -> str | None:
    """Resolve um import relativo ('./x', '../y') pra um path conhecido do repo.
    Bare imports (pacotes npm) retornam None — viram nó 'module', não edge de arquivo."""
    if not spec.startswith("."):
        return None
    base = posixpath.normpath(posixpath.join(posixpath.dirname(from_rel), spec))
    if base.startswith(".."):
        return None
    candidates = [base, base + ".ts", base + ".tsx", base + "/index.ts", base + "/index.tsx"]
    for cand in candidates:
        if cand in known:
            return cand
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
    print(f"structure-cache: varrendo {root.name}…", flush=True)
    files = iter_source_files(root)
    print(f"  {len(files)} arquivos de código (TS/TSX). Extraindo…", flush=True)
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


def _graph_view_data(index: dict) -> dict:
    """Reduz o index a um grafo FILE-LEVEL pra visualização: nós = arquivos,
    edges = imports arquivo→arquivo (edges a pacotes npm são omitidas). Grau =
    nº de edges tocando o arquivo (dimensiona o nó)."""
    file_set: set[str] = {n["file"] for n in index.get("nodes", [])}
    links: list[dict] = []
    deg: dict[str, int] = {}
    for e in index.get("edges", []):
        a, b = e["from"], e["to"]
        if b.startswith("pkg:"):
            continue
        file_set.add(a)
        file_set.add(b)
        links.append({"s": a, "t": b})
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    nodes = []
    for f in sorted(file_set):
        top = "/".join(f.split("/")[:2]) if "/" in f else "(root)"
        nodes.append({"id": f, "dir": top, "deg": deg.get(f, 0)})
    return {"nodes": nodes, "links": links}


def export_html(root: Path, out: Path | None) -> int:
    """Gera um graph.html LOCAL e self-contained (força-dirigido em canvas, sem
    CDN). Abre via file://. Não sobe nada pra lugar nenhum."""
    index = _load_json(root / CACHE_SUBDIR / INDEX_NAME)
    if index is None:
        print("structure-cache: sem cache — rode 'structure-cache build' primeiro", file=sys.stderr)
        return 3
    data = _graph_view_data(index)
    out = out or (root / CACHE_SUBDIR / "graph.html")
    html = _GRAPH_HTML_TEMPLATE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"structure-cache: {len(data['nodes'])} nós, {len(data['links'])} edges")
    print(f"  → {out}")
    print(f"  abra: file://{out}")
    return 0


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
    pe = sub.add_parser("export", help="gera graph.html local (self-contained)")
    pe.add_argument("--root", default=None, help="raiz do projeto (default: git toplevel do dir atual)")
    pe.add_argument("--html", default=None, metavar="PATH", help="saída (default: thoughts/cache/structure/graph.html)")
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
    if args.cmd == "export":
        return export_html(root, Path(args.html).resolve() if args.html else None)
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
