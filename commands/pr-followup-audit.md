---
description: Auditoria contínua de follow-ups de code review — varre PRs mergeados num período, extrai o que os revisores levantaram, verifica ponto por ponto se ainda vive no código atual, cruza com o backlog/tracker do projeto e alimenta uma issue perene (body = checklist do que está aberto, um comentário por rodada). Use sempre que o usuário quiser saber "que dívida técnica sobrou dos meus PRs", "o que ficou pendente das reviews", "quais follow-ups nunca foram feitos", "mapear dívida antes de prosseguir", ou pedir auditoria/varredura de PRs de um período ("últimas N semanas", "desde o release X"). Use também quando pedirem para registrar follow-ups de review num lugar rastreável, ou quando desconfiarem que o backlog está desalinhado do que já foi mergeado. Não confundir com relatório de produtividade de PRs (volume, velocity — isso é /pr-report) nem com review de um diff específico (/sdd-review).
model: claude-sonnet-5
argument-hint: [--janela <3 semanas | desde <marco>>] [--autor @me] [--revisor <login>]
allowed-tools: Read, Write, Glob, Grep, Agent, AskUserQuestion, Bash(gh *), Bash(git log*), Bash(git diff*), Bash(git check-ignore *), Bash(git worktree list*), Bash(ls *), Bash(find *), Bash(mkdir *), Bash(structure-cache *), Bash(structure-cache)
---

# Auditoria de follow-ups de review

Review gera duas classes de resultado: o que o autor corrigiu antes do merge, e o que
todo mundo concordou em deixar pra depois. A segunda classe é a que evapora — vira
comentário enterrado num PR fechado, sem dono e sem prazo. Este command existe pra
recuperá-la e transformá-la em algo que o time consiga ver e priorizar.

A regra que governa tudo aqui: **nada é reportado sem evidência no código atual.**
"O autor prometeu no PR" não é estado; `arquivo:linha` é.

## Guardrails (não-negociáveis)

- **Subagentes são READ-ONLY.** Não editam arquivo, não commitam, não abrem issue.
- **Criar ou comentar issue exige OK explícito.** Mostre o conteúdo que vai subir e pergunte antes (`AskUserQuestion`). Auditoria é leitura; publicar é ação outward-facing.
- **Nunca comente nos PRs auditados.** Este command lê review; não responde, não resolve thread.
- **Sem evidência, sem afirmação.** "Resolvido" só com `arquivo:linha` conferido. Caso contrário: *"não verificável — <motivo>"*.
- **Nunca commita nem pusha.**

## Parâmetros

Resolva antes de começar — perguntando só o que não conseguir inferir:

- **Janela**: período (default: 3 semanas) ou marco ("desde o release X").
- **Autor**: default `@me`. Pode ser o time inteiro.
- **Revisor de interesse**: se o usuário nomeou alguém ("revisados pelo `<revisor>`"), priorize os PRs revisados por essa pessoa — mas não descarte os outros, apenas ordene.
- **Destino do registro**: issue perene do tracker (default). Se o projeto usa o vault de roadmap do toolkit (`thoughts/roadmap/`), ofereça registrar lá também — ver *Relação com outros commands*. Sem tracker acessível, entregue só o relatório.

## Fase 1 — montar a lista

```bash
gh pr list --author @me --state all --limit 60 \
  --json number,title,state,createdAt,mergedAt,updatedAt,reviews \
  --jq '.[] | {n:.number, t:.title, s:.state, merged:.mergedAt,
               reviewers:[.reviews[].author.login]|unique}'
```

Inclua na varredura:

- PRs **mergeados** na janela → fonte de dívida.
- PRs **abertos com review** → não são dívida (ver Fase 3), mas precisam aparecer no relatório porque muitas vezes é onde está o trabalho mais urgente.
- PRs **fechados sem merge** → ignore, salvo se o usuário pedir (WIP abandonado às vezes esconde decisão que ainda vale).

Ancore a janela em `mergedAt`, não em `createdAt` — o review acontece perto do merge.

Antes do fan-out, levante o **inventário do tracker**: itens do backlog, issues abertas e, se
o projeto tiver, os documentos de plano/spec. Os subagentes vão precisar cruzar contra isso, e
é mais barato descobrir a forma do tracker uma vez do que N vezes.

## Fase 2 — um subagente por grupo de PRs

Agrupe 2 a 3 PRs por subagente, **por tema** (mesmo subsistema no mesmo grupo) — isso deixa o
agente reaproveitar contexto de código entre PRs do grupo. Dispare todos **na mesma mensagem**
para rodarem em paralelo (paralelismo exige emitir todas as chamadas `Agent` num único turno).

Não faça isso sequencialmente na thread principal: cada PR consome muito contexto em
comentários e leitura de código, e o valor está na síntese cruzada no fim.

Use `subagent_type: general-purpose` com `model: opus` — é trabalho de julgamento, e o
contexto de cada grupo é focado.

Template do prompt (adapte repo, PRs e o contexto específico):

> Você é auditor de dívida técnica no repo `<CAMINHO>` (branch `<BASE>`, `<stack/contexto em 1 linha>`).
> READ-ONLY: não edite arquivos, não commite, não abra issues.
>
> Audite os PRs **#A**, **#B** (um por um, nessa ordem).
>
> Para cada PR:
> **Você coleta e verifica; você NÃO decide o que vira item.** A triagem é centralizada na thread
> principal (pra não divergir entre agentes). Seu trabalho é devolver os pontos **com os campos
> que permitem triar** — sobretudo `Fonte`, `Classe` e as datas. Ponto sem esses campos é
> inútil pra quem decide.
>
> Colete **nesta ordem de densidade** — a primeira fonte é onde o follow-up realmente mora:
>
> 1. **Reviews com body** (fonte principal):
>    `gh api repos/<OWNER>/<REPO>/pulls/<N>/reviews --jq '.[] | select(.body != "") | {user:.user.login, state, body, submitted_at}'`
>    Review **`APPROVED` com `body` não-vazio é a assinatura mais comum do follow-up**: o revisor
>    destravou o merge justamente porque decidiu não bloquear por aquilo, às vezes oferecendo
>    corrigir no mesmo PR ("opcional", "se quiser já ajusta aqui"). **Aprovado com texto não quer
>    dizer resolvido — quer dizer o oposto.** Já `CHANGES_REQUESTED` com body normalmente foi
>    resolvido antes do merge; confira no diff antes de tratar como pendência.
> 2. **Comentários inline** (segunda fonte):
>    `gh api repos/<OWNER>/<REPO>/pulls/<N>/comments --paginate --jq '.[] | {user:.user.login, path, line, body}'`
> 3. **Metadados e conversa geral** (fonte mais fraca — frequentemente vazia; nunca a única base):
>    `gh pr view <N> --json title,body,state,mergedAt,headRefName,files,commits`
>    `gh pr view <N> --comments`
>    Guarde a data do **último commit** (`.commits[-1].committedDate`): a thread principal precisa
>    dela pra distinguir follow-up de review que o autor ainda não respondeu.
> 4. Extraia **todos** os pontos levantados (humanos e bots) e classifique cada um:
>    `RESOLVIDO-NO-PR` / `FOLLOW-UP-PROMETIDO` / `OPCIONAL-NÃO-FEITO` (o revisor ofereceu corrigir
>    no mesmo PR e mergeou sem) / `NÃO-ENDEREÇADO`.
> 5. Para cada ponto não resolvido no PR, verifique no **código atual** se foi resolvido depois.
>    Grep/Read nos arquivos relevantes, evidência `arquivo:linha`. Seja rigoroso: sem ver o
>    código, não afirme "resolvido". Se não achou, escreva "não verificável — <motivo>".
> 6. Cruze com o tracker: `<como listar o backlog>` e
>    `gh issue list --state all --limit 100 --json number,title,state`.
>    Diga se cada follow-up está **rastreado** (qual item) ou **ÓRFÃO**.
>
> Para pergunta de dependência/impacto ("quem importa isso", "o que quebra"), rode
> `structure-cache query --importers/--defs/--hotspots` ANTES de grepar; Grep/Read só no fallback.
>
> Retorne (o texto final é o resultado — ninguém vê seu raciocínio) em markdown:
>
> ## PR #N — título
> **Status:** merged em <data> / open
> **Último commit:** <data>
> **Reviews:** <login> APPROVED (<data>, body: sim/não) · <login> CHANGES_REQUESTED (<data>, body: sim/não)
> **Pontos do review:** <total>
> ### Pendências (dívida viva)
> | # | Ponto | Quem | Fonte | Classe | Opcional? | Estado no código atual (evidência) | Rastreado? | Risco | Ativo? |
> ### Já resolvido depois do merge
> - <ponto> → resolvido em <arquivo:linha> ou PR #<x>
>
> **Fonte**: `review-APPROVED` / `review-CHANGES_REQ` / `inline` / `conversa`.
> **Opcional?**: sim, se o revisor ofereceu corrigir no próprio PR sem bloquear; senão não.
> **Risco** — classifique pela **natureza**, não por sensação de gravidade. Use exatamente um:
> `SEGURANCA` (auth/authz, exposição de dado, injeção, secret) · `DADO` (dado errado gravado ou
> exibido, cálculo financeiro, perda irreversível) · `CONTRATO` (API pública, schema, evento,
> retorno de que outro consumidor depende) · `DISPONIBILIDADE` (CI travado, deploy, timeout,
> query que derruba) · `ROBUSTEZ` (erro engolido, sem log, retry ausente) · `COBERTURA` (falta
> teste) · `HIGIENE` (duplicação, nome, nit).
>
> **Ativo?** — `ativo` se algum caminho de código alcança o problema hoje; `armado` se só
> acontece quando algo futuro executar (**diga o quê**: qual plano, flag ou rota ainda não
> existente arma o furo). Não inflacione: furo inalcançável hoje é armado, não ativo.
>
> Não atribua prioridade nem "ALTA/MÉDIA/BAIXA" — a ordem é derivada na thread principal a
> partir de `Risco` × `Ativo?`. Você reporta o fato; quem ordena é quem tem a visão do lote.

Dê a cada subagente o contexto que só você tem: PRs derivados que podem já ter fechado o
ponto, uma issue que serve de checklist, um diagnóstico anterior a confirmar. Isso muda a
qualidade do retorno mais que qualquer ajuste de formato.

## Fase 3 — triagem antes de registrar

Aqui é onde a auditoria fica útil ou vira ruído. A triagem é **centralizada aqui**, não delegada
aos subagentes — eles auditam PRs diferentes e triariam com critérios divergentes.

Os dados vêm das colunas que o retorno da Fase 2 obriga: `Fonte`, `Classe`, `Opcional?`, mais o
**Último commit** e as datas dos reviews no cabeçalho. Se um subagente devolveu pontos sem esses
campos, **não triague por adivinhação** — reprocesse aquele grupo pedindo o formato completo.

### Três coisas que parecem dívida e não são

**Review pendente de resposta.** Se o review mais recente é `CHANGES_REQUESTED` (coluna `Fonte` =
`review-CHANGES_REQ`) com `submitted_at` **posterior** ao **Último commit** do cabeçalho, o autor
simplesmente ainda não respondeu. Isso pertence ao PR, não a um backlog — registrar ali contorna
o revisor. Compare as duas datas explicitamente; é fácil confundir com abandono.

**Follow-up que já tem PR aberto.** O problema é merge, não registro. Vai pro relatório como
contexto, não pro checklist — senão o checklist enche de item que já tem dono e caminho.

**Decisão deliberada de adiar.** "Não adicione o método agora, o contrato vai mudar" é
engenharia, não dívida. Registre como decisão se houver onde; não cobre como pendência.

### E uma que é dívida, mas não do jeito que parece

**Opcional que o revisor ofereceu e ninguém fez.** Aprovação com "se quiser já corrige nesse PR"
e o PR mergeou sem a correção — no retorno, `Classe = OPCIONAL-NÃO-FEITO` e `Opcional? = sim`.

Aqui há uma pegadinha que inverte a intuição. O reflexo é rebaixar o item *porque* o revisor
liberou o merge — e é exatamente assim que se constrói o loop que mata backlog: item nasce baixo
porque foi adiado, nunca é pego porque está baixo.

**Adiado uma vez já é dívida confirmada.** O revisor ofereceu a janela mais barata que existia —
corrigir dentro do PR, código aberto, contexto quente — e ela foi recusada por decisão explícita,
não por esquecimento. Corrigir agora custa PR novo, review novo, contexto frio. Então o item
**não entra como "talvez"**: entra na fila, e a posição vem da **natureza do risco** (ver ordem
de urgência na Fase 5), nunca do fato de ter sido adiado.

Mantenha **a marca de que o revisor não bloqueava** — sem ela o item lê como pedido ignorado do
revisor, e uma auditoria útil passa a soar como acusação. A marca explica a origem; ela não
rebaixa a prioridade.

Se o PR mergeou **com** a correção, não é dívida — confirme no diff antes de descartar.

### Duas coisas que não parecem dívida e são

**Fix aceito que nunca executa.** Um `if (campo > 0)` aprovado no review onde o campo nunca é
populado naquele caminho. Passa em review, passa em teste, e a tela segue errada. Sempre que
um fix depender de um campo, confirme que quem serve aquela rota realmente o preenche.

**Regressão de escopo entre PRs.** Um PR estabelece uma invariante, um PR posterior encolhe o
alcance dela, e ninguém liga os dois porque foram reviews diferentes. Compare PRs que tocaram
os mesmos arquivos de configuração/seed dentro da janela.

Verifique também **código sem consumidor**: tabela, coluna ou módulo que mergeou e nunca foi
usado. Um grep pelo símbolo respondendo só com a própria definição e artefatos de migration é
dívida — e frequentemente é a metade 1 de um plano cuja metade 2 nunca abriu.

## Fase 4 — o tracker está mentindo?

Compare o estado de cada item do backlog com o que os PRs efetivamente entregaram. Os
desalinhamentos são achado de primeira classe, porque um backlog que mente causa retrabalho:

- Item aberto descrevendo problema **já corrigido** por um PR mergeado.
- Item dizendo "nunca implementado" quando o PR mergeou.
- Item bloqueado por dependência **que já caiu** (e segue despriorizado por inércia).
- Item pedindo decisão que outro PR já tomou.
- Plano/spec arquivado como concluído com tarefas em aberto — pior variante: o documento
  arquivado descreve o desenho que o review **derrubou**, e vai orientar errado quem reler.

## Fase 5 — alimentar a issue perene

Uma issue por repositório, reaproveitada a cada rodada. Se já existir, adicione comentário e
atualize o body; se não, crie. **Sempre sob confirmação** — mostre o que vai subir antes.

**Body = só o que está aberto.** É de lá que sai o contador de progresso do checklist
(comentário não agrega em nada), e é o único sinal agregado de "quanto falta". Quando um bloco
fecha inteiro, sai do body e sobrevive no comentário da rodada. Body que só cresce tem
contador travado em "45 of 120" e para de significar algo.

Estrutura do body:

- **Nota de precedência**: onde a prioridade se decide (o backlog, normalmente) e que a issue
  é o espelho. Duas fontes sem hierarquia divergem — foi assim que o backlog começou a mentir.
- **Critério do que entra**: ponto **sem dono**, ou bloqueante independente de rastreio.
- **Checklist agrupado**: bloqueantes primeiro, depois por eixo (segurança/auth, contrato,
  cobertura, infra/DX, higiene de tracker). Cada item: uma frase de consequência,
  `arquivo:linha`, o PR de origem, e o `Risco` + `ativo|armado` que definem a posição na fila.
- **Nits agregados** num único checkbox por bloco, com o detalhe no comentário.

### Ordem de urgência (pela natureza do risco)

Tudo que chega aqui **já foi adiado ao menos uma vez** — ou não seria dívida. Então "foi adiado"
não ordena nada: é o pré-requisito de entrada. **O que ordena é a natureza do risco**, na ordem
abaixo, e ela é a ordem de ataque sugerida na rodada.

| Ordem | `Risco` | Por que vem antes | Ativo | Armado |
|---|---|---|---|---|
| 1 | `SEGURANCA` | explorável por terceiro; não dá pra "descobrir depois" | urgente | pré-requisito de `<o que arma>` |
| 2 | `DADO` | dado errado é silencioso e **irreversível** — corrompe histórico enquanto ninguém olha | urgente | pré-requisito |
| 3 | `CONTRATO` | quebra consumidor externo; o custo cresce com cada novo integrador | urgente | pré-requisito |
| 4 | `DISPONIBILIDADE` | dói, mas **é visível na hora** — por isso vem depois de `DADO` | urgente | pré-requisito |
| 5 | `ROBUSTEZ` | transforma falha silenciosa em falha diagnosticável | fila normal | fila normal |
| 6 | `COBERTURA` | é rede de proteção, não correção | fila normal | fila normal |
| 7 | `HIGIENE` | agregue num checkbox só; nunca disputa espaço com o resto | fila normal | fila normal |

Dois critérios de desempate, nessa ordem:

- **`ativo` antes de `armado`.** Furo alcançável hoje vence furo que só dispara quando um plano futuro executar. Item `armado` **não é urgente — é pré-requisito**: registre como "pré-requisito de `<plano/rota que o arma>`", que é acionável, em vez de "urgente e ignorado", que é ruído.
- **Irreversível antes de reversível.** Dado corrompido você não desfaz; indisponibilidade você percebe e corrige.

Formato do item no checklist:

```markdown
- [ ] Cupom aplicado duas vezes em pedido reenviado — grava total errado, sem trilha de correção.
      `DADO` · ativo · `src/checkout/cart.ts:88` · PR #142 · rev. marcou opcional no PR
```

A marca de origem (`rev. marcou opcional no PR`) fica no item para explicar **de onde veio**, sem
alterar a posição na fila.

### Quando um item não sai

Se um item continua aberto rodada após rodada, o problema não é prioridade — é que ele está mal
descrito, mal dimensionado ou não tem dono possível. **Proponha ao usuário decidir**: fazer,
redimensionar (quebrar em algo executável), ou **fechar explicitamente como risco aceito**.

Esse último caminho importa tanto quanto os outros: item eternamente aberto que ninguém vai fazer
corrói a confiança em todo o checklist. Fechar como decisão consciente é resultado legítimo — o
que não pode é seguir aberto por inércia, fingindo ser trabalho planejado.

**Comentário = a rodada, append-only.** Nunca reeditado; é o histórico. Inclua: escopo (quais
PRs, qual janela), volume, **o que ficou fora e por quê** (Fase 3 — essa seção é o que impede
a próxima rodada de re-litigar), o estado do CI se for relevante, e a ordem sugerida de ataque.

Registre também **o que foi saudável**. Um PR com 30 pontos cujos graves fecharam antes do
merge é informação — mostra que o processo funciona e evita que a issue leia como acusação.

```bash
gh issue create --title "chore: Auditoria contínua de follow-ups de review" --body-file <body.md>
gh issue comment <N> --body-file <rodada.md>
```

Use **sempre `--body-file`, nunca heredoc**: o conteúdo tem backticks, crases e pipes de
tabela que o shell corrompe.

Fixe a issue — é o endereço estável do quadro. `gh issue pin` não existe em toda versão do
`gh`; o fallback é a mutation `pinIssue` via `gh api graphql` com o `node_id`. Se o ambiente
bloquear, entregue o comando pro usuário rodar em vez de insistir.

**Link nos dois sentidos.** A issue referencia os itens do backlog; o backlog referencia a
issue, no topo, onde quem entra por ali tropece nela. Sem isso, quem só olha um dos dois nunca
vê o outro — e essa é a falha que a auditoria inteira existe pra corrigir.

## Armadilhas

**Bot que "revisou" sem revisar.** Ferramentas de review em plano gratuito costumam gerar só
um walkthrough do diff, sem nenhum achado por linha — e às vezes nem isso, quando batem rate
limit e o review não é re-disparado. Verifique se há achado real antes de contar o PR como
revisado por máquina; a diferença muda a leitura do risco de todo o lote.

**Tracker invisível.** Se o backlog vive em diretório ignorado pelo version control
(`git check-ignore -v <caminho>` confirma), então "rastreado" ali significa "visível só pra
uma pessoa". Isso não invalida o tracker, mas é exatamente o que a issue conserta — e vale
dizer explicitamente, senão o usuário conta como resolvido algo que segue invisível.

**Urgência inflada.** Um furo real que nenhum caminho de código alcança hoje é `armado`, não
`ativo`. Diga qual mudança futura o arma — normalmente um plano já escrito. Isso transforma o
item de "urgente e ignorado" em "pré-requisito de X", que é acionável.

**Ordenar pelo histórico em vez da natureza.** Quantas vezes o item foi adiado não diz nada sobre
o dano que ele causa — e, como a janela da auditoria é móvel, um PR antigo simplesmente sai do
escopo e o histórico deixa de ser observável. Ordene por `Risco` × `ativo|armado`. "Foi adiado" é
o critério de **entrada** na dívida, não de posição na fila.

**Confiar no corpo do PR.** Descrição de PR envelhece: cita migration que virou outra, declara
limitação que foi resolvida, promete runbook que nunca existiu. O código é a fonte.

## Limites de escopo

- **GitHub via `gh`.** Em GitLab/Bitbucket o esqueleto de fases continua valendo, mas os
  comandos precisam de tradução.
- **"Tracker" é deliberadamente vago** (issues do GitHub, Jira, Linear, backlog em markdown,
  vault de roadmap): o que este command precisa saber é só **onde a prioridade se decide**, não
  qual ferramenta hospeda.
- **Sem script empacotado.** A montagem da lista de PRs muda de `jq` conforme o filtro; um
  script fixo seria contornado na primeira variação.

## Relação com outros commands

- **`/sdd-close`** colhe follow-ups de **um** PR no momento do merge (fluxo normal, previne
  acumulação futura). Este command varre **N PRs já mergeados** retroativamente — recupera o
  passivo que existe antes de o `/sdd-close` estar em uso, ou o que escapou. São
  complementares: um é profilaxia, o outro é resgate.
- **`/pr-report`** mede volume e velocity. Este mede **dívida**. Não se sobrepõem.
- **`/sdd-review`** revisa um diff/PR específico. Este audita o que reviews passados deixaram.
- **`/roadmap`**: se o projeto usa o vault (`thoughts/roadmap/`), os achados sem dono podem
  virar itens em `backlog/` além da issue — mesmo contrato do reference `roadmap-item.md`. Nesse
  caso a **issue é o espelho público** e o vault continua sendo onde a prioridade se decide.
- **`/sdd-learning`** extrai *regra de comportamento* dos comentários de review (o que não
  repetir). Este extrai *trabalho pendente*. Mesma fonte, saídas diferentes.
