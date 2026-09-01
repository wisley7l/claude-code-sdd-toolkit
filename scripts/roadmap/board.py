#!/usr/bin/env python3
"""board — espelho HTML do roadmap. Determinístico, sem LLM.

Lê o mesmo vault que o `roadmap` opera e escreve um site estático:

    thoughts/roadmap/board.html          índice — contagens, DAG, listas, consistência
    thoughts/roadmap/board/NNN-slug.html uma página por item — corpo, vizinhança, ações

Nenhum estado novo: o board é derivado e regenerável, e a fonte da verdade continua sendo a
pasta de `.md`. Abre em `file://`, e por isso **uma página por item** — clicar num card é
navegação de verdade (voltar do navegador, nova aba, favorito), sem depender do `obsidian://`,
que o navegador confirma a cada clique e que só resolve dentro de um vault registrado.

Entra pelo `roadmap board`; depois de existir uma vez, toda mutação do vault o regenera.

Sem dependência e sem CDN: markdown por subset próprio, CSS e JS embutidos em cada página —
o board precisa abrir offline e sem carregar nada de fora.
"""
from __future__ import annotations
import html
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import roadmap as rm

BOARD_ROOT = Path("thoughts") / "board"   # todas as views derivadas moram aqui, longe do dado
BOARD_NAME = "roadmap.html"               # arquivo único: o caminho que se fixa no navegador
LEGADO_ARQ = (Path("thoughts") / "roadmap" / "board.html",)
LEGADO_DIR = (Path("thoughts") / "roadmap" / "board", BOARD_ROOT / "roadmap")
NODE_W, NODE_H = 208, 62
GAP_X, GAP_Y = 88, 18
PAD = 28

STATUS_ROTULO = {"em-progresso": "Em progresso", "backlog": "Backlog", "concluido": "Concluído"}
CLASSE_ROTULO = {"aberto": "desbloqueado", "andando": "em progresso",
                 "feito": "concluído", "travado": "travado"}


# ---------------------------------------------------------------- links

def repo_slug(root: Path) -> str:
    """`owner/repo` do remote origin. Sem remote, o `#PR` fica texto — nunca link quebrado."""
    try:
        url = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
    m = re.search(r"(?:github\.com[:/])([^/]+/[^/]+?)(?:\.git)?$", url)
    return m.group(1) if m else ""


def href_obsidian(path: Path) -> str:
    return "obsidian://open?path=" + quote(str(path.resolve()), safe="")


def href_pr(item, slug: str) -> str:
    n = item.pr.lstrip("#")
    return f"https://github.com/{slug}/pull/{n}" if (slug and n.isdigit()) else ""


def classe(item, desbloq) -> str:
    if item.status == "concluido":
        return "feito"
    if item.status == "em-progresso":
        return "andando"
    return "aberto" if item.nnn in desbloq else "travado"


def esc(t: str) -> str:
    return html.escape(t)


def board_root(root: Path) -> Path:
    return root / BOARD_ROOT


def limpar_legado(root: Path) -> bool:
    """Apaga board de layout antigo — outra pasta, ou a era das páginas por item. Tudo derivado."""
    achou = False
    for rel in LEGADO_ARQ:
        if (alvo := root / rel).is_file():
            alvo.unlink()
            achou = True
    for rel in LEGADO_DIR:
        pasta = root / rel
        if not pasta.is_dir():
            continue
        for f in pasta.glob("*.html"):
            if re.match(r"^\d{3}-.+\.html$", f.name):
                f.unlink()
                achou = True
        if not any(pasta.iterdir()):
            pasta.rmdir()
    return achou


# ---------------------------------------------------------------- markdown

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<![\*\w])\*([^*\n]+)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]*)\)")
_WIKI = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
_CAMPO = re.compile(r"^\*\*[^*]+:\*\*")


def inline(txt: str, items, root: Path, base: str) -> str:
    """Subset inline: código, negrito, itálico, link e wikilink. Escapa antes de marcar."""
    out = esc(txt)
    guarda: list[str] = []

    def parquear(marcado: str) -> str:  # trecho pronto sai da fila das próximas regex
        guarda.append(marcado)
        return f"\x00{len(guarda) - 1}\x00"

    def wiki(m):
        alvo, rotulo = m.group(1), m.group(2) or m.group(1)
        item = rm.resolve(items, alvo)
        if item is not None:  # item do roadmap: troca a ficha aberta, sem sair da página
            return parquear(f'<a class="wiki" href="#item-{item.nnn}" '
                            f'data-ir="{item.nnn}">{rotulo}</a>')
        arq = root / "thoughts" / f"{alvo}.md"  # nota de thoughts/ fora do roadmap
        if arq.is_file():
            return parquear(f'<a class="wiki externo" href="{href_obsidian(arq)}">{rotulo}</a>')
        return parquear(f'<span class="wiki-morto" title="não encontrado">{rotulo}</span>')

    out = _INLINE_CODE.sub(lambda m: parquear(f"<code>{m.group(1)}</code>"), out)
    out = _WIKI.sub(wiki, out)
    out = _LINK.sub(lambda m: parquear(
        f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>'), out)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _ITALIC.sub(r"<em>\1</em>", out)
    return re.sub(r"\x00(\d+)\x00", lambda m: guarda[int(m.group(1))], out)


def markdown(corpo: str, items, root: Path, base: str) -> str:
    """Heading, campo, lista (aninhada e numerada), tabela, citação, code fence, régua, parágrafo.

    Não é CommonMark: é o que os documentos de `thoughts/` de fato usam. O que não couber aqui
    continua legível no Obsidian — a view mostra o essencial, não substitui o editor.
    """
    out: list[str] = []
    buffer_p: list[str] = []
    lista: list[tuple[int, str, bool]] = []   # (nível, texto, é numerada)
    tabela: list[list[str]] = []
    fence: list[str] | None = None

    def fecha_p():
        if buffer_p:
            out.append("<p>" + inline(" ".join(buffer_p), items, root, base) + "</p>")
            buffer_p.clear()

    def fecha_lista():
        """Fecha respeitando nível e numeração — pesquisa usa lista aninhada e ordenada."""
        if not lista:
            return
        html_ = ""
        pilha: list[str] = []
        for nivel, texto, num in lista:
            tag = "ol" if num else "ul"
            while len(pilha) > nivel + 1:
                html_ += f"</li></{pilha.pop()}>"
            if len(pilha) == nivel + 1:
                html_ += "</li>"
            else:
                html_ += f"<{tag}>"
                pilha.append(tag)
            html_ += f"<li>{inline(texto, items, root, base)}"
        while pilha:
            html_ += f"</li></{pilha.pop()}>"
        out.append(html_)
        lista.clear()

    def fecha_tabela():
        if not tabela:
            return
        cab, resto = tabela[0], tabela[1:]
        th = "".join(f"<th>{inline(c, items, root, base)}</th>" for c in cab)
        tr = "".join("<tr>" + "".join(f"<td>{inline(c, items, root, base)}</td>" for c in linha)
                     + "</tr>" for linha in resto)
        out.append(f'<div class="tabela"><table><thead><tr>{th}</tr></thead>'
                   f"<tbody>{tr}</tbody></table></div>")
        tabela.clear()

    for ln in corpo.split("\n"):
        if ln.startswith("```"):
            if fence is None:
                fecha_p(); fecha_lista(); fecha_tabela(); fence = []
            else:
                out.append("<pre><code>" + esc("\n".join(fence)) + "</code></pre>")
                fence = None
            continue
        if fence is not None:
            fence.append(ln)
            continue
        if not ln.strip():
            fecha_p(); fecha_lista(); fecha_tabela()
            continue
        if m := re.match(r"^(#{1,6})\s+(.*)$", ln):
            fecha_p(); fecha_lista(); fecha_tabela()
            if len(m.group(1)) == 1:
                continue  # o h1 repete o título que a página já mostra em cima
            out.append(f"<h{min(len(m.group(1)) + 1, 6)}>"
                       f"{inline(m.group(2), items, root, base)}</h{min(len(m.group(1)) + 1, 6)}>")
            continue
        if _CAMPO.match(ln):  # linha de campo do template: fica em linha só dela
            fecha_p(); fecha_lista(); fecha_tabela()
            out.append(f'<p class="campo">{inline(ln.strip(), items, root, base)}</p>')
            continue
        if m := re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", ln):
            fecha_p(); fecha_tabela()
            lista.append((len(m.group(1)) // 2, m.group(3), m.group(2)[0].isdigit()))
            continue
        if ln.lstrip().startswith("|") and ln.rstrip().endswith("|"):
            fecha_p(); fecha_lista()
            celulas = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in celulas):  # a linha de traços some
                tabela.append(celulas)
            continue
        if re.fullmatch(r"\s*([-*_])\1{2,}\s*", ln):
            fecha_p(); fecha_lista(); fecha_tabela()
            out.append("<hr>")
            continue
        if m := re.match(r"^>\s?(.*)$", ln):
            fecha_p(); fecha_lista(); fecha_tabela()
            out.append(f"<blockquote>{inline(m.group(1), items, root, base)}</blockquote>")
            continue
        fecha_lista(); fecha_tabela()
        buffer_p.append(ln.strip())

    if fence is not None:  # fence sem fechamento: mostra o que veio, não engole
        out.append("<pre><code>" + esc("\n".join(fence)) + "</code></pre>")
    fecha_p(); fecha_lista(); fecha_tabela()
    return "".join(out)


# ---------------------------------------------------------------- grafo

def layers(items, by_nnn) -> dict[int, list]:
    """Nível topológico: 0 sem dependência, senão 1 + o mais profundo dos alvos."""
    nivel: dict[str, int] = {}

    def deep(nnn, seen):
        if nnn in nivel:
            return nivel[nnn]
        if nnn in seen:  # ciclo: o motor barra na escrita, mas o board nunca trava por dado ruim
            return 0
        alvos = [rm.resolve(items, d) for d in by_nnn[nnn].deps]
        n = max((deep(t.nnn, seen | {nnn}) + 1 for t in alvos if t), default=0)
        nivel[nnn] = n
        return n

    for nnn in by_nnn:
        deep(nnn, set())
    cols: dict[int, list] = {}
    for i in items:
        cols.setdefault(nivel[i.nnn], []).append(i)
    return cols


def ordena(cols, items, pos):
    """Barycenter: cada nó desce pra perto da média das suas dependências. Desempate por NNN."""
    for _ in range(3):
        for lvl in sorted(cols)[1:]:
            def chave(i):
                ys = [pos[t.nnn] for d in i.deps
                      if (t := rm.resolve(items, d)) and t.nnn in pos]
                return (sum(ys) / len(ys) if ys else 1e6, i.nnn)
            cols[lvl].sort(key=chave)
            for k, i in enumerate(cols[lvl]):
                pos[i.nnn] = k
    return cols


def svg(items, desbloq, base: str, foco: str = "") -> str:
    """O DAG dos `items` dados. `foco` marca o nó central (usado no mapa da página do item)."""
    by_nnn = {i.nnn: i for i in items}
    cols = layers(items, by_nnn)
    pos = {i.nnn: k for lvl in sorted(cols) for k, i in enumerate(cols[lvl])}
    cols = ordena(cols, items, pos)

    xy: dict[str, tuple[float, float]] = {}
    for lvl in sorted(cols):
        for k, i in enumerate(cols[lvl]):
            xy[i.nnn] = (PAD + lvl * (NODE_W + GAP_X), PAD + k * (NODE_H + GAP_Y))
    alt = max(len(v) for v in cols.values())
    w = PAD * 2 + (max(cols) + 1) * NODE_W + max(cols) * GAP_X
    h = PAD * 2 + alt * NODE_H + (alt - 1) * GAP_Y

    out = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
           f'aria-label="Grafo de dependências do roadmap">',
           '<defs>'
           '<marker id="seta" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" '
           'markerHeight="6" orient="auto"><path d="M0 0 L8 4 L0 8 z" class="ponta"/></marker>'
           '<marker id="seta-viva" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" '
           'markerHeight="6" orient="auto"><path d="M0 0 L8 4 L0 8 z" class="ponta-viva"/>'
           '</marker></defs>']

    for i in items:  # arestas primeiro: passam por baixo dos cards
        for d in i.deps:
            t = rm.resolve(items, d)
            if not t or t.nnn not in xy:
                continue
            x1, y1 = xy[t.nnn][0] + NODE_W, xy[t.nnn][1] + NODE_H / 2
            x2, y2 = xy[i.nnn][0], xy[i.nnn][1] + NODE_H / 2
            c = (x2 - x1) * 0.5
            viva = t.status == "concluido"
            out.append(f'<path d="M{x1} {y1} C{x1 + c} {y1} {x2 - c} {y2} {x2} {y2}" '
                       f'class="aresta {"solta" if viva else "presa"}" '
                       f'data-de="{t.nnn}" data-para="{i.nnn}" '
                       f'marker-end="url(#{"seta-viva" if viva else "seta"})"/>')

    for i in items:
        x, y = xy[i.nnn]
        quebrado = textwrap.wrap(i.titulo, 26)
        linhas = quebrado[:2]
        if len(quebrado) > 2:  # não coube: corta na última linha visível
            linhas[-1] = linhas[-1][:23].rstrip() + "…"
        rotulos = "".join(f'<text class="rot" x="{x + 12}" y="{y + 39 + n * 14}">{esc(ln)}</text>'
                          for n, ln in enumerate(linhas))
        pr_txt = (f'<text class="pr" x="{x + NODE_W - 12}" y="{y + 21}" text-anchor="end">'
                  f'#{esc(i.pr.lstrip("#"))}</text>') if i.pr else ""
        cls = classe(i, desbloq) + (" foco" if i.nnn == foco else "")
        out.append(f'<g class="no {cls}" data-nnn="{i.nnn}">'
                   f'<a href="{base}{i.slug}.html" aria-label="Abrir o item {i.nnn}">'
                   f'<title>{esc(i.titulo)}</title>'
                   f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="3"/>'
                   f'<text class="nnn" x="{x + 12}" y="{y + 21}">{i.nnn}</text>'
                   f'{rotulos}{pr_txt}</a>'
                   + (f'<circle class="pin" cx="{x + NODE_W - 10}" cy="{y + NODE_H - 11}" r="3"/>'
                      if i.is_next else "")
                   + '</g>')
    out.append('</svg>')
    return "\n".join(out)


# ---------------------------------------------------------------- peças

def card(i, desbloq, slug, base: str) -> str:
    cls = classe(i, desbloq)
    pr = ""
    if i.pr:
        n, link = esc(i.pr.lstrip("#")), href_pr(i, slug)
        pr = (f'<a class="pr-tag" href="{link}" target="_blank" rel="noopener">#{n}</a>'
              if link else f'<span class="pr-tag">#{n}</span>')
    marca = ""
    if cls == "aberto":
        marca = '<span class="tag aberto">desbloqueado</span>'
    elif i.is_next:
        marca = '<span class="tag next">próximo</span>'
    deps = (f'<span class="deps" title="Depende de">↖ {", ".join(d[:3] for d in i.deps)}</span>'
            if i.deps else "")
    return (f'<li class="item {cls}" data-nnn="{i.nnn}" '
            f'data-busca="{html.escape((i.nnn + " " + i.titulo).lower(), quote=True)}">'
            f'<a class="alvo" href="#item-{i.nnn}">'
            f'<span class="id">{i.nnn}</span><span class="t">{esc(i.titulo)}</span></a>'
            f'{deps}{pr}{marca}</li>')


def pagina(titulo: str, corpo: str, live: int) -> str:
    """Casca comum. CSS embutido de propósito: `file://` não garante carregar folha externa."""
    refresh = f'<meta http-equiv="refresh" content="{live}">' if live else ""
    return ("<!doctype html>\n<html lang=\"pt-BR\"><head><meta charset=\"utf-8\">\n"
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"{refresh}<title>{titulo}</title>\n"
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
            'family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600'
            '&display=swap">\n<style>\n' + ESTILO + "\n</style></head><body>\n"
            + corpo + "\n</body></html>\n")


# ---------------------------------------------------------------- índice

def grupo(chave: str, rotulo: str, dica: str, itens, desbloq, slug, base: str,
          vazio: str = "") -> str:
    """Uma seção que nasce fechada. O que interessa está na contagem do cabeçalho."""
    if not itens and not vazio:
        return ""
    corpo = ("".join(card(i, desbloq, slug, base) for i in itens)
             or f'<li class="vazio">{vazio}</li>')
    return (f'<details class="grupo" data-grupo="{chave}">'
            f'<summary><span class="rot">{rotulo}</span>'
            f'<span class="cont">{len(itens)}</span>'
            f'<span class="dica">{dica}</span></summary>'
            f'<ul class="lista">{corpo}</ul>'
            f'<p class="sem-resultado" hidden>Nada aqui com esse filtro.</p></details>')


def render_indice(root: Path, ctx: dict, live: int) -> str:
    items, desbloq, slug = ctx["items"], ctx["desbloq"], ctx["slug"]
    base = ""
    c = {s: sum(1 for i in items if i.status == s) for s in rm.STATUSES}
    proximos = [i for i in items if i.is_next]

    grupos = (
        grupo("proximos", "🔴 Próximos", "a fila que você priorizou", proximos, desbloq, slug,
              base, vazio="Nada marcado. Priorize com <code>roadmap set NNN --next true</code>.")
        + grupo("agora", "🔓 Dá pra começar agora", "dependências todas mergeadas",
                [i for i in items if i.nnn in desbloq], desbloq, slug, base,
                vazio="Nada desbloqueado — o que está aberto já está em andamento.")
        + "".join(grupo(s, STATUS_ROTULO[s], d, [i for i in items if i.status == s],
                        desbloq, slug, base)
                  for s, d in (("em-progresso", "com PR aberto"),
                               ("backlog", "identificado, sem PR"),
                               ("concluido", "PR mergeado")))
    )

    dups, orfaos, ciclos = ctx["dups"], ctx["orfaos"], ctx["ciclos"]
    if dups or orfaos or ciclos:
        sinais = "".join(
            [f'<li class="ruim">NNN duplicado · {d[0]} em '
             f'{" e ".join(esc(x) for x in d[1])}</li>' for d in dups]
            + [f'<li class="ruim">link órfão · {o[0]} aponta pra [[{esc(o[1])}]]</li>'
               for o in orfaos]
            + [f'<li class="ruim">ciclo · {" → ".join(x)}</li>' for x in ciclos])
        problemas = len(dups) + len(orfaos) + len(ciclos)
    else:
        sinais = f'<li class="ok">Sem ciclo, órfão ou NNN repetido nos {len(items)} itens.</li>'
        problemas = 0
    sinais += ('<li class="nota">PR parado e PR aberto sem item saem do '
               '<code>roadmap sync</code>, que consulta o GitHub — o board só lê o vault.</li>')
    saude = (f'<details class="grupo{" alerta" if problemas else ""}" data-grupo="check"'
             f'{" open" if problemas else ""}>'
             f'<summary><span class="rot">Consistência do vault</span>'
             f'<span class="cont">{problemas}</span>'
             f'<span class="dica">{"precisa de atenção" if problemas else "tudo certo"}</span>'
             f'</summary><ul>{sinais}</ul></details>')

    dados = {i.nnn: {
        "t": i.titulo, "c": classe(i, desbloq), "s": STATUS_ROTULO[i.status],
        "pr": i.pr.lstrip("#"), "n": i.is_next,
        "d": [t.nnn for d in i.deps if (t := rm.resolve(items, d))],
        "l": [x.nnn for x in ctx["destrava"][i.nnn]],
    } for i in items}

    fichas = "".join(ficha(i, root, ctx) for i in items)
    tem_changes = any((root / "thoughts" / "changes").glob("[0-9]*/"))
    aba_changes = ('<a class="aba" href="changes.html">Changes</a>' if tem_changes else "")

    metricas = [("Desbloqueados", len(desbloq), "aberto"), ("Próximos", len(proximos), "next"),
                ("Em progresso", c["em-progresso"], "andando"),
                ("Backlog", c["backlog"], "travado"), ("Concluído", c["concluido"], "feito")]
    tiles = "".join(f'<div class="tile {k}"><span class="n">{v}</span>'
                    f'<span class="l">{rot}</span></div>' for rot, v, k in metricas)

    corpo = f"""<div class="wrap">
  <nav class="abas" aria-label="Views">
    <span class="aba ativa">Roadmap</span>{aba_changes}
  </nav>

  <header>
    <h1>Roadmap <span>· {esc(root.name)}</span></h1>
    <p class="meta">{len(items)} ITENS · GERADO EM {ctx["gerado"]}</p>
  </header>

  <div class="tiles">{tiles}</div>

  <div class="busca">
    <input type="search" id="q" placeholder="Filtrar por número ou título…"
           aria-label="Filtrar itens" autocomplete="off">
  </div>

  <div class="grupos">{grupos}{saude}</div>

  <footer>
    Clique num item pra abrir a ficha: o corpo, a vizinhança no grafo, e o que ele destrava.
    Dentro dela, clicar em outro item troca a ficha.<br>
    Espelho gerado de <code>thoughts/roadmap/</code>: a fonte da verdade é a pasta, editar aqui
    não muda nada lá. Regenera sozinho a cada mutação do <code>roadmap</code>.
  </footer>
</div>

<div id="painel" hidden>
  <div class="gaveta" role="dialog" aria-modal="true">{fichas}</div>
</div>
<script>
var DADOS = {json.dumps(dados, ensure_ascii=False, separators=(',', ':'))};
{JS_INDICE}
</script>"""
    return pagina(f"Roadmap · {esc(root.name)}", corpo, live)


# ---------------------------------------------------------------- ficha do item

def ficha(item, root: Path, ctx: dict) -> str:
    """O conteúdo do item, pronto no HTML. Só o grafo é desenhado na hora, pelo JS."""
    items, desbloq, slug = ctx["items"], ctx["desbloq"], ctx["slug"]
    cls = classe(item, desbloq)
    deps = [t for d in item.deps if (t := rm.resolve(items, d))]
    libera = ctx["destrava"][item.nnn]
    link_pr = href_pr(item, slug)

    meta = [("Status", STATUS_ROTULO[item.status]), ("Criado", item.fm.get("criado", "—"))]
    if item.pr:
        n = esc(item.pr.lstrip("#"))
        meta.append(("PR", f'<a href="{link_pr}" target="_blank" rel="noopener">#{n}</a>'
                     if link_pr else f"#{n}"))
    if item.fm.get("change"):
        meta.append(("Mudança", esc(item.fm["change"])))
    if item.is_next:
        meta.append(("Fila", "🔴 próximo"))
    grade = "".join(f"<div><dt>{r}</dt><dd>{v}</dd></div>" for r, v in meta)

    def bloco(titulo, lista, vazio):
        if not lista:
            return f'<h4>{titulo}</h4><p class="vazio">{vazio}</p>'
        li = "".join(f'<li class="item {classe(x, desbloq)}">'
                     f'<a class="alvo" href="#item-{x.nnn}" data-ir="{x.nnn}">'
                     f'<span class="id">{x.nnn}</span><span class="t">{esc(x.titulo)}</span></a>'
                     f'<span class="tag {classe(x, desbloq)}">'
                     f'{CLASSE_ROTULO[classe(x, desbloq)]}</span></li>' for x in lista)
        return f'<h4>{titulo}</h4><ul>{li}</ul>'

    corpo_md = markdown(item.body, items, root, "") or \
        '<p class="vazio">Sem corpo — só o título.</p>'
    caminho = esc(str(item.path.resolve()))
    cmd = f'roadmap set {item.nnn} --next {"false" if item.is_next else "true"}'
    rot_cmd = "tirar dos próximos" if item.is_next else "marcar como próximo"

    return (f'<article class="ficha" id="item-{item.nnn}" data-nnn="{item.nnn}" tabindex="-1">'
            f'<div class="ficha-topo">'
            f'<button class="voltar" data-voltar hidden></button>'
            f'<span class="id grande">{item.nnn}</span>'
            f'<span class="tag {cls}">{CLASSE_ROTULO[cls]}</span>'
            f'<button class="fechar" data-fechar-ficha aria-label="Fechar">×</button></div>'
            f'<h3>{esc(item.titulo)}</h3>'
            f'<dl class="meta-grade">{grade}</dl>'
            f'<h4>Vizinhança</h4><div class="viz" data-viz="{item.nnn}"></div>'
            f'<div class="ficha-baixo">'
            f'<div><div class="corpo">{corpo_md}</div></div>'
            f'<aside class="lado">'
            f'{bloco("Depende de", deps, "Não espera por ninguém.")}'
            f'{bloco("Destrava", libera, "Ninguém espera por este item.")}'
            f'<div class="acoes">'
            f'<a class="botao" href="{href_obsidian(item.path)}">Editar no Obsidian</a>'
            + (f'<a class="botao secundario" href="{link_pr}" target="_blank" '
               f'rel="noopener">Ver PR</a>' if link_pr else "")
            + f'<button class="botao secundario" data-cmd="{cmd}">Copiar: {rot_cmd}</button>'
              f'<button class="botao secundario" data-cmd="{caminho}">Copiar caminho</button>'
              f'</div><p class="caminho"><code>{caminho}</code></p>'
              f'</aside></div>'
              f'</article>')


# ---------------------------------------------------------------- escrita

def escrever(root: Path, live: int = 0) -> list[Path]:
    """Escreve o índice e uma página por item. Devolve tudo que foi escrito."""
    items = rm.load_items(root)
    if not items:
        rm.die("vault vazio — nada pra desenhar")

    destrava: dict[str, list] = {i.nnn: [] for i in items}  # o grafo invertido: os backlinks
    for i in items:
        for d in i.deps:
            if (t := rm.resolve(items, d)) is not None:
                destrava[t.nnn].append(i)

    ctx = {
        "items": items,
        "desbloq": {i.nnn for i in rm.unblocked(items)},
        "slug": repo_slug(root),
        "destrava": destrava,
        "dups": rm.duplicados(items),
        "orfaos": rm.orphans(items),
        "ciclos": rm.cycles(items),
        "gerado": rm.date.today().strftime("%d-%m-%Y"),
    }

    base = board_root(root)
    base.mkdir(parents=True, exist_ok=True)
    alvo = base / BOARD_NAME
    alvo.write_text(render_indice(root, ctx, live), encoding="utf-8")
    return [alvo]


def render(root: Path, live: int = 0) -> str:
    """Compatibilidade: devolve o índice como texto, sem escrever nada."""
    items = rm.load_items(root)
    destrava: dict[str, list] = {i.nnn: [] for i in items}
    for i in items:
        for d in i.deps:
            if (t := rm.resolve(items, d)) is not None:
                destrava[t.nnn].append(i)
    return render_indice(root, {
        "items": items, "desbloq": {i.nnn for i in rm.unblocked(items)},
        "slug": repo_slug(root), "destrava": destrava, "dups": rm.duplicados(items),
        "orfaos": rm.orphans(items), "ciclos": rm.cycles(items),
        "gerado": rm.date.today().strftime("%d-%m-%Y")}, live)


# ---------------------------------------------------------------- estilo e script

ESTILO = """
:root {
  color-scheme:light dark;
  --ground:#eceff4; --surface:#fbfcfd; --ink:#111a24; --muted:#65788c; --rule:#cdd7e2;
  --linha-fraca:#a9b8c9; --quente:#c8501f; --quente-fraca:#f7e6dd;
  --ativo:#2b6cb0; --ativo-fraca:#dde8f4; --feito:#8496a8; --feito-fraca:#e4e9ef;
  --sombra:0 1px 2px rgba(17,26,36,.06), 0 8px 24px -18px rgba(17,26,36,.4);
  --veu:rgba(17,26,36,.34);
  --t-feito:#2f7d5b; --t-feito-bg:#dcefe5;
  --t-travado:#6a5f86; --t-travado-bg:#e7e3f0;
  --t-next:#a83545; --t-next-bg:#f6dfe3;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ground:#0d1319; --surface:#141c25; --ink:#e6edf4; --muted:#8ba0b5; --rule:#26323f;
    --linha-fraca:#31404f; --quente:#f0794a; --quente-fraca:#3a2117;
    --ativo:#63a2e0; --ativo-fraca:#1b2c3d; --feito:#5f7488; --feito-fraca:#1b242e;
    --sombra:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -18px rgba(0,0,0,.9);
    --veu:rgba(0,0,0,.6);
    --t-feito:#5cb98c; --t-feito-bg:#152a20;
    --t-travado:#a99bcc; --t-travado-bg:#241f31;
    --t-next:#e8828f; --t-next-bg:#33191e;
  }
}
* { box-sizing:border-box; }
body {
  background:var(--ground); color:var(--ink); margin:0;
  font:400 15px/1.55 Archivo, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap { max-width:1180px; margin:0 auto; padding:40px 24px 64px;
  display:flex; flex-direction:column; gap:26px; }
.item-pagina { max-width:760px; gap:0; }
header { display:flex; align-items:baseline; justify-content:space-between; gap:16px;
  flex-wrap:wrap; border-bottom:1px solid var(--rule); padding-bottom:18px; }
h1 { font-size:26px; font-weight:700; letter-spacing:-.015em; margin:0; text-wrap:balance; }
h1 span { color:var(--muted); font-weight:500; }
.meta { font:500 12px/1 "IBM Plex Mono", ui-monospace, monospace; color:var(--muted);
  letter-spacing:.04em; margin:0; }

.abas { display:flex; gap:4px; border-bottom:1px solid var(--rule); margin-bottom:-14px; }
.aba { font:600 12px Archivo, sans-serif; text-transform:uppercase; letter-spacing:.08em;
  padding:8px 14px; color:var(--muted); text-decoration:none; border-bottom:2px solid transparent;
  margin-bottom:-1px; }
.aba:hover { color:var(--ink); }
.aba.ativa { color:var(--quente); border-bottom-color:var(--quente); }
.trilha { font-size:13px; margin-bottom:22px; display:flex; gap:9px; align-items:center; }
.trilha a { color:var(--ativo); text-decoration:none; font-weight:500; }
.trilha a:hover { text-decoration:underline; }
.trilha .sep, .trilha .atual { color:var(--muted); }
.cabeca { display:block; border:0; padding:0; margin-bottom:20px; }
.cabeca h1 { font-size:30px; margin-top:12px; }
.ficha-topo { display:flex; align-items:center; gap:10px; }
.id.grande { font-size:14px; }

.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(132px,1fr)); gap:10px; }
.tile { background:var(--surface); border:1px solid var(--rule); border-top:2px solid var(--rule);
  border-radius:4px; padding:14px 16px; display:flex; flex-direction:column; gap:2px; }
.tile .n { font:600 28px/1 "IBM Plex Mono", ui-monospace, monospace;
  font-variant-numeric:tabular-nums; }
.tile .l { font-size:11px; text-transform:uppercase; letter-spacing:.09em; color:var(--muted);
  font-weight:600; }
.tile.aberto { border-top-color:var(--quente); } .tile.aberto .n { color:var(--quente); }
.tile.andando { border-top-color:var(--ativo); } .tile.andando .n { color:var(--ativo); }
.tile.feito .n, .tile.travado .n, .tile.next .n { color:var(--muted); }

.busca { position:relative; }
.busca input { width:100%; font:400 14px Archivo, sans-serif; color:var(--ink);
  background:var(--surface); border:1px solid var(--rule); border-radius:4px;
  padding:11px 14px 11px 36px; }
.busca input:focus { outline:2px solid var(--quente); outline-offset:1px;
  border-color:transparent; }
.busca::before { content:"⌕"; position:absolute; left:13px; top:9px; font-size:17px;
  color:var(--muted); }

.grafo { background:var(--surface); border:1px solid var(--rule); border-radius:4px;
  box-shadow:var(--sombra); padding:4px; overflow-x:auto; }
.mini-grafo { margin-bottom:8px; box-shadow:none; }
.correntes { display:grid; grid-template-columns:repeat(auto-fill,minmax(430px,1fr)); gap:16px;
  align-items:start; }
.corrente { display:flex; flex-direction:column; gap:7px; min-width:0; }
.corrente.larga { grid-column:1 / -1; }
.corrente-topo { display:flex; align-items:center; gap:9px; padding-left:2px; }
.quantos { font:600 11px "IBM Plex Mono", ui-monospace, monospace; color:var(--muted);
  text-transform:uppercase; letter-spacing:.07em; }
.nota-grafo { font-size:12.5px; color:var(--muted); margin:12px 0 0; }
.grupos { display:flex; flex-direction:column; gap:8px; }
.grupo { background:var(--surface); border:1px solid var(--rule); border-radius:4px; }
.grupo summary { display:flex; align-items:center; gap:10px; padding:14px 18px; cursor:pointer;
  list-style:none; border-radius:4px; }
.grupo summary::-webkit-details-marker { display:none; }
.grupo summary::before { content:"▸"; color:var(--muted); font-size:11px;
  transition:transform .12s; display:inline-block; }
.grupo[open] summary::before { transform:rotate(90deg); }
.grupo summary:hover { background:var(--ground); }
.grupo summary:focus-visible { outline:2px solid var(--quente); outline-offset:-2px; }
.grupo .rot { font-size:13.5px; font-weight:600; }
.grupo .cont { font:600 11px "IBM Plex Mono", ui-monospace, monospace; color:var(--muted);
  border:1px solid var(--rule); border-radius:99px; padding:1px 8px;
  font-variant-numeric:tabular-nums; }
.grupo .dica { font-size:12px; color:var(--muted); margin-left:auto; }
.grupo .lista, .grupo ul { padding:4px 18px 18px; }
.grupo .sem-resultado { padding:0 18px 16px; margin:0; }
.grupo.alerta { border-color:var(--quente); }
.grupo.alerta .cont { color:var(--quente); border-color:var(--quente); }

#painel { position:fixed; inset:0; z-index:30; background:var(--veu);
  display:flex; justify-content:flex-end; }
#painel[hidden] { display:none; }
.gaveta { width:calc(100% - 56px); height:100%; background:var(--surface);
  border-left:1px solid var(--rule); box-shadow:-20px 0 60px -30px rgba(0,0,0,.6);
  display:flex; flex-direction:column; }
@media (max-width:720px) { .gaveta { width:calc(100% - 16px); } }
.ficha { display:none; }
.ficha.ativa { display:block; overflow-y:auto; height:100%; padding:28px 40px 56px;
  outline:none; animation:entra .16s ease-out; }
.ficha-baixo { display:grid; grid-template-columns:minmax(0,1.7fr) minmax(260px,1fr);
  gap:38px; align-items:start; margin-top:26px; }
@media (max-width:900px) { .ficha-baixo { grid-template-columns:1fr; gap:0; } }
.ficha-baixo .corpo { max-width:68ch; }
.ficha-baixo h4:first-child { margin-top:0; }
.lado { border-left:1px solid var(--rule); padding-left:26px; }
@media (max-width:900px) { .lado { border-left:0; padding-left:0; } }
@keyframes entra { from { transform:translateX(16px); opacity:.5; } }
.ficha-topo { display:flex; align-items:center; gap:10px; margin-bottom:12px; }
.voltar { font:600 12px "IBM Plex Mono", ui-monospace, monospace; color:var(--ativo);
  background:var(--ativo-fraca); border:0; border-radius:99px; padding:4px 11px;
  cursor:pointer; }
.voltar:hover { filter:brightness(.96); }
.voltar[hidden] { display:none; }
.ficha h3 { font-size:24px; margin:0 0 18px; letter-spacing:-.015em; text-wrap:balance; }
.ficha h4 { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted);
  margin:28px 0 10px; }
.ficha .grafo { box-shadow:none; margin:0; }
.viz { display:flex; flex-direction:column; gap:10px; }
.legenda-popup { font-size:11.5px; color:var(--muted); margin:0; }
.acoes { display:flex; gap:8px; margin-top:26px; flex-wrap:wrap; }
.lado .acoes .botao { flex:1 1 auto; text-align:center; }
.fechar { background:none; border:0; color:var(--muted); font-size:20px; line-height:1;
  cursor:pointer; padding:2px 6px; border-radius:3px; margin-left:auto; }
.fechar:hover { background:var(--ground); color:var(--ink); }
.foco-vazio { color:var(--muted); font-size:13.5px; line-height:1.6; margin:14px 0 0; }
.foco-resumo { font-size:13px; color:var(--muted); margin:0; }
.no[data-ir] { cursor:pointer; }
.no[data-ir]:hover rect { stroke-width:2.5; stroke-dasharray:none; }
.no.foco rect { stroke:var(--ink); stroke-width:2.5; stroke-dasharray:none; }
.grafo svg { display:block; }
.aresta { fill:none; stroke-width:1.5; }
.aresta.presa { stroke:var(--linha-fraca); stroke-dasharray:3 4; }
.aresta.solta { stroke:var(--quente); }
.ponta { fill:var(--linha-fraca); } .ponta-viva { fill:var(--quente); }
.no a { cursor:pointer; }
.no rect { fill:var(--surface); stroke:var(--rule); stroke-width:1.5;
  transition:stroke-width .12s, filter .12s; }
.no .nnn { font:600 11px "IBM Plex Mono", ui-monospace, monospace; fill:var(--muted);
  letter-spacing:.06em; }
.no .pr { font:500 11px "IBM Plex Mono", ui-monospace, monospace; fill:var(--muted); }
.no .rot { font:500 12.5px Archivo, sans-serif; fill:var(--ink); }
.no .pin { fill:var(--quente); }
.no.travado rect { fill:none; stroke-dasharray:4 3; }
.no.travado .rot { fill:var(--muted); }
.no.feito rect { fill:var(--feito-fraca); stroke:var(--feito-fraca); }
.no.feito .rot, .no.feito .nnn, .no.feito .pr { fill:var(--feito); }
.no.andando rect { fill:var(--ativo-fraca); stroke:var(--ativo); }
.no.andando .nnn, .no.andando .pr { fill:var(--ativo); }
.no.aberto rect { fill:var(--quente-fraca); stroke:var(--quente); stroke-width:2; }
.no.aberto .nnn, .no.aberto .pr { fill:var(--quente); }
.no.foco rect { stroke:var(--ink); stroke-width:2.5; stroke-dasharray:none; }
.no a:hover rect, .no a:focus-visible rect { stroke-width:2.5; stroke-dasharray:none;
  filter:drop-shadow(0 2px 6px rgba(17,26,36,.16)); }
.no a:focus-visible { outline:none; }
.no.apagado, .no.filtrado { opacity:.22; }
.no.vizinho rect { stroke-width:2.5; }
.aresta.apagada { opacity:.12; }

.legenda { display:flex; gap:20px; flex-wrap:wrap; font-size:12px; color:var(--muted);
  align-items:center; margin-top:-14px; }
.legenda i { width:20px; height:11px; border-radius:2px; display:inline-block;
  vertical-align:-1px; margin-right:6px; border:1.5px solid var(--rule); }
.legenda .l-aberto { background:var(--quente-fraca); border-color:var(--quente); }
.legenda .l-andando { background:var(--ativo-fraca); border-color:var(--ativo); }
.legenda .l-feito { background:var(--feito-fraca); border-color:var(--feito-fraca); }
.legenda .l-travado { background:none; border-style:dashed; }

section { background:var(--surface); border:1px solid var(--rule); border-radius:4px;
  padding:20px 22px; }
h2 { font-size:12px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted);
  margin:0 0 14px; font-weight:700; display:flex; align-items:center; gap:8px; }
h2 .cont { font:600 11px "IBM Plex Mono", ui-monospace, monospace; color:var(--muted);
  border:1px solid var(--rule); border-radius:99px; padding:1px 7px; letter-spacing:0; }
h4 { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted);
  margin:30px 0 10px; }
.destaque { border-left:3px solid var(--quente); }
.colunas { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
  gap:20px; align-items:start; }
ul { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:4px; }
.item { display:flex; align-items:baseline; gap:9px; flex-wrap:wrap;
  border-radius:3px; padding:5px 8px; margin:0 -8px; transition:background .12s; }
.item:hover { background:var(--ground); }
.item[hidden] { display:none; }
.item-pagina .item:hover { background:var(--surface); }
.alvo { display:flex; align-items:baseline; gap:9px; flex:1; min-width:0;
  color:inherit; text-decoration:none; }
.alvo:hover .t { text-decoration:underline; text-underline-offset:2px; }
.alvo:focus-visible { outline:2px solid var(--quente); outline-offset:3px; border-radius:2px; }
.id { font:600 12px "IBM Plex Mono", ui-monospace, monospace; color:var(--muted);
  font-variant-numeric:tabular-nums; }
.t { flex:1; min-width:0; font-size:14px; }
.item.travado .t { color:var(--muted); }
.item.feito .t, .item.feito .id { color:var(--feito); }
.item.aberto .id { color:var(--quente); }
.item.andando .id { color:var(--ativo); }
.deps { font:500 11px "IBM Plex Mono", ui-monospace, monospace; color:var(--muted);
  white-space:nowrap; }
.pr-tag { font:500 11px "IBM Plex Mono", ui-monospace, monospace; color:var(--muted);
  text-decoration:none; }
a.pr-tag:hover { color:var(--ativo); text-decoration:underline; }
.tag { font-size:10px; text-transform:uppercase; letter-spacing:.07em; font-weight:700;
  padding:2px 7px; border-radius:99px; white-space:nowrap; }
.tag.aberto { color:var(--quente); background:var(--quente-fraca); }
.tag.andando { color:var(--ativo); background:var(--ativo-fraca); }
.tag.feito { color:var(--t-feito); background:var(--t-feito-bg); }
.tag.travado { color:var(--t-travado); background:var(--t-travado-bg); }
.tag.next { color:var(--t-next); background:var(--t-next-bg); }
li.ok { color:var(--muted); } li.ruim { color:var(--quente); font-weight:500; }
li.nota, li.vazio, .vazio, .sem-resultado { color:var(--muted); font-size:13px; line-height:1.5; }
code { font:500 12px "IBM Plex Mono", ui-monospace, monospace; background:var(--ground);
  padding:1px 5px; border-radius:3px; }
footer { font-size:12.5px; color:var(--muted); border-top:1px solid var(--rule);
  padding-top:16px; margin-top:36px; line-height:1.6; }

.meta-grade { display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:14px;
  margin:0 0 24px; padding:16px 0; border-top:1px solid var(--rule);
  border-bottom:1px solid var(--rule); }
.meta-grade dt { font-size:10px; text-transform:uppercase; letter-spacing:.08em;
  color:var(--muted); font-weight:700; margin-bottom:4px; }
.meta-grade dd { margin:0; font:500 13px "IBM Plex Mono", ui-monospace, monospace; }
.meta-grade a { color:var(--ativo); }
.corpo { font-size:15.5px; line-height:1.65; }
.corpo p { margin:0 0 13px; }
.corpo p.campo { margin:0 0 5px; font-size:14px; }
.corpo p.campo + p:not(.campo) { margin-top:16px; }
.corpo ul { display:block; margin:0 0 13px; padding-left:20px; }
.corpo li { display:list-item; list-style:disc; margin-bottom:5px; }
.corpo ol { display:block; margin:0 0 13px; padding-left:22px; }
.corpo ol > li { list-style:decimal; }
.corpo ul ul, .corpo ol ol, .corpo ul ol, .corpo ol ul { margin:5px 0 0; }
.corpo ul ul > li { list-style:circle; }
.corpo hr { border:0; border-top:1px solid var(--rule); margin:22px 0; }
.tabela { overflow-x:auto; margin:0 0 16px; }
.tabela table { border-collapse:collapse; width:100%; font-size:13.5px; }
.tabela th { text-align:left; font-size:10.5px; text-transform:uppercase; letter-spacing:.07em;
  color:var(--muted); font-weight:700; padding:8px 12px; border-bottom:1.5px solid var(--rule);
  white-space:nowrap; }
.tabela td { padding:9px 12px; border-bottom:1px solid var(--rule); vertical-align:top;
  line-height:1.5; }
.tabela tr:last-child td { border-bottom:0; }
.tabela tbody tr:hover { background:var(--ground); }
.corpo blockquote { margin:0 0 13px; padding:2px 0 2px 14px; border-left:2px solid var(--rule);
  color:var(--muted); }
.corpo pre { background:var(--surface); border:1px solid var(--rule); padding:13px 15px;
  border-radius:4px; overflow-x:auto; font-size:13px; }
.corpo pre code { background:none; padding:0; }
.wiki { color:var(--ativo); text-decoration:none; border-bottom:1px solid transparent; }
.wiki:hover { border-bottom-color:currentColor; }
.wiki-morto { color:var(--muted); text-decoration:line-through; }

.acoes { display:flex; gap:10px; margin-top:32px; flex-wrap:wrap; align-items:center; }
.botao { font:600 13px Archivo, sans-serif; text-decoration:none; padding:9px 16px;
  border-radius:4px; background:var(--quente); color:#fff; border:0; cursor:pointer; }
.botao.secundario { background:none; color:var(--ink); border:1px solid var(--rule); }
.botao:hover { filter:brightness(1.08); }
.botao.secundario:hover { background:var(--surface); }
.caminho { margin:12px 0 0; font-size:12px; color:var(--muted); word-break:break-all; }
/* --- view de changes: requisito, decisão, tarefa e as abas da ficha --- */
.prog { display:flex; align-items:center; gap:7px; white-space:nowrap; }
.trilho { width:52px; height:5px; border-radius:99px; background:var(--rule); overflow:hidden; }
.cheio { display:block; height:100%; background:var(--t-feito); border-radius:99px; }
.frac { font:600 11px "IBM Plex Mono", ui-monospace, monospace; color:var(--muted);
  font-variant-numeric:tabular-nums; }
.vazio-prog { font-size:11px; color:var(--muted); }
.falta { font-size:10px; text-transform:uppercase; letter-spacing:.06em; color:var(--t-next);
  background:var(--t-next-bg); padding:2px 7px; border-radius:99px; white-space:nowrap; }

.chips { display:flex; gap:6px; flex-wrap:wrap; border-bottom:1px solid var(--rule);
  margin:24px 0 20px; }
.chip { font:600 12px Archivo, sans-serif; background:none; border:0; cursor:pointer;
  color:var(--muted); padding:9px 14px; border-bottom:2px solid transparent; margin-bottom:-1px;
  display:flex; align-items:center; gap:7px; }
.chip:hover { color:var(--ink); }
.chip.on { color:var(--quente); border-bottom-color:var(--quente); }
.chip-n { font:600 10px "IBM Plex Mono", ui-monospace, monospace; background:var(--ground);
  border-radius:99px; padding:1px 6px; }
.tela { display:none; }
.tela.on { display:block; }

.lead { font-size:16px; line-height:1.6; margin:0 0 12px; }
.fora { font-size:13.5px; color:var(--muted); margin:0 0 22px; padding:10px 14px;
  background:var(--ground); border-radius:4px; }
.req { padding:16px 0; border-top:1px solid var(--rule); }
.req-topo { display:flex; align-items:baseline; gap:9px; flex-wrap:wrap; }
.req-id { font:700 12px "IBM Plex Mono", ui-monospace, monospace; color:var(--quente); }
.req-tipo { font:600 10px "IBM Plex Mono", ui-monospace, monospace; text-transform:uppercase;
  letter-spacing:.05em; color:var(--ativo); background:var(--ativo-fraca); padding:2px 7px;
  border-radius:99px; }
.req h5 { font-size:15.5px; margin:0; font-weight:600; flex:1 1 260px; }
.req-regra { font-size:14px; margin:9px 0 0; max-width:72ch; }
.cenarios { margin:12px 0 0; display:flex; flex-direction:column; gap:8px; }
.cenarios li { display:grid; grid-template-columns:minmax(120px,190px) 1fr; gap:14px;
  font-size:13.5px; align-items:baseline; }
@media (max-width:760px) { .cenarios li { grid-template-columns:1fr; gap:2px; } }
.cen-nome { font-weight:600; }
.cen-txt { color:var(--muted); line-height:1.55; }

.sub { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted);
  margin:24px 0 10px; }
.decisoes { display:flex; flex-direction:column; gap:9px; margin:0; padding:0; }
.decisoes li { display:flex; gap:11px; font-size:14px; align-items:baseline; }
.dec-id { font:700 11px "IBM Plex Mono", ui-monospace, monospace; color:var(--ativo);
  background:var(--ativo-fraca); padding:2px 7px; border-radius:3px; }

.pr-bloco { margin-bottom:26px; }
.pr-topo { display:flex; align-items:center; gap:12px; flex-wrap:wrap;
  border-bottom:1px solid var(--rule); padding-bottom:8px; }
.pr-topo h5 { font-size:14px; margin:0; font-weight:600; flex:1 1 auto; }
.pr-nota { font-size:12.5px; color:var(--muted); margin:8px 0 0; }
.tarefas { margin-top:12px; gap:10px; }
.tarefa { display:flex; gap:11px; align-items:flex-start; font-size:13.5px; }
.caixa { width:16px; height:16px; border:1.5px solid var(--rule); border-radius:3px; flex:none;
  margin-top:2px; font-size:11px; line-height:14px; text-align:center; color:var(--t-feito); }
.tarefa.ok .caixa { background:var(--t-feito-bg); border-color:var(--t-feito); }
.tarefa.ok .t-txt { color:var(--muted); }
.tarefa.movida .caixa { color:var(--muted); border-style:dashed; }
.tarefa.movida .t-txt, .tarefa.movida .t-id { color:var(--muted); text-decoration:line-through; }
.t-corpo { display:flex; flex-wrap:wrap; gap:6px 9px; align-items:baseline; }
.t-id { font:700 11px "IBM Plex Mono", ui-monospace, monospace; color:var(--muted); }
.t-req { font:600 10px "IBM Plex Mono", ui-monospace, monospace; color:var(--quente);
  background:var(--quente-fraca); padding:1px 6px; border-radius:99px; }
.t-txt { flex:1 1 260px; line-height:1.5; }
.t-det { flex:1 1 100%; font-size:12.5px; color:var(--muted); line-height:1.55; }
.nota { border:1px solid var(--rule); border-radius:4px; margin-bottom:8px; }
.nota summary { padding:11px 15px; cursor:pointer; font-size:13px; font-weight:600; }
.nota summary:hover { background:var(--ground); }
.nota .corpo { padding:0 15px 15px; }
.acoes-rot { font-size:12px; color:var(--muted); align-self:center; margin-right:2px; }

@media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
"""

JS_INDICE = """
(function () {
  var NS = 'http://www.w3.org/2000/svg';
  var LARG = 208, ALT = 62, GX = 88, GY = 18, PAD = 28;
  var q = document.getElementById('q');
  var painel = document.getElementById('painel');
  var voltarFoco = null;
  var pilha = [];          // por onde passei até aqui — clicar em dependência afunda rápido
  var atual = null;

  function el(nome, attrs, texto) {
    var n = document.createElementNS(NS, nome);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (texto != null) n.textContent = texto;
    return n;
  }

  function quebrar(txt, max) {
    var linhas = [], atual = '';
    txt.split(' ').forEach(function (p) {
      if ((atual + ' ' + p).trim().length > max) { if (atual) linhas.push(atual); atual = p; }
      else atual = (atual + ' ' + p).trim();
    });
    if (atual) linhas.push(atual);
    if (linhas.length > 2) { linhas = linhas.slice(0, 2); linhas[1] = linhas[1].slice(0, 23) + '…'; }
    return linhas;
  }

  function no(svg, nnn, x, y, central) {
    var d = DADOS[nnn];
    var g = el('g', { class: 'no ' + d.c + (central ? ' foco' : ''), 'data-ir': nnn });
    g.appendChild(el('title', {}, d.t + (central ? '' : ' — clique pra abrir este')));
    g.appendChild(el('rect', { x: x, y: y, width: LARG, height: ALT, rx: 3 }));
    g.appendChild(el('text', { class: 'nnn', x: x + 12, y: y + 21 }, nnn));
    if (d.pr) g.appendChild(el('text',
      { class: 'pr', x: x + LARG - 12, y: y + 21, 'text-anchor': 'end' }, '#' + d.pr));
    quebrar(d.t, 26).forEach(function (ln, k) {
      g.appendChild(el('text', { class: 'rot', x: x + 12, y: y + 39 + k * 14 }, ln));
    });
    svg.appendChild(g);
  }

  function aresta(svg, x1, y1, x2, y2, viva) {
    var c = (x2 - x1) * 0.5;
    svg.appendChild(el('path', {
      d: 'M' + x1 + ' ' + y1 + ' C' + (x1 + c) + ' ' + y1 + ' ' + (x2 - c) + ' ' + y2 +
         ' ' + x2 + ' ' + y2,
      class: 'aresta ' + (viva ? 'solta' : 'presa'),
      'marker-end': 'url(#' + (viva ? 'seta-viva' : 'seta') + ')'
    }));
  }

  function desenhar(caixa, nnn) {
    var d = DADOS[nnn];
    caixa.innerHTML = '';
    var presos = d.d.filter(function (x) { return DADOS[x].c !== 'feito'; });
    var resumo = document.createElement('p');
    resumo.className = 'foco-resumo';
    resumo.textContent = d.d.length
      ? ('espera por ' + d.d.length + (presos.length
          ? ' — ' + presos.length + ' ainda em aberto (' + presos.join(', ') + ')'
          : ' — todas concluídas') + ' · destrava ' + d.l.length)
      : ('não espera por ninguém · destrava ' + d.l.length);
    caixa.appendChild(resumo);

    if (!d.d.length && !d.l.length) {
      var p = document.createElement('p');
      p.className = 'vazio';
      p.textContent = 'Sem dependência nos dois sentidos. Pra ligar: roadmap dep ' + nnn +
        ' --on MMM';
      caixa.appendChild(p);
      return;
    }
    var col = Math.max(d.d.length, 1, d.l.length);
    var temEsq = d.d.length > 0, temDir = d.l.length > 0;
    var cols = 1 + (temEsq ? 1 : 0) + (temDir ? 1 : 0);
    var w = PAD * 2 + cols * LARG + (cols - 1) * GX;
    var h = PAD * 2 + col * ALT + (col - 1) * GY;
    var svg = el('svg', { viewBox: '0 0 ' + w + ' ' + h, width: w, height: h });
    var defs = el('defs', {});
    [['seta', 'ponta'], ['seta-viva', 'ponta-viva']].forEach(function (m) {
      var mk = el('marker', { id: m[0], viewBox: '0 0 8 8', refX: 7, refY: 4,
        markerWidth: 6, markerHeight: 6, orient: 'auto' });
      mk.appendChild(el('path', { d: 'M0 0 L8 4 L0 8 z', class: m[1] }));
      defs.appendChild(mk);
    });
    svg.appendChild(defs);

    var xEsq = PAD, xC = PAD + (temEsq ? LARG + GX : 0), xDir = xC + LARG + GX;
    function ypos(k, total) { return PAD + (col - total) * (ALT + GY) / 2 + k * (ALT + GY); }
    var yc = ypos(0, 1);
    d.d.forEach(function (x, k) {
      aresta(svg, xEsq + LARG, ypos(k, d.d.length) + ALT / 2, xC, yc + ALT / 2,
             DADOS[x].c === 'feito');
    });
    d.l.forEach(function (x, k) {
      aresta(svg, xC + LARG, yc + ALT / 2, xDir, ypos(k, d.l.length) + ALT / 2, d.c === 'feito');
    });
    d.d.forEach(function (x, k) { no(svg, x, xEsq, ypos(k, d.d.length)); });
    d.l.forEach(function (x, k) { no(svg, x, xDir, ypos(k, d.l.length)); });
    no(svg, nnn, xC, yc, true);

    var box = document.createElement('div');
    box.className = 'grafo';
    box.appendChild(svg);
    caixa.appendChild(box);
    var leg = document.createElement('p');
    leg.className = 'legenda-popup';
    leg.textContent = 'seta cheia = dependência já mergeada · tracejada = ainda trava · ' +
      'clique num card pra abrir aquele item';
    caixa.appendChild(leg);
  }

  function abrir(nnn, comoVim) {
    var alvo = painel.querySelector('.ficha[data-nnn="' + nnn + '"]');
    if (!alvo) return;
    if (comoVim === 'trilha' && atual && atual !== nnn) pilha.push(atual);
    else if (comoVim !== 'volta') pilha = [];        // entrada nova pela lista: trilha zerada
    atual = nnn;

    painel.querySelectorAll('.ficha.ativa').forEach(function (f) { f.classList.remove('ativa'); });
    alvo.classList.add('ativa');
    painel.hidden = false;

    var b = alvo.querySelector('[data-voltar]');
    if (b) {
      b.hidden = pilha.length === 0;
      if (pilha.length) {
        var de = pilha[pilha.length - 1];
        b.textContent = '← ' + de;
        b.setAttribute('title', 'Voltar para ' + de + ' — ' + DADOS[de].t);
      }
    }
    desenhar(alvo.querySelector('.viz'), nnn);
    alvo.scrollTop = 0;
    alvo.focus({ preventScroll: true });
    try { history.replaceState(null, '', '#item-' + nnn); } catch (_) {}
  }

  function voltar() {
    if (!pilha.length) return;
    abrir(pilha.pop(), 'volta');
  }

  function fechar() {
    painel.hidden = true;
    pilha = [];
    atual = null;
    painel.querySelectorAll('.ficha.ativa').forEach(function (f) { f.classList.remove('ativa'); });
    try { history.replaceState(null, '', location.pathname + location.search); } catch (_) {}
    if (voltarFoco) { voltarFoco.focus(); voltarFoco = null; }
  }

  function copiar(b) {
    var txt = b.getAttribute('data-cmd'), antes = b.textContent;
    function ok() { b.textContent = 'Copiado'; setTimeout(function () { b.textContent = antes; }, 1400); }
    if (navigator.clipboard) { navigator.clipboard.writeText(txt).then(ok, manual); } else manual();
    function manual() {
      var c = document.createElement('textarea');
      c.value = txt; document.body.appendChild(c); c.select();
      try { document.execCommand('copy'); ok(); } catch (_) { b.textContent = 'Ctrl+C: ' + txt; }
      setTimeout(function () { c.remove(); }, 100);
    }
  }

  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var cmd = e.target.closest('[data-cmd]');
    if (cmd) { e.preventDefault(); return copiar(cmd); }
    if (e.target.closest('[data-voltar]')) { e.preventDefault(); return voltar(); }
    var pulo = e.target.closest('[data-ir]');
    if (pulo) {
      e.preventDefault();
      return abrir(pulo.getAttribute('data-ir'), painel.contains(pulo) ? 'trilha' : 'novo');
    }
    var alvo = e.target.closest('.item .alvo');
    if (alvo && !painel.contains(alvo)) {
      e.preventDefault();
      voltarFoco = alvo;
      return abrir(alvo.closest('.item').getAttribute('data-nnn'));
    }
    if (e.target.closest('[data-fechar-ficha]') || e.target === painel) fechar();
  });

  function filtrar() {
    var termo = q.value.trim().toLowerCase();
    document.querySelectorAll('.grupo .item').forEach(function (li) {
      li.hidden = !!termo && li.getAttribute('data-busca').indexOf(termo) === -1;
    });
    document.querySelectorAll('.grupo').forEach(function (g) {
      var lista = g.querySelector('.lista');
      if (!lista) return;
      var achou = !!lista.querySelector('.item:not([hidden])');
      var aviso = g.querySelector('.sem-resultado');
      if (aviso) aviso.hidden = achou;
      if (termo) g.open = achou;          // busca abre só o que tem resultado
    });
  }
  q.addEventListener('input', filtrar);

  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    if ((e.key === 'Backspace' || e.key === 'ArrowLeft') && !painel.hidden
        && document.activeElement !== q && pilha.length) { e.preventDefault(); return voltar(); }
    if (e.key === 'Escape') {
      if (!painel.hidden) return fechar();
      if (document.activeElement === q && q.value) { q.value = ''; filtrar(); }
    }
  });

  if (location.hash.indexOf('#item-') === 0) abrir(location.hash.slice(6));
})();
"""
