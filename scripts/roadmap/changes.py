#!/usr/bin/env python3
"""changes — espelho HTML das mudanças em `thoughts/changes/`. Determinístico, sem LLM.

Uma mudança é uma pasta com `spec.md` (o quê), `plan.md` (o como), `tasks.md` (o checklist TDD)
e `notes*.md` (execução). Este módulo lê os quatro e escreve `thoughts/board/changes.html`.

Não é markdown renderizado: é **view tipada**. A spec vira requisito com os cenários DADO/QUANDO/
ENTÃO abertos; o plano vira abordagem e decisões numeradas; as tarefas viram progresso por PR
previsto. Ler o `.md` cru é denso justamente porque tudo tem o mesmo peso visual — aqui não tem.

Escreve junto com o board do roadmap (`roadmap board`), pra as duas views ficarem coerentes.
Compartilha casca, CSS e o renderizador de markdown com `board.py`.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board as bd
import roadmap as rm

CHANGES_NAME = "changes.html"
CHANGES_SUBDIR = Path("thoughts") / "changes"
DOCS = ("spec", "plan", "tasks", "notes")

_REQ = re.compile(r"^## (R\d+)\s*·\s*\[([^\]]+)\]\s*(.+)$")
_CENARIO = re.compile(r"^-\s+\*\*(.+?)\*\*\s+[—–-]\s+(.+)$")
# O agrupador de `tasks.md` não é só "PR N": mudanças reais usam "Etapa N", e o que importa é
# que é um `##` que junta tarefas. O id da tarefa também varia (T1, S1) e o estado tem três
# valores — `[~]` é tarefa MOVIDA pra outra mudança, que não é feita nem pendente.
_BLOCO = re.compile(r"^## +(.+?)\s*$")
_TAREFA = re.compile(r"^-\s+\[([ xX~])\]\s+\*\*([A-Z]+\d+[a-z]?)([^*]*)\*\*\s*[—–-]?\s*(.*)$")
_PR_NOTA = re.compile(r"\*\*#(\d+)\*\*")
_BRANCH = re.compile(r"branch `([^`]+)`")
_DECISAO = re.compile(r"^### (D\d+[a-z]?)\s*[—–-]\s*(.+)$")
_TITULO = re.compile(r"^#\s+(.+)$", re.M)
_FORA = re.compile(r"^\*\*Fora de escopo:\*\*\s*(.+)$", re.M)


# ---------------------------------------------------------------- modelo

class Mudanca:
    """Uma pasta de `thoughts/changes/`. Tudo derivado da leitura — nada é escrito de volta."""

    def __init__(self, pasta: Path, arquivada: bool):
        self.pasta = pasta
        self.arquivada = arquivada
        self.nome = pasta.name
        m = re.match(r"^(?:(\d{4}-\d{2})-)?(\d{3})-(.+)$", self.nome)
        self.nnn = m.group(2) if m else self.nome[:3]
        self.slug = m.group(3) if m else self.nome
        self.arquivo = {d: (pasta / f"{d}.md") for d in DOCS}
        self.notas = sorted(p for p in pasta.glob("notes*.md"))
        self.texto = {d: (p.read_text(encoding="utf-8") if p.is_file() else "")
                      for d, p in self.arquivo.items()}

    @property
    def tem(self) -> list[str]:
        return [d for d in DOCS if self.texto[d] or (d == "notes" and self.notas)]

    @property
    def titulo(self) -> str:
        for d in ("spec", "plan"):
            if m := _TITULO.search(self.texto[d]):
                return re.sub(r"^Plano\s*[—–-]\s*", "", m.group(1)).strip()
        return self.slug.replace("-", " ")

    @property
    def resumo(self) -> str:
        """A frase logo abaixo do h1 da spec — o que passa a ser possível, e pra quem."""
        corpo = self.texto["spec"]
        if not corpo:
            return ""
        depois = corpo.split("\n", 1)[1] if "\n" in corpo else ""
        for linha in depois.split("\n"):
            t = linha.strip()
            if t and not t.startswith(("#", "**", ">", "-", "|")):
                return t
        return ""

    @property
    def fora_escopo(self) -> str:
        m = _FORA.search(self.texto["spec"])
        return m.group(1).strip() if m else ""

    @property
    def requisitos(self) -> list[dict]:
        out, atual = [], None
        for linha in self.texto["spec"].split("\n"):
            if m := _REQ.match(linha):
                atual = {"id": m.group(1), "tipo": m.group(2).strip(), "nome": m.group(3).strip(),
                         "regra": "", "cenarios": []}
                out.append(atual)
            elif atual is not None:
                if linha.startswith("## "):
                    atual = None
                elif m := _CENARIO.match(linha):
                    atual["cenarios"].append((m.group(1).strip(), m.group(2).strip()))
                elif linha.strip() and not atual["regra"] and not linha.startswith(("-", ">")):
                    atual["regra"] = linha.strip()
        return out

    @property
    def blocos_pr(self) -> list[dict]:
        """As tarefas agrupadas pelo PR em que nascem, como o `plan` escreveu."""
        out: list[dict] = []
        atual: dict | None = None
        tarefa: dict | None = None
        for linha in self.texto["tasks"].split("\n"):
            if m := _BLOCO.match(linha):
                atual = {"rotulo": m.group(1).strip(), "nota": [], "pr": "", "branch": "",
                         "tarefas": []}
                out.append(atual)
                tarefa = None
            elif atual is None:
                continue
            elif linha.startswith(">") and not atual["tarefas"]:
                atual["nota"].append(linha.lstrip("> ").strip())
            elif m := _TAREFA.match(linha):
                estado = m.group(1).lower()
                tarefa = {"feita": estado == "x", "movida": estado == "~", "id": m.group(2),
                          "reqs": m.group(3).replace("·", "").strip(),
                          "texto": m.group(4).strip(), "detalhe": []}
                atual["tarefas"].append(tarefa)
            elif tarefa is not None and linha.startswith(("      ", "\t")):
                tarefa["detalhe"].append(linha.strip())
            elif not linha.strip():
                tarefa = None

        for b in out:  # a primeira linha de `>` costuma carregar o PR e o branch
            juntas = " ".join(b["nota"])
            if m := _PR_NOTA.search(juntas):
                b["pr"] = m.group(1)
            if m := _BRANCH.search(juntas):
                b["branch"] = m.group(1)
            b["nota"] = re.sub(r"\*\*#\d+\*\*\s*·?\s*", "", juntas).strip(" ·")
        return [b for b in out if b["tarefas"]]   # `## Notas` e afins não são bloco de tarefa

    @property
    def tarefas(self) -> tuple[int, int]:
        """Feitas e total. Tarefa `[~]` saiu pra outra mudança: não conta dos dois lados."""
        vivas = [t for b in self.blocos_pr for t in b["tarefas"] if not t["movida"]]
        return sum(1 for t in vivas if t["feita"]), len(vivas)

    @property
    def movidas(self) -> int:
        return sum(1 for b in self.blocos_pr for t in b["tarefas"] if t["movida"])

    @property
    def decisoes(self) -> list[tuple[str, str]]:
        return [(m.group(1), m.group(2).strip())
                for m in (_DECISAO.match(l) for l in self.texto["plan"].split("\n")) if m]

    @property
    def secao_plan(self):
        def pega(titulo: str) -> str:
            m = re.search(rf"^##\s+{titulo}\s*$(.*?)(?=^##\s|\Z)", self.texto["plan"],
                          re.M | re.S)
            return m.group(1).strip() if m else ""
        return pega

    @property
    def estado(self) -> str:
        if self.arquivada:
            return "feito"
        feitas, total = self.tarefas
        if total and feitas == total:
            return "andando"          # tudo marcado, mas a pasta ainda não foi arquivada
        if feitas:
            return "andando"
        if self.texto["tasks"]:
            return "aberto"
        return "travado"              # só spec/plan: ainda não virou checklist


ESTADO_ROTULO = {"feito": "arquivada", "andando": "em execução", "aberto": "pronta pra implementar",
                 "travado": "sem tarefas ainda"}


def carregar(root: Path) -> list[Mudanca]:
    base = root / CHANGES_SUBDIR
    if not base.is_dir():
        return []
    ativas = [Mudanca(p, False) for p in sorted(base.iterdir())
              if p.is_dir() and p.name != "archive"]
    arq = base / "archive"
    velhas = [Mudanca(p, True) for p in sorted(arq.iterdir())] if arq.is_dir() else []
    return ativas + velhas


# ---------------------------------------------------------------- peças

def barra(feitas: int, total: int) -> str:
    if not total:
        return '<span class="prog vazio-prog">sem tarefas</span>'
    pct = round(feitas * 100 / total)
    return (f'<span class="prog"><span class="trilho">'
            f'<span class="cheio" style="width:{pct}%"></span></span>'
            f'<span class="frac">{feitas}/{total}</span></span>')


def linha_mudanca(m: Mudanca) -> str:
    faltando = [d for d in DOCS if d not in m.tem]
    falta = (f'<span class="falta" title="ainda não existe">falta {", ".join(faltando)}</span>'
             if faltando else "")
    feitas, total = m.tarefas
    return (f'<li class="item {m.estado}" data-nnn="{m.nnn}" '
            f'data-busca="{bd.html.escape((m.nnn + " " + m.titulo + " " + m.slug).lower(), quote=True)}">'
            f'<a class="alvo" href="#mud-{m.nnn}">'
            f'<span class="id">{m.nnn}</span>'
            f'<span class="t">{bd.esc(m.titulo)}</span></a>'
            f'{barra(feitas, total)}{falta}'
            f'<span class="tag {m.estado}">{ESTADO_ROTULO[m.estado]}</span></li>')


def pr_link(slug: str, numero: str) -> str:
    return f"https://github.com/{slug}/pull/{numero}" if slug and numero.isdigit() else ""


def painel_docs(m: Mudanca, root: Path, slug: str = "") -> str:
    """Spec, plano, tarefas e notas — cada um do jeito que se lê melhor, não como markdown cru."""
    abas, telas = [], []

    def aba(chave, rotulo, conteudo, selo=""):
        if not conteudo:
            return
        n = len(abas)
        abas.append(f'<button class="chip{" on" if n == 0 else ""}" data-aba="{chave}" '
                    f'data-mud="{m.nnn}">{rotulo}{selo}</button>')
        telas.append(f'<div class="tela{" on" if n == 0 else ""}" data-tela="{chave}" '
                     f'data-mud="{m.nnn}">{conteudo}</div>')

    # --- spec: requisito como bloco, cenário como par nome/regra
    reqs = m.requisitos
    if reqs:
        blocos = ""
        for r in reqs:
            cen = "".join(f'<li><span class="cen-nome">{bd.esc(nome)}</span>'
                          f'<span class="cen-txt">{bd.esc(txt)}</span></li>'
                          for nome, txt in r["cenarios"])
            blocos += (f'<section class="req"><div class="req-topo">'
                       f'<span class="req-id">{r["id"]}</span>'
                       f'<span class="req-tipo">{bd.esc(r["tipo"])}</span>'
                       f'<h5>{bd.esc(r["nome"])}</h5></div>'
                       + (f'<p class="req-regra">{bd.esc(r["regra"])}</p>' if r["regra"] else "")
                       + (f'<ul class="cenarios">{cen}</ul>' if cen else "")
                       + '</section>')
        topo = ""
        if m.resumo:
            topo += f'<p class="lead">{bd.esc(m.resumo)}</p>'
        if m.fora_escopo:
            topo += (f'<p class="fora"><strong>Fora de escopo:</strong> '
                     f'{bd.esc(m.fora_escopo)}</p>')
        aba("spec", "Spec", topo + blocos, f'<span class="chip-n">{len(reqs)}</span>')
    elif m.texto["spec"]:
        aba("spec", "Spec", f'<div class="corpo">{bd.markdown(m.texto["spec"], [], root, "")}</div>')

    # --- plano: abordagem em texto, decisões enumeradas
    if m.texto["plan"]:
        pega = m.secao_plan
        conteudo = ""
        if abordagem := pega("Abordagem"):
            conteudo += (f'<h5 class="sub">Abordagem</h5><div class="corpo">'
                         f'{bd.markdown(abordagem, [], root, "")}</div>')
        if dec := m.decisoes:
            itens = "".join(f'<li><span class="dec-id">{i}</span>{bd.esc(t)}</li>'
                            for i, t in dec)
            conteudo += f'<h5 class="sub">Decisões técnicas</h5><ol class="decisoes">{itens}</ol>'
        for nome in ("Testes", "Suposições", "Riscos"):
            if trecho := pega(nome):
                conteudo += (f'<h5 class="sub">{nome}</h5><div class="corpo">'
                             f'{bd.markdown(trecho, [], root, "")}</div>')
        if not conteudo:
            conteudo = f'<div class="corpo">{bd.markdown(m.texto["plan"], [], root, "")}</div>'
        aba("plan", "Plano", conteudo,
            f'<span class="chip-n">{len(m.decisoes)}</span>' if m.decisoes else "")

    # --- tarefas: o PR previsto é o agrupador, e o progresso é dele
    blocos = m.blocos_pr
    if blocos:
        corpo = ""
        for b in blocos:
            vivas = [t for t in b["tarefas"] if not t["movida"]]
            feitas = sum(1 for t in vivas if t["feita"])
            tarefas = "".join(
                f'<li class="tarefa{" ok" if t["feita"] else ""}'
                f'{" movida" if t["movida"] else ""}">'
                f'<span class="caixa">{"✓" if t["feita"] else ("→" if t["movida"] else "")}</span>'
                f'<span class="t-corpo"><span class="t-id">{t["id"]}</span>'
                + (f'<span class="t-req">{bd.esc(t["reqs"])}</span>' if t["reqs"] else "")
                + f'<span class="t-txt">{bd.esc(t["texto"])}</span>'
                + ("".join(f'<span class="t-det">{bd.inline(x, [], root, "")}</span>'
                           for x in t["detalhe"]) if t["detalhe"] else "")
                + '</span></li>' for t in b["tarefas"])
            corpo += (f'<section class="pr-bloco"><div class="pr-topo">'
                      f'<h5>{bd.esc(b["rotulo"])}</h5>'
                      + (f'<a class="pr-tag" href="{pr_link(slug, b["pr"])}" target="_blank" '
                         f'rel="noopener">#{b["pr"]}</a>' if pr_link(slug, b["pr"]) else
                         (f'<span class="pr-tag">#{b["pr"]}</span>' if b["pr"] else ""))
                      + f'{barra(feitas, len(vivas))}</div>'
                      + (f'<p class="pr-nota">{bd.esc(b["nota"])}</p>' if b["nota"] else "")
                      + f'<ul class="tarefas">{tarefas}</ul></section>')
        f, t = m.tarefas
        aba("tasks", "Tarefas", corpo, f'<span class="chip-n">{f}/{t}</span>')
    elif m.texto["tasks"]:
        aba("tasks", "Tarefas", f'<div class="corpo">{bd.markdown(m.texto["tasks"], [], root, "")}</div>')

    # --- notas: uma ou várias (notes-pr1.md, notes-etapa2.md…)
    if m.notas:
        corpo = ""
        for p in m.notas:
            rot = p.stem.replace("notes", "notas").replace("-", " ")
            corpo += (f'<details class="nota"><summary>{bd.esc(rot)}</summary>'
                      f'<div class="corpo">'
                      f'{bd.markdown(p.read_text(encoding="utf-8"), [], root, "")}</div></details>')
        aba("notes", "Notas", corpo, f'<span class="chip-n">{len(m.notas)}</span>')

    if not abas:
        return '<p class="vazio">Pasta sem spec, plano, tarefas ou notas.</p>'
    return f'<div class="chips">{"".join(abas)}</div>{"".join(telas)}'


def ficha(m: Mudanca, root: Path, slug: str = "", item_roadmap: str = "") -> str:
    feitas, total = m.tarefas
    meta = [("Estado", ESTADO_ROTULO[m.estado]),
            ("Requisitos", str(len(m.requisitos)) or "—"),
            ("PRs previstos", str(len(m.blocos_pr)) or "—"),
            ("Tarefas", f"{feitas}/{total}" if total else "—")]
    if item_roadmap:
        meta.append(("Roadmap", f'<a class="wiki" href="roadmap.html#item-{item_roadmap}">'
                                f'item {item_roadmap}</a>'))
    grade = "".join(f"<div><dt>{r}</dt><dd>{v}</dd></div>" for r, v in meta)

    atalhos = "".join(
        f'<a class="botao secundario" href="{bd.href_obsidian(p)}">{p.stem}.md</a>'
        for p in ([m.arquivo[d] for d in DOCS if m.arquivo[d].is_file()] + m.notas))
    return (f'<article class="ficha" id="mud-{m.nnn}" data-nnn="{m.nnn}" tabindex="-1">'
            f'<div class="ficha-topo"><span class="id grande">{m.nnn}</span>'
            f'<span class="tag {m.estado}">{ESTADO_ROTULO[m.estado]}</span>'
            f'<button class="fechar" data-fechar-ficha aria-label="Fechar">×</button></div>'
            f'<h3>{bd.esc(m.titulo)}</h3>'
            f'<dl class="meta-grade">{grade}</dl>'
            f'{painel_docs(m, root, slug)}'
            f'<div class="acoes"><span class="acoes-rot">Abrir no Obsidian:</span>{atalhos}</div>'
            f'<p class="caminho"><code>{bd.esc(str(m.pasta.resolve()))}</code></p>'
            f'</article>')


# ---------------------------------------------------------------- página

def render(root: Path, live: int = 0) -> str:
    muds = carregar(root)
    if not muds:
        rm.die(f"nenhuma mudança em {root / CHANGES_SUBDIR}")

    de_item: dict[str, str] = {}      # a mudança sabe quem a puxou no roadmap
    try:
        for i in rm.load_items(root):
            if (ch := (i.fm.get("change") or "").strip()):
                de_item[ch[:3] if re.match(r"^\d{3}", ch) else ch] = i.nnn
    except Exception:  # noqa: BLE001 — sem vault de roadmap a view de changes segue de pé
        pass

    ativas = [m for m in muds if not m.arquivada]
    arquivadas = [m for m in muds if m.arquivada]
    em_exec = [m for m in ativas if m.estado == "andando"]
    prontas = [m for m in ativas if m.estado in ("aberto", "travado")]
    feitas = sum(m.tarefas[0] for m in ativas)
    total = sum(m.tarefas[1] for m in ativas)

    def secao(chave, rotulo, dica, lista):
        if not lista:
            return ""
        return (f'<details class="grupo" data-grupo="{chave}">'
                f'<summary><span class="rot">{rotulo}</span>'
                f'<span class="cont">{len(lista)}</span>'
                f'<span class="dica">{dica}</span></summary>'
                f'<ul class="lista">{"".join(linha_mudanca(m) for m in lista)}</ul>'
                f'<p class="sem-resultado" hidden>Nada aqui com esse filtro.</p></details>')

    grupos = (secao("exec", "Em execução", "com tarefa marcada", em_exec)
              + secao("prontas", "Prontas pra implementar", "spec e plano escritos, nada feito",
                      prontas)
              + secao("arquivadas", "Arquivadas", "PR mergeado, pasta fechada", arquivadas))

    metricas = [("Ativas", len(ativas), "aberto"), ("Em execução", len(em_exec), "andando"),
                ("Tarefas feitas", f"{feitas}/{total}" if total else "—", "next"),
                ("Arquivadas", len(arquivadas), "feito")]
    tiles = "".join(f'<div class="tile {k}"><span class="n">{v}</span>'
                    f'<span class="l">{rot}</span></div>' for rot, v, k in metricas)

    slug = bd.repo_slug(root)
    # projeto pode ter changes e nenhum roadmap: aba que apontaria pra arquivo inexistente não nasce
    aba_roadmap = (f'\n    <a class="aba" href="{bd.BOARD_NAME}">Roadmap</a>'
                   if rm.vault(root).is_dir() else "")
    fichas = "".join(ficha(m, root, slug, de_item.get(m.nnn, "")) for m in muds)
    corpo = f"""<div class="wrap">
  <nav class="abas" aria-label="Views">{aba_roadmap}
    <span class="aba ativa">Changes</span>
  </nav>

  <header>
    <h1>Changes <span>· {bd.esc(root.name)}</span></h1>
    <p class="meta">{len(muds)} MUDANÇAS · GERADO EM {rm.date.today().strftime("%d-%m-%Y")}</p>
  </header>

  <div class="tiles">{tiles}</div>

  <div class="busca">
    <input type="search" id="q" placeholder="Filtrar por número, título ou slug…"
           aria-label="Filtrar mudanças" autocomplete="off">
  </div>

  <div class="grupos">{grupos}</div>

  <footer>
    Clique numa mudança pra abrir a ficha: spec com os requisitos, plano com as decisões,
    tarefas com o progresso por PR, e as notas de execução.<br>
    Espelho gerado de <code>thoughts/changes/</code>: a fonte da verdade são os <code>.md</code>,
    e editar aqui não muda nada lá.
  </footer>
</div>

<div id="painel" hidden>
  <div class="gaveta" role="dialog" aria-modal="true">{fichas}</div>
</div>
<script>
{JS_CHANGES}
</script>"""
    return bd.pagina(f"Changes · {bd.esc(root.name)}", corpo, live)


def escrever(root: Path, live: int = 0) -> list[Path]:
    if not carregar(root):
        return []
    base = bd.board_root(root)
    base.mkdir(parents=True, exist_ok=True)
    alvo = base / CHANGES_NAME
    alvo.write_text(render(root, live), encoding="utf-8")
    return [alvo]


CSS_EXTRA = """
.tarefa.movida .t-txt { color:var(--muted); }
"""

JS_CHANGES = """
(function () {
  var q = document.getElementById('q');
  var painel = document.getElementById('painel');
  var voltarFoco = null;

  function abrir(nnn) {
    var alvo = painel.querySelector('.ficha[data-nnn="' + nnn + '"]');
    if (!alvo) return;
    painel.querySelectorAll('.ficha.ativa').forEach(function (f) { f.classList.remove('ativa'); });
    alvo.classList.add('ativa');
    painel.hidden = false;
    alvo.scrollTop = 0;
    alvo.focus({ preventScroll: true });
    try { history.replaceState(null, '', '#mud-' + nnn); } catch (_) {}
  }

  function fechar() {
    painel.hidden = true;
    painel.querySelectorAll('.ficha.ativa').forEach(function (f) { f.classList.remove('ativa'); });
    try { history.replaceState(null, '', location.pathname + location.search); } catch (_) {}
    if (voltarFoco) { voltarFoco.focus(); voltarFoco = null; }
  }

  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var chip = e.target.closest('[data-aba]');
    if (chip) {
      var mud = chip.getAttribute('data-mud'), aba = chip.getAttribute('data-aba');
      painel.querySelectorAll('[data-mud="' + mud + '"]').forEach(function (n) {
        var meu = n.getAttribute('data-aba') === aba || n.getAttribute('data-tela') === aba;
        n.classList.toggle('on', meu);
      });
      return;
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
      if (termo) g.open = achou;
    });
  }
  q.addEventListener('input', filtrar);

  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    if (e.key === 'Escape') {
      if (!painel.hidden) return fechar();
      if (document.activeElement === q && q.value) { q.value = ''; filtrar(); }
    }
  });

  if (location.hash.indexOf('#mud-') === 0) abrir(location.hash.slice(5));
})();
"""
