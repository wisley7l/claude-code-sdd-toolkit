---
name: implement
description: Executa as tarefas do plano com TDD — teste primeiro, red verificado, implementação, green. Delega tarefas independentes a subagentes em paralelo e valida cada retorno. Faz git add por tarefa e nunca commita sozinho.
disable-model-invocation: true
argument-hint: <pasta da mudança em thoughts/changes/, ou nada pra usar a mais recente>
allowed-tools: Read Edit Write Grep Glob Agent Skill AskUserQuestion Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git add*) Bash(git branch*) Bash(git worktree list*) Bash(npm *) Bash(npx *) Bash(pnpm *) Bash(bun *) Bash(bunx *) Bash(node *) Bash(go *) Bash(ls *) Bash(mkdir *) Bash(cat *) Bash(curl -s -o /dev/null *) mcp__context7__resolve-library-id mcp__context7__query-docs
---

# implement

Executa o `tasks.md` de uma mudança. Você **orquestra e valida**: identifica o que é independente,
delega esses grupos a subagentes que rodam em paralelo, e confere cada retorno contra o gate e a
contagem de testes. O que é sequencial você executa direto — delegar aí é só overhead.

Entrada: `<root>/thoughts/changes/<NNN>-<slug>/` — `tasks.md` diz o que fazer, `plan.md` diz por quê
e com que verificação, `spec.md` diz qual comportamento é o alvo. **`root` é o repositório
principal** (`git worktree list | head -1`): você quase sempre roda dentro de uma worktree, onde
`thoughts/` local está vazio porque é gitignored. Vale para toda leitura e escrita em `thoughts/`,
inclusive o `notes.md` que você escreve. Leia `CLAUDE.md` e
`ARCHITECTURE.md` antes de escrever qualquer linha.

## O ciclo, que não tem atalho

Para cada tarefa, nesta ordem:

1. **Contagem baseline.** Rode o gate da tarefa e anote quantos testes existem **antes** de você
   tocar em qualquer coisa.
2. **Escreva o teste que falta.** O tipo e o ambiente vêm da tarefa — `unit` não é default, e o
   plano já decidiu isso com o usuário.
3. **Rode o teste e confirme o red.** Ele precisa falhar **pelo motivo certo**: o comportamento
   ainda não existe. Falha por import quebrado, sintaxe ou setup é red ilegítimo — conserte o
   setup e rode de novo até a falha ser a real.
4. **Implemente** o mínimo que faz o teste passar, seguindo os padrões do codebase. Quando o
   codebase e o plano divergirem, siga o codebase e anote o desvio.
5. **Rode o gate e confirme o green**, com a contagem esperada.
6. **`git add`** dos arquivos da tarefa e marque `[x]` no `tasks.md`.

**Falso-verde é parada dura.** Se o teste passa *antes* de você escrever o código de produção,
ele não está exercitando o comportamento novo — não importa quão razoável ele pareça. Pare,
reescreva o teste, e só siga com um red legítimo na mão.

A única dispensa do red é a tarefa que o `test-plan` já marcou como verificação manual, com o
usuário tendo aprovado. Você não cria essa exceção aqui; registra a que já existe.

## Paradas duras

Param a execução em qualquer circunstância, e vão pro usuário com o que você tem:

- **Falso-verde** — teste passando sem o código.
- **Contagem de testes caiu** — mostre quantos existiam, quantos deveriam ter entrado, quantos
  existem agora, e o diff dos arquivos de teste. Não conserte sozinho: apagar teste pra fazer
  passar é o bug mais perigoso que existe aqui, e ele se disfarça de progresso.
- **Teste que passava começou a falhar** — pode significar que o entendimento mudou, não que o
  código está errado. Mostre o que quebrou e por quê.
- **Ambiente que o plano exige não sobe** — não substitua por mock. O plano pediu integração ou
  e2e porque unit não responderia a pergunta.
- **Comportamento fora da spec** — se a tarefa só fecha entregando algo que a spec não pede, isso
  é lacuna da spec, não licença pra inventar.
- **Encruzilhada com solução não óbvia** — investigue a cadeia inteira antes de propor, e traga
  as opções. A primeira solução que compila não é evidência de que o lugar está certo.

## Como as tarefas são escalonadas

O `plan` já declarou o ambiente de cada tarefa. **É por ele que se agrupa:**

| Tarefas | Como rodam |
|---|---|
| Ambiente `none` (unit, lógica pura) | **Paralelo** — vários subagentes de uma vez |
| Mesmo ambiente compartilhado (`sandbox`, `server-local`, `browser-playwright`) | **Grupo sequencial** — o ambiente sobe uma vez e as tarefas passam por ele em fila |
| Com dependência declarada entre si | Sequencial, na ordem da dependência |

Agrupar por ambiente é o que deixa o red sobreviver ao paralelismo: cada tarefa do grupo tem sua
vez com o ambiente de pé, em vez de todas disputarem a mesma porta. Rodar integração e e2e só no
fim pareceria mais simples e destruiria o red dessas tarefas — o teste nasceria depois do código.

Antes de paralelizar um grupo, confirme que as tarefas não tocam o mesmo arquivo e não compartilham
estado mutável. Se tocarem, elas são sequenciais, independentemente do que a leitura inicial
sugeriu.

## O ambiente compartilhado é de quem chegou primeiro

O usuário pode ter outra execução em andamento em outra worktree, com o mesmo ambiente. **Antes de
subir ou usar qualquer ambiente**, verifique — e o marcador vive no **repositório principal**
(`git worktree list | head -1`), porque é o único lugar visível às outras worktrees:

```
<root>/thoughts/.env-em-uso     # branch · tarefa · hora em que foi adquirido
```

- **Livre** — registre o uso no marcador, suba o ambiente, rode o grupo, e **apague o marcador ao
  terminar**, mesmo que o grupo tenha parado no meio.
- **Em uso por outra execução** — pergunte, dizendo **quem** está usando e **desde quando**:

  > O ambiente `sandbox` está em uso pela branch `feat/estorno` desde 14:32.
  > Posso subir os testes de integração agora, ou prefere que eu aguarde?

  Se ele mandar aguardar, **siga com as tarefas que não precisam de ambiente** e volte a perguntar
  quando ele liberar. Ficar parado esperando é desperdiçar o paralelismo que justifica o modo.

Ambiente de teste nunca é produção. Efeito colateral real só contra sandbox.

## Delegar

Um grupo paralelo vira uma única resposta com **todas** as chamadas `Agent` juntas — lançar uma,
esperar, lançar a próxima serializa e o paralelismo evapora.

Cada subagente (`subagent_type: general-purpose`) recebe:

> Leia `${CLAUDE_SKILL_DIR}/worker.md` e siga exatamente. Sua tarefa é **T\<N\>**, e apenas ela:
> `<bloco da tarefa, literal do tasks.md>`
> Constitution: `<conteúdo de CLAUDE.md e ARCHITECTURE.md>`
> Convenções de teste: `<síntese>`. Ambiente: `<none, ou o que já está de pé e como alcançá-lo>`.

Subagente não herda estas instruções nem o histórico desta sessão — o que não estiver no prompt
dele não existe.

## Validar o que volta

Cada retorno traz status, arquivos alterados, resultado do gate, contagem antes e depois, e a
**saída literal do teste falhando** no red. Confira, antes de aceitar:

- A contagem subiu o que a tarefa previa — esta é a parte determinística e é a que você confia.
- A falha do red é de comportamento ausente, não de import ou setup. **Você não re-executa o red**
  (o código já existe, refazer custaria tudo de novo), então a evidência é relato verificado na
  forma, não prova. Vale saber disso ao ler.
- O gate está verde e nenhum arquivo colidiu entre tarefas do grupo.

Retorno bloqueado ou parcial não vira "quase pronto": pare o grupo e leve ao usuário.

## Quando as tarefas acabam

**Gate de verde primeiro.** Rode a suíte **completa** do projeto, não só os testes tocados, mais
typecheck e lint. Compare a contagem global com a do início mais o que as tarefas somaram.

## A passada de simplificação

Com o verde na mão e **antes do review**, ofereça a passada do `code-simplifier`. É o refactor do
ciclo: o comportamento já está preso por teste, então dá pra mexer na forma com rede embaixo.

**Sob confirmação, toda vez** — ter aceitado antes não é aceitar agora:

> Suíte completa verde, 47 testes. Posso passar o `code-simplifier` nos 9 arquivos staged?

Aprovado, lance `Agent` com `subagent_type: code-simplifier`, escopado aos **arquivos staged desta
mudança** (`git diff --cached --name-only`), e com esta restrição no prompt:

> Aplique direto o que é local: comentário redundante, `let` que devia ser `const`, early return
> óbvio, guard duplicado, nome de variável dentro da função.
> **Não aplique mudança estrutural** — split de função, arquivo novo, mudança de assinatura
> pública, código movido entre arquivos, abstração extraída. Encontrando uma, **descreva no
> retorno** em vez de aplicar.

A fronteira não é capricho. O que parece óbvio de extrair costuma ser design deliberado, e quem
decide isso é o usuário. As estruturais que voltarem viram **uma** pergunta, com o diff em mãos —
e recusa é decisão, não ponto a rebater.

Uma passada, sobre o conjunto. Por tarefa colidiria com os subagentes paralelos e encheria de ruído
o diff entre uma tarefa e outra.

**Depois dela, o gate inteiro de novo** — suíte completa e contagem de testes. Simplificação que
quebra teste que passava não é limpeza, é mudança de comportamento: **parada dura**, com o teste
quebrado na tela. Não reverta sozinho nem ajuste o teste — o simplifier pode ter esbarrado num
acoplamento real, e isso é conversa, não conserto.

**Plugin ausente** (`code-simplifier@claude-plugins-official`): diga isso e siga. Não improvise um
subagente genérico com o mesmo nome — a passada é ganho, não gate.

## Depois, o review

Você **não invoca** o review — nenhuma peça deste toolkit invoca outra. Termine mostrando o estado
e peça:

> Tarefas concluídas, suíte verde, 47 testes. Rode **`/tk7:imp-review`** sobre o que está
> staged — seis lentes independentes, e o review não é meu porque acabei de escrever este código.

Deixe isso como a última linha, não como sugestão no meio de um resumo. E não commite antes: review
depois do commit é review que já chegou tarde.

O review não é seu: você acabou de escrever este código e não enxerga o que faltou. E se uma
correção de lá quebrar um teste ou derrubar a contagem, isso é parada dura como qualquer outra.

## O commit é dele

`git add` por tarefa é livre. **Commit e push exigem OK explícito** — e push é sempre ação do
usuário, nunca sua.

No fim, mostre o que está staged agrupado por tarefa e ofereça: um commit único com o corpo
listando as tarefas, ou um commit por tarefa. Se a mesma tarefa e outra tocaram o mesmo arquivo,
diga isso antes — commits atômicos ali perdem contexto.

## O registro

`thoughts/changes/<NNN>-<slug>/notes.md`, escrito conforme a execução avança, não no fim de
memória:

```markdown
# Execução — <slug>

## Tarefas
| T | Red (evidência) | Testes | Gate | Arquivos |
|---|---|---|---|---|
| T1 | `calcula estorno parcial` falhou: `calcRefund is not a function` | 12 → 17 | verde | `src/refund/calc.ts` |

## Desvios do plano
- <o que mudou durante, e por quê>

## Simplificação
- <o que a passada mexeu> · Estruturais propostas: <aceita | recusada pelo usuário>

## Review
- Aplicado: <achado> · Descartado: <achado> — <motivo>

## Dívida
- <o que ficou, incluindo verificação manual pendente>
```

`thoughts/` é local e gitignored — não commite.

## Ao terminar

Em tela: tarefas executadas, contagem de testes do início ao fim, quais ambientes foram usados,
os desvios do plano, o que a simplificação mexeu (e o que ela propôs e você recusou), os achados
do review com o que foi feito de cada um, e a dívida que ficou.
Depois o que está staged, e a pergunta de como commitar.
