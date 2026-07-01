---
description: Investigação de bug não-óbvio via protocolo de hipóteses — evidência em subagents paralelos, root cause com fonte, handoff pra /quick-task ou /sdd-plan. Alimenta blockers/lessons na memória.
model: claude-sonnet-5
allowed-tools: Read, Write, Glob, Grep, Agent, Skill, AskUserQuestion, Bash(git log*), Bash(git diff*), Bash(git show*), Bash(git blame*), Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(gh *), Bash(npm *), Bash(npx *), Bash(bun *), Bash(bunx *), Bash(pnpm *), Bash(node *), Bash(go *), Bash(ls *), Bash(mkdir *), Bash(grep *), WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Investiga — root cause de bug não-óbvio

Você investiga problemas cuja causa **não é óbvia** — o meio-termo entre `/quick-task` (root cause conhecido, só corrigir) e `/sdd-plan` (exige redesign). O método: sintoma estruturado → hipóteses com mecanismo causal → evidência em paralelo → eliminação → root cause **com fonte**. Você não conserta — entrega a causa provada e o handoff.

**Quando NÃO usar**: causa já conhecida (`/quick-task` direto); "investigar" genérico sem sintoma concreto (`/busca`).

## Princípios

- **Hipótese exige mecanismo causal**: "algo no cache" não entra. "O TTL do cache X (30s) expira antes do retry do worker Y (60s), então o retry lê dado frio" entra
- **Evidência decide, não plausibilidade**: cada hipótese é confirmada/eliminada por evidência citável (`path:linha`, log, commit, doc oficial)
- **Memória primeiro**: blockers/lessons conhecidos podem resolver em 1 passo
- **Produção é read-only**: logs e dados podem ser lidos; nada é executado/alterado em produção
- **Reprodução sem efeito colateral**: nunca rode migration, delete ou operação destrutiva pra reproduzir sem OK explícito

## Fluxo

### 1. Sintoma estruturado

Capture (pergunte o que faltar):

```
Sintoma: [o que acontece, literal — mensagem de erro, comportamento errado]
Esperado: [o que deveria acontecer]
Desde quando: [data/deploy/sempre]
Onde: [local/dev/staging/produção · serviço/endpoint/job]
Reprodutível: [sempre/às vezes/uma vez · como]
Evidência bruta: [stack trace, log, screenshot, link]
```

### 2. Memória primeiro

No `MEMORY.md` (já carregado), procure `blocker`/`lesson` cujo hook bata com o sintoma. Match → abra a nota, apresente ("blocker_X documenta exatamente isso: workaround Y") e pergunte se encerra por aí.

### 3. Delimitar o quando (se "desde quando" é conhecido)

`git log --since=<data> --oneline -- <área suspeita>` — mudanças recentes na área são as primeiras suspeitas. PR/deploy correlacionado entra como evidência.

### 4. Reproduzir (se viável)

Tente o repro mínimo: teste em `thoughts/tests/` que demonstra o sintoma, ou comando que o dispara. Conseguiu → vira o critério de verificação do fix. Não conseguiu → siga com evidência estática e marque `[SEM REPRO]` no relatório.

### 5. Hipóteses (3-6)

Liste cada uma com: **mecanismo causal** (por que causaria exatamente este sintoma) + **evidência que confirmaria** + **evidência que eliminaria**. Hipóteses devem ser distinguíveis entre si — duas hipóteses que a mesma evidência confirma são uma só.

### 6. Verificação em paralelo

Pra cada hipótese, um subagente `Agent` (`subagent_type: Explore`) busca a evidência no codebase/logs/git.

> **Paralelismo real = todas as chamadas `Agent` numa ÚNICA mensagem** (múltiplos blocos no mesmo turno). Lançar uma por vez serializa.

Prompt de cada um: a hipótese + mecanismo + onde procurar + regra de output: "Retorne veredito CONFIRMA / ELIMINA / INCONCLUSIVO + evidência (path:linha ou trecho de log) + 1-2 linhas. Sem narrativa."

Hipótese envolvendo comportamento de lib/API externa: verifique via Context7/doc oficial (Zero Inferência) — comportamento de lib assumido errado é root cause clássico.

### 7. Eliminação

- **Sobrou 1 confirmada** → root cause. Valide: o mecanismo explica TODOS os fatos do sintoma (inclusive o "desde quando")? Fato não explicado = causa parcial, continue.
- **Sobraram 2+** → proponha o discriminador: qual evidência/instrumentação separa as duas? (log temporário, teste dirigido, pergunta ao usuário sobre o ambiente).
- **Sobrou 0** → refine: o que as eliminações ensinaram? Nova rodada de hipóteses (máx **3 rodadas**; depois, apresente o mapa do que foi eliminado e discuta com o usuário — investigação sem fim é smell de falta de observabilidade).

### 8. Relatório + handoff

Salve `thoughts/research/INV-DD-MM-YYYY-[slug].md`:

```markdown
# Investigação: [sintoma em 1 linha]

Data · Reprodutível: [como / SEM REPRO]

## Root cause
[mecanismo completo, com evidência: path:linha, commit, log]

## Hipóteses testadas
| Hipótese | Veredito | Evidência |
|---|---|---|

## Fix sugerido
[direção do fix + arquivos prováveis]

## Verificação do fix
[o repro do passo 4, ou como provar que resolveu]
```

Handoff:
- Fix ≤3 arquivos, sem decisão arquitetural → **`/quick-task`** (o INV vira contexto)
- Fix exige redesign/decisão → **`/sdd-spec`** (especifica o novo comportamento) → **`/sdd-plan`** (o INV vira input da pesquisa)
- Workaround temporário existe → registre no relatório com prazo de validade

### 9. Memória (a colheita mais valiosa deste command)

Proponha (confirmação por item, via skill `memory-keeper`):
- Sintoma + causa + workaround → `blocker`
- "Parecia X, era Y" / armadilha do domínio → `lesson`

## Guardrails

- **Nunca conserte sem root cause confirmado** — "parou de dar erro" não é causa. Fix sem causa entendida volta
- **Hipótese sem mecanismo causal não entra na lista**
- **Toda conclusão cita evidência** (`path:linha`, log, commit, doc)
- **Produção read-only; repro destrutivo só com OK**
- **Máx 3 rodadas de hipóteses** — depois, devolva ao usuário com o mapa do eliminado
- **Lib externa = verificar na doc** (Context7/oficial), nunca assumir comportamento
- **Nunca commita/pusha**
