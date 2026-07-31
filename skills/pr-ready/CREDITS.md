# Créditos — skill `pr-ready`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Correção do usuário (31-07-2026) — a espera pelo CI

*"Ele não espera o CI ficar verde para solicitar o review e precisamos que ele espere, pq é ruim eu
pedir pro time revisar sem que o CI passe, e isso serve tanto para o primeiro review quanto para um
re-review."*

O texto original dizia "nunca com o CI ainda rodando", mas mandava **parar e reportar** — o que
devolve o problema em vez de resolvê-lo, e deixa a espera por conta do usuário. Virou espera ativa
com `gh pr checks --watch --interval 30`, que bloqueia até os checks concluírem, com instrução
explícita de **rodar de novo** se estourar o tempo da ferramenta (CI de dez minutos leva dez
minutos; esperar é o trabalho).

Dois pontos que o usuário fez questão de cobrir e que estavam ausentes:

- **Vale igual no re-review.** Era o buraco maior: as correções são pequenas, o time já está
  esperando, e re-solicitar parece barato. Não é — notificar alguém pra olhar de novo um PR ainda
  compilando gasta a segunda passada, que é a mais cara.
- **Re-verificação antes do handoff.** Push novo ou check reiniciado entre a verificação e a
  pergunta invalida o verde; o gate volta pro `--watch`.

## Origem

Construção própria, do `pr-ready.v9.md` (251 linhas, **sem atribuição de terceiros**), reduzido ao
que ele tinha de próprio: **o gate de verde e o handoff**.

O nome ficou porque o usuário já o usa, e porque descreve o que a peça faz.

## Por que separado do `code-review`

Gatilhos distintos (I.22 — divida por gatilho ou sequência, nunca por tamanho): "revisa isso" e
"manda pro time" são pedidos diferentes, em momentos diferentes. E o segundo tem **gates
irreversíveis** que o primeiro não tem — sair do draft e notificar pessoas são ações que o time vê.

Confirmado pela descrição do usuário (31-07-2026): *"quando eu pedia para pr-ready o que queria é
que ele validasse que estava tudo coerente, que o código fosse bom, para então tirar o pr de draft e
marcar o revisor."*

## O que saiu

- **O loop de correção** (Passo 3 do v9: avalia → corrige via `quick-task` → re-avalia até zero
  must-fix, freado por progresso). Duas razões: a avaliação virou responsabilidade do `code-review`,
  e a correção que muda comportamento agora volta pro `implement` com TDD. Um loop que corrige
  sozinho até o painel calar é exatamente o placar que a I.14 manda cortar — o usuário via
  *"aprovado em k rodadas"* em vez dos achados.
- **`Skill sdd-review` embutida** (Passo 2b) — a peça invocava o review e extraía o veredito do
  relatório. Agora o review roda antes, por decisão do usuário, e esta peça assume que rodou.
- **Validação do alinhamento com o review do time** (Passo 2a) → foi pro `code-review`, que é onde
  se avalia se um pedido foi atendido.

## Preservado do v9, e é o coração da peça

- **⭐ Verde é pré-requisito, não formalidade.** CI passou (**incluindo o de deploy**), ou a suíte
  local **completa** — todas as camadas, todos os testes, não só os do PR. É gate de **regressão**:
  o objetivo é saber que nada de antes quebrou. Invariante E.5.
- **⭐ Nunca inventar comando de teste.** Vem do `CLAUDE.md`, do `ARCHITECTURE.md` ou da memória do
  projeto; se não estiver documentado, **pergunta**. Comando inventado produz um verde sem
  significado, que é pior que vermelho.
- **⭐ Commit e push são humanos** — não estão nem no `allowed-tools`. A peça entrega os comandos
  exatos, já preenchidos, e **espera o push concluir** antes de verificar o CI.
- **⭐ Sair do draft e marcar revisor são gates separados**, cada um com "agora não". Aprovar o
  código, atualizar o corpo e ainda assim manter em draft é escolha legítima. **O handle do revisor
  jamais é chumbado na peça** — candidatos são apoio, nunca suposição.
- **Nunca handoff no escuro** — CI ainda rodando não é verde.
- **Sem PR aberto, não cria** — orienta o `pr-draft` e para.
- **Segundo momento re-solicita os mesmos revisores**, não escolhe alguém novo.
- **Nunca posta nas threads** — só entrega rascunhos pro usuário colar.
- **Bloqueio vira instrução**, não contorno.
- **O corpo roda sem perguntar** (via `pr-draft sync`): melhorar o texto não muda status nem expõe
  nada. É a única ação da peça que não é gate.
- **Reporte final reflete o que aconteceu**, não o caminho feliz — o que ficou por fazer aparece com
  o mesmo destaque do que foi feito.
