---
name: implement-strict
description: Executa as tarefas do plano com TDD de papéis separados — um subagente só escreve o teste, outro só escreve o código, e a fronteira entre os dois é verificada no diff. O red é rodado por você, com o código de produção ainda ausente. Faz git add por tarefa e nunca commita sozinho.
disable-model-invocation: true
argument-hint: <pasta da mudança em thoughts/changes/, ou nada pra usar a mais recente>
allowed-tools: Read Edit Write Grep Glob Agent Skill AskUserQuestion Monitor Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git add*) Bash(git branch*) Bash(git worktree list*) Bash(npm *) Bash(npx *) Bash(pnpm *) Bash(bun *) Bash(bunx *) Bash(node *) Bash(go *) Bash(docker compose *) Bash(ls *) Bash(mkdir *) Bash(cat *) Bash(lsof *) Bash(kill *) Bash(curl -s -o /dev/null *) mcp__context7__resolve-library-id mcp__context7__query-docs
---

# implement-strict

Irmã do `implement`, não substituta. Lá um subagente faz o ciclo inteiro de uma tarefa; **aqui o
ciclo é cortado no meio**: um subagente escreve o teste, outro escreve o código, nenhum dos dois
cruza a fronteira, e você fica no meio rodando o red.

Escolha esta quando quiser a disciplina do TDD verificada em vez de relatada — refactor delicado,
comportamento que já falso-verdejou antes, área onde o teste tende a nascer amaciado. Nas tarefas
de rotina, o `implement` custa menos.

## O que essa variante compra, e o que cobra

**Compra:** no momento do handoff o código de produção **ainda não existe**. Então você roda o
teste com as próprias mãos e **vê** o vermelho, em vez de auditar a saída que um subagente relatou
— o limite declarado do `implement` (o red é auditado, não re-executado) simplesmente não existe
aqui. E quem escreveu o teste não tem depois como amaciá-lo pra ele passar, porque não volta a
tocar naquele arquivo. Isso é checável no `git diff --name-only`, não é promessa.

**Cobra:** dois handoffs por tarefa em vez de um, e uma rodada de teste sua entre eles.

## Entrada

`<root>/thoughts/changes/<NNN>-<slug>/` — `tasks.md` diz o que fazer, `plan.md` diz por quê e com
que verificação, `spec.md` diz qual comportamento é o alvo. **`root` é o repositório principal**
(`git worktree list | head -1`): você quase sempre roda dentro de uma worktree, onde `thoughts/`
local está vazio porque é gitignored. Vale pra toda leitura e escrita em `thoughts/`, inclusive o
`notes.md`.

## Primeiro o levantamento, uma vez só

Subagente não herda seu contexto: **o que não estiver no prompt dele não existe.** Antes de
despachar qualquer coisa, junte o material e depois distribua por papel:

1. **Constituição do projeto** — `CLAUDE.md`, `ARCHITECTURE.md`, e o `CLAUDE.md` de subdiretório
   se a tarefa mexe num deles. Vai pros dois papéis.
2. **Skills do projeto e do usuário** — liste `.claude/skills/*/SKILL.md` do repo e
   `~/.claude/skills/*/SKILL.md`, com nome e `description`. Separe:
   - as de **teste** (nome ou description falando de teste, mock, fixture, factory, coverage) →
     prompt do test-writer;
   - as de **convenção, estilo, lint, arquitetura, domínio** → prompt do code-writer;
   - as que servem aos dois entram nos dois.
   Passe o **caminho absoluto** pra ele ler, não um resumo seu: resumo de skill perde o exemplo,
   que é a parte que faz o subagente acertar o padrão.
3. **Convenção de teste concreta** — o arquivo de teste **vizinho do alvo**, não a descrição da
   convenção. Um exemplo real vale mais que três parágrafos sobre estrutura de `describe`.
4. **O gate** — o comando declarado na tarefa, e o comando da suíte completa do projeto.

Se o projeto tem skill de teste própria, ela ganha do que você inferiu do vizinho — e diga isso no
prompt, pra não sobrar ambiguidade sobre quem manda.

## O contrato é travado antes do primeiro teste

Escrever teste é escolher assinatura. Um test-writer solto fixa a API por via indireta, e o
code-writer herda um design que você nunca aprovou. Então:

- **A tarefa traz `Contrato:`** — assinatura, origem de cada parâmetro, efeito e erro, escritos pelo
  `plan` e revisados pelo usuário. É **lei** pros dois papéis, literal no prompt de cada um.
- **Não traz** (plano anterior a este formato) → derive do codebase e da spec, e **trave com o
  usuário numa pergunta só**, listando as assinaturas de todas as tarefas do lote antes do primeiro
  handoff. Delegar com contrato aberto é entregar a decisão pro subagente.
- **O code-writer objeta que o contrato não fecha** com o que já existe → **parada dura**, vai pro
  usuário com a objeção e o código vizinho na mão. Decidido o novo contrato, é o **test-writer**
  que reescreve o teste. O code-writer nunca ajusta teste, nem quando está certo.

## Os passos vão só pro code-writer

A tarefa também traz `Passos:` — a sequência prevista pelo `plan`. **Ela não entra no prompt do
test-writer**, e essa assimetria é deliberada.

Teste que conhece a ordem das chamadas testa a implementação, não o comportamento: passa a quebrar
em refactor que não mudou nada de fora, e aí o time aprende que teste vermelho às vezes é ruído —
que é como a suíte inteira perde autoridade. O test-writer trabalha com **contrato e comportamento
da spec**, e nada mais. Se ele receber a sequência, vai ancorar nela sem perceber.

Pro code-writer os passos são **intenção, não roteiro**: código vizinho que contradiz a ordem ganha,
e o desvio volta em `desvios`. Desvio de passo é registro no `notes.md`; desvio de **contrato** ou de
**comportamento** é parada dura.

## O ciclo, por tarefa

1. **Baseline.** Você roda o gate da tarefa e anota quantos testes existem antes de qualquer coisa.
2. **test-writer.** Subagente com `test-writer.md`. Volta com os arquivos de teste, os casos, a
   saída literal do red e a contagem.
3. **Você roda o red.** Não confie no relato — o código não existe, o custo de verificar é uma
   execução. Precisa dar: vermelho **pelo comportamento ausente**, contagem subindo o previsto,
   nenhum teste que passava quebrado.
4. **code-writer.** Subagente com `code-writer.md`, recebendo a saída do red e os arquivos de teste
   como leitura.
5. **Você roda o gate.** Verde, com a **mesma** contagem do passo 3 — subiu ou caiu, é parada dura.
6. **`git add`** dos arquivos da tarefa e `[x]` no `tasks.md`.

Os workers **não fazem `git add`**. Deixar no working tree é o que te permite ler a fronteira no
`git status --porcelain` sem desempilhar staging alheio.

## A fronteira, e como ela se verifica

Depois de cada retorno, olhe o diff antes de olhar o relato.

| Papel | Pode tocar | Parada dura se tocar |
|---|---|---|
| test-writer | arquivos de teste, fixtures, factories, helpers de teste — e o **esqueleto** do módulo de produção: assinatura do contrato e corpo que lança "não implementado", nada mais | qualquer lógica de produção |
| code-writer | arquivos de produção | qualquer arquivo de teste, fixture ou factory |

**Por que o esqueleto é do test-writer.** Sem ele, o primeiro red de um módulo novo falha em
`cannot find module` — que é red ilegítimo, indistinguível de um caminho de import errado. Com o
esqueleto no lugar, a falha vira "não implementado": prova que o teste **alcança** o alvo, que o
path está certo e que só falta comportamento. O esqueleto é o contrato escrito em código, e o
contrato já foi travado antes. Diff de esqueleto que traz condicional, laço ou cálculo deixou de
ser esqueleto — parada dura.

Nas duas linhas: **mostre o diff e pare, não reverta sozinho.** O desvio pode ser um setup legítimo
que o levantamento não previu, e essa distinção é do usuário.

## Paradas duras

Param a execução, e vão pro usuário com o que você tem:

- **Falso-verde** — o teste do passo 3 passa sem o código de produção. Não é "teste otimista", é
  teste que não exercita o comportamento novo. O test-writer volta, ou o comportamento já existe e
  a tarefa está errada.
- **Red ilegítimo insistente** — falhou por import, sintaxe ou setup e continuou falhando assim
  depois de uma volta ao test-writer. Não conserte o teste você mesmo: você é quem verifica, e
  quem verifica não escreve.
- **Contagem de testes caiu** — mostre quantos existiam, quantos deveriam entrar, quantos existem,
  e o diff dos arquivos de teste. Apagar teste pra fazer passar é o bug mais perigoso daqui, e se
  disfarça de progresso.
- **Fronteira cruzada** — qualquer linha da tabela acima.
- **Teste que passava começou a falhar.**
- **Ambiente que o plano exige não sobe** — não substitua por mock. O plano pediu integração ou e2e
  porque unit não responderia a pergunta.
- **Comportamento fora da spec** — lacuna da spec não é licença pra inventar.
- **Contrato objetado** — decisão do usuário, sempre.

## Como as tarefas são escalonadas

Igual ao `implement`: a unidade é o `env` declarado por tarefa no `tasks.md`.

| Tarefas | Como rodam |
|---|---|
| Ambiente `none` (unit, lógica pura) | **Paralelo** — vários pares de uma vez |
| Mesmo ambiente compartilhado (`sandbox`, `server-local`, `browser-playwright`) | **Grupo sequencial** — o ambiente sobe uma vez e as tarefas passam em fila |
| Com dependência declarada | Sequencial, na ordem da dependência |

Paralelismo aqui é **por par**: despache os test-writers das tarefas independentes numa única
resposta com todas as chamadas `Agent` juntas, rode o red de cada retorno, e só então despache os
code-writers — também juntos. Lançar uma chamada, esperar, lançar a próxima serializa e o
paralelismo evapora.

Antes de paralelizar, confirme que as tarefas não tocam o mesmo arquivo e não compartilham estado
mutável. Se tocarem, são sequenciais, independentemente do que a leitura inicial sugeriu.

## O ambiente é seu, não dos workers

Worker que sobe server é worker que retenta pra sempre contra uma porta morta. **Você** é a única
ponta que sobrevive à sessão inteira e enxerga o processo, então o ambiente fica aqui.

**Antes de subir**, confira o marcador — ele vive no **repositório principal**, único lugar visível
às outras worktrees:

```
<root>/thoughts/.env-em-uso     # branch · tarefa · hora em que foi adquirido
```

- **Livre** — registre o uso, suba, rode o grupo, e **apague o marcador ao terminar**, mesmo que o
  grupo tenha parado no meio.
- **Em uso por outra execução** — pergunte, dizendo **quem** usa e **desde quando**:

  > O ambiente `sandbox` está em uso pela branch `feat/estorno` desde 14:32.
  > Posso subir os testes de integração agora, ou prefere que eu aguarde?

  Se ele mandar aguardar, **siga com as tarefas de ambiente `none`** e volte a perguntar quando ele
  liberar. Ficar parado esperando desperdiça o paralelismo.

**Subir e vigiar:**

1. O comando de subida é o declarado no plano; sem declaração, o script de dev do projeto
   (`package.json`, `docker compose`, `Makefile`). Rode com `run_in_background`.
2. **Espere o boot** com `Monitor` até o health check responder, com teto de tempo — `sleep` em
   primeiro plano é bloqueado, e loop de `curl` sem teto é o mesmo desperdício que você está
   evitando nos workers.
3. **Health check** é o endpoint declarado, ou `curl -s -o /dev/null` na porta, ou `lsof` nela.
4. **Checar quando:** antes de despachar cada tarefa do grupo, e ao receber cada retorno. Retorno
   verde com ambiente caído é retorno suspeito — o gate pode ter passado por cache ou por skip.
5. **Caiu:** **uma** tentativa de subir de novo, com a saída do processo na mão pra saber por que
   morreu. Se não subir, **parada dura**: aborte o resto do grupo, diga quais tarefas ficaram sem
   rodar, e siga com as de ambiente `none`.
6. **Ao fim do grupo:** derrube o que você subiu e apague o marcador.

Worker que devolve `ambiente-caiu` **não é redespachado às cegas** — o ambiente volta de pé
primeiro, ou a tarefa fica pra depois. Ambiente de teste nunca é produção: efeito colateral real só
contra sandbox.

## Delegar

Duas chamadas `Agent` por tarefa, `subagent_type: general-purpose` e **`model: sonnet`** nas duas.
A tarefa chega decidida — o `plan` fechou o como, o `test-plan` fechou a verificação, o contrato
está travado, o protocolo está no arquivo; o que sobra é executar bem. O julgamento fica desta
ponta, que valida o que volta e roda no modelo da sessão. **Se um code-writer voltar bloqueado por
encruzilhada de implementação** (não por contrato), a segunda tentativa vai em `model: opus` com o
motivo da parada anexado — subir modelo é resposta a dificuldade demonstrada, não default.

Se o ambiente do usuário tiver um subagente dedicado a testes (`test-author` e afins), ele serve
como `subagent_type` no passo 2 — o protocolo continua sendo o `test-writer.md`. Sem ele,
`general-purpose` faz o mesmo trabalho.

**test-writer:**

> Leia `${CLAUDE_SKILL_DIR}/test-writer.md` e siga exatamente. Sua tarefa é **T\<N\>**, e apenas a
> parte de teste dela:
> `<bloco da tarefa, literal do tasks.md, SEM a linha de Passos>`
> Contrato travado: `<assinatura, origem dos parâmetros, efeito, erro>` — use exatamente esta, não
> proponha outra.
> Comportamento alvo: `<os cenários do requisito, literal da spec>`
> Constituição: `<CLAUDE.md e ARCHITECTURE.md>`
> Skills de teste do projeto: `<caminhos absolutos>` — leia antes de escrever.
> Exemplo de teste vizinho: `<caminho>`. Gate: `<comando>`. Ambiente: `<none, ou o que está de pé
> e como alcançá-lo>`.

**code-writer:**

> Leia `${CLAUDE_SKILL_DIR}/code-writer.md` e siga exatamente. Sua tarefa é **T\<N\>**, e apenas o
> código de produção dela:
> `<bloco da tarefa, literal do tasks.md — inclusive Passos>`
> Contrato travado: `<assinatura, origem dos parâmetros, efeito, erro>` — implemente exatamente
> esta; se não fechar com o codebase, pare e objete.
> Passos previstos: `<a sequência>` — intenção, não roteiro: vizinho que contradiz ganha, e o desvio
> vai no retorno.
> Testes que precisam passar (leitura, jamais edição): `<caminhos>`
> Red verificado: `<saída literal do teste falhando>`
> Constituição: `<CLAUDE.md e ARCHITECTURE.md>`
> Skills de convenção do projeto: `<caminhos absolutos>`.
> Gate: `<comando>`. Contagem esperada: `<N>`. Ambiente: `<none, ou o que está de pé>`.

## Validar o que volta

Ordem: **diff, contagem, relato.** As duas primeiras são determinísticas e são as que você confia.

- `git status --porcelain` bate com a tabela de fronteira do papel.
- A contagem subiu no passo 3 exatamente o que a tarefa previa, e ficou **igual** no passo 5.
- No passo 3, o vermelho é o seu, não o dele.
- No passo 5, verde de verdade: nenhum `skip`, nenhum `only`, nenhum teste desabilitado no diff.

Retorno bloqueado ou parcial não vira "quase pronto": pare e leve ao usuário.

## Quando as tarefas acabam

**Gate de verde primeiro.** Rode a suíte **completa** do projeto, não só os testes tocados, mais
typecheck e lint. Compare a contagem global com a do início mais o que as tarefas somaram.

## A passada de simplificação

Com o verde na mão e **antes do review**, ofereça a passada do `code-simplifier`. É o refactor do
ciclo: o comportamento já está preso por teste, então dá pra mexer na forma com rede embaixo.

**Sob confirmação, toda vez** — ter aceitado antes não é aceitar agora:

> Suíte completa verde, 47 testes. Posso passar o `code-simplifier` nos 9 arquivos de produção
> staged?

Aprovado, lance `Agent` com `subagent_type: code-simplifier`, escopado aos **arquivos de produção
staged desta mudança** (`git diff --cached --name-only`, menos os de teste), e com esta restrição:

> Aplique direto o que é local: comentário redundante, `let` que devia ser `const`, early return
> óbvio, guard duplicado, nome de variável dentro da função.
> **Não aplique mudança estrutural** — split de função, arquivo novo, mudança de assinatura
> pública, código movido entre arquivos, abstração extraída. Encontrando uma, **descreva no
> retorno** em vez de aplicar.
> **Não toque em arquivo de teste.**

Teste fora do escopo não é descuido: aqui o teste é a verificação, e simplificar verificação é
mudar o que está sendo verificado. A fronteira que valeu durante o ciclo vale na limpeza.

As estruturais que voltarem viram **uma** pergunta, com o diff em mãos — e recusa é decisão, não
ponto a rebater.

**Depois dela, o gate inteiro de novo.** Simplificação que quebra teste que passava não é limpeza,
é mudança de comportamento: **parada dura**, com o teste quebrado na tela. Não reverta sozinho nem
ajuste o teste — o simplifier pode ter esbarrado num acoplamento real, e isso é conversa.

**Plugin ausente** (`code-simplifier@claude-plugins-official`): diga isso e siga. A passada é
ganho, não gate.

## Depois, o review

Você **não invoca** o review — nenhuma peça deste toolkit invoca outra. Termine mostrando o estado
e peça:

> Tarefas concluídas, suíte verde, 47 testes. Rode **`/tk7:imp-review`** sobre o que está
> staged — seis lentes independentes, e o review não é meu porque acabei de orquestrar este código.

Deixe isso como a última linha, não como sugestão no meio de um resumo. E não commite antes:
review depois do commit é review que já chegou tarde.

## O commit é dele

`git add` por tarefa é livre. **Commit e push exigem OK explícito** — e push é sempre ação do
usuário, nunca sua.

No fim, mostre o que está staged agrupado por tarefa e ofereça: um commit único com o corpo listando
as tarefas, ou um commit por tarefa. Se duas tarefas tocaram o mesmo arquivo, diga isso antes.

## O registro

`thoughts/changes/<NNN>-<slug>/notes.md`, escrito conforme a execução avança, não no fim de memória:

```markdown
# Execução (strict) — <slug>

## Contrato
| T | Assinatura | Origem |
|---|---|---|
| T1 | `calcRefund(order, amount) → Result<Refund, RefundError>` | plan.md · travada com o usuário |

## Tarefas
| T | Casos | Red (verificado por mim) | Testes | Gate | Produção |
|---|---|---|---|---|---|
| T1 | 5 | `calcRefund` lançou `não implementado` | 12 → 17 | verde | `src/refund/calc.ts` |

## Fronteira
- <cruzamento detectado e o que o usuário decidiu, ou "nenhum">

## Ambiente
- <o que subiu, quando caiu, o que ficou sem rodar>

## Desvios do plano
- <o que mudou durante, e por quê>

## Simplificação
- <o que a passada mexeu> · Estruturais propostas: <aceita | recusada pelo usuário>

## Dívida
- <o que ficou, incluindo casos que o test-writer sugeriu e não entraram>
```

`thoughts/` é local e gitignored — não commite.

## Ao terminar

Em tela: tarefas executadas, contagem de testes do início ao fim, os contratos travados e quem os
decidiu, quais ambientes foram usados e se algum caiu, cruzamentos de fronteira, os desvios do
plano, o que a simplificação mexeu (e o que ela propôs e você recusou), e a dívida que ficou.
Depois o que está staged, e a pergunta de como commitar.
