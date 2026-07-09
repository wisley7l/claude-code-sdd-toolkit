---
description: Checa o status das dependências externas — Cloudflare, GitHub, PlanetScale (Vitess) e AWS — via status pages oficiais. Read-only, sem side effects. Reporta um resumo com nível por serviço e um veredito geral.
model: claude-sonnet-5
argument-hint: (vazio — checa tudo)
allowed-tools: Bash(python3 *)
---

# Status das dependências externas

Checa, em uma passada, o status público de: **Cloudflare**, **GitHub**, **PlanetScale (Vitess)** e **AWS**. Puramente read-only (só HTTP GET nos status pages oficiais) — não toca em nada.

## Fontes (verificadas)

- Cloudflare / GitHub / PlanetScale → Statuspage.io `.../api/v2/status.json` (`indicator`: `none|minor|major|critical`).
- AWS → `health.aws.amazon.com/public/currentevents` (JSON **UTF-16**, lista de eventos). **Só eventos dos últimos 7 dias** contam como ativos — entradas antigas persistem no feed e não devem ser reportadas como incidente atual.

## Protocolo

1. Rode o checker abaixo (tem retry contra timeout transiente; degrada pra `❔` se um serviço não responder, sem quebrar):

```bash
python3 - <<'PY'
import json, sys, urllib.request
from datetime import datetime, timezone

STATUSPAGE = [
    ("Cloudflare", "https://www.cloudflarestatus.com/api/v2/status.json"),
    ("GitHub", "https://www.githubstatus.com/api/v2/status.json"),
    ("PlanetScale (Vitess)", "https://www.planetscalestatus.com/api/v2/status.json"),
]
AWS_URL = "https://health.aws.amazon.com/public/currentevents"
EMOJI = {"none": "✅", "minor": "🟡", "major": "🟠", "critical": "🔴", "unknown": "❔"}
RANK = {"none": 0, "minor": 1, "major": 2, "critical": 3, "unknown": 1}

def _get(url, timeout=12, tries=2):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "status-deps/1"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
    raise last

def check_statuspage(name, url):
    try:
        d = json.loads(_get(url))
        return {"name": name, "level": d["status"]["indicator"], "desc": d["status"]["description"], "detail": []}
    except Exception as e:
        return {"name": name, "level": "unknown", "desc": f"não consegui checar ({e})", "detail": []}

def check_aws():
    try:
        events = json.loads(_get(AWS_URL).decode("utf-16", "replace"))
        now = datetime.now(timezone.utc).timestamp()
        recent, det = [], []
        for e in events:
            try:
                ts = int(e.get("date", 0))
            except Exception:
                ts = 0
            if now - ts <= 7 * 86400:
                recent.append(e)
                when = datetime.fromtimestamp(ts, timezone.utc).strftime("%d/%m %H:%M UTC")
                det.append(f"{e.get('region_name','?')} · {e.get('service_name','?')} · {e.get('summary','?')} ({when})")
        older = len(events) - len(recent)
        if not recent:
            desc = "sem eventos recentes (7d)" + (f"; {older} antigo(s) ignorado(s)" if older else "")
            return {"name": "AWS", "level": "none", "desc": desc, "detail": []}
        return {"name": "AWS", "level": "major", "desc": f"{len(recent)} evento(s) nos últimos 7d", "detail": det[:12]}
    except Exception as e:
        return {"name": "AWS", "level": "unknown", "desc": f"não consegui checar ({e})", "detail": []}

def main():
    results = [check_statuspage(n, u) for n, u in STATUSPAGE] + [check_aws()]
    worst = max(RANK[r["level"]] for r in results)
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    print(f"Status das dependências — {now}\n")
    for r in results:
        print(f"  {EMOJI[r['level']]}  {r['name']:<22} {r['desc']}")
        for d in r["detail"]:
            print(f"        └ {d}")
    verdict = {0: "✅ tudo operacional", 1: "🟡 atenção — degradação parcial",
               2: "🟠 incidente ativo", 3: "🔴 incidente crítico"}[worst]
    print(f"\n{verdict}")
    return 1 if worst > 0 else 0

if __name__ == "__main__":
    sys.exit(main())
PY
```

2. **Apresente a saída** ao usuário como está (ela já vem formatada). Se **algo não estiver `✅`**, destaque o serviço e o que aparece de detalhe (região/serviço/resumo no caso do AWS) — e, se for uma dependência crítica do trabalho em curso, avise do possível impacto. Se tudo `✅`, uma linha curta basta.

## Guardrails

- **Read-only**: só GET em status pages públicos. Nunca autentica, nunca muda nada.
- **Não invente status**: se um serviço vier `❔` (timeout/erro), reporte como "não consegui checar" — não afirme que está ok nem que está fora.
- **AWS por recência**: eventos com mais de 7 dias no feed **não** são incidente atual; não os reporte como ativos.
- **Sem polling automático**: é um check pontual. Pra monitorar em intervalo, o usuário pode usar `/loop <intervalo> /status-deps`.
