---
name: pr-audit
description: Audita a dívida que os code reviews deixaram para trás — varre PRs mergeados de um período, extrai o que os revisores levantaram, confere ponto por ponto no código de hoje, e alimenta uma issue perene com o que continua aberto. Só afirma o que tem evidência em arquivo:linha. Nunca comenta nos PRs auditados.
disable-model-invocation: true
argument-hint: '[<4 semanas atrás | de DD-MM a DD-MM | desde <tag/release>>] [--autor @me] [--revisor <login>]'
allowed-tools: Read Write Grep Glob Agent AskUserQuestion Bash(gh *) Bash(git log*) Bash(git diff*) Bash(git check-ignore *) Bash(git worktree list*) Bash(roadmap:*) Bash(roadmap) Bash(ls *) Bash(find *) Bash(structure-cache *) Bash(structure-cache)
---

# pr-audit

Review produz duas classes de resultado: o que o autor corrigiu antes do merge, e o que todo mundo
concordou em deixar pra depois. **A segunda evapora** — vira comentário enterrado num PR fechado,
sem dono e sem prazo. Esta peça recupera esse passivo e o transforma em algo que o time consegue ver.

A regra que governa tudo: **nada é reportado sem evidência no código atual.** "O autor prometeu no
PR" não é estado; `arquivo:linha` é.

Isto é **resgate**, não profilaxia. O `pr-close` colhe follow-up de um PR no momento do merge; aqui se
varre N PRs já mergeados pra recuperar o que escapou, ou o que se acumulou antes de existir fluxo.

## Guardrails

- **Subagentes são read-only.** Não editam, não commitam, não abrem issue.
- **Criar ou comentar issue exige OK explícito**, com o conteúdo na tela antes. Auditoria é leitura;
  publicar é ação que o time inteiro vê.
- **Nunca comente nos PRs auditados.** Aqui se lê review; não se responde, não se resolve thread.
- **Sem evidência, sem afirmação.** "Resolvido" só com `arquivo:linha` conferido. Senão:
  *"não verificável — <motivo>"*.

## 1 · A janela, e depois a lista

A janela é sempre ancorada em **`mergedAt`**, nunca em `createdAt` — o review acontece perto do
merge, e um PR aberto há três meses que mergeou ontem pertence à rodada de ontem.

Aceite as três formas que a pessoa realmente usa, e **resolva tudo em datas absolutas** antes de
consultar:

| O que ele diz | Como resolver |
|---|---|
| "4 semanas atrás", "últimos 10 dias" | `date -d '4 weeks ago' +%Y-%m-%d` como início, hoje como fim |
| "de 01-07 a 15-07", "do dia 1 ao dia 15" | as duas datas como vieram; ano corrente se ele omitir |
| "desde o release 2.3", "desde a tag v1.8" | `git log -1 --format=%cs <tag>` dá a data do marco |

Sem argumento nenhum, o default é **3 semanas** — mas diga qual janela assumiu. Se o pedido for
ambíguo ("desde o último release", com três tags candidatas), pergunte: janela errada faz a rodada
inteira olhar pro período errado, e isso só aparece no fim.

Com as datas na mão, filtre **no servidor** — o range vai na `--search`, que é onde o GitHub sabe
filtrar por data:

```bash
gh pr list --search "is:pr is:merged merged:2026-07-01..2026-07-15 author:@me" \
  --state all --limit 100 \
  --json number,title,state,createdAt,mergedAt,updatedAt,reviews
```

Puxar os últimos N e filtrar no cliente parece equivalente e não é: o `--limit` corta pelos **mais
recentes**, então uma janela antiga volta vazia sem erro nenhum — e vazio silencioso lê como "nenhuma
dívida", que é a conclusão errada mais cara desta peça.

**Confirme a janela resolvida na tela** antes de gastar subagente:

> Janela: **01-07-2026 a 15-07-2026** · autor `@me` · 9 PRs mergeados.

Mergeados na janela são a fonte de dívida. **Abertos com review entram no relatório** mesmo não
sendo dívida — é frequentemente onde está o trabalho mais urgente. Fechados sem merge ficam de
fora, salvo pedido.

Antes de disparar os subagentes, levante o **inventário do tracker** (backlog, issues abertas, e o
`roadmap list --json` se o projeto usa o vault). Eles vão cruzar contra isso, e é mais barato
descobrir a forma do tracker uma vez do que N vezes.

## 2 · Um subagente por grupo

Agrupe 2–3 PRs **por tema** — mesmo subsistema no mesmo grupo, pra o agente reaproveitar o contexto
de código entre eles. Dispare todos **numa única resposta**; em turnos separados, o paralelismo
evapora.

`subagent_type: general-purpose`, `model: opus` — é trabalho de julgamento.

> Leia `${CLAUDE_SKILL_DIR}/audit-worker.md` e siga exatamente.
> Repo `<caminho>`, branch `<base>`, `<stack em uma linha>`. Audite os PRs **#A**, **#B**.
> Tracker: `<como listar o backlog>`.
> Contexto que só eu tenho: `<PRs derivados que podem ter fechado o ponto, issue que serve de
> checklist, diagnóstico anterior a confirmar>`.

Essa última linha muda a qualidade do retorno mais que qualquer ajuste de formato.

## 3 · Triagem — aqui a auditoria vira útil ou vira ruído

**Centralizada aqui, nunca no subagente.** Eles auditam PRs diferentes e triariam com critérios
divergentes. Se algum retorno veio sem `Fonte`, `Classe` ou as datas, **não triague por adivinhação**:
reprocesse aquele grupo.

### Três coisas que parecem dívida e não são

**Review esperando resposta.** `CHANGES_REQUESTED` com `submitted_at` **posterior** ao último commit
significa que o autor ainda não respondeu. Isso pertence ao PR, não a um backlog — registrar ali
contorna o revisor. Compare as duas datas explicitamente.

**Follow-up que já tem PR aberto.** O problema é merge, não registro. Vai pro relatório como
contexto; no checklist, encheria a lista de item que já tem dono e caminho.

**Decisão deliberada de adiar.** "Não adicione o método agora, o contrato vai mudar" é engenharia,
não dívida. Registre como decisão se houver onde; não cobre como pendência.

### Uma que é dívida, mas não do jeito que parece

**Opcional que o revisor ofereceu e ninguém fez** — aprovação com "se quiser já corrige aqui", e o
PR mergeou sem.

O reflexo é rebaixar o item *porque* o revisor liberou o merge. É exatamente assim que se constrói
o loop que mata backlog: **item nasce baixo porque foi adiado, e nunca é pego porque está baixo.**

Adiar uma vez já confirma a dívida. O revisor ofereceu a janela mais barata que existia — dentro do
PR, código aberto, contexto quente — e ela foi recusada por decisão explícita. Corrigir agora custa
PR novo, review novo, contexto frio. O item entra na fila, e a posição vem da **natureza do risco**,
nunca do fato de ter sido adiado.

Mantenha a marca de que o revisor não bloqueava. Sem ela o item lê como pedido ignorado, e uma
auditoria útil passa a soar como acusação — a marca explica a origem sem mudar a posição.

Se o PR mergeou **com** a correção, não é dívida. Confirme no diff.

### Duas que não parecem dívida e são

**Fix aceito que nunca executa.** Um `if (campo > 0)` aprovado no review, num caminho onde o campo
nunca é populado. Passa em review, passa em teste, e a tela segue errada. Fix que depende de um
campo pede confirmação de que quem serve aquela rota o preenche.

**Regressão de escopo entre PRs.** Um PR estabelece uma invariante, outro encolhe o alcance dela, e
ninguém liga os dois porque foram reviews diferentes. Compare PRs que tocaram os mesmos arquivos de
configuração e seed dentro da janela.

Some-se **código sem consumidor**: tabela, coluna ou módulo que mergeou e nunca foi usado. Grep pelo
símbolo que só responde com a própria definição e a migration é dívida — costuma ser a metade 1 de
um plano cuja metade 2 nunca abriu.

## 4 · O tracker está mentindo?

Desalinhamento é achado de primeira classe, porque backlog que mente causa retrabalho:

- Item aberto descrevendo problema que um PR mergeado já corrigiu.
- Item dizendo "nunca implementado" quando o PR mergeou.
- Item bloqueado por dependência que já caiu, seguindo despriorizado por inércia.
- Item pedindo decisão que outro PR já tomou.
- Mudança arquivada como concluída com tarefa em aberto — pior variante: o documento arquivado
  descreve o desenho que o review derrubou, e vai orientar errado quem reler.

## 5 · A issue perene

**Uma por repositório**, reaproveitada a cada rodada. Título canônico:

```
chore: Auditoria contínua de follow-ups de review
```

**Procure antes de criar** (`gh issue list --search`): ela provavelmente já existe. Abrir uma segunda
divide o histórico em dois lugares e nenhum passa a valer.

**Body = só o que está aberto.** É de lá que sai o contador do checklist, o único sinal agregado de
quanto falta. Bloco que fecha inteiro **sai do body** e sobrevive no comentário da rodada. Body que
só cresce trava o contador em "45 of 120" e para de significar.

O body carrega: a **nota de precedência** (onde a prioridade se decide de verdade — a issue é o
espelho, e duas fontes sem hierarquia divergem), o **critério de entrada** (ponto sem dono, ou
bloqueante independente de rastreio), e o **checklist agrupado** — bloqueantes primeiro, depois por
eixo. Nits vão agregados num único checkbox, com o detalhe no comentário.

```markdown
- [ ] Cupom aplicado duas vezes em pedido reenviado — grava total errado, sem trilha de correção.
      `DADO` · ativo · `src/checkout/cart.ts:88` · PR #142 · rev. marcou opcional no PR
```

### A ordem é a natureza do risco

Tudo que chega aqui **já foi adiado ao menos uma vez** — senão não seria dívida. Então "foi adiado"
não ordena nada: é o critério de entrada.

| # | Risco | Por que vem antes |
|---|---|---|
| 1 | `SEGURANCA` | explorável por terceiro; não dá pra descobrir depois |
| 2 | `DADO` | dado errado é silencioso e **irreversível** — corrompe histórico enquanto ninguém olha |
| 3 | `CONTRATO` | quebra consumidor externo; o custo cresce a cada novo integrador |
| 4 | `DISPONIBILIDADE` | dói, mas **é visível na hora** — por isso vem depois de `DADO` |
| 5 | `ROBUSTEZ` | transforma falha silenciosa em falha diagnosticável |
| 6 | `COBERTURA` | é rede de proteção, não correção |
| 7 | `HIGIENE` | um checkbox agregado; nunca disputa espaço com o resto |

Desempate, nesta ordem: **`ativo` antes de `armado`** — e item armado não é urgente, é
**pré-requisito de `<o plano ou rota que o arma>`**, o que é acionável em vez de ruído. Depois,
**irreversível antes de reversível**.

### Quando um item nunca sai

Item aberto rodada após rodada não é problema de prioridade: está **mal descrito, mal dimensionado,
ou sem dono possível**. Proponha ao usuário decidir entre fazer, redimensionar em algo executável,
ou **fechar explicitamente como risco aceito**.

Esse último caminho vale tanto quanto os outros. Item eterno que ninguém vai fazer corrói a
confiança no checklist inteiro; fechar como decisão consciente é resultado legítimo. O que não pode
é seguir aberto por inércia, fingindo ser trabalho planejado.

**Comentário = a rodada, append-only.** Nunca reeditado. Traz o escopo (quais PRs, qual janela), o
volume, **o que ficou fora e por quê** — essa seção é o que impede a próxima rodada de re-litigar —
e a ordem sugerida de ataque.

Registre também **o que foi saudável**: um PR com 30 pontos cujos graves fecharam antes do merge
mostra que o processo funciona, e evita que a issue leia como acusação.

```bash
gh issue create --title "chore: Auditoria contínua de follow-ups de review" --body-file <body.md>
gh issue comment <N> --body-file <rodada.md>
```

**Sempre `--body-file`, nunca heredoc** — o conteúdo tem backticks e pipes de tabela que o shell
corrompe.

**Link nos dois sentidos:** a issue referencia os itens do backlog, e o backlog referencia a issue no
topo, onde quem entra por ali tropece nela. Sem isso, quem olha só um dos dois nunca vê o outro — e
é exatamente essa a falha que a auditoria existe pra corrigir.

Se o projeto usa o vault, os achados sem dono também podem virar item (`roadmap add`). Nesse caso a
issue é o **espelho público** e o vault segue sendo onde a prioridade se decide.

**O `pr-close` escreve aqui também.** Ele publica o follow-up de um PR no momento do merge, no mesmo
formato de item. Então antes de adicionar qualquer coisa, **leia o body atual** e trate o que já
está lá como rastreado — reabrir um item que o fechamento já registrou é a forma mais rápida de o
time parar de confiar no checklist.

## Armadilhas

**Bot que "revisou" sem revisar.** Ferramenta em plano gratuito costuma gerar só um walkthrough do
diff, sem achado por linha — às vezes nem isso, quando bate rate limit. Confirme que houve achado
real antes de contar o PR como revisado por máquina; muda a leitura do risco do lote inteiro.

**Tracker invisível.** Backlog em diretório ignorado pelo git (`git check-ignore -v` confirma)
significa "visível só pra uma pessoa". Não invalida o tracker — é justamente o que a issue conserta —
mas diga explicitamente, senão o usuário conta como resolvido algo que segue invisível.

**Urgência inflada.** Furo real que nenhum caminho alcança hoje é `armado`, não `ativo`. Diga qual
mudança futura o arma.

**Ordenar pelo histórico.** Quantas vezes o item foi adiado não diz nada sobre o dano — e como a
janela é móvel, um PR antigo simplesmente sai do escopo e o histórico deixa de ser observável.

**Confiar no corpo do PR.** Descrição envelhece: cita migration que virou outra, declara limitação
já resolvida, promete runbook que nunca existiu. O código é a fonte.

## Limites

GitHub via `gh` — em GitLab ou Bitbucket o esqueleto de fases vale, os comandos precisam de tradução.
"Tracker" é deliberadamente vago: o que importa saber é **onde a prioridade se decide**, não qual
ferramenta hospeda.

**Sem script aqui, de propósito.** A montagem da lista muda de filtro conforme a pergunta, e um
script fixo seria contornado na primeira variação — diferente do `roadmap`, onde o formato é fixo e
o cálculo é sempre o mesmo.
