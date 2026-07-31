# Créditos — skill `code-review`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

Construção própria, consolidando três peças do v9 que a Parte C do `REFACTOR-v10.md` já havia
marcado como **duplication** — nenhuma delas com atribuição de terceiros:

- `sdd-review.v9.md` (373L) + references (221L) — as lentes e o relatório
- `pair-review.v9.md` (157L) — a validação contra o review humano
- parte do `pr-ready.v9.md` (251L) — o alinhamento com o que o time pediu

O restante do `pr-ready` (verde, commit/push, handoff) virou peça própria.

## O fluxo que o usuário descreveu (31-07-2026)

Foi ele quem separou as águas, descrevendo o uso real:

> *"o code-review aqui é revisar toda a implementação feita caso não tenha feito review, ter as
> lentes para revisar tudo e corrigir o que tiver errado ou delegar novamente para implement.
> [...] quando eu pedia sdd-review era depois das correções feitas avaliar que o que foi pedido no
> review pelo time foi atendido pra depois solicitar nova revisão."*

Daí os **dois momentos** numa peça só, detectados pelo estado do PR — mesma estrutura que o
`pr-ready` v9 já tinha (dois modos automáticos), e que estava certa; errado era ter três peças
fazendo pedaços disso.

## ⭐ Correção que muda comportamento volta pro `implement`

Mudança em relação ao v9, e veio do usuário: *"corrigir o que tiver errado ou delegar novamente para
implement para poder fazer as devidas correções."*

No v9 as correções iam pro `/quick-task` (Action Plan, Etapa 6), que **não tem TDD, red verificável
nem test count protection**. Uma correção de review que altera comportamento entrava por um caminho
paralelo que escapava de todos os invariantes da Parte E.5 — e é justamente o tipo de mudança feita
com pressa, no fim do ciclo.

Aqui a fronteira é explícita: o que não muda comportamento se corrige na hora (com gate e proteção
de contagem); o que muda **vira tarefa no `tasks.md`**, num bloco `## Correções do review`, e o
`implement` executa no ciclo normal.

## O `pair-review` não sobreviveu como peça

Ele existia porque o `/sdd-review` era **batch**: gerava relatório e encerrava, então era preciso um
segundo comando pra conversar sobre o que ele achou. Com a I.14 (achados na tela, não placar), a
conversa acontece sozinha.

O que ele tinha de único foi preservado aqui:

- **Validar cada fix contra o comentário que o originou** — status `atendido` / `parcial` /
  `não endereçado` / `divergente`. "Mudou algo por perto" não conta; o comentário humano é o contrato.
- **Rascunhos de resposta pras threads**, prontos pro usuário colar. O agente **nunca posta no PR**.
- **Subagente Opus escopado** no ponto em dúvida, não no diff inteiro.

Não sobreviveram: os modos `walkthrough` e `hotspots` (viram formas de apresentar achados, não
comandos), e a re-hidratação por `thoughts/.executor-staged.log` — a I.12 pôs tudo na pasta da
mudança.

## O relatório em arquivo separado também não

O v9 salvava `thoughts/reviews/REV-DD-MM-YYYY-slug.md` com template de 163 linhas — mais um lugar
onde uma mudança morava (eram cinco; a I.12 fez virar um). Achados vão pra tela, e o que sobrevive é
registrado no `notes.md` da própria mudança.

Um relatório salvo também é um convite a não ler: o arquivo existe, logo o review "aconteceu".

## Preservado do v9, quase intacto

As checagens das lentes são específicas e testadas em uso real — foram herdadas quase inteiras:

- **Threshold de confiança ≥ 80**, e nomenclatura/style **nunca** sobem de grau. O v9 chamava isso
  de "anti-nit reforçado": *"talvez fique melhor" não é evidência*.
- **Não reportar pré-existente**, nem o que o linter já pega, nem preocupação hipotética.
- **Toda sugestão com base verificável** — padrão do projeto (`arquivo:linha`), constraint
  documentado, ou doc oficial. Sem exigir URL externa.
- **Pular a lente cujo escopo não aparece no diff** — sem query, sem lente de queries.
- **Queries: risco futuro conta** — query sem limite "funciona hoje" e é catastrófica em escala.
- **Complexidade só no diff**, só em funções tocadas, e **nunca bloqueante**.
- **Comentário humano é contexto, não verdade absoluta** — dá pra discordar com evidência, expondo
  as duas leituras.
- **Não duplicar achado humano** — repetir o que um revisor já apontou infla o resultado e afoga o
  que só a máquina viu.
- **Build quebrado é parada** — review sobre build quebrado gera ruído.
- **Nunca comentar no PR.** Ler via `gh` é livre; escrever é humano.

As três checagens de concorrência da lente de Bugs (serialização desperdiçada, hoist inseguro,
fan-out de query) vieram do **corpo do `/executor-plan`**, onde eram instrução de como escrever
código. Viraram checagem de review: é coisa que se pega revisando, não regra que se segue digitando.

## O que saiu

- **Action Plan com cinco opções** (a/b/c/d/e) e cadeia de `quick-task` — virou a fronteira
  "corrige aqui / volta pro `implement`".
- **Agente 7 (Style Pass) opt-in** com três condições de ativação — dobrado na lente de
  Conformidade, que já lê o `CLAUDE.md`.
- **`feature-dev:code-reviewer` → `code-reviewer` → `general-purpose`** em cascata — dependia de
  pack instalado, com fallback silencioso.
