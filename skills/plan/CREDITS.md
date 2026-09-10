# Créditos — skill `plan`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origens

**tlc-spec-driven** (tech-leads-club/agent-skills) por Felipe Rodrigues — **CC-BY-4.0**.
⚠️ Atribuição obrigatória e permanente, inclusive em adaptações reescritas.

O `/sdd-plan` v9 declarava no próprio frontmatter: *"Conceitos adaptados: doc auto-sized,
Knowledge Verification Chain, memória persistente, checks de qualidade, test co-location,
handoff explícito."* Do que sobreviveu ao v10:

- **Test co-location** — a verificação nasce na mesma tarefa que cria o código; adiar é
  anti-pattern. Aqui é a regra "a verificação nasce junto com o código".
- **Test count protection** — contagem esperada por tarefa, pra a suíte não encolher em silêncio.
- **Checks de qualidade antes de apresentar** — virou a seção "A barra", com 6 itens em vez dos
  5 checks tabulados.
- **Knowledge Verification Chain** — a cadeia de 6 steps virou uma linha ("zero inferência") mais
  a ordem de fontes do legwork. O ritual saiu; o princípio ficou.

**Conceitos recusados** desta fonte, com motivo:

- **Doc auto-sized (Quick/Medium/Large/Complex)** — calibrava "profundidade da pesquisa" por
  classificação declarada no início. O critério real de parada é a spec, que já delimita o
  comportamento; a classificação virava cerimônia que não mudava a decisão seguinte.
- **Template de 13 seções** — mesmo defeito das 8 seções da spec já recusadas: orienta completude
  de seção, não qualidade de tarefa.
- **Verificação de links por subagente** (`WebFetch` em cada URL pra montar uma tabela) — custo
  alto, ninguém lê o resultado.

**OpenSpec** (Fission-AI) — MIT © 2024 OpenSpec Contributors.
Texto da licença: `../../LICENSES/` · Conceitos, sem cópia de texto.

- **`tasks.md` como artefato separado** do documento de design — checklist com checkbox que a
  execução lê e marca. Confirmou nossa separação `plan.md` / `tasks.md`, cujo motivo mecânico é
  que só o `tasks.md` muda de estado durante a execução.
- **Design é opcional** (*"You can skip design if you don't need it"*) — pré-requisito é estado do
  filesystem, não posição no processo. É o que sustenta a seção "Se o plano já existe" em vez de
  um phase gate.
- **Two-minute pass sobre tarefas** — *"you're checking that the plan matches the requirements you
  already accepted"*, procurando tarefa sem requisito correspondente e tarefa misteriosa ou fora
  de escopo. Virou os itens 1 e 6 da barra, e a pergunta de fechamento.

**Divergência consciente:** no OpenSpec **testes não são artefato formal**. Cenários são
"testáveis" no papel, e a cobertura só é olhada depois do código, pelo `/opsx:verify`, que emite
`"Scenario ... has no test coverage"` como WARNING e — literalmente — *"Does not block archive."*
Aqui a cobertura é decidida **antes** da quebra de tarefas e **bloqueia**: requisito sem
verificação nenhuma exige pergunta explícita ao usuário (ver `../test-plan/CREDITS.md`).

**Gist "Formação da especificação" por @parruda** — **não contribuiu com esta peça.** Verificado
em 31-07-2026: a gist tem um arquivo só, restrito à especificação, e declara que o output não deve
conter *"planos técnicos, quebra de tarefas, detalhes de implementação ou código de teste"*.

## Adaptações nossas

- **Fronteira de PR dentro do `tasks.md`**, agrupando tarefas por bloco, em vez do "Check 5" do v9
  que calculava no fim e anotava uma linha (`PRs: 3`) no topo do PLAN. Assim a contagem é a união
  verificável dos paths do bloco, e o corte respeita dependência por construção.
- **Faixa apertada**: ≤8 segue · 9–13 anota · ≥14 propõe corte e pergunta. O v9 tratava 11–15 como
  "aceitável"; na prática do usuário é justamente onde o review humano começa a falhar.
- **Formato de tarefa enxugado de 12 campos para 4 linhas.** Saíram `Skills:` (a execução lê as
  skills do projeto sozinha), `Riscos:` (virava ruído por tarefa), `Commit:` (mensagem é da
  execução) e `[P]` (paralelismo se deriva das dependências explícitas).
- **Pair de testes extraído pra skill própria** (`test-plan`), chamada daqui. Ganho por sequência:
  a quebra de tarefas fica atrás do mapa fechado. A matriz continua escrita **dentro** do
  `plan.md` — peça própria não implica arquivo próprio, e o usuário pediu explicitamente menos
  arquivos por mudança.
- **`[A VERIFICAR]`** em vez de `[NEEDS VERIFICATION]` — corpo em pt-BR (regra 7 do `CLAUDE.md`).

## As lentes de revisão (`review-lenses.md`)

Herdam o **painel de 4 lentes** do v9 (`sdd-plan-panel-review.md`), com duas correções e uma
subtração:

- **A lente Tests saiu** — virou a skill `test-plan` inteira, com três lentes próprias. Mantê-la
  aqui seria revisar de novo o que o usuário acabou de decidir.
- **Uma rodada, sem loop até `APPROVED`.** O v9 mandava o agente verificar cada `must-fix`,
  aplicar, e rodar novas rodadas com subagentes frescos até o painel calar — o usuário via só
  `"Aprovada em 2 rodadas — 0 must-fix aberto"`. Toda a avaliação era consumida pelo agente antes
  de chegar nele.
- **Sem veredito.** Achados vão pra tela como vieram, incluindo os que o agente discorda — com a
  discordância anotada junto, não filtrando.

**Decisão explícita do usuário (31-07-2026):** as lentes **ficam**. O pedido não foi cortar
avaliação e sim entrar nela — *"as avaliações não precisam ser excluídas, eu entrar mais nesse
processo é mais para agregar"*. O que se corta é o veredito e o loop, não a perspectiva. Mesma
correção já aplicada na `spec` ("adversário, não juiz").

## Contrato e passos na tarefa (02-09-2026)

*"queria que me mostrasse meio que um passo a passo do código que vão implementar. não o código em
si, mas dizer vamos criar uma função tal que recebe parâmetros tais vindos de tal."*

Ele cogitou peça nova e perguntou se o lugar era o `plan` ou o `implement`. Ficou aqui: quem tem
`structure-cache`, `Explore` e Context7 no `allowed-tools` é esta peça, e o executor descobrindo a
origem dos parâmetros na hora de executar é o executor decidindo design. Peça própria não passaria
pela Parte C.4 — o `plan` já para pra aprovação, que é o momento em que ele quer ver o desenho.

**Escolhas dele:** contrato e passos **dentro da tarefa** (não em seção separada do `plan.md`, que
obrigaria a cruzar dois arquivos e abriria espaço pra divergência), e **com a sequência de chamadas**
— apesar do risco de pseudocódigo, que foi apontado antes da escolha.

O risco virou desenho em vez de discussão: teto de 5 passos como **sinal de tarefa grande demais**
(o `plan` propõe dividir), passo declarado como **intenção** que o codebase sobrepõe, e — a parte
que só funciona por causa da I.43 — **o test-writer do `implement-strict` não recebe os passos**.
Teste que conhece a ordem das chamadas quebra em refactor que não mudou nada de fora.

A lente de **Executabilidade** ganhou o contrato como material: assinatura com tipo que não existe,
origem apontando pra função que não devolve aquilo, erro que o chamador de cima não trata. Era a
pergunta que ela queria fazer e não tinha onde.

Registro completo em I.44 do `REFACTOR-v10.md`.

## O mapa dos PRs (10-09-2026)

Pedido do usuário: *"na skill de criação de tasks seria legal ele fazer um mapa no final de prs que
pode ser em paralelo e prs que deve seguir uma pilha, é como se a gnt desenhasse uma
pipeline/fluxo da ordem que os prs são criados"*.

A informação **já existia** e era jogada fora: a fronteira de PR decide os slices, o
`roadmap add --dep` grava as arestas, e nada nunca mostrava o resultado junto. Quem lia o
`tasks.md` via os blocos em sequência e não tinha como saber que dois deles podiam abrir na mesma
tarde, em worktrees separadas.

**A regra da onda veio dele, corrigindo o primeiro desenho.** A proposta inicial tratava paralelo
como "PR sem dependência" e empilhava o resto; ele apontou o caso que isso erra: *"isso se tivesse
um pr5 que dependesse de pr1 e pr3 por exemplo ele deveria ser paralelo ao pr4"*. Está certo —
paralelismo não é ausência de dependência, é **estar livre no mesmo momento**. Daí a definição
que ficou: `onda = 1 + a maior onda entre as dependências`, e tudo que cai na mesma onda corre
junto, mesmo vindo de pilhas diferentes. Sem isso o mapa subestima o paralelismo justamente nos
planos grandes, que são os que mais precisam dele.

**Por que texto e não mermaid.** Coerente com a decisão já registrada no `roadmap.py` ("o grafo é
nativo do Obsidian, não se gera mermaid"): a tabela + as ondas leem igual no terminal, no Obsidian
e na view HTML, que abre sem CDN e sem lib. Diagrama ASCII foi oferecido e não escolhido; a
manutenção na mão quando o plano muda era o contra.

**Compatibilidade com a view de changes:** o parser de `tasks.md` (`changes.py`) agrupa por
qualquer `##` e descarta no fim os blocos sem tarefa — `## Mapa dos PRs` cai nesse filtro e não
vira PR previsto fantasma. A view não *mostra* o mapa; mostrá-la na aba Tarefas exigiria mexer no
parser, e ficou de fora.

**Caminho crítico como número na tela:** a pilha mais longa entra no fechamento porque é o que
responde "quantos merges em série isso custa" — o insumo da decisão dele de cortar mais fino ou
seguir assim.
