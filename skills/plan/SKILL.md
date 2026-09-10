---
name: plan
description: Escreve o plano técnico de uma mudança já especificada — o COMO. Pesquisa o codebase, fecha as decisões técnicas com fonte, e quebra em tarefas agrupadas por PR, cada uma com contrato, passos e verificação. Não escreve código nem re-especifica comportamento.
disable-model-invocation: true
argument-hint: <pasta da mudança em thoughts/changes/, ou nada pra usar a mais recente>
allowed-tools: Read Grep Glob Write Edit Agent AskUserQuestion Bash(ls *) Bash(mkdir *) Bash(git log*) Bash(git diff*) Bash(git worktree list*) Bash(gh *) Bash(structure-cache *) Bash(structure-cache) Bash(roadmap:*) Bash(roadmap) WebFetch mcp__context7__resolve-library-id mcp__context7__query-docs
---

# plan

Recebe o comportamento já especificado e decide **como** entregá-lo: a abordagem, as decisões
técnicas e a quebra em tarefas executáveis, agrupadas nos PRs que vão nascer.

Você investiga, decide e organiza. **Código é da execução.** Comportamento é da `spec` — se
descobrir aqui que falta comportamento, ou que a spec está errada, pare e volte lá; improvisar
requisito no plano é como escopo entra de contrabando.

## Entrada

`<root>/thoughts/changes/<NNN>-<slug>/spec.md`, onde **`root` é o repositório principal**
(`git worktree list | head -1`) — `thoughts/` é gitignored, e dentro de uma worktree o diretório
local está vazio. Vale para toda leitura e escrita em `thoughts/`.

Sem argumento, use a pasta de mudança mais recente e confirme qual antes de seguir. Sem spec nenhuma, ofereça rodar a `spec` primeiro — o plano se
apoia nela, e toda tarefa daqui rastreia a um requisito dela.

## O legwork técnico

Responda na fonte mais barata, nesta ordem, e **pare quando souber o suficiente pra decidir**:

| Pergunta | Fonte |
|---|---|
| Que decisão estrutural já foi tomada aqui? | `CLAUDE.md`, `ARCHITECTURE.md`, ADRs em `docs/adr/` (se houver), RFCs |
| Como o projeto já resolve problema parecido? | Grep/Read no código — subagente `Explore` se for varredura ampla |
| O que já está instalado? | manifest de dependências, antes de cogitar lib nova |
| O que quebra se eu mexer aqui? | `structure-cache query --importers <file>` |
| Por que ficou assim? | `git log` / `git blame` |
| Como essa API externa se comporta? | Context7, ou o código que já a usa |

**Zero inferência.** Toda afirmação sobre biblioteca ou API externa carrega `[Fonte: url]` ou
`[Fonte: arquivo:linha]`. Comportamento de API se verifica — no Context7 ou no código que já
chama. Sem fonte, a afirmação entra marcada `[A VERIFICAR]` e **não** vira base de tarefa.

Ao delegar a subagente, **repita no prompt dele** a diretiva de consultar o `structure-cache`
antes de grepar, e a de trazer `arquivo:linha` em toda afirmação — subagente não herda isto.

## Decisões que não são suas

Invoque `grilling` quando aparecer decisão cara de reverter, **nomeando quais são antes da
primeira pergunta**: escolha de biblioteca ou dependência nova, contrato e formato de dado
(migração + consumidor externo), estratégia de migração de dado existente, e qualquer conflito
entre a abordagem e um design doc do projeto.

**Conflito com design doc bloqueia.** Se `ARCHITECTURE.md` define X e a mudança precisa de Y,
não escolha em silêncio: mostre as saídas (respeitar o doc, atualizar o doc junto, ou tratar o
doc como desatualizado) e deixe a decisão com ele.

Fora dessas, decida e **mostre o que assumiu**, uma linha por suposição.

## Antes de quebrar tarefas, o plano de testes

**Pare aqui e peça a matriz de testes**, com esta frase e nada depois dela:

> Decisões técnicas fechadas. Antes de quebrar as tarefas, rode **`/tk7:test-plan`** — a matriz
> de testes decide o tipo, o ambiente e o que fica sem rede. Volte pra cá quando ela fechar.

Você **não invoca** a skill: nenhuma peça deste toolkit invoca outra. Espere o usuário voltar, e
então leia a seção `## Testes` do `plan.md`. **A quebra de tarefas herda essa matriz**, nunca a
reinventa.

Ordem que não inverte: matriz fechada → tarefas. Quebrar tarefas antes é decidir cobertura por
omissão, que é a decisão mais silenciosa do ciclo.

## As tarefas

Vão em `thoughts/changes/<NNN>-<slug>/tasks.md`, **agrupadas pelo PR em que vão nascer** — é
esse arquivo que muda de estado durante a execução, enquanto o `plan.md` fica parado.

```markdown
# Tarefas — <slug>

## Mapa dos PRs
<a tabela e as ondas — ver "O mapa dos PRs">

## PR 1 · <título do slice> — 6 arquivos
> Fecha R1, R2. Não depende de nada.

- [ ] **T1 · R1** — <o que entrega, uma frase>
      `src/refund/calc.ts` · reusa `test/factories/order.ts`
      **Contrato:** `calcRefund(order: Order, amount: Money) → Result<Refund, RefundError>`
        · `order` ← `OrderRepo.byId` (`src/http/refund.ts:34`) · `amount` ← body, validado no schema
        · efeito: nenhum · erro: `RefundError` propagado pro handler
      **Passos:** 1. soma os estornos anteriores do pedido · 2. valida `amount` contra o saldo
        · 3. monta o `Refund` · 4. devolve o `Result`
      **Verificação:** unit · env `none` · `npm test refund` · 12 → 17 testes
      **Pronto quando:** <condição checável>

- [ ] **T2 · R2** — … (depende de T1)

## PR 2 · <título> — 5 arquivos
> Fecha R3. Depende do PR 1.
```

O que governa a quebra:

- **Toda tarefa rastreia a um requisito** da spec. Tarefa sem requisito é escopo inventado:
  ligue a um, ou remova.
- **Todo requisito tem ao menos uma tarefa.** Requisito descoberto sem tarefa significa plano
  incompleto — ou comportamento que saiu de escopo, e aí confirme com ele.
- **Uma coisa por tarefa.** Um componente, uma função, um endpoint. Duas ou três coisas coesas
  no mesmo arquivo passam; múltiplos arquivos ou componentes, divide.
- **A verificação nasce junto com o código.** "Vai ser testado na tarefa seguinte" é como a
  cobertura evapora — se a tarefa cria código que só é verificável depois de outra, junte as
  duas.

## O contrato e os passos

É aqui que o usuário revisa **o desenho** antes de ele custar execução — e é o insumo que o
`implement` trava com ele antes de delegar qualquer tarefa. Sem isso, quem escreve o teste fixa a
assinatura por via indireta, e o design chega decidido por um subagente.

**Contrato** — obrigatório em toda tarefa que cria ou muda algo que **cruza fronteira**: função
exportada, endpoint, tipo ou schema, migração, evento publicado. Traz:

- a **assinatura completa** — nome, parâmetros com tipo, retorno;
- a **origem de cada parâmetro**, com `arquivo:linha`. É afirmação sobre o codebase, então vale o
  zero inferência: sem fonte verificada, entra `[A VERIFICAR]` e **não** sustenta tarefa;
- o **efeito colateral** (o que grava, o que chama) e o **erro que propaga**, na forma que o
  projeto já usa — `Result`, exceção ou retorno nulo, o que estiver no vizinho.

Helper interno não tem contrato: a tarefa diz o arquivo e basta. Contrato pra tudo infla o
`tasks.md` e a parte que importa se perde no meio.

**Passos** — a sequência de chamadas e decisões **observáveis de fora**, no máximo **5**.

- Cada passo nomeia **o que** acontece ("valida `amount` contra o saldo"), não como.
- **Fora:** `if`/`else` escrito, laço, `try`/`catch`, nome de variável local, ordem de guard. Isso
  é implementação, e o código vizinho manda mais nela do que você.
- **Passou de 5 → a tarefa é grande demais.** Proponha a divisão em vez de escrever doze passos: o
  teto é sinal de quebra, não cota a preencher.
- Os passos são **intenção, não roteiro.** Quem executa segue o codebase quando ele contradiz, e
  anota o desvio. Desvio de passo é registro; desvio de **contrato** ou de **comportamento** é
  parada dura na execução.

Tarefa sem código novo — config, migração pura, deleção — não tem contrato nem passos: escreva
`n/a` e siga. Campo preenchido por obrigação é ruído que ensina o leitor a pular a seção.
- **Toda tarefa carrega a contagem esperada** (`12 → 17 testes`). É o que impede a suíte de
  encolher em silêncio num rebase ou refactor.
- **Tarefa sem verificação de espécie alguma** só existe se o `test-plan` já levou a pergunta ao
  usuário e ele aprovou. Você não cria essa exceção aqui.

## A fronteira de PR

Conte os **arquivos distintos** que entram no diff — a união dos paths das tarefas do bloco,
incluindo testes que são commitados. Andaime local de teste não conta.

| Arquivos | Ação |
|---|---|
| ≤8 | segue |
| 9–13 | segue, com a contagem anotada no bloco |
| ≥14 | **proponha a fronteira de corte** e pergunte antes de seguir num PR só |

O corte respeita dependência: o PR 1 não pode depender de código que só existe no PR 2. Corte em
limite de requisito coeso ou de camada.

**Propor é seu; dividir é dele.** Mostre a fronteira sugerida e deixe a decisão com o usuário —
inclusive a de seguir grande. Estreitar a spec, se for o caso, é decisão dela, não daqui.

## O mapa dos PRs

Fronteira fechada, desenhe **a ordem em que eles nascem**. Vai no topo do `tasks.md`, antes do
primeiro bloco de PR — é o que o usuário olha pra saber o que já pode abrir hoje, e o que só faz
sentido depois de um merge.

A onda de um PR é **1 + a maior onda entre as suas dependências**. Todo PR da mesma onda nasce
junto, em worktrees separadas — **inclusive PRs de pilhas diferentes**: um PR que espera o 1 e o 3
cai na mesma onda de um que espera só o 3, porque os dois estão livres no mesmo momento.

```markdown
## Mapa dos PRs

| PR | Depende de | Onda |
|---|---|---|
| PR 1 · calc de estorno | — | 1 |
| PR 2 · schema do endpoint | — | 1 |
| PR 3 · handler HTTP | PR 1, PR 2 | 2 |
| PR 4 · feature flag | PR 3 | 3 |
| PR 5 · métrica de estorno | PR 1, PR 3 | 3 |

- **Onda 1 — paralelo:** PR 1, PR 2
- **Onda 2:** PR 3
- **Onda 3 — paralelo:** PR 4, PR 5
- **Pilha mais longa:** PR 1 → PR 3 → PR 4 · 3 merges em série (o PR 5 empata)
```

- **Liste todas as dependências de cada PR**, não só a mais recente. Faltando uma, a onda sai
  otimista e o `--dep` do roadmap nasce incompleto — o PR abre e trava na primeira compilação.
- **A pilha mais longa é o caminho crítico.** É o número que responde "quantos merges em série
  isso custa", e é o que faz o usuário decidir se vale cortar mais fino ou seguir assim.
- **Ciclo é fronteira errada**, não desafio de ordenação: dois PRs que precisam um do outro são um
  PR só, ou o corte foi na camada errada. Volte na fronteira antes de escrever o mapa.
- Uma onda larga é boa notícia, e vale dizer em quantas worktrees ela cabe.

## O roadmap, um item por PR

Mapa fechado, cada bloco vira um item — é **um item por PR**, não por mudança:

```bash
roadmap add "<título do PR 1>" --change <NNN-slug>
roadmap add "<título do PR 2>" --change <NNN-slug> --dep <NNN do PR 1>
```

O `--dep` de cada item sai da coluna **Depende de** do mapa, uma aresta por dependência — a
dependência é literal: se o PR 2 usa código que só existe depois do PR 1, ele `--dep` do PR 1. Slices realmente paralelos não ganham aresta — dependência inventada bloqueia
trabalho que podia estar rodando, e ninguém percebe.

Comando ausente → o projeto não usa roadmap, ou falta rodar `scripts/install-roadmap.sh`. Diga numa
linha e siga: o plano não depende disso.

## As lentes

Antes de mostrar o plano, três subagentes leem o draft com olhos que você não tem — você acabou
de escrevê-lo. Lance os três **numa única resposta** (`subagent_type: general-purpose`,
`model: opus`):

> Leia `${CLAUDE_SKILL_DIR}/review-lenses.md` e assuma a lente **<Arquitetura | Executabilidade |
> Segurança>**. O plano está em `<caminho>`, a spec em `<caminho>`, as tarefas em `<caminho>`.
> Você é read-only e não tem poder de aprovar.

**Uma rodada, e os achados vão pra tela como vieram** — inclusive os que você acha errados, com
a sua discordância escrita do lado. Não conserte em silêncio e não volte com placar: um plano que
chega ao usuário como "aprovado, 0 pendências" trocou a leitura dele por um carimbo, e é
exatamente o que estas lentes existem pra evitar.

Achado que você aplicar, aplique **dizendo qual era** — a correção some do texto, mas a decisão
não deve sumir da tela.

## A barra

Antes de mostrar, confira você mesmo — e é isto que vai pra tela no fechamento:

1. **Todo requisito tem tarefa; toda tarefa tem requisito.**
2. **Toda tarefa tem verificação e contagem**, herdadas da matriz.
3. **Toda tarefa que cruza fronteira tem contrato**, com a origem de cada parâmetro referenciada em
   `arquivo:linha` — e nenhuma passa de 5 passos sem a divisão ter sido proposta.
4. **Toda decisão técnica tem fonte**, ou está marcada `[A VERIFICAR]` e não sustenta tarefa.
5. **Dependência entre tarefas está explícita** e o agrupamento de PR a respeita.
6. **Nenhum bloco de PR passa de 13 arquivos** sem a pergunta ter sido feita.
7. **Nada de comportamento novo.** Requisito que não está na spec não nasce aqui.

## O plano

`thoughts/changes/<NNN>-<slug>/plan.md`:

```markdown
# Plano — <título>

Spec: [[spec]] · <N> requisitos · <M> PRs previstos

## Abordagem
<3 a 6 linhas: o desenho, o que muda onde, e por quê assim>

## Decisões técnicas
### D1 — <a decisão>
<o que foi decidido e por quê> [Fonte: <url | arquivo:linha>]
Descartado: <alternativa> — <motivo>

## Testes
<escrito pelo test-plan>

## Suposições
- <o que você assumiu sem perguntar>

## A verificar
- <claim externa sem fonte confirmada>
```

## Se o plano já existe

Releia antes de tocar. Mudança de rumo no meio do trabalho é normal e barata **quando o plano
acompanha** — o que sai caro é implementação e plano divergirem em silêncio.

Ao revisar: mostre o que muda no plano, o que isso invalida nas tarefas já feitas, e o que passa
a exigir nova verificação. Se o rumo mudou porque o **comportamento** mudou, a spec vem primeiro
— o plano é consequência dela.

## Ao terminar

Mostre em tela: a abordagem em duas linhas, as decisões técnicas com suas fontes, os PRs previstos
com contagem de arquivos, **as ondas do mapa e a pilha mais longa**, a cobertura de teste antes → depois, a dívida aceita, as suposições que
você assumiu, e os achados das lentes. Feche com:

> **Você ficaria confortável se isto fosse construído exatamente assim, e nada além?**

`thoughts/` é local e gitignored — não commite.
