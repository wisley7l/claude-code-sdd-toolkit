---
description: Entrega de PR de ponta a ponta — avalia se o PR segue os padrões do projeto; se sim, sync do body + tira de draft + marca reviewer; se não, loop de correção até convergir (para se não houver progresso) → commit/push humano → handoff. Nunca commita/pusha sozinho.
model: claude-sonnet-4-6
argument-hint: [N (PR) | branch | vazio = PR da branch atual]
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Agent, AskUserQuestion, Bash(git status*), Bash(git diff*), Bash(git log*), Bash(git show*), Bash(git branch*), Bash(git worktree list*), Bash(git rev-parse*), Bash(git add*), Bash(gh *), Bash(npm *), Bash(npx *), Bash(bun *), Bash(bunx *), Bash(pnpm *), Bash(node *), Bash(go *), Bash(lizard *), Bash(ls *), Bash(mkdir *)
---

# PR Ready — Entrega de PR (avaliar → corrigir → handoff)

Você fecha o ciclo de um PR já implementado: **avalia** se ele está bom e segue os padrões do projeto, **corrige** o que faltar em loop autônomo, e faz o **handoff pro review humano** (atualiza o body, tira de draft, marca o reviewer). É o passo final do workflow:

```
/sdd-spec → /sdd-plan → /pr-draft → /executor-plan → /verifica → /pr-ready
                                                        ↑ você está aqui
```

**Você orquestra, não reinventa.** A avaliação é o `/sdd-review`, as correções são `/quick-task`, o body é o `/pr-draft sync`. O valor do `/pr-ready` é o **loop** (avalia → corrige → re-avalia **até passar**) e o **handoff** sob gate humano.

> **Loop nativo, não builtin `/goal`.** Este command implementa o "corrige até tudo ok" no próprio protocolo (Passo 3) — reproduz o comportamento do builtin `/goal` sem depender dele, porque (a) um command não consegue acionar `/goal` por dentro e (b) o `/goal` roda autônomo e atropelaria as paradas humanas deste fluxo (commit/push, escolha do reviewer). Você dispara tudo com um `/pr-ready` só.

**Roda de sessão limpa** (recomendado, pós-`/clear`, dentro da worktree da feature): tudo é re-hidratado do PR + diff + PLAN/IMP — nada depende do histórico da conversa.

## Argumentos

- `$ARGUMENTS` vazio → usa o PR aberto da branch atual.
- `N` (número) → usa o PR `#N`.
- `branch` → resolve o PR aberto daquela branch.

## Princípios

- **Avaliação independente**: quem avalia é um "cérebro" diferente de quem implementou. Delega ao `/sdd-review` (subagentes Opus, sem o viés de "isso foi decidido por boa razão na execução").
- **Padrões do projeto são o critério**: "bom PR" = conformidade com `CLAUDE.md`/`ARCHITECTURE.md` + zero bug/segurança/teste must-fix. MINOR (nomenclatura, style) não bloqueia.
- **Loop até convergir, freado por progresso (não por contador)**: corrige e re-avalia **até zero must-fix** — sem teto fixo de rodadas. O que para o loop antes disso é **falta de progresso** (uma rodada que não reduz os must-fix) ou **decisão arquitetural** (fix que estoura o safety valve do quick-task), não um número arbitrário. Insistir num must-fix que não cede é loop improdutivo → para e escala pra `/sdd-plan`.
- **Commit/push é sempre humano**: o loop só faz `git add`. Quando tudo passa, você PARA, entrega os comandos exatos de commit+push e **espera o usuário concluir o push** antes de qualquer coisa remota.
- **Saída de draft e reviewer são gates seus**: tirar de draft (`gh pr ready`) e marcar reviewer são **sempre perguntados** (`AskUserQuestion`), nunca automáticos — cada um com a opção de "agora não". O handle do reviewer nunca é chumbado no command. Você pode aprovar o PR, atualizar o body e mesmo assim deixá-lo em draft / sem reviewer: a decisão de expor pro time é humana.
- **Saída só com base pronta**: `gh pr ready` só é oferecido depois de (PR aprovado) **E** (código commitado + pushado). Nunca antes da avaliação passar.
- **Bloqueio → instrução, não contorno**: se `gh pr ready`/`gh pr edit` for negado por permissão, vira guia comando-por-comando e espera o usuário.

## Fluxo de Execução

### Passo 1 — Resolver o PR e o estado

```bash
ROOT=$(git worktree list | head -1 | awk '{print $1}')
BRANCH=$(git rev-parse --abbrev-ref HEAD)
```

Detecte o PR conforme o argumento:
- vazio → `gh pr list --head "$BRANCH" --state open --json number,title,url,isDraft,baseRefName --limit 1`
- `N` → `gh pr view N --json number,title,url,isDraft,baseRefName`
- `branch` → `gh pr list --head <branch> ...`

**Sem PR aberto** → PARE. O `/pr-ready` finaliza um PR existente; ele não cria. Oriente: rode `/pr-draft` primeiro.

Capture `número`, `url`, `isDraft`, `base`. Se o PR **não** estiver em draft, avise (vai marcar reviewer mas não precisa de `pr ready`) e siga.

### Passo 2 — Avaliar (delegado ao /sdd-review)

Invoque a avaliação via **Skill `sdd-review`** sobre o PR detectado. O `/sdd-review` roda a thread em Sonnet e spawna os reviewers Opus em paralelo (bugs, segurança, queries, testes) + os mecânicos (conformidade, nomenclatura, style) — exatamente a independência que queremos.

**Você assume o controle das fixes** — não execute o Action Plan interativo (Etapa 6) do `/sdd-review`. Use-o só para **gerar o relatório e o veredito**. Após ele salvar o relatório em `thoughts/reviews/REV-*.md`, leia esse relatório e extraia:

- **must-fix** = issues 🔴 CRITICAL + 🟡 MAJOR
- **MINOR** = informativo, **não** entra no loop

**Veredito:**
- **0 must-fix** → PR aprovado. Vá pro Passo 5 (Handoff).
- **≥1 must-fix** → PR bloqueado. Vá pro Passo 3 (loop).

### Passo 3 — Loop de correção (até convergir)

Repita rodadas **enquanto houver must-fix**. **Não há teto fixo de rodadas** — o loop vai até zero must-fix (é o "continue até tudo ok"). O que interrompe antes disso é **falta de progresso** ou **decisão arquitetural**, nunca um contador.

A cada rodada `k` (1, 2, 3, …):

1. **Mostre as pendências da rodada** (relatório de pendências):
   ```
   Rodada <k> — <N> pendências must-fix:
     1. 🔴 CRITICAL — <título> — <arquivo:linha>
     2. 🟡 MAJOR — <título> — <arquivo:linha>
   Corrigindo via /quick-task (autônomo, staging only)...
   ```

2. **Corrija cada must-fix** seguindo o protocolo da Etapa 6 do `/sdd-review` (reference `sdd-review-action-plan.md`): pra cada issue, crie `<root>/thoughts/quick/NNN-fix-<slug>/TASK.md` derivado da pendência e invoque o `/quick-task` via `Agent` (`subagent_type: general-purpose`, prompt com o TASK.md + conteúdo de `quick-task.md` + **`mode: autonomo-invocado`** + instrução de **nunca commitar, só `git add`**). Acumule os resultados; se um fix bloquear (safety valve do quick-task: >5 passos, decisão arquitetural, nova lib), **pare o loop** e trate como não-convergência (item 5).

3. **Re-avalie** — rode o `/sdd-review` de novo, focando nos arquivos tocados pelas fixes + um regression check do gate do projeto. Recompute os must-fix.

4. **Mediu progresso?** Compare os must-fix desta rodada com os da anterior:
   - **Zero must-fix** → convergiu. Saia do loop, vá pro Passo 4.
   - **Total de must-fix caiu** (as pendências estão sendo resolvidas, mesmo que reste alguma) → **progresso**: próxima rodada.
   - **Total não caiu** — a(s) mesma(s) pendência(s) persiste(m) depois de uma tentativa de corrigi-la(s), ou só trocou uma issue por outra equivalente sem reduzir o total → **sem progresso**: pare (item 5). Insistir é loop improdutivo.

5. **Não-convergência** (sem progresso numa rodada, ou fix bloqueado pelo safety valve) → PARE. Não force. Reporte:
   ```
   ⚠️ PR ainda não passa nos padrões após <k> rodada(s) — o loop travou (sem progresso).

   Pendências remanescentes:
     - <issue> — <por que o quick-task não resolveu / o que estourou o safety valve>

   Isso costuma sinalizar decisão arquitetural, não quick-fix.
   Sugiro: revisar o relatório (thoughts/reviews/REV-*.md) e rodar /sdd-plan
   pra repensar a abordagem. O PR segue em draft, sem reviewer marcado.
   ```
   Encerre aqui — o handoff só acontece com PR aprovado.

### Passo 4 — Commit + push (sempre humano)

Chegou aqui = PR aprovado **com** fixes aplicadas (há mudanças staged pelo `git add` dos quick-tasks). Verifique:

```bash
git status --short
```

**Há mudanças não commitadas** → PARE e entregue os comandos exatos (já preenchidos, sem placeholders), pra rodar com o prefixo `!` na sessão ou no terminal:

```
✅ PR aprovado — 0 must-fix. As correções estão staged (não commitadas).

Commit e push são seus. Rode:

  !git commit -m "<mensagem conventional commit derivada das fixes>"
  !git push

Me avise quando o push concluir que eu sigo pro handoff (sync do body + ready + reviewer).
```

**Aguarde o usuário confirmar o push.** Não prossiga sem isso. (Working tree já limpo e branch já pushada — caso do PR aprovado sem fixes no Passo 2 — pule direto pro Passo 5.)

### Passo 5 — Handoff pro review (sob confirmação)

PR aprovado e código pushado. **Nada aqui sai sozinho** — cada ação que expõe o PR pro time é um gate seu.

1. **Atualize o body** — invoque a Skill **`pr-draft`** com argumento `sync`. Ela reescreve o body do PR como prévia pro reviewer (O quê / Por quê / Como / Test plan), rastreável a PLAN/IMP/diff, respeitando os guardrails de body público (nunca vaza caminho de `thoughts/`, link de sessão nem ROADMAP). É seguro fazer mesmo em draft — só melhora o texto, não muda status — então roda direto, sem perguntar.

2. **Pergunte as duas decisões de saída** numa única chamada `AskUserQuestion` (duas perguntas):
   - **Tirar de draft agora?** → opções: *Sim, marcar como ready* / *Não, deixar em draft*. (Pule esta pergunta se o PR já não estava em draft — detectado no Passo 1.)
   - **Marcar reviewer agora?** → ofereça candidatos como apoio (autores recentes via `gh pr list --state merged --json author --limit 20`, ou `CODEOWNERS` se existir) + a opção *Não marcar agora*. O usuário escolhe um candidato, digita outro handle (campo livre) ou recusa. **Nunca** assuma um nome.

3. **Execute só o que foi escolhido:**
   ```bash
   gh pr ready <número>                          # SÓ se "tirar de draft" = Sim
   gh pr edit <número> --add-reviewer <handle>   # SÓ se um reviewer foi escolhido
   ```
   - Se ambos forem "não/agora não": não faça nada remoto. O body já foi atualizado; informe que o PR segue em draft / sem reviewer e que a saída fica pra quando você quiser (`gh pr ready <N>` / `gh pr edit <N> --add-reviewer <handle>`).
   - Se qualquer comando for negado por permissão (ou `gh` não autenticado), **modo manual**: entregue os comandos exatos e espere o usuário rodar. Não tente contornar.

### Passo 6 — Reporte final

Reflita o que **de fato** aconteceu — `Status` e `Reviewer` dependem das suas escolhas no Passo 5:

```
🎯 PR pronto.

PR: <url>  (<base> ← <branch>)
Avaliação: ✅ aprovado (<k> rodada(s) de correção, <M> fixes aplicadas)
Body: atualizado via /pr-draft sync
Status: ready for review (saiu de draft)   ← ou: 🚧 segue em draft (a seu pedido)
Reviewer: @<handle> marcado                ← ou: não marcado (a seu pedido)

Relatório de review: thoughts/reviews/REV-*.md
```

Se ficou em draft ou sem reviewer, lembre os comandos pra completar depois: `gh pr ready <N>` e `gh pr edit <N> --add-reviewer <handle>`.

## Guardrails

- **Nunca commita nem pusha sozinho** — o loop só faz `git add`. Commit e push são do usuário, com comandos prontos e espera explícita pelo push. Não há `git commit`/`git push` no `allowed-tools` deste command.
- **Tirar de draft e marcar reviewer só sob confirmação** — ambos via `AskUserQuestion`, nunca automáticos, cada um com opção de "agora não". O handle do reviewer jamais é chumbado no command; sem reviewer escolhido, não marca ninguém; "não tirar de draft" mantém o PR em draft. O body (sync) pode ser atualizado mesmo assim.
- **Saída só com base pronta** — `gh pr ready` só é oferecido com PR aprovado (0 must-fix) **E** código pushado. Nunca antes da avaliação passar.
- **Loop até convergir, freado por progresso** — sem teto fixo de rodadas: vai até zero must-fix. Para só quando uma rodada não reduz os must-fix (sem progresso) ou um fix estoura o safety valve do quick-task → escala pro humano (`/sdd-plan`). O circuit-breaker de progresso é o que impede loop infinito, não um contador.
- **Avaliação independente** — quem avalia é o `/sdd-review` (subagentes Opus), não a thread que orquestra. Não "aprove" por conta própria sem rodar a avaliação.
- **MINOR não bloqueia** — só CRITICAL + MAJOR entram no loop. Nomenclatura/style ficam no relatório como informação.
- **Sem PR = sem entrega** — o command finaliza PR existente, não cria. Sem PR aberto, oriente `/pr-draft` e pare.
- **Body público** — o `/pr-draft sync` cuida disso; não reescreva o body por fora burlando seus guardrails (nunca vaze `thoughts/`, sessão do Claude, ROADMAP).
- **Bloqueio → instrução, não contorno** — push/ready/reviewer negado vira guia comando-por-comando, esperando o usuário.
- **GitHub via `gh` CLI** — nunca tokens manuais.
