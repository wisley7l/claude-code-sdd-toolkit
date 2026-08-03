---
name: pr-ready
description: Fecha a entrega de um PR — confirma que está verde (CI ou suíte completa), atualiza o corpo, e faz o handoff pro time tirando do draft e marcando o revisor. Depois de corrigir o que o time pediu, re-solicita a revisão. Nunca commita, nunca faz push, nunca expõe o PR sem você confirmar.
disable-model-invocation: true
argument-hint: [número do PR | branch | vazio = PR da branch atual]
allowed-tools: Read Grep Glob Skill AskUserQuestion Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git branch*) Bash(git rev-parse*) Bash(git worktree list*) Bash(gh *) Bash(npm *) Bash(npx *) Bash(pnpm *) Bash(bun *) Bash(bunx *) Bash(node *) Bash(go *) Bash(make *) Bash(docker *) Bash(docker-compose *) Bash(ls *)
---

# pr-ready

O passo que expõe o trabalho ao time. Confirma que o PR está **verde**, atualiza o corpo, e entrega
— tirando do draft e marcando quem revisa.

Dois momentos, detectados pelo estado do PR:

- **Primeira entrega** — ninguém revisou ainda: verde → corpo → sai do draft → revisor.
- **Depois do review do time** — você já corrigiu o que pediram: verde → corpo → **re-solicita a
  revisão de quem pediu mudanças**.

**Você não avalia código aqui.** Isso é do `code-review`, e ele deve ter rodado antes — inclusive,
no segundo momento, para confirmar que cada ponto do time foi atendido. Se ainda houver pendência
conhecida, volte pra lá: entregar com pendência aberta gasta o tempo de quem revisa.

Roda bem de **sessão limpa**, dentro da worktree. Tudo é lido do PR e do repositório.

## Achar o PR

Sem argumento, o PR aberto da branch atual (`gh pr list --head <branch> --state open`). Com número
ou branch, aquele.

**Sem PR aberto, pare** — esta peça finaliza um PR existente, não cria. O `pr-draft` é quem abre.

Guarde número, URL, base e se está em draft. E detecte o momento:

```bash
gh pr view <N> --json reviews,latestReviews,reviewRequests,author
```

Review submetido por outra pessoa, ou comentário inline humano → **segundo momento**. Registre
**quem** revisou: são essas pessoas que serão notificadas de novo, não alguém novo.

## Verde é pré-requisito, não formalidade

Nada de handoff sem verde confirmado. E verde significa **regressão coberta**: todas as camadas,
todos os testes — não só os que este PR tocou. O objetivo é saber que nada de antes quebrou.

**Com CI** (`ls .github/workflows/`, `gh pr checks <N>`): o verde é o do CI, **incluindo o de deploy**
quando existir. O CI roda no push, então a ordem é commit e push primeiro, verificação depois.

**Espere o CI terminar. Não é opcional e não é "checar uma vez".**

```bash
gh pr checks <N> --watch --interval 30
```

Isso bloqueia até todos os checks concluírem — exit 0 quando tudo passou, diferente de zero quando
algo falhou. Se o comando estourar o tempo da ferramenta antes de o CI acabar, **rode de novo**;
CI de dez minutos leva dez minutos, e esperar é o trabalho. Se preferir não segurar a sessão, rode
em background e volte quando terminar — o que não existe é seguir sem o resultado.

Enquanto está amarelo, **nada de handoff**: não tire do draft, não marque revisor, não re-solicite
revisão. Pedir review com CI rodando entrega ao time a chance de revisar um PR que vai quebrar em
dois minutos — e o custo cai inteiro em quem revisou.

**Sem CI**: a suíte local completa, antes do push. Descubra no `CLAUDE.md`, no `ARCHITECTURE.md` e
na memória do projeto como subir o que for necessário e qual o comando de cada camada. **Se não
achar, pergunte** — comando de teste inventado produz um verde que não significa nada.

Vermelho é pendência, não obstáculo a contornar:

- Falha que uma correção resolve → volte ao `code-review` com o teste quebrado como ponto de partida.
  A origem da pendência é o teste, não um achado inventado.
- Flaky, infra, ou algo maior → pare e reporte. **Nunca entregue com vermelho.**

**O gate vale igual nos dois momentos.** No re-review a tentação é maior — as correções são pequenas,
o time já está esperando, e re-solicitar parece barato. Não é: notificar alguém para olhar de novo
um PR que ainda está compilando gasta a segunda passada dele, que é a mais cara. Push das correções
→ `--watch` → verde → só então re-solicitar.

## Commit e push são seus

Esta peça **não commita e não faz push** — não estão nem nas ferramentas dela.

Havendo mudanças pendentes, pare e entregue os comandos exatos, já preenchidos, para você rodar com
o prefixo `!` ou no terminal:

```
As correções estão staged, não commitadas. Commit e push são seus:

  !git commit -m "<mensagem derivada do que mudou>"
  !git push

Me avise quando o push concluir que eu confirmo o CI e sigo.
```

E **espere de fato**. Só depois do push confirmado o CI tem o que verificar.

## O corpo

Com verde na mão, o corpo precisa refletir o que foi implementado. Isso é do `pr-draft`, e **você
não o invoca** — nenhuma peça deste toolkit invoca outra:

> Verde confirmado. Rode **`/tk7:pr-draft sync`** pra reescrever o corpo como prévia de quem
> revisa. Volte pra cá e eu sigo pro handoff.

Espere ele fechar antes de oferecer o handoff. Entregar o PR com corpo desatualizado gasta o tempo
de quem revisa logo no primeiro contato.

## O handoff é seu, item por item

Tudo o que expõe o PR ao time passa por você, via `AskUserQuestion`, **cada um com a opção de não
fazer agora**. Aprovar o código, atualizar o corpo e ainda assim manter o PR em draft é uma escolha
legítima.

Chegar aqui exige o CI concluído e verde. Se algo mudou desde a última verificação — um push novo,
um check que reiniciou — **volte pro `--watch`** antes de oferecer qualquer item abaixo.

**Primeira entrega:**

- **Sair do draft?** — `gh pr ready <N>` só se você disser sim.
- **Marcar revisor?** — ofereça candidatos como apoio (autores de PRs recentes, ou o `CODEOWNERS`
  se existir), mais a opção de digitar outro e a de não marcar. **Nunca assuma um nome**, e nunca
  deixe um handle escrito nesta peça.

**Depois do review do time:**

- **Re-solicitar revisão** de quem pediu mudanças? O PR normalmente já saiu do draft — aqui é só
  notificar de novo quem revisou, não escolher alguém diferente.
- Ofereça os **rascunhos de resposta** das threads que o `code-review` levantou, prontos pra você
  colar. Esta peça **não posta no PR**.

Comando negado por permissão vira guia comando a comando, com os valores reais preenchidos. Sem
contornar.

## Ao terminar

Reflita o que **de fato** aconteceu, não o caminho feliz:

```
PR: <url>  (<base> ← <branch>)
Verde:    CI concluído e verde (deploy incluído)   |   suíte local completa passou (sem CI)
Corpo:    atualizado
Status:   pronto pra review   |   segue em draft, a seu pedido
Revisor:  @<handle>   |   revisão re-solicitada a @<handle>   |   não marcado, a seu pedido
```

Ficou em draft ou sem revisor, lembre o comando pra completar depois. O que não foi feito aparece
com o mesmo destaque do que foi.
