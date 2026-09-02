# Créditos — skill `test-qa`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

Construção própria. Ocupa o slot que a Onda 3 reservava pro `verifica` (`MANTER conceito` — *"sem
equivalente na referência e resolve o buraco real entre testes verdes e funciona"*), e vai além dele.

Herdado do `verifica.v9.md` (90L), quase verbatim porque foi testado em uso:

- **Evidência > suposição** — checagem sem output capturado não vira ✅.
- **Nunca produção**, e **pagamento sempre em test mode** (chave live no env = parada antes de
  qualquer chamada).
- **Side effect externo só com OK item a item.**
- **Zero inferência no boot** — o comando vem do `CLAUDE.md`, das skills do projeto ou dos scripts
  declarados; nunca se chuta.
- **Derrube o que subiu**, com sucesso ou sem.
- **Não conserta aqui** — falha vira handoff.

## O que o usuário pediu (07-08-2026)

> *"quero poder pedir para ele para fazer testes por mim ele vai pedir um agente para subir os
> servers necessarios [...] se for uma rota ele vai testar tudo que puder, para tentar encontra
> possiveis bugs. [...] o qa vai testar tudo na tela que o cliente pediu e listar os bugs
> inconsitencias erros de escita comportortamenteos insperados"*

Duas coisas dele que o `verifica` v9 não tinha e que são o coração da peça:

1. **Exploração adversarial.** O v9 era checklist derivada do IMP — confirmava o que já se sabia. Aqui
   as lentes atacam a entrada procurando o que ninguém previu. `escrita` como grau de primeira classe
   também é dele, e é achado que nenhuma lente de código pega.
2. **O boot como conhecimento que se aprende uma vez.** *"se não souber ou não encontrar a resposta nas
   memorias ou sozinho que ele pergunte a usuario"* — a metade que faltava era **gravar a resposta**,
   senão a pergunta se repete toda rodada.

## Quatro decisões tomadas contra o desenho original

Apresentadas com o porquê, e escolhidas por ele:

1. **Uma peça, dois momentos.** `verifica` sai da fila da Onda 3. Mesmo recurso (subir ambiente),
   mesmo conhecimento, mesmos guardrails — é o argumento da I.19 (`worktree`) e da I.22 (`pr-draft
   sync`). Momento detectado pelo estado, como `imp-review` e `pr-close` já fazem.
2. **O main sobe o ambiente; subagente só explora.** No desenho original um agente dedicado subia os
   servidores e sinalizava. Subagente termina quando devolve o resultado — o processo fica sem dono
   pro teardown, e o marcador `<root>/thoughts/.env-em-uso` do `implement` (I.16) fica órfão. Invertido:
   o main sobe, registra, derruba; o paralelismo vai pra exploração, que é onde ele vale.
3. **Achados na tela e no `notes.md`, não em `thoughts/qa/`.** Ele mesmo hesitou (*"talvez dentro dos
   changes né, para seguir o padrão"*) e a hesitação estava certa: a I.25 matou `thoughts/reviews/`
   porque relatório salvo é convite a não ler, e a I.12 reduziu uma mudança a uma pasta só. Pasta nova
   seria o sexto lugar onde uma mudança mora.
4. **O nome.** Proposto `qa-sweep` pelo risco da I.35 (nome curto genérico num plugin global é
   reivindicação sobre todos os projetos da máquina). Ele escolheu **`test-qa`** — e formou par
   simétrico com `test-plan`, argumento melhor do que os três que eu tinha listado: o `test-plan`
   decide o que a mudança garante, o `test-qa` vai lá ver se garante mesmo.

## O que veio das peças vizinhas

- **Fronteira de correção** (`I.24`, escrita pro `imp-review`): não muda comportamento → corrige na
  hora · muda → tarefa em `tasks.md` → `implement` · cresce → é mudança de spec/plan. Reusada literal.
  O que muda comportamento não se conserta à mão no fim do ciclo — foi assim que o v9 acumulou dívida.
- **Escalonamento por recurso compartilhado** (`I.16`): lá o critério era o `Test env:` da tarefa; aqui
  é o navegador (um só, logo lentes de tela serializam) e o dado (lentes que tocam a mesma entidade
  serializam). Mesma lógica, recurso diferente.
- **Sem veredito, sem loop, achados como vieram** (`I.14`): a régua geral do refactor pra todo
  mecanismo de avaliação portado do v9.
- **Nenhuma peça invoca outra** (`I.27`): a transição é a última linha, com o comando preenchido.
- **Instrução volumosa fica no arquivo do subagente** (`I.11`): as lentes vivem em `lenses.md`, lido
  via `${CLAUDE_SKILL_DIR}` pelo subagente, nunca pelo contexto principal.

## O invariante que a peça fecha

E.5, endurecido em 31-07-2026: *"todo requisito sai do planejamento com uma forma de verificação. Piso:
verificação manual executada pelo usuário, com evidência registrada — e isso é dívida, não pronto."*

O `test-plan` **cria** essa dívida e, até aqui, nenhuma peça a **fechava**. É o primeiro item da rodada
quando existe mudança associada.

## Riscos registrados

- **Fuzzing suja ambiente compartilhado.** Daí o prefixo obrigatório nos dados criados, a listagem do
  que ficou e a oferta de limpeza. O usuário não levantou isso; apareceu ao desenhar as lentes.
- **Falso positivo de subagente custa mais que achado a menos.** Daí a exigência de reprodução e
  evidência literal, e a re-execução pelo main do que parecer decisivo.
- **Inventar requisito.** O grau `duvida` existe pra isso: comportamento não especificado que parece
  errado vira **pergunta** ao usuário, nunca bug. Sem essa separação a peça vira lista de opinião — o
  mesmo vício da spec, um passo mais tarde.
