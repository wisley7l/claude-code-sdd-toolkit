# Reference: pair de testes (/sdd-plan — Passo 7.5)

> Carregado sob demanda pelo `/sdd-plan` no Passo 7.5, **antes** de quebrar tarefas.
>
> **Objetivo**: o usuário vê o quadro completo em tela — o que temos, o que não temos,
> o que esta feature adiciona e pra onde a cobertura caminha — **antes de qualquer teste
> ser escrito**, e decide os pontos que são de produto. A IA propõe; quem corta,
> prioriza e aceita risco é o usuário.

## Por que este passo é interativo

Matriz de testes montada de forma autônoma tira a mão do produto: quando o quadro aparece
consolidado no checkpoint (Passo 10), já não há espaço pra discutir **quais cenários
importam**. Testes são a codificação do comportamento esperado — decidir isso sozinho é
decidir produto sozinho. Este passo devolve essa decisão ao usuário, com a IA fazendo o
trabalho pesado (inventário, propostas, trade-offs) e o usuário fazendo as escolhas.

**Não é um checkpoint de aprovação** ("tá bom assim?"). É uma sessão de par: propostas com
recomendação explícita, divergências expostas, decisão dele registrada com autoria.

## Fluxo (5 etapas)

| Etapa | O que acontece | Quem faz |
|---|---|---|
| 1 | Inventário: o que já é testado nos componentes tocados | subagente `Explore` |
| 2 | Proposta de cobertura por RF/AT, em 3 lentes paralelas | 3 subagentes |
| 3 | **Mapa de Testes em tela** — quadro completo, bloqueante | main |
| 4 | Discussão dos pontos que precisam do usuário, um por vez | main ↔ usuário |
| 5 | Fechamento: matriz final + rastro de decisões | main |

Etapa 3 é **bloqueante e sem atalho**: nenhuma tarefa é quebrada (Passo 8) antes do mapa
ir pra tela e a etapa 4 fechar.

---

## Etapa 1 — Inventário (o que temos hoje)

Pros componentes que a feature toca (do Passo 3), levante:

- Que arquivos de teste existem e o que cada um cobre hoje
- **Contagem baseline** por arquivo/suíte (alimenta o test count protection das tarefas)
- Padrão reusável (fixtures, factories, helpers) — poupa tokens na execução
- Lacunas **já existentes** nesses componentes (não criadas por esta feature)

Delegue a um subagente `Agent` (`subagent_type: Explore`) quando for varredura ampla —
devolve só a síntese. Profundidade: **Large/Complex** = módulos afetados + vizinhos;
**Medium** = só os arquivos diretamente tocados.

---

## Etapa 2 — Três lentes em paralelo

As 3 rodam **no mesmo turno** (emita as 3 chamadas `Agent` numa única resposta — ver
`[[subagent-paralelismo-mesmo-turno]]`; turnos separados serializam):

- `subagent_type: general-purpose`
- `model: opus` (no `/sdd-plan-eco`: `sonnet`)
- `description`: `"Lente Produto/QA"` / `"Lente Engenharia de teste"` / `"Lente Adversarial"`

**Proporcionalidade** (evita gastar 3 Opus em escopo trivial):

| Situação | Lentes |
|---|---|
| Default | 3 lentes |
| `--rapido` | 2 — Produto/QA + Engenharia (adversarial embutido na de Produto/QA) |
| `--solo`, ou ≤2 RF/AT com `Ambiente: none` em todos | 0 — a main propõe o mapa direto |

Com 0 lentes, as etapas 3, 4 e 5 continuam **obrigatórias**: o que se corta é a diversidade
de propostas, nunca a tela e a decisão do usuário.

### As lentes (focos disjuntos)

- **Produto/QA** — parte das histórias e critérios de sucesso da SPEC: que cenário real de
  uso cada RF/AT representa? O que dói pro usuário se quebrar? Prioriza por **impacto no
  usuário**, não por facilidade de testar. Sinaliza RF/AT cujo valor só existe na jornada
  completa (indício de e2e).
- **Engenharia de teste** — tipo pela natureza do comportamento (lógica pura → unit;
  interação entre módulos/DB/fila → integração; fluxo de usuário/tela/rota → e2e);
  ambiente exigido; estratégia de mock (o que é real, o que é dublê); **custo e risco de
  flakiness**; reuso de fixtures/factories existentes; onde o arquivo fica.
- **Adversarial** — o que ninguém pensou: edge, negativo, caminho de erro, concorrência e
  ordering, dado sujo, limites, idempotência, timeout. **Não repete happy path.** Cada caso
  vem com "o que quebra na prática se isto não for testado".

### Prompt (base comum — troque só a linha de foco)

```
Você é a Lente [Produto/QA | Engenharia de teste | Adversarial] no planejamento
de testes de uma feature.

Seu foco: [<lente, da lista acima>].

SPEC de comportamento: <path da SPEC> (leia na íntegra — RFs e ATs numerados)
Constitution: CLAUDE.md / ARCHITECTURE.md
Convenções de teste do projeto:
---
<síntese do passo 6 da Configuração inicial: framework, runner, comando por tipo,
estrutura/naming, mocking, fixtures, onde ficam, ambiente por tipo>
---
Cobertura existente (inventário da etapa 1):
---
<síntese: arquivos de teste, o que cobrem, contagem baseline, lacunas atuais>
---
Componentes que a feature toca:
---
<paths + 1 linha do papel de cada>
---

Proponha a cobertura de teste para CADA RF/AT da SPEC, sob a SUA lente
(as outras lentes cobrem o resto — não tente cobrir tudo).

Regras:
- Tipo por NECESSIDADE, não por default: unit não é a resposta automática.
- Nunca só happy path.
- NÃO invente requisito que não está na SPEC. Se um comportamento parece faltar
  na SPEC, registre em `lacunas_da_spec` — não crie o requisito.
- Marque explicitamente o que exige ambiente real (server local, browser, sandbox).
- Onde a decisão é de PRODUTO (o cenário vale o custo? o caso acontece na
  prática?), NÃO decida: coloque em `duvidas_pro_usuario` com recomendação.

Retorne SOMENTE JSON válido:

{
  "por_rf": [
    {
      "rf": "RF3",
      "tipo": "unit" | "integracao" | "e2e",
      "por_que_esse_tipo": "<1 frase>",
      "casos": [
        {"caso": "<nome do cenário>",
         "categoria": "happy" | "edge" | "negativo" | "erro",
         "por_que_importa": "<o que quebra se não testar>"}
      ],
      "ambiente": "none" | "server-local" | "browser-playwright" | "sandbox",
      "prioridade": "critico" | "importante" | "marginal",
      "custo": "baixo" | "medio" | "alto",
      "reusa": "<fixture/factory/helper existente, ou —>"
    }
  ],
  "gaps_preexistentes": [
    {"componente": "<path>", "o_que_falta": "...", "por_que_importa": "..."}
  ],
  "duvidas_pro_usuario": [
    {"ancora": "RF3" | "AT2",
     "pergunta": "<decisão de produto, 1 frase>",
     "opcoes": ["<a>", "<b>"],
     "recomendacao": "<qual e por quê>"}
  ],
  "lacunas_da_spec": [
    {"ancora": "RF3", "o_que_falta_especificar": "..."}
  ]
}
```

### Reconciliação na main (antes da tela)

1. Agrupe as propostas por RF/AT e classifique cada linha:
   - ✅ **consenso** — as lentes concordam em tipo e o conjunto de casos é compatível
   - ⚠️ **divergência** — lentes discordam do tipo, do ambiente ou do valor de um caso
   - ❓ **decisão sua** — apareceu em `duvidas_pro_usuario`, ou é corte/custo/prioridade
2. Deduplique casos equivalentes com nomes diferentes (mantenha o enunciado mais claro).
3. **Verifique você mesmo** as afirmações técnicas (arquivo existe? fixture existe? o
   ambiente é mesmo exigido?) — lente erra. Descarte o inválido registrando o motivo.
4. `lacunas_da_spec` não vira teste inventado: some as lentes e leve como aviso na tela.
   Lacuna real de comportamento = **volte pro `/sdd-spec`** (guardrail do `/sdd-plan`).

---

## Etapa 3 — Mapa de Testes em tela (bloqueante)

Antes de discutir qualquer ponto, mostre o quadro inteiro. É o que dá ao usuário a visão
de **o que temos, o que não temos e pra onde estamos caminhando**.

```
# Mapa de Testes — <feature>
SPEC: <path> · <N> RF/AT · <M> componentes tocados · <K> lentes consultadas

## 1. O que temos hoje
| Componente | Testado por | Cobre hoje | Testes |
|---|---|---|---|
| `path/x.ts` | `x.spec.ts` | happy path do cálculo | 6 |
| `path/y.ts` | — | nada | 0 |
Baseline: <N> testes nos componentes tocados.

## 2. O que NÃO temos
### Desta feature (vira teste novo)
| RF/AT | Comportamento sem teste hoje | Impacto se quebrar |
|---|---|---|
| RF3 | estorno parcial | usuário vê valor errado |

### Já existente nos componentes tocados (fora do escopo desta feature)
| Componente | Lacuna | Sugestão |
|---|---|---|
| `path/y.ts` | sem teste nenhum | item separado no roadmap |
→ Fora de escopo: não viram tarefa deste PLAN, a não ser que você peça.

## 3. O que esta feature adiciona (proposta)
| RF/AT | Tipo | Casos | Ambiente | Prio | Custo | |
|---|---|---|---|---|---|---|
| RF1 | unit | happy, zero, negativo | none | crítico | baixo | ✅ |
| RF3 | integração | 4 casos | sandbox | crítico | alto | ⚠️ |
| AT2 | e2e | 6 casos | server-local + Playwright | importante | alto | ❓ |
✅ consenso das lentes · ⚠️ lentes divergem · ❓ precisa da sua decisão

## 4. Pra onde caminhamos
- Cobertura: <N> testes hoje → <M> depois (+<K>) · <a> unit / <b> integração / <c> e2e
- Ambiente novo exigido: <sandbox de pagamento / Playwright / nenhum>
- Custo de suíte: <sinal de tempo — e2e novo pesa no CI>
- Fica de fora (dívida): <lacuna pré-existente, caso cortado>
- Risco que sobra: <o que continua sem rede de proteção depois deste PR>

<X> pontos precisam de você (⚠️/❓). Antes de entrar neles: esse quadro
representa o que você tem em mente pra essa feature?
```

**Regras da tela**:
- Números reais — contagem do inventário, não estimativa inventada. Sem dado, escreva `?`.
- Bloco 4 é obrigatório: é a parte "pra onde estamos caminhando". Nunca omita.
- Se a resposta do usuário ao quadro reenquadrar a feature (ex.: "esse fluxo aí nem é o
  principal"), isso é sinal de **lacuna da SPEC** — trate antes de seguir.

---

## Etapa 4 — Discussão dos pontos (um por vez)

Todos os pontos ⚠️/❓ já estão visíveis no bloco 3. Resolva **em ordem de impacto**
(crítico → importante → marginal), um por turno, mantendo o progresso à vista:

```
Ponto <i> de <N> — <âncora: RF3>

Produto/QA:  <posição> — <motivo em 1 linha>
Engenharia:  <posição> — <motivo em 1 linha>
Adversarial: <posição> — <motivo em 1 linha>

Trade-off: <o que se ganha vs o que se perde, 1 linha>
Minha recomendação: <qual, e por quê>

<pergunta fechada>
```

- **Opções discretas (2-4)** → `AskUserQuestion`, com a recomendação como primeira opção
  marcada `(Recomendado)`.
- **Pergunta aberta** ("quais desses cenários acontecem de verdade?") → texto, sem menu.
- Omita as linhas de lente quando não houve divergência (ponto ❓ puro de produto).

### Regras de decisão

- **A decisão do usuário vence sempre** — inclusive contra as 3 lentes. Registre e siga;
  no máximo uma linha anotando o risco aceito. Não reargumente o ponto já decidido.
- **Caso que o usuário adiciona** e nenhuma lente propôs → marque `[fonte: usuário]` na
  matriz. É sinal de conhecimento de produto que a IA não tinha: candidato a `lesson` no
  `/sdd-learning`.
- **Caso cortado** → não desaparece: vai pra "dívida/risco aceito" da seção 6 do PLAN, com
  o motivo dado pelo usuário.
- **RF/AT que fica sem teste nenhum** → só com justificativa explícita, e a tarefa nasce
  com `Tests: none` justificado (o Check 3 do Passo 9 cobra isso).
- **Usuário pede teste de comportamento que não está na SPEC** → é lacuna da SPEC: pare e
  ofereça voltar pro `/sdd-spec`, ou registre como fora de escopo. Não invente RF.
- **Revalidação barata**: se a decisão abrir um tipo/ambiente que nenhuma lente avaliou
  (ex.: um RF virou e2e com Playwright), rode **só a lente de Engenharia** de novo pra
  conferir ambiente, custo e mock. Não rode o painel inteiro por isso.
- Se o usuário mudar linhas do bloco 3, reapresente **só o delta** (blocos 3 e 4
  atualizados), não o mapa inteiro.

---

## Etapa 5 — Fechamento

Consolide e mostre em 1 tela curta:

```
Mapa fechado — <N> RF/AT cobertos · <a> unit / <b> integração / <c> e2e
Ambiente exigido: <...>

| # | Ponto | Decisão | Quem decidiu | Motivo / risco aceito |
|---|---|---|---|---|
| 1 | RF3: tipo | integração | você | e2e ficaria flaky no gateway |
| 2 | AT2: 2 casos cortados | cortados | você | não acontece na prática |
| 3 | RF6 sem teste | risco aceito | você | sandbox indisponível |

Vou quebrar as tarefas herdando esta matriz.
```

A matriz final e essa tabela de decisões vão pra **seção 6 do PLAN** (`6.3 Matriz`,
`6.5 Decisões do pair de testes`, `6.6 Dívida e risco aceito`). Cada tarefa do Passo 8
herda daqui `Tests:`, `Test env:` e os casos — **a tarefa não reinventa a estratégia**.

Resumo pro checkpoint do Passo 10:

```
## Plano de Testes (pair)
- Hoje: [N testes] → depois: [M] (+K) — [a unit / b integração / c e2e]
- Ambiente: [server-local / Playwright / sandbox / nenhum]
- Decidido com você: [X pontos] ([Y cortes], [Z casos adicionados por você])
- Dívida aceita: [lista curta]
```

---

## Guardrails

- **A tela vem antes da decisão**: nada é quebrado em tarefa antes do Mapa ir pra tela e a
  etapa 4 fechar. Sem atalho, em nenhum escopo.
- **Bloco 4 ("pra onde caminhamos") é obrigatório** — cobertura antes/depois, ambiente novo,
  dívida, risco restante.
- **A IA propõe, o usuário decide** — corte, prioridade e "vale o custo?" são dele.
- **Tipo por necessidade**: unit não é default; o tipo sai do comportamento do RF/AT.
- **Nunca invente RF**: lacuna da SPEC volta pro `/sdd-spec`.
- **Nada se perde em silêncio**: caso cortado vira dívida registrada, não esquecimento.
- **Rastro de autoria**: a matriz distingue o que a IA propôs do que o usuário decidiu.
