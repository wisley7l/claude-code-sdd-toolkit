# Reference: revisão por painel de subagentes (/sdd-plan)

> Carregado sob demanda pelo `/sdd-plan` no Passo 9.5 (entre os 4 checks e o checkpoint).
> Inspirado na gist "plan" por @parruda — adaptado à filosofia do toolkit: achados
> estruturados (não "APPROVED" cego), verificação de cada achado antes de aplicar,
> subagentes Opus pra julgamento (ver `[[modelo-leve-subagente]]`), lentes diversas
> (perspective-diverse verify) em vez de reviewers redundantes.

## Quando roda

- **Por default em todo escopo** — Medium, Large e Complex. Quick não chega aqui (foi encaminhado pro `/quick-task` no Passo 1).
- **Flags** (de `$ARGUMENTS`): `--rapido` roda só **Pro + Fast**; `--solo` pula o painel (fica só nos 4 checks self-run).
- O `/sdd-plan-eco` também roda sem painel por design.

## Painel — 4 lentes disjuntas

Perspectivas diferentes pegam falhas que redundância não pega. As lentes NÃO se sobrepõem:

- **Reviewer Pro** — arquitetura, consistência com codebase/constitution/ADRs, decisões técnicas embasadas, reaproveitamento (`Reuses:`), **rastreabilidade estrutural** (todo RF/AT tem tarefa em `Covers:`), riscos arquiteturais.
- **Reviewer Fast** — clareza e ausência de ambiguidade, completude dos detalhes de implementação (dá pra executar sem chutar?), granularidade das tarefas (nem gigante nem fatiada demais), diagrama x dependências.
- **Reviewer Security** — domínio pagamentos/e-commerce: verificação de assinatura HMAC de webhook, idempotência de operações que mutam pagamento, money handling (inteiros/decimal, **nunca float**), PCI (não logar cartão/CVV/dado sensível), authz, validação runtime de input não-confiável (Zod/schema do projeto), race conditions e ordering de webhook. **APPROVED rápido se o plano não toca nenhuma superfície sensível — não invente risco.**
- **Reviewer Tests** — todo RF/AT tem teste que o *exercita* (não só a tarefa que o entrega), test co-location respeitada, gate e test count coerentes, casos de borda/negativos e caminhos de erro cobertos, estratégia de mock (sandbox vs unit).

## Como disparar

As 4 lentes rodam **em paralelo, no mesmo turno** (emita as 4 chamadas `Agent` numa única resposta — ver `[[subagent-paralelismo-mesmo-turno]]`; turnos separados serializam). Cada uma:

- `subagent_type: general-purpose`
- `model: opus`
- `description`: `"Reviewer Pro"` / `"Reviewer Fast"` / `"Reviewer Security"` / `"Reviewer Tests"`
- `prompt`: o **draft completo do PLAN** (inline, montado no contexto da main nos Passos 8-9 — o arquivo ainda não foi escrito, o checkpoint vem depois) + o path da SPEC (o subagente lê) + paths de `CLAUDE.md`/`ARCHITECTURE.md` + a lente + o formato de saída.

## Prompt (base comum às 4 lentes — só troque a linha de foco)

```
Você é o Reviewer [Pro | Fast | Security | Tests].
Seu foco: [<lente do reviewer, da lista acima>].

Avalie o PLAN abaixo contra a SPEC de comportamento em: <path da SPEC>
(leia a SPEC na íntegra) e a constitution (CLAUDE.md / ARCHITECTURE.md).

PLAN (draft, ainda não escrito em arquivo):
---
<draft completo do PLAN>
---

Critérios (avalie SÓ pela sua lente de foco — as outras lentes cobrem o resto):
- Cobertura: o que é do seu foco na SPEC virou tarefa/teste no plano?
- Precisão e consistência com o codebase e a constitution.
- Riscos e lacunas dentro do seu foco.

NÃO reescreva o plano. NÃO invente requisito que não está na SPEC.
Se sua lente não se aplica a este plano (ex.: Security num plano sem superfície
sensível), retorne APPROVED sem findings — não force achado.
Retorne SOMENTE JSON válido neste formato:

{
  "verdict": "APPROVED" | "CHANGES",
  "findings": [
    {
      "severidade": "must-fix" | "should" | "nit",
      "ancora": "RF3" | "AT2" | "T4" | "seção X",
      "problema": "<1-2 frases: o que está errado/faltando>",
      "correcao": "<ajuste concreto sugerido>"
    }
  ]
}

`verdict: "APPROVED"` só quando NÃO houver nenhum finding `must-fix`.
Se estiver tudo certo, retorne `{"verdict":"APPROVED","findings":[]}`.
```

## Loop de reconciliação (na main)

1. Junte os findings das 4 lentes.
2. **Verifique cada `must-fix` você mesmo** contra a SPEC/codebase antes de aplicar — reviewer pode errar. Aplique só os válidos; descarte os inválidos registrando o motivo (1 linha) pra levar ao checkpoint.
3. `should`/`nit`: aplique se barato e claramente melhor; senão, anote como observação no PLAN.
4. Se aplicou algum `must-fix` → **nova rodada com subagentes frescos** (novo painel, contexto limpo). Repita até **todo o painel** retornar `APPROVED` (zero `must-fix` válido).
5. **Guarda de convergência** (espelha o `/pr-ready`): se uma rodada **não reduz** a contagem de `must-fix` válidos, ou após **3 rodadas**, pare e leve os itens abertos ao checkpoint (Passo 10) pro usuário decidir — não fique em loop.

**Teto de custo**: 4 lentes × até 3 rodadas. Na prática os especialistas (Security/Tests) curto-circuitam com `APPROVED` quando seu domínio não aparece no plano, então o custo real escala com a superfície do plano, não com burocracia.

## Saída pro checkpoint (Passo 10)

Adicione uma linha ao preview:

```
## Revisão por painel (Pro / Fast / Security / Tests)
- Aprovada em [N] rodada(s) — 0 must-fix aberto
  (ou) Aberta: [X] must-fix não resolvidos após [N] rodadas → [lista curta por lente]
- Findings aplicados: [contagem]; descartados (com motivo): [contagem]
```
