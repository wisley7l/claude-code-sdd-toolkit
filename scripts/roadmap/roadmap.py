#!/usr/bin/env python3
"""roadmap — vault Obsidian de itens do roadmap. Determinístico, sem LLM.

Cada item é um `.md` em `thoughts/roadmap/<status>/NNN-slug.md`. O **status é a pasta**
(fonte única da verdade — não existe `status:` no frontmatter). Cada dependência é um
wikilink `[[NNN-slug]]` no corpo, e o grafo é nativo do Obsidian (não se gera mermaid).

Worktree-safe: opera SEMPRE no **repositório principal** (`git worktree list | head -1`),
porque `thoughts/` é gitignored e uma worktree nasce sem ele.

O que este script NÃO faz, de propósito: decidir título, slug, escopo, se algo vale virar
item, ou se uma dependência existe. Isso é julgamento e mora na skill `roadmap`.

Uso (de qualquer lugar dentro do repo/worktree):
  roadmap init                                        # cria o vault
  roadmap add "<título>" [--dep NNN,MMM] [--change NNN-slug]
                         [--issue N --issue-url URL] [--next]
  roadmap dep NNN --on MMM[,PPP] | --clear            # liga/desliga dependências
  roadmap move NNN --to backlog|em-progresso|concluido [--pr N]
  roadmap set NNN [--pr N] [--change NNN-slug] [--next true|false]
  roadmap hub                                         # regenera ROADMAP.md
  roadmap status [--json]                             # contagens, sinais, desbloqueados
  roadmap list [--status X] [--json]                  # itens
  roadmap check                                       # exit 1 se houver ciclo ou órfão
  roadmap board [-a] [--live SEG]                     # espelho HTML em <vault>/board.html

Toda mutação regenera o hub. Todo comando é idempotente.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

STATUSES = ("backlog", "em-progresso", "concluido")
ROADMAP_SUBDIR = Path("thoughts") / "roadmap"
HUB_NAME = "ROADMAP.md"
LEGACY_HUB = Path("thoughts") / "ROADMAP.md"

_ITEM_RE = re.compile(r"^(\d{3})-(.+)\.md$")
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
_DEPENDE_RE = re.compile(r"^\*\*Depende de:\*\*.*$", re.M)

STOPWORDS = {"de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "em", "no",
             "na", "para", "por", "com", "um", "uma", "the", "of", "to", "for"}


# ---------------------------------------------------------------- infra

def die(msg: str, code: int = 1) -> "None":
    print(f"erro: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main_root(explicit: str | None) -> Path:
    """A âncora estável do projeto — nunca a worktree em que estamos. `thoughts/` vive lá.

    Dois layouts, duas âncoras:

    - **Clone normal + worktrees:** a primeira linha de `git worktree list` é o main
      worktree, e é ele. Worktrees de feature nascem e morrem; o main fica.
    - **Bare + worktrees** (`projeto/.bare` com `projeto/main`, `projeto/feat-x` irmãs):
      não existe main worktree. A linha `(bare)` vem primeiro e é um diretório git —
      escrever nela enterraria o vault dentro do `.bare/`. E pegar a primeira árvore é
      pior ainda: o git lista em ordem alfabética, então o vault cairia numa worktree
      de feature qualquer, sumindo quando o PR fechasse. A âncora é o **pai do bare**,
      que é o diretório do projeto e sobrevive a todas elas.
    """
    if explicit:
        return Path(explicit).resolve()
    try:
        out = subprocess.run(["git", "worktree", "list"], capture_output=True,
                             text=True, check=True).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        die("não estou num repositório git (use --root)")

    lines = [l for l in out if l.strip()]
    if not lines:
        die("`git worktree list` não retornou nada (use --root)")

    bare = next((l for l in lines if l.rstrip().endswith("(bare)")), None)
    trees = [Path(l.split()[0]).resolve() for l in lines if l is not bare]
    if bare is None:
        return trees[0]

    anchor = Path(bare.split()[0]).resolve().parent
    if trees and not any(anchor in t.parents or anchor == t for t in trees):
        # bare fora do diretório do projeto (ex.: /srv/git/x.git). O pai dele não é
        # âncora de nada — melhor uma árvore real do que um caminho sem relação.
        print(f"aviso: repositório bare em {bare.split()[0]} está fora das worktrees; "
              f"ancorando em {trees[0]} (use --root pra fixar outro lugar)", file=sys.stderr)
        return trees[0]
    if not trees:
        die("só achei um repositório bare, sem árvore de trabalho — use --root")
    return anchor


def slugify(text: str, max_words: int = 6, min_words: int = 3) -> str:
    norm = unicodedata.normalize("NFKD", text)
    ascii_only = "".join(c for c in norm if not unicodedata.combining(c))
    words = re.findall(r"[a-z0-9]+", ascii_only.lower())
    meaningful = [w for w in words if w not in STOPWORDS] or words
    picked = meaningful[:max_words]
    if len(picked) < min_words:  # curto demais: recupera stopwords pra ter corpo
        picked = words[:max_words]
    return "-".join(picked) or "item"


# ---------------------------------------------------------------- modelo

class Item:
    """Um arquivo `NNN-slug.md`. `fm` é frontmatter cru; `body` nunca é reescrito inteiro."""

    def __init__(self, path: Path, status: str, fm: dict, body: str):
        self.path, self.status, self.fm, self.body = path, status, fm, body
        self.nnn = path.name[:3]
        self.slug = path.stem

    @property
    def titulo(self) -> str:
        return self.fm.get("titulo") or self.slug

    @property
    def pr(self) -> str:
        return (self.fm.get("pr") or "").strip()

    @property
    def is_next(self) -> bool:
        return (self.fm.get("next") or "").strip().lower() == "true"

    @property
    def deps(self) -> list[str]:
        """Os `[[...]]` da linha `**Depende de:**` — a única linha do corpo que é aresta."""
        m = _DEPENDE_RE.search(self.body)
        return _WIKILINK_RE.findall(m.group(0)) if m else []


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm: dict = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, text[end + 4:].lstrip("\n")


def render_frontmatter(fm: dict) -> str:
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in fm.items()) + "---\n"


def vault(root: Path) -> Path:
    return root / ROADMAP_SUBDIR


def load_items(root: Path) -> list[Item]:
    items: list[Item] = []
    for status in STATUSES:
        d = vault(root) / status
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.md")):
            if not _ITEM_RE.match(path.name):
                continue
            fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            items.append(Item(path, status, fm, body))
    return sorted(items, key=lambda i: i.nnn)


def find(items: list[Item], nnn: str) -> Item | None:
    nnn = nnn.strip().lstrip("#").zfill(3)
    return next((i for i in items if i.nnn == nnn), None)


def next_nnn(items: list[Item]) -> str:
    """max + 1 sobre TODAS as pastas. Nunca reusa — é o id estável do nó no grafo."""
    return f"{max((int(i.nnn) for i in items), default=0) + 1:03d}"


# ---------------------------------------------------------------- grafo

def resolve(items: list[Item], link: str) -> Item | None:
    """Wikilink resolve por nome de arquivo; aceita também só o NNN."""
    link = link.strip()
    hit = next((i for i in items if i.slug == link), None)
    return hit or (find(items, link[:3]) if re.match(r"^\d{3}", link) else None)


def duplicados(items: list[Item]) -> list[tuple[str, list[str]]]:
    """Dois arquivos com o mesmo NNN. `find` só enxerga o primeiro, e o outro vira nó fantasma.

    Não nasce do motor (`next_nnn` é max+1), mas nasce de edição à mão e de merge de vault.
    """
    por_nnn: dict[str, list[str]] = {}
    for i in items:
        por_nnn.setdefault(i.nnn, []).append(i.slug)
    return [(n, slugs) for n, slugs in sorted(por_nnn.items()) if len(slugs) > 1]


def orphans(items: list[Item]) -> list[tuple[str, str]]:
    return [(i.nnn, d) for i in items for d in i.deps if resolve(items, d) is None]


def cycles(items: list[Item]) -> list[list[str]]:
    """DFS com pilha. Devolve os ciclos encontrados, como lista de NNN."""
    by_nnn = {i.nnn: i for i in items}
    found: list[list[str]] = []
    seen: set[str] = set()

    def walk(nnn: str, stack: list[str]) -> None:
        if nnn in stack:
            cyc = stack[stack.index(nnn):] + [nnn]
            if sorted(set(cyc)) not in [sorted(set(c)) for c in found]:
                found.append(cyc)
            return
        if nnn in seen:
            return
        seen.add(nnn)
        for dep in by_nnn[nnn].deps:
            target = resolve(items, dep)
            if target:
                walk(target.nnn, stack + [nnn])

    for i in items:
        walk(i.nnn, [])
    return found


def unblocked(items: list[Item]) -> list[Item]:
    """Em backlog/ E tem dependência E todas em concluido/.

    Item de backlog sem dependência nunca esteve bloqueado — não conta.
    """
    done = {i.nnn for i in items if i.status == "concluido"}
    out = []
    for i in items:
        if i.status != "backlog" or not i.deps:
            continue
        targets = [resolve(items, d) for d in i.deps]
        if all(t is not None and t.nnn in done for t in targets):
            out.append(i)
    return out


def would_cycle(items: list[Item], nnn: str, new_deps: list[str]) -> bool:
    """A aresta nova alcança nnn de volta?"""
    by_nnn = {i.nnn: i for i in items}
    stack, seen = list(new_deps), set()
    while stack:
        cur = resolve(items, stack.pop())
        if cur is None or cur.nnn in seen:
            continue
        if cur.nnn == nnn:
            return True
        seen.add(cur.nnn)
        stack.extend(by_nnn[cur.nnn].deps)
    return False


# ---------------------------------------------------------------- escrita

def write_item(path: Path, fm: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_frontmatter(fm) + "\n" + body.rstrip() + "\n", encoding="utf-8")


def set_deps_line(body: str, links: list[str]) -> str:
    """Escreve/remove a linha `**Depende de:**` sem tocar no resto do corpo."""
    line = "**Depende de:** " + ", ".join(f"[[{l}]]" for l in links) if links else ""
    if _DEPENDE_RE.search(body):
        out = _DEPENDE_RE.sub(line, body, count=1)
        return re.sub(r"\n{3,}", "\n\n", out.replace("\n\n\n", "\n\n")) if not links else out
    if not links:
        return body
    lines = body.splitlines()
    at = 1 if lines and lines[0].startswith("# ") else 0
    lines.insert(at, ("\n" if at else "") + line)
    return "\n".join(lines)


def regen_hub(root: Path) -> None:
    items = load_items(root)
    unb = {i.nnn for i in unblocked(items)}

    def bullet(i: Item) -> str:
        return f"- [[{i.slug}]] — {i.titulo}" + (f" · {i.pr}" if i.pr else "")

    out = [
        "# Roadmap",
        "",
        "> Vault Obsidian: cada item é um `.md`, dependência é `[[link]]`, o grafo é nativo.",
        "> Status = pasta (`backlog/` · `em-progresso/` · `concluido/`). Abra o Graph View pra ver a ordem.",
        "> Gerado por `roadmap hub` — **não editar à mão** (exceto `next:` nos itens, que é curadoria sua).",
        "",
        "## 🔴 Próximos (fila priorizada)",
        "",
    ]
    out += [bullet(i) for i in items if i.is_next] or ["_vazio — marque com `roadmap set NNN --next true`._"]
    out += ["", "## 🔓 Desbloqueados agora", ""]
    out += [bullet(i) for i in items if i.nnn in unb] or ["_nenhum._"]
    for status, title in zip(STATUSES, ("Backlog", "Em progresso", "Concluído")):
        out += ["", f"## {title}", ""]
        out += [bullet(i) for i in items if i.status == status] or ["_vazio._"]
    (vault(root) / HUB_NAME).write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- comandos

def regen_board(root: Path) -> None:
    """Espelho HTML, best-effort: board quebrado nunca pode derrubar uma mutação do vault.

    Só regenera o que já existe — quem nunca rodou `roadmap board` não ganha arquivo novo.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import board
        if not (board.board_root(root) / board.BOARD_NAME).exists():
            return
        board.escrever(root)
        import changes
        changes.escrever(root)
    except Exception as e:  # noqa: BLE001 — o board é acessório; o vault é o que importa
        print(f"aviso: board não regenerado ({e})", file=sys.stderr)


def cmd_init(root: Path, _a) -> int:
    for s in STATUSES:
        (vault(root) / s).mkdir(parents=True, exist_ok=True)
    regen_hub(root)
    regen_board(root)
    print(f"vault pronto: {vault(root)}")
    return 0


def cmd_add(root: Path, a) -> int:
    items = load_items(root)
    if a.issue and any(f"#{a.issue}" in i.body for i in items):
        die(f"issue #{a.issue} já tem item no roadmap")

    nnn = next_nnn(items)
    slug = f"{nnn}-{slugify(a.titulo)}"
    fm = {
        "id": nnn,
        "titulo": a.titulo,
        "pr": f"#{a.pr}" if a.pr else "",
        "criado": date.today().strftime("%d-%m-%Y"),
        "change": a.change or "",
        "next": "true" if a.next else "false",
    }

    deps: list[str] = []
    for raw in (a.dep or "").replace(" ", "").split(","):
        if not raw:
            continue
        target = resolve(items, raw)
        if target is None:
            print(f"aviso: dependência {raw} não existe — ignorada", file=sys.stderr)
        else:
            deps.append(target.slug)

    body = [f"# {nnn} — {a.titulo}", ""]
    if deps:
        body += ["**Depende de:** " + ", ".join(f"[[{d}]]" for d in deps)]
    if a.change:
        body += [f"**Docs:** [[changes/{a.change}/spec|spec]] · [[changes/{a.change}/plan|plan]]"]
    if a.issue:
        body += [f"**Issue:** [#{a.issue}]({a.issue_url or ''})"]
    if a.contexto:
        body += ["", a.contexto]

    write_item(vault(root) / "backlog" / f"{slug}.md", fm, "\n".join(body))
    regen_hub(root)
    regen_board(root)
    print(f"{nnn}\t{slug}\tbacklog" + (f"\tdepende de: {', '.join(deps)}" if deps else ""))
    return 0


def cmd_dep(root: Path, a) -> int:
    items = load_items(root)
    item = find(items, a.nnn)
    if item is None:
        die(f"item {a.nnn} não existe")

    if a.clear:
        links: list[str] = []
    else:
        links = []
        for raw in a.on.replace(" ", "").split(","):
            if not raw:
                continue
            target = resolve(items, raw)
            if target is None:
                print(f"aviso: {raw} não existe — ignorado", file=sys.stderr)
            elif target.nnn == item.nnn:
                die("auto-dependência é inválida")
            else:
                links.append(target.slug)
        if not links:
            # apagar dependência é `--clear`, explícito. Um NNN digitado errado não
            # pode virar remoção silenciosa das arestas que já existiam.
            die(f"nenhum alvo de --on existe ({a.on}) — nada foi escrito; use --clear pra remover")
        if would_cycle(items, item.nnn, links):
            die(f"essa aresta fecha um ciclo com {a.on} — ordem impossível, nada foi escrito")

    write_item(item.path, item.fm, set_deps_line(item.body, links))
    regen_hub(root)
    regen_board(root)
    print(f"{item.nnn} depende de: {', '.join(links) or '(nada)'}")
    return 0


def cmd_move(root: Path, a) -> int:
    items = load_items(root)
    item = find(items, a.nnn)
    if item is None:
        die(f"item {a.nnn} não existe")
    if a.to not in STATUSES:
        die(f"status inválido: {a.to} (use {' | '.join(STATUSES)})")

    if a.pr:
        item.fm["pr"] = f"#{a.pr.lstrip('#')}"
    dest = vault(root) / a.to / item.path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    write_item(dest, item.fm, item.body)
    if dest != item.path:
        item.path.unlink()          # `thoughts/` é gitignored — nunca `git mv`
    regen_hub(root)
    regen_board(root)

    freed = [i.nnn for i in unblocked(load_items(root))]
    print(f"{item.nnn} → {a.to}" + (f" · {item.fm['pr']}" if item.fm.get("pr") else ""))
    if a.to == "concluido" and freed:
        print(f"desbloqueados agora: {', '.join(freed)}")
    return 0


def cmd_set(root: Path, a) -> int:
    items = load_items(root)
    item = find(items, a.nnn)
    if item is None:
        die(f"item {a.nnn} não existe")
    if a.pr is not None:
        item.fm["pr"] = f"#{a.pr.lstrip('#')}" if a.pr else ""
    if a.change is not None:
        item.fm["change"] = a.change
    if a.next is not None:
        item.fm["next"] = a.next
    write_item(item.path, item.fm, item.body)
    regen_hub(root)
    regen_board(root)
    print(f"{item.nnn} atualizado")
    return 0


def collect(root: Path) -> dict:
    items = load_items(root)
    return {
        "root": str(root),
        "vault": str(vault(root)),
        "legado_formato_antigo": (root / LEGACY_HUB).is_file() and not any(
            (vault(root) / s).is_dir() and any((vault(root) / s).glob("*.md")) for s in STATUSES),
        "contagem": {s: sum(1 for i in items if i.status == s) for s in STATUSES},
        "proximos": [{"nnn": i.nnn, "slug": i.slug, "titulo": i.titulo} for i in items if i.is_next],
        "desbloqueados": [{"nnn": i.nnn, "slug": i.slug, "titulo": i.titulo} for i in unblocked(items)],
        "em_progresso_com_pr": [{"nnn": i.nnn, "pr": i.pr} for i in items
                                if i.status == "em-progresso" and i.pr],
        "orfaos": [{"item": n, "link": l} for n, l in orphans(items)],
        "duplicados": [{"nnn": n, "slugs": s} for n, s in duplicados(items)],
        "ciclos": cycles(items),
        "proximo_nnn": next_nnn(items),
    }


def cmd_status(root: Path, a) -> int:
    data = collect(root)
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    if data["legado_formato_antigo"]:
        print("⚠️  achei thoughts/ROADMAP.md (formato antigo) e nenhum vault — migre antes de operar.\n")
    c = data["contagem"]
    print(f"Roadmap · {data['vault']}\n")
    print(f"  🔴 Próximos:          {len(data['proximos'])}")
    print(f"  🔓 Desbloqueados:     {len(data['desbloqueados'])}")
    print(f"  Backlog:              {c['backlog']}")
    print(f"  Em progresso:         {c['em-progresso']}")
    print(f"  Concluído:            {c['concluido']}")
    for i in data["desbloqueados"]:
        print(f"    🔓 {i['nnn']} — {i['titulo']}")
    if data["orfaos"]:
        print(f"\n  ⚠ links órfãos: " + ", ".join(f"{o['item']}→{o['link']}" for o in data["orfaos"]))
    if data["ciclos"]:
        print("  ⚠ ciclos: " + " · ".join(" → ".join(c) for c in data["ciclos"]))
    if data["duplicados"]:
        print("  ⚠ NNN duplicado: " + ", ".join(
            f"{d['nnn']} ({' e '.join(d['slugs'])})" for d in data["duplicados"]))
    return 0


def cmd_list(root: Path, a) -> int:
    items = [i for i in load_items(root) if not a.status or i.status == a.status]
    if a.json:
        print(json.dumps([{"nnn": i.nnn, "slug": i.slug, "titulo": i.titulo, "status": i.status,
                           "pr": i.pr, "next": i.is_next, "deps": i.deps,
                           "change": i.fm.get("change", ""), "plan": i.fm.get("plan", "")}
                          for i in items], ensure_ascii=False, indent=2))
        return 0
    for i in items:
        print(f"{i.nnn}\t{i.status}\t{i.pr or '-'}\t{i.titulo}")
    return 0


def cmd_hub(root: Path, _a) -> int:
    regen_hub(root)
    regen_board(root)
    print(f"hub regenerado: {vault(root) / HUB_NAME}")
    return 0


def cmd_check(root: Path, _a) -> int:
    items = load_items(root)
    bad = False
    for nnn, slugs in duplicados(items):
        print(f"NNN duplicado: {nnn} em {' e '.join(slugs)}", file=sys.stderr)
        bad = True
    for nnn, link in orphans(items):
        print(f"órfão: {nnn} aponta pra [[{link}]], que não existe", file=sys.stderr)
        bad = True
    for cyc in cycles(items):
        print("ciclo: " + " → ".join(cyc), file=sys.stderr)
        bad = True
    if not bad:
        print(f"ok — {len(items)} itens, sem ciclo nem órfão")
    return 1 if bad else 0


# ---------------------------------------------------------------- cli

def cmd_board(root: Path, a) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import board
    tem_vault = vault(root).is_dir()
    if a.out:  # destino avulso: só o índice, sem a pasta de páginas
        Path(a.out).write_text(board.render(root, live=a.live), encoding="utf-8")
        alvo = Path(a.out).resolve()
        print(f"índice gerado: file://{alvo}", flush=True)
    else:
        if board.limpar_legado(root):
            print("board de layout antigo removido — é tudo regenerável", flush=True)
        import changes
        escritos = (board.escrever(root, live=a.live) if tem_vault else [])
        escritos += changes.escrever(root, live=a.live)
        if not escritos:
            die("nada pra gerar: nem vault de roadmap, nem pasta em thoughts/changes/")
        alvo = escritos[0].resolve()
        for f in escritos:
            print(f"{'board' if f.name == board.BOARD_NAME else 'changes'}: "
                  f"file://{f.resolve()}", flush=True)

    if a.abrir:
        import webbrowser
        if not webbrowser.open(f"file://{alvo}"):
            print("aviso: não achei navegador — abra o caminho acima à mão", file=sys.stderr)
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="roadmap", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=None, help="repositório principal (default: git worktree list | head -1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="cria o vault")

    pa = sub.add_parser("add", help="cria item em backlog/")
    pa.add_argument("titulo")
    pa.add_argument("--dep", default="", help="NNN[,MMM] — dependências")
    pa.add_argument("--change", default="", help="pasta da mudança em thoughts/changes/")
    pa.add_argument("--pr", default="", help="número do PR, se já existir")
    pa.add_argument("--issue", default="", help="número da issue do GitHub")
    pa.add_argument("--issue-url", default="", dest="issue_url")
    pa.add_argument("--contexto", default="", help="uma linha de contexto")
    pa.add_argument("--next", action="store_true", help="já entra na fila 🔴 Próximos")

    pd = sub.add_parser("dep", help="liga/desliga dependências")
    pd.add_argument("nnn")
    g = pd.add_mutually_exclusive_group(required=True)
    g.add_argument("--on", help="MMM[,PPP] — passa a depender destes")
    g.add_argument("--clear", action="store_true")

    pm = sub.add_parser("move", help="move entre pastas (= muda status)")
    pm.add_argument("nnn")
    pm.add_argument("--to", required=True, choices=STATUSES)
    pm.add_argument("--pr", default="", help="preenche pr: ao mover")

    ps = sub.add_parser("set", help="edita campos do frontmatter")
    ps.add_argument("nnn")
    ps.add_argument("--pr", default=None)
    ps.add_argument("--change", default=None)
    ps.add_argument("--next", default=None, choices=["true", "false"])

    sub.add_parser("hub", help="regenera ROADMAP.md")

    pst = sub.add_parser("status", help="estado do vault")
    pst.add_argument("--json", action="store_true")

    pl = sub.add_parser("list", help="lista itens")
    pl.add_argument("--status", choices=STATUSES)
    pl.add_argument("--json", action="store_true")

    sub.add_parser("check", help="exit 1 se houver ciclo ou órfão")

    pb = sub.add_parser("board", help="espelho HTML do vault, pra abrir no navegador")
    pb.add_argument("-o", "--out", default=None, help="default: <vault>/board.html")
    pb.add_argument("--live", type=int, metavar="SEG", default=0,
                    help="recarrega sozinho a cada N segundos (aba deixada aberta)")
    pb.add_argument("-a", "--abrir", action="store_true",
                    help="abre no navegador padrão depois de gerar")

    a = p.parse_args(argv)
    root = main_root(a.root)
    if a.cmd not in ("init", "board") and not vault(root).is_dir():
        die(f"vault não existe em {vault(root)} — rode `roadmap init`")
    return {"init": cmd_init, "add": cmd_add, "dep": cmd_dep, "move": cmd_move, "set": cmd_set,
            "hub": cmd_hub, "status": cmd_status, "list": cmd_list, "check": cmd_check,
            "board": cmd_board}[a.cmd](root, a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
