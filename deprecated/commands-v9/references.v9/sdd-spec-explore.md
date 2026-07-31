# Reference: 🧭 Modo Explore do `/sdd-spec`

Protocolo do `/sdd-spec --explore`: a fase **sem compromisso** que antecede a especificação. Pesa direções antes de existir SPEC.

Carregado **apenas** quando a flag `--explore` é passada — quem vai direto pra SPEC não paga esse contexto.

## O que o explore é (e não é)

O explore responde **"o que devemos fazer aqui, e vale a pena?"**. Ele termina numa **decisão**, não num arquivo.

- **NÃO escreve arquivo nenhum.** Sem SPEC, sem PLAN, sem doc em `thoughts/`. Guardrail duro — se você se pegar montando template de SPEC, pare: a decisão ainda não foi tomada.
- **Pesa direção, não desenho.** "Estender o modelo atual" vs "tabela nova" é direção (explore). "Criar a função `applyCoupon` em `pricing/coupon.ts`" é desenho — é do `/sdd-plan`, não faça aqui.
- **Pode terminar em "não fazer".** Esse é um resultado legítimo e frequentemente o mais valioso: evita SPEC de coisa que não se sustenta.

### Quando o explore é desperdício

Se o usuário já descreveu o comportamento com clareza e só quer o documento, o explore é overhead. Detecte e diga:

```
Sua demanda já está clara e não vejo direções concorrentes a pesar.
Sugiro ir direto pra SPEC (/sdd-spec sem --explore). Quer explorar mesmo assim?
```

Se a demanda é **bug de causa desconhecida**, não é explore — é `/investiga`. Encaminhe.

## Fluxo

### E1 — Contexto (o que já existe)

Na ordem, parando quando tiver o suficiente:

1. **Constitution** — `CLAUDE.md` / `ARCHITECTURE.md`: o que é possível e desejável aqui.
2. **Capabilities** — `thoughts/capabilities/*.md` do domínio da demanda. É o que o sistema **promete hoje** sem reler código. Reference `capability-template.md`. Ausente → siga sem (não é dependência).
3. **Memória** — o `MEMORY.md` já está carregado. Abra notas do domínio: `decision` (já decidimos isso?), `blocker` (já tentamos e travou?), `idea` (já foi adiado antes?).

Uma direção que já foi decidida ou já travou antes **não** volta pra mesa como novidade — traga com o histórico: *"isso foi adiado em <nota> porque X"*.

### E2 — Custo estrutural (o `structure-cache`)

É o que diferencia este explore de uma conversa: cada direção candidata recebe **custo medido**, não estimado.

```bash
structure-cache query --importers <arquivo que a direção tocaria>   # blast radius
structure-cache query --hotspots --top 10                           # a direção mexe num god-node?
```

- `exit 3` (sem cache) → `structure-cache build` e reconsulte (barato, sem LLM).
- Stale → `structure-cache build`.
- Sem servir → **fallback gracioso**: Grep/Glob/Read. Aceleração, nunca dependência.
- **Ao delegar a subagente `Explore`, repita a diretiva no prompt dele** — ele não herda o corpo do command e vai direto ao Grep.

`structure-cache open` (abre o grafo no navegador) **só sob pedido do usuário** — é side effect, não rode por iniciativa própria.

Escopo do `sc` é TS/JS. Em outra stack, o custo estrutural vem do Grep e você **diz** que é estimado, não medido.

### E3 — Painel de direções

Duas ou três direções. Uma só não é escolha; mais de três é ruído.

```
## Explore — <demanda>

**O que o sistema já promete aqui**
- checkout C1: no máximo um cupom por pedido [spec-1730… · PR #142]
- (ou: sem capability pro domínio — comportamento atual lido do código)

**Histórico relevante**
- Cupom cumulativo já foi adiado em <nota de memória> porque <motivo>

**Onde isso encosta** (structure-cache)
- src/checkout/cart.ts — 23 importadores ⚠️ hotspot #2
- src/pricing/coupon.ts — 4 importadores

### Opção A — <nome curto>
**Direção**: <1-2 linhas — o QUE muda no comportamento, não como>
**Custo estrutural**: toca N arquivos · M importadores · <hotspot? sim/não>
**Trade-off**: + <ganho concreto> / − <custo concreto>
**Mexe no que já é prometido**: modifica checkout C1 | nada

### Opção B — <nome curto>
...

**Recomendação**: <A|B>, porque <motivo em 1 linha>.

Como seguir?
  (1) SPEC da opção <X>        → /sdd-spec (levo este contexto)
  (2) quick-task               → escopo trivial, sem SPEC formal
  (3) /investiga primeiro      → falta entender a causa antes de decidir
  (4) não fazer agora          → registro como idea e paramos aqui
```

**Dê recomendação, sempre.** Painel sem recomendação empurra a decisão de volta pro usuário sem agregar julgamento. Mas a escolha é dele — corte, prioridade e risco aceito são do usuário.

### E4 — Fechar na decisão

| Escolha | O que fazer |
|---|---|
| **(1) SPEC** | Siga pro fluxo normal do `/sdd-spec` a partir do **Passo 2**, carregando o contexto do explore (capabilities lidas, custo estrutural, direção escolhida). Não repita a pesquisa do E1/E2. |
| **(2) quick-task** | Encerre apontando `/quick-task`. Passe a direção escolhida. |
| **(3) investiga** | Encerre apontando `/investiga`. Passe as hipóteses levantadas. |
| **(4) não fazer** | Ofereça registrar nota `idea` (via `memory-keeper`), **sob confirmação**: a direção, por que foi adiada e o que mudaria a decisão. Encerre. |

A opção (4) é o que impede o explore de ser trabalho perdido: a próxima vez que a ideia aparecer, o histórico já está lá.

## Guardrails

- **Nunca escreva arquivo em `thoughts/`** — o explore não produz documento. Sem exceção.
- **Nunca escreva código.** Nem protótipo, nem rascunho.
- **Nunca escreva na memória sem confirmação** — a nota `idea` da opção (4) é oferecida, não aplicada.
- **Direção, não desenho** — desenho de implementação é do `/sdd-plan`.
- **Custo medido ou declarado como estimado** — nunca apresente número de blast radius sem ter rodado o `sc` (ou diga que é estimativa do Grep).
- **Histórico antes de propor** — direção já decidida/travada vem com a nota de memória, não como ideia nova.
- **Sempre termine numa das 4 saídas.** Explore que acaba em "e agora?" falhou.
- **Máximo 3 direções.**
