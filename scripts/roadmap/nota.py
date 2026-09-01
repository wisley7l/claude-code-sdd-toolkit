#!/usr/bin/env python3
"""nota — transforma um `.md` em página HTML com a mesma casca do board. Sem LLM.

Serve pra qualquer documento de `thoughts/` que o agente escreva pra você **ler**: pesquisa,
diagnóstico, comparação de opções. O agente escreve markdown — que é o que ele escreveria de
qualquer jeito — e este script faz o HTML, que assim custa zero token e sai igual toda vez.

    nota <arquivo.md> [-o saida.html] [-a] [--live SEG]

Sem `-o`, escreve em `thoughts/board/<nome>.html`. A página tem sumário lateral quando o
documento tem seções, e abre em `file://` — sem CDN, sem lib, offline.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board as bd
import roadmap as rm

_H = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.M)

CSS = "<style>\n" + '''.nota-wrap { max-width:1080px; }
.nota-corpo { display:grid; grid-template-columns:220px minmax(0,1fr); gap:44px;
  align-items:start; }
@media (max-width:880px) { .nota-corpo { grid-template-columns:1fr; gap:0; } }
.sumario { position:sticky; top:32px; }
@media (max-width:880px) { .sumario { position:static; margin-bottom:26px;
  border-bottom:1px solid var(--rule); padding-bottom:16px; } }
.sum-rot { font-size:10px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted);
  font-weight:700; margin:0 0 10px; }
.sumario ul { gap:2px; }
.sumario li { font-size:13px; line-height:1.45; }
.sumario li.n3 { padding-left:14px; font-size:12.5px; }
.sumario a { color:var(--muted); text-decoration:none; display:block; padding:3px 0; }
.sumario a:hover { color:var(--quente); }
.doc { font-size:16px; line-height:1.7; max-width:72ch; }
.doc h3 { font-size:21px; margin:38px 0 14px; letter-spacing:-.01em; text-wrap:balance; }
.doc h4 { font-size:16px; margin:28px 0 10px; text-transform:none; letter-spacing:0;
  color:var(--ink); font-weight:700; }
.doc h5, .doc h6 { font-size:14px; margin:22px 0 8px; color:var(--muted); }
.doc > h3:first-child { margin-top:0; }
.doc blockquote { font-size:15px; }
.doc strong { font-weight:700; }
''' + "</style>"


def ancora(texto: str) -> str:
    base = rm.slugify(texto, max_words=8, min_words=1)
    return f"s-{base}" if base else "s"


def sumario(corpo: str) -> tuple[str, dict[str, str]]:
    """Índice lateral a partir dos h2/h3. Documento curto não ganha sumário — seria ruído."""
    achados = [(len(m.group(1)), m.group(2)) for m in _H.finditer(corpo) if len(m.group(1)) > 1]
    if len(achados) < 3:
        return "", {}
    ids: dict[str, str] = {}
    itens = ""
    for nivel, texto in achados:
        limpo = re.sub(r"[*`\[\]]", "", texto).strip()
        ids[texto] = ancora(limpo)
        itens += (f'<li class="n{nivel}"><a href="#{ids[texto]}">{bd.esc(limpo)}</a></li>')
    return f'<nav class="sumario"><p class="sum-rot">Neste documento</p><ul>{itens}</ul></nav>', ids


def render(caminho: Path, live: int = 0) -> str:
    bruto = caminho.read_text(encoding="utf-8")
    if bruto.startswith("---"):                      # frontmatter não é conteúdo
        fim = bruto.find("\n---", 3)
        if fim != -1:
            bruto = bruto[fim + 4:]

    m = re.match(r"^#\s+(.+)$", bruto.lstrip().split("\n", 1)[0])
    titulo = m.group(1).strip() if m else caminho.stem.replace("-", " ")
    sum_html, ids = sumario(bruto)

    corpo_md = bd.markdown(bruto, [], caminho.parent, "")
    for texto, ident in ids.items():                 # âncora em cada seção, pro sumário pular
        limpo = bd.esc(re.sub(r"[*`\[\]]", "", texto).strip())
        for n in (3, 4):
            corpo_md = corpo_md.replace(f"<h{n}>{limpo}</h{n}>",
                                        f'<h{n} id="{ident}">{limpo}</h{n}>', 1)

    palavras = len(re.findall(r"\w+", bruto))
    corpo = f"""<div class="wrap nota-wrap">
  <header>
    <h1>{bd.esc(titulo)}</h1>
    <p class="meta">{palavras} PALAVRAS · ~{max(1, round(palavras / 220))} MIN ·
       {rm.date.today().strftime("%d-%m-%Y")}</p>
  </header>

  <div class="nota-corpo">
    {sum_html}
    <article class="corpo doc">{corpo_md}</article>
  </div>

  <footer>
    Gerado de <code>{bd.esc(caminho.name)}</code> — a fonte é o <code>.md</code>, e editar
    aqui não muda nada lá. <a href="{bd.href_obsidian(caminho)}">Abrir no Obsidian</a>
  </footer>
</div>
{CSS}"""
    return bd.pagina(bd.esc(titulo), corpo.replace("{CSS}", CSS), live)


def escrever(caminho: Path, saida: Path | None, live: int = 0) -> Path:
    if saida is None:
        raiz = rm.main_root(None)
        alvo = bd.board_root(raiz) / f"{caminho.stem}.html"
    else:
        alvo = saida
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(render(caminho, live), encoding="utf-8")
    return alvo


def main(argv):
    p = argparse.ArgumentParser(prog="nota", description="markdown → página HTML")
    p.add_argument("arquivo")
    p.add_argument("-o", "--out", default=None, help="default: thoughts/board/<nome>.html")
    p.add_argument("-a", "--abrir", action="store_true", help="abre no navegador padrão")
    p.add_argument("--live", type=int, metavar="SEG", default=0)
    a = p.parse_args(argv)

    caminho = Path(a.arquivo).expanduser().resolve()
    if not caminho.is_file():
        rm.die(f"não achei {caminho}")
    alvo = escrever(caminho, Path(a.out).resolve() if a.out else None, a.live)
    print(f"nota gerada: file://{alvo}", flush=True)
    if a.abrir:
        import webbrowser
        if not webbrowser.open(f"file://{alvo}"):
            print("aviso: não achei navegador — abra o caminho acima à mão", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
