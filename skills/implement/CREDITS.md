# Créditos — skill `implement`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

**tlc-spec-driven** (tech-leads-club/agent-skills) por Felipe Rodrigues — **CC-BY-4.0**.
⚠️ Atribuição obrigatória e permanente, inclusive em adaptações reescritas.

O `/executor-plan` v9 declarava no frontmatter: *"Conceitos adaptados: sub-agent paralelo para
`[P]`, Test count protection, memória persistente via memory-keeper, Gate commands explícitos."*
Do que sobreviveu:

- **Test count protection** — contagem que cai é parada dura, não algo a consertar sozinho.
- **Gate explícito por tarefa** — comando de verificação declarado, não inferido.
- **Subagente paralelo para tarefas independentes** — mantido e ampliado (ver abaixo).

**Red verificável e falso-verde como parada dura** são construção nossa, sem equivalente em
nenhuma das fontes mapeadas — inclusive o OpenSpec, cujo `/opsx:verify` só olha cobertura **depois**
do código e não bloqueia. É o invariante mais forte do toolkit (Parte E.5 do `REFACTOR-v10.md`).

## O que saiu das 736 linhas

- **Duplicação autônomo / `--step`** (~150 linhas) — cada passo aparecia escrito duas vezes, e a
  diferença era só pausa entre tarefas e momento do commit. **Um modo só.** Pausa entre tarefas é
  incompatível com subagentes paralelos de qualquer forma, e o que mantém o usuário no circuito são
  as paradas duras, que nunca dependeram do modo. O commit atômico não se perdeu: continua como
  opção no fim.
- **Gate de complexidade ciclomática** (3 ferramentas em cascata, 2 tentativas de refactor,
  ~45 linhas) → skill própria `complexidade`.
- **Passadas do code-simplifier** — o v9 tinha **três** pontos de invocação (fim de cada tarefa,
  fim do grupo paralelo, verificação final). Ficou **um**: no fim, entre o verde e o review. Por
  tarefa colide com os subagentes paralelos, e o próprio v7 já reconhecia isso ("em modo autônomo:
  pule, simplifier no fim, reduz ruído entre tarefas").
- **Validador Haiku** (`{complete: true|false}`) — as cinco checagens dele eram determinísticas
  (marcação `[x]`, contagem, gate, staging), e ele só via a transcript, auditando relato e não
  fato. Um subagente que devolve booleano é o placar que a I.14 manda cortar; as checagens viraram
  verificação direta do orquestrador.
- **Detecção de agente especializado** + **delegação da escrita de testes** a agente externo — o
  usuário decidiu que o TDD acontece dentro da tarefa, não terceirizado pra fora dela.
- **`PushNotification`, modo-livre, `/compact`, verificação de links, memória** — infra de outras
  peças, ou Onda 2.
- **Concorrência de I/O** (~15 linhas de instrução sobre `await` sequencial, hoist e N+1) — bom
  conteúdo no lugar errado. Virou checagem da lente de Bugs em `review-lenses.md`: é coisa que se
  pega revisando, não instrução que se segue enquanto escreve. Hoje vive em `../imp-review/lenses.md`.

## Decisões do usuário (31-07-2026)

- **⭐ O paralelismo fica, e é central.** *"Ele identificar as tarefas que são independentes entre
  si e pedir para subagentes realizá-las em paralelo. O agente principal fica responsável em
  delegar e validar no final."* O main deixou de ser implementador com ajuda e virou orquestrador
  e validador.
- **⭐ Agrupamento por ambiente** — a unidade de escalonamento é o `Test env:` que o `plan` declara.
  Ambiente `none` paraleliza; tarefas que dividem um ambiente formam grupo sequencial com o
  ambiente subindo uma vez. Foi a resposta ao conflito que o usuário levantou: o red de um e2e
  precisa do ambiente, e o ambiente é um só. As alternativas que ele mesmo listou tinham custo —
  "rodar integração/e2e só no final" mataria o red dessas tarefas (o teste nasceria depois do
  código, falso-verde garantido).
- **⭐ O ambiente compartilhado tem o usuário como árbitro** — não um lock cego. Marcador no repo
  principal (visível entre worktrees) registra quem usa e desde quando; ocupado, o agente
  **pergunta** e aguarda o OK, adiantando enquanto isso as tarefas sem ambiente. Motivo:
  *"eu posso já tá fazendo teste de uma tarefa, a outra entrou na fase de teste e viu que o
  ambiente está de pé — pergunta ao usuário se pode iniciar os testes dele."*
- **⭐ A simplificação volta, como refactor do TDD.** *"Antes de delegar para o code-review acho
  que ele pode pedir o code-simplifier... porque meio que atende o fluxo do TDD né, que vai
  refatorar pra simplificar daí os testes têm que passar de novo."* Lugar exato: depois do gate de
  verde, antes do review — o red-green-**refactor** completo, com a suíte rodando de novo depois.
- **Fronteira trivial × estrutural**, vinda de memória de feedback do usuário no projeto gopay
  (`simplify-ask-before-structural-changes`, com casos reais: PRs #270 e #272, o mesmo split de
  `buildCustomerPayload` sugerido e **rejeitado duas vezes** — design unificado com flag era
  intencional). O agent oficial "operates autonomously and proactively", então a restrição vai no
  prompt de invocação: local aplica, estrutural descreve e não aplica.
- **Pendência declarada, sem bloquear:** isolar ambiente por worktree (porta e banco por env var).
  *"Posso pensar em depois isolar os ambientes de teste por worktree, mas é uma preocupação que não
  teremos agora."* Quando existir, some a pergunta e sobra o caminho livre — o desenho atual não
  precisa mudar.

## ⭐ Worker é Sonnet, orquestrador é a sessão (03-08-2026)

Decisão do usuário: *"acho q para escrever código o sonnet é suficiente"*.

Antes disso a peça não declarava modelo em lugar nenhum — nem no frontmatter, nem nas chamadas
`Agent`. O efeito era invisível e caro: quem escolhia era a sessão, então entrar em Opus fazia
**cada worker paralelo** ser Opus. Quatro grupos independentes, quatro Opus executando um `tasks.md`
que já estava decidido.

A divisão que ficou segue a natureza do trabalho, não a hierarquia: **executar é Sonnet, julgar é a
sessão.** O worker recebe tarefa fechada — o `plan` decidiu o como, o `test-plan` decidiu a
verificação, o `worker.md` fixa o protocolo (red verificável incluso). Não sobra decisão de projeto
pra tomar, sobra execução, e ela precisa de disciplina, não de potência. Já a validação do que
volta — gate, contagem de testes, red que falhou pelo motivo certo, desvio do plano — é onde o
falso-verde passa despercebido, e essa ponta segue no modelo da sessão.

Fica coerente com as três peças que já pediam `model: opus` explicitamente (`spec` no adversário,
`imp-review` na dúvida sobre correção, `pr-close` na destilação): **em toda elas o Opus está no
julgamento, nunca na execução.** O `implement` era o furo desse padrão, por omissão.

**Não estendido de propósito:** os subagentes `Explore` de `spec`, `baseline` e `test-plan` fazem
varredura de codebase e continuam sem modelo declarado. Varredura também não é julgamento e
provavelmente merece o mesmo tratamento, mas a decisão foi sobre escrever código — expandir por
conta própria seria decidir no lugar do usuário.

## Dependência externa, não incorporação

O `code-simplifier` é agent do plugin oficial **`code-simplifier@claude-plugins-official`**
(Anthropic). A skill **invoca**, não copia — nada do prompt dele entra aqui, então não há
obrigação de atribuição de licença. É dependência **opcional**: ausente, a skill avisa e segue,
porque simplificar é ganho e não gate.

## Limite declarado, não escondido

O red do subagente é **auditado, não re-executado**. Refazer o red no orquestrador exigiria desfazer
a implementação, e custaria a execução inteira de novo. O que é determinístico é a contagem de
testes; a evidência do red (`red.saida`, a saída literal do runner) é relato verificado na forma —
falha de comportamento ausente versus falha de import ou setup.

Isso está escrito no `SKILL.md` de propósito. Um invariante que se apresenta como garantido sem ser
é pior que um invariante com limite conhecido: o primeiro produz confiança falsa exatamente onde
o usuário deixaria de olhar.

## O review saiu daqui

Cheguei a escrever três lentes próprias (segurança, bugs, testes) em `review-lenses.md`, herdadas do
review interno do v9 (`executor-plan-review.md`). **Removidas em 31-07-2026**, quando o usuário
descreveu o papel do `imp-review`: *"revisar toda a implementação feita caso não tenha feito review,
ter as lentes para revisar tudo."*

Duas peças com painel de review é a `duplication` que a Parte C manda caçar — e o `imp-review` tem
seis lentes contra as três daqui. As checagens do v9 foram preservadas lá, incluindo as três de
concorrência (serialização desperdiçada, hoist inseguro, fan-out de query) que vieram do corpo do
`/executor-plan`.

O `implement` **invoca** o `imp-review` sobre o staged. Mesmo padrão do `plan` → `test-plan`: quem
faz não revisa a si mesmo.
