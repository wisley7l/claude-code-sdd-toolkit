---
description: Checa o status das dependências externas — Cloudflare, GitHub, PlanetScale (Vitess) e AWS — via status pages oficiais. Mostra os PRODUTOS/REGIÕES com falha (não só o nível geral), pra você julgar se afeta sua stack. Read-only, sem side effects.
model: claude-sonnet-5
argument-hint: (vazio — checa tudo)
allowed-tools: Bash(python3 *)
---

# Status das dependências externas

Checa, numa passada, o status público de: **Cloudflare**, **GitHub**, **PlanetScale (Vitess)** e **AWS**. Além do nível geral por serviço, lista **o que exatamente está com falha** — incidentes ativos (com produto afetado), áreas/produtos e localidades — pra você decidir se toca na sua stack (algo fora do seu uso pode estar degradado sem te impactar). Puramente read-only.

## Fontes (verificadas)

- Cloudflare / GitHub / PlanetScale → Statuspage.io `.../api/v2/summary.json` — traz `status.indicator` (`none|minor|major|critical`), **incidentes ativos** (nome + impacto + componentes afetados) e **componentes** (produtos/regiões/datacenters com seu status).
- AWS → `health.aws.amazon.com/public/currentevents` (JSON **UTF-16**, lista de eventos com região + serviço + resumo). **Só eventos dos últimos 7 dias** contam como ativos — entradas antigas persistem no feed e não são incidente atual.

## Protocolo

1. Rode o checker abaixo (retry contra timeout transiente; degrada pra `❔` se um serviço não responder, sem quebrar):

```bash
python3 - <<'PY'
import json, sys, urllib.request
from datetime import datetime, timezone

STATUSPAGE = [
    ("Cloudflare", "https://www.cloudflarestatus.com"),
    ("GitHub", "https://www.githubstatus.com"),
    ("PlanetScale (Vitess)", "https://www.planetscalestatus.com"),
]
AWS_URL = "https://health.aws.amazon.com/public/currentevents"
EMOJI = {"none": "✅", "minor": "🟡", "major": "🟠", "critical": "🔴", "unknown": "❔"}
RANK = {"none": 0, "minor": 1, "major": 2, "critical": 3, "unknown": 1}
OUTAGE = {"degraded_performance", "partial_outage", "major_outage"}

def _get(url, timeout=12, tries=3):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "status-deps/1"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
    raise last

def check_statuspage(name, base):
    try:
        s = json.loads(_get(base + "/api/v2/summary.json"))
        detail = []
        for inc in s.get("incidents", []):
            aff = ", ".join(c.get("name", "?") for c in inc.get("components", [])) or "—"
            detail.append(f"⚠ [{inc.get('impact')}] {inc.get('name')} → afeta: {aff}")
        comps = s.get("components", [])
        areas = [c["name"] for c in comps if c.get("status") in OUTAGE and c.get("group")]
        indiv = [c for c in comps if c.get("status") in OUTAGE and not c.get("group")]
        maint = sum(1 for c in comps if c.get("status") == "under_maintenance")
        if areas:
            detail.append("áreas/produtos afetados: " + ", ".join(areas))
        if indiv:
            sample = ", ".join(c["name"] for c in indiv[:5])
            extra = f" (+{len(indiv) - 5})" if len(indiv) > 5 else ""
            detail.append(f"localidades/componentes específicos: {len(indiv)} — {sample}{extra}")
        if maint:
            detail.append(f"em manutenção: {maint}")
        return {"name": name, "level": s["status"]["indicator"], "desc": s["status"]["description"], "detail": detail}
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

2. **Apresente a saída** como está (já vem formatada). Se algo não estiver `✅`, foque no que **de fato pode te afetar**: o produto do incidente (ex.: "Workers AI"), as áreas/produtos e — no AWS — a região·serviço. Diga explicitamente se o que está degradado **parece fora da stack do usuário** (então provável não-impacto) ou dentro dela. Se tudo `✅`, uma linha basta.

## Guardrails

- **Read-only**: só GET em status pages públicos. Nunca autentica, nunca muda nada.
- **Mostra o QUÊ, não só o nível**: sempre liste os produtos/regiões degradados quando houver — é o que permite julgar impacto. Nunca reduza a só "🟡 minor".
- **Não invente status**: serviço `❔` (timeout/erro) = "não consegui checar" — não afirme ok nem fora.
- **AWS por recência**: eventos com mais de 7 dias no feed **não** são incidente atual; não os reporte como ativos.
- **Sem polling automático**: check pontual. Pra monitorar em intervalo: `/loop <intervalo> /status-deps`.
