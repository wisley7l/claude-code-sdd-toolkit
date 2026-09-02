---
name: pr-draft
description: Abre o pull request inicial em draft de uma mudança planejada — branch, commit vazio, título e corpo derivados da spec. Com `stack`, abre de uma vez a cadeia de PRs que o plano previu, empilhada via `gh stack`, todos em draft. Com `restack`, rebaseia as camadas de cima quando a base avança, com worktree ou sem. Com `sync`, reescreve o corpo depois da implementação pra refletir o que foi feito de fato. Nunca tira o PR do draft.
disable-model-invocation: true
argument-hint: '[nome-da-branch] | stack | restack | sync'
allowed-tools: Read Write Grep Glob Agent Skill AskUserQuestion Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git worktree list*) Bash(git branch*) Bash(git fetch*) Bash(git switch*) Bash(git checkout*) Bash(git commit --allow-empty*) Bash(git push*) Bash(git remote show origin*) Bash(git rev-parse*) Bash(git ls-remote*) Bash(git rebase*) Bash(git -C * status*) Bash(git -C * log*) Bash(git -C * rev-parse*) Bash(git -C * rebase*) Bash(gh *) Bash(ls *) Bash(mktemp) Bash(command -v *) Bash(roadmap:*) Bash(roadmap)
---

# pr-draft

Cuida do PR nos momentos em que ele importa antes do review:

- **sem argumento** — o **kickoff**: abre um PR em draft antes da primeira linha de código.
- **`stack`** — o kickoff de **vários PRs de uma vez**: a cadeia que o plano previu nasce empilhada,
  cada camada baseada na anterior, todas em draft.
- **`restack`** — a base avançou: rebaseia as camadas de cima, com worktree ou sem.
- **`sync`** — depois da implementação: reescreve o corpo pra refletir o que foi feito de fato,
  como prévia pra quem vai revisar.

**O PR nasce e permanece em draft**, nos quatro modos. `gh pr ready` é o seu clique.

## O corpo é público — vale em todos os modos

Quem lê o PR não tem acesso ao seu ambiente. **Nunca** entram no corpo:

- caminhos de `thoughts/` — `spec.md`, `plan.md`, `tasks.md`, `notes.md` são locais e não
  versionados; pro leitor são ruído que parece referência;
- link ou id de sessão do Claude;
- número de item de roadmap ou qualquer numeração de planejamento interno.

Esses arquivos são **insumo pra escrever o corpo, nunca conteúdo dele**. Sobrevive só o que o leitor
consegue abrir: o link da issue. Na dúvida sobre um item, deixe de fora.

A tentação é maior no `sync`, porque você acabou de ler os artefatos todos.

## Onde estão os artefatos

Em `<root>/thoughts/changes/<NNN>-<slug>/`, onde **`root` é o repositório principal**
(`git worktree list | head -1`). `thoughts/` é gitignored, então dentro de uma worktree o diretório
local está vazio — e no `sync` você quase sempre está dentro de uma.

---

# Kickoff (sem argumento)

Abre o PR antes do código existir, pra sinalizar ao time que o trabalho começou e o que ele vai
entregar. Você não implementa nada aqui: o commit é vazio, e seu único propósito é dar ao PR um
ponto de partida.

## Antes de tocar em qualquer coisa

Resolva o root e a branch default (`git remote show origin`, com fallback pra `main`, `master` ou
`dev` local), e **cheque o estado**:

- **Working tree sujo é parada.** Mudanças não commitadas viajariam junto no checkout. Diga o que
  está pendente e pergunte se é pra commitar ou guardar antes.
- **Fora da branch default** — o kickoff parte dela. Volte (só se limpo) ou pergunte.

Depois `git fetch` da default: o PR nasce da versão atual, não da de ontem.

## Título, branch e corpo

- **`spec.md`** — o comportamento e para quem. Fonte do "o quê" e do "por quê".
- **`plan.md`** — a abordagem e quantos PRs foram previstos.
- **`tasks.md`** — se o plano previu mais de um PR, **qual bloco este PR fecha**. Com vários blocos
  e nenhuma indicação, pergunte antes de abrir: PR errado é caro de desfazer depois de publicado.
  Se os blocos formam cadeia (`> Depende do PR 1`), ofereça o modo **`stack`** antes de abrir só o
  primeiro — abrir a cadeia de uma vez é mais barato agora que enxertar um PR no meio depois.

Sem artefato nenhum, sintetize da conversa e registre no corpo que não houve planejamento formal.

**Branch:** `<tipo>/<slug>` — `feat/` para comportamento novo, `fix/` para correção, `refactor/`
para mudança sem efeito observável, `chore/` para infra e configuração. O slug vem da pasta da
mudança. Confirme que a branch não existe local nem remotamente; se existir, pergunte antes de
reusar.

**Título:** `<tipo>: <descrição curta>`. O commit vazio usa o mesmo texto.

```markdown
## Contexto

<o que vai ser implementado e pra quem — 2 a 3 linhas, da spec>

## Plano

- Planejado via spec + plano técnico
- Tarefas: <N>, em <M> PR(s)
- Issue: <link, quando houver>

## Status

🚧 **Draft** — implementação ainda não iniciada.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Escreva num arquivo temporário e use `--body-file`; corpo inline quebra com aspas e quebras de linha.

## Abrir

```bash
git checkout -b "<branch>" "origin/$DEFAULT"
git commit --allow-empty -m "<título>"
git push -u origin "<branch>"
gh pr create --draft --base "$DEFAULT" --head "<branch>" --title "<título>" --body-file "$BODY"
```

Guarde a URL e o número.

**Promova o item do roadmap**, se houver um pra este slice — o número do PR é o que faz o item sair
do backlog:

```bash
roadmap list --json          # ache o item pelo change: desta mudança
roadmap move <NNN> --to em-progresso --pr <N>
```

Sem item correspondente, ou sem o comando instalado: siga em frente, dizendo numa linha. O roadmap
reflete o trabalho, não autoriza o trabalho.

**Se `push` ou `gh` forem negados**, ou o `gh` não estiver autenticado: não contorne e não desista.
Entregue os comandos exatos, já com os valores reais preenchidos, **um por vez** quando houver
dependência, e espere a confirmação de cada um antes do próximo. O resto do fluxo é local.

## Isolar e devolver

`git switch` de volta pra default — o repositório principal nunca fica preso na branch da feature.

A worktree é o passo seguinte e é **do usuário**: nenhuma peça deste toolkit invoca outra. Feche
pedindo, com o nome da branch já preenchido:

> PR draft aberto. Agora rode **`/tk7:worktree <branch>`** — ela monta a worktree sobre a branch
> recém-publicada, aplica as permissões e centraliza a memória.

```
PR draft: <url>
Branch:   <branch>  (base: <default>)
Root:     de volta em <default>

  /tk7:worktree <branch>     # e, lá dentro, `implement` executa as tarefas
```

---

# Stack (`stack`)

Quando o plano previu **mais de um PR e eles dependem um do outro**, abrir um por vez esconde o
desenho: o time vê um PR isolado, e os outros aparecem semanas depois sem contexto. Este modo abre a
cadeia inteira em draft, empilhada — cada camada tem como base a anterior, e o GitHub monta o mapa
da stack.

## A ferramenta, e o que ela não faz

Empilhar é da extensão oficial `gh stack` (stacked PRs do GitHub, public preview desde 30-07-2026):

```bash
gh extension list | grep -q gh-stack || echo "falta: gh extension install github/gh-stack"
```

Sem a extensão, **não improvise a stack na mão**: `--base` a cada `gh pr create` cria a cadeia de
bases, mas não cria o objeto de stack no GitHub, e o rebase em cascata fica sem dono. Diga o comando
de instalação e ofereça o kickoff um-a-um enquanto isso.

Três fatos que decidem o passo a passo:

- **`gh stack submit` sem flag abre uma TUI de tela única** — você não a opera. `--auto` faz o
  trabalho sem editor **e cria os PRs em draft**. `--open` tira do draft, e por isso não se usa
  aqui: sair do draft é do `pr-ready`.
- **`--auto` gera título e corpo automáticos**, derivados do commit. Servem de placeholder, não de
  entrega — o corpo curado entra depois, com `gh pr edit`.
- **Cada camada precisa de commit próprio.** Duas branches no mesmo commit não têm diff entre si, e
  o GitHub recusa o PR. Daí o commit vazio de sempre, um por camada.

## O que empilha, e o que não

Leia os blocos de PR do `tasks.md` com a linha de dependência de cada um (`> Depende do PR 1`,
`> Não depende de nada`).

**Só a cadeia dependente é empilhada.** Bloco independente não entra: ele nasce como PR irmão da
branch default. Stack linear entre coisas independentes inventa uma ordem de merge que não existe —
quem revisa passa a esperar o PR de baixo sem motivo, e o de cima fica bloqueado por nada. Com dois
grupos independentes, são duas stacks, ou uma stack mais um kickoff simples.

Mostre o agrupamento que você leu — camada por camada, com o que cada uma fecha — e **confirme antes
de criar a primeira branch**. PR publicado é caro de desfazer, e stack errada se desfaz em N PRs.

## Abrir a cadeia

Do repositório principal, na branch default e com working tree limpo — as mesmas paradas do
kickoff. Nomes de branch e títulos pela mesma regra (`<tipo>/<slug>`, `<tipo>: <descrição>`), com o
slug ganhando o sufixo do slice quando a mudança é uma só.

```bash
git switch "$DEFAULT" && git fetch origin "$DEFAULT"
git checkout -b "<b1>" "origin/$DEFAULT" && git commit --allow-empty -m "<t1>"
git checkout -b "<b2>"                   && git commit --allow-empty -m "<t2>"
git checkout -b "<b3>"                   && git commit --allow-empty -m "<t3>"
gh stack init "<b1>" "<b2>" "<b3>"   # adota as branches existentes, de baixo pra cima
gh stack submit --auto               # push de todas, PRs em draft, stack criada no GitHub
git switch "$DEFAULT"                # o principal nunca fica preso numa camada
```

`gh stack init` adota branch que já existe e cria a que falta, então a ordem acima é a que dá
controle sobre commit e mensagem. Confirme que nenhuma das branches existe antes — local ou remota —
e pergunte se existir.

**Se `push` ou `gh` forem negados**, ou o `gh` não estiver autenticado: entregue os comandos exatos
com os valores reais, na ordem, e espere a confirmação de cada um. Não contorne e não desista.

## O corpo de cada PR

`gh stack view --json` casa branch com número de PR. Para cada um, o mesmo template do kickoff, com
a linha do plano trocada pela posição na cadeia:

```markdown
## Plano

- Planejado via spec + plano técnico
- Camada <i> de <N> desta stack · base: `<branch de baixo>`
- Issue: <link, quando houver>
```

```bash
gh pr edit <N> --title "<título>" --body-file "$BODY"
```

Vale integralmente a regra do corpo público: nome de branch e número de PR são públicos, `tasks.md`
e número de item de roadmap não entram.

## O roadmap

**Promova só a camada de baixo** — `roadmap move <NNN> --to em-progresso --pr <N>`. As de cima têm
PR aberto e nenhum trabalho começado; promover todas apaga a informação de onde a fila realmente
está. Cada uma sobe quando chegar a vez, com o número que já existe.

## A entrega

Worktree é passo do usuário, e a stack não muda isso — **nenhuma peça deste toolkit invoca outra**.
Aqui, porém, o comando vem com um aviso: **PR empilhado é PR dependente.** Abrir os N terminais de
uma vez deixa as sessões de cima escrevendo sobre uma base que ainda vai mudar, e cada avanço da
base cobra um `restack`. O caminho barato é subir a cadeia — a worktree da camada de baixo agora, a
seguinte quando a de baixo estiver verde.

```
Stack aberta — <N> PRs em draft, base: <default>

  1º  #<n1>  <b1>  ← <default>   <url>
  2º  #<n2>  <b2>  ← <b1>        <url>
  3º  #<n3>  <b3>  ← <b2>        <url>

Comece por baixo:

  /tk7:worktree <b1>        # e, lá dentro, `implement`

Quando a de baixo estiver entregue, a camada seguinte:

  /tk7:worktree <b2>
  /tk7:worktree <b3>

Base avançou antes disso? `pr-draft restack`.
```

---

# Restack (`restack`)

A camada de baixo ganhou commits, ou foi mergeada, e as de cima ficaram atrás. Sem rebase em
cascata o diff do PR de cima passa a mostrar código que não é dele, e o review vira arqueologia.

Rode do **repositório principal**. De dentro de uma worktree o `gh stack` não enxerga a stack: o
metadado vive em `$GIT_DIR/gh-stack`, e na worktree o `$GIT_DIR` é `.git/worktrees/<nome>/` —
a resposta é `current branch "<b>" is not part of a stack`, que parece stack perdida e não é.

`gh stack view --short` mostra quem precisa: `⚠ Needs rebase`.

## Dois caminhos, e a worktree decide qual

**Nenhuma camada de cima está em worktree** (`git worktree list`) → o caminho oficial:

```bash
gh stack sync            # fetch, cascade rebase, push atômico, estado dos PRs
gh stack sync --prune    # idem, apagando a branch local de PR já mergeado
```

**Alguma está em worktree** → `gh stack sync` e `gh stack rebase` falham, e falham cedo:

```
✗ could not start rebase of feat/two onto feat/one:
  fatal: 'feat/two' is already used by worktree at '.worktrees/feat-two'
```

Git não deixa duas árvores na mesma branch, e a extensão rebaseia por checkout. Aqui o cascade é
manual, **de baixo pra cima**, cada worktree rebaseando a própria branch:

```bash
git -C <wt-de-b2> status --porcelain    # sujo é parada: rebase come trabalho não commitado
git -C <wt-de-b2> rebase <b1>
git -C <wt-de-b3> rebase <b2>
```

A ordem não inverte. Rebasear a camada 3 antes da 2 a empilha sobre uma base que ainda vai mudar, e
o mesmo conflito aparece duas vezes.

**Conflito para tudo.** Mostre os arquivos e deixe a resolução onde ela pertence — a worktree é a
sessão de quem está trabalhando nela, e resolver conflito de fora, sem o contexto daquele trabalho,
é como se escolhe o lado errado em silêncio. `git rebase --abort` só se ele pedir.

## Publicar é dele

Rebase reescreve os commits da camada de cima, então o PR remoto só atualiza com
`git push --force-with-lease` — que o `tk7-guard` barra de propósito. Não contorne: entregue o
comando pronto, uma branch por linha, na mesma ordem de baixo pra cima.

```
Rebase local pronto:  <b2> ← <b1>,  <b3> ← <b2>

  git -C <wt-de-b2> push --force-with-lease
  git -C <wt-de-b3> push --force-with-lease
```

Ao terminar, `gh stack view --short` de novo, e diga o que sobrou de `⚠`.

---

# Sync (`sync`)

O corpo do kickoff ("draft, implementação não iniciada") fica obsoleto no minuto em que o código
existe. Este modo o troca por uma prévia pra quem vai revisar: o que mudou, por quê, como foi
resolvido e como foi verificado.

**Funciona de sessão limpa**, e esse é o uso recomendado — tudo é re-hidratado dos artefatos e do
diff, nada depende do histórico. Sessão longa carrega a narrativa da implementação, e narrativa
mente por omissão: o que foi difícil parece importante, o que foi trivial some.

**Numa stack, é um `sync` por camada**, rodado de dentro da worktree daquela camada. O diff que
importa é o da camada contra a base dela, e `gh pr diff <N>` já é exatamente isso — não some o
trabalho das camadas de baixo no corpo de quem está em cima.

## Reunir o estado real

Detecte o PR pela branch atual (`gh pr list --head $(git branch --show-current)`). Sem PR aberto,
pare e diga — o sync atualiza, não cria.

| Fonte | O que tirar dela |
|---|---|
| `spec.md` | o problema e o comportamento prometido → **por quê** e **o quê** |
| `plan.md` | decisões técnicas com justificativa → **como**; a seção `## Testes` → **verificação** |
| `notes.md` | o que foi feito de fato, **desvios do plano**, contagem de testes, dívida |
| `gh pr diff <N>` | o diff **completo**, não só os nomes — é dele que sai o "o quê" real |
| o código | quando o diff não se explica: o contrato que mudou, o contexto em volta |

Diff grande (mais de 10 arquivos): delegue a leitura a um subagente `Explore` que devolve a síntese
por arquivo. O corpo descreve **o código que existe**, não a intenção que o plano tinha.

## O corpo novo

```markdown
## O quê

<a mudança em si, 1 a 3 linhas diretas>

## Por quê

<o que estava errado ou faltando, e por que importa — 2 a 4 linhas>

## Como

<a estratégia em 2 a 3 linhas, seguida das decisões que valem explicação:>

- <decisão — e por quê>
- <desvio do plano — o que mudou e por quê>
- Comece o review por: `<arquivo central>` — <papel dele, e o ponto de atenção>

## Verificação

- Testes: <N novos, contagem de X para Y>
- Gates: <typecheck e lint>
- <verificação manual, quando houver: o que foi exercitado, e o que ficou de fora>
- Pra testar: <passos curtos, se aplicável>

---
Issue: <link, quando houver>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**Desvio do plano nunca é omitido.** É o que quem revisa mais precisa saber, e o que mais some por
parecer feio: o plano dizia X, o código faz Y, e a razão importa. Corpo que descreve o plano em vez
do código transforma o review numa caça ao erro.

**"Comece o review por"** aponta arquivo real do diff, com o motivo — trade-off, borda delicada,
área sensível. Genérico ("comece pelos testes") é ruído.

**Dívida aceita aparece.** O `plan.md` registra o que foi cortado e o que ficou como verificação
manual, com quem decidiu. Isso vai pro corpo em linguagem que quem revisa entende — sem apontar o
arquivo interno. Comportamento sem rede de proteção que não aparece no PR é o defeito que mais
escapa do review.

Toda afirmação rastreia a um artefato ou ao diff. Sem artefato nenhum (PR fora do fluxo), derive do
diff e dos commits, e diga no corpo que foi derivado assim.

## Aplicar

Mostre o corpo novo e o que ele substitui **antes** de aplicar, e espere o OK.

```bash
gh pr edit <N> --body-file "$BODY"
```

O título só muda se você pedir. Se estiver tudo pronto, feche dizendo isso — sair do draft é seu.

---

## Sempre

- **Draft sempre.** `gh stack submit --open` não se usa aqui.
- **Commit vazio, nunca código.**
- **`gh stack merge` nunca** — mergeia a cadeia inteira num comando, e mergear é do time. O
  `tk7-guard` barra; não procure outra forma.
- **Sem force-push, sem reescrever histórico, sem deletar branch.** O rebase do `restack` é local;
  o push que o publica é do usuário.
- **GitHub pelo `gh`**, nunca token na mão.
