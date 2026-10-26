---
name: triage
description: Destrincha o que chegou denso e pede decisão — review que o time fez no PR dele, ou relatório de um comando que rodou. Cada ponto vira sintoma, explicação em prosa, evidência verificada no código e a correção já escrita — o texto ou o diff, pronto pra colar. Sai como página local com o que procede, o que não, e em que ordem atacar. Use quando ele disser que recebeu review no PR, ou colar o resumo de um comando.
argument-hint: [número do PR | URL | nada, se ele colou o relatório | vazio = o PR da branch atual]
allowed-tools: Read Write Grep Glob Agent Skill AskUserQuestion Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git show*) Bash(git branch*) Bash(git worktree list*) Bash(gh *) Bash(ls *) Bash(mkdir *) Bash(cat *) Bash(base64 *) Bash(python3 *) Bash(structure-cache *) Bash(structure-cache)
---

# triage

Chegou algo denso que pede decisão dele. Aqui você **entende, verifica, escreve o conserto e
prioriza**.

**Escrever o conserto não é aplicá-lo.** Você não edita arquivo, não commita, não responde ao
revisor e não posta em lugar nenhum. A página mostra o texto pronto; colar é dele.

O problema que esta peça resolve não é falta de qualidade: é forma de entrega. Review e relatório
bons vêm escritos por quem **descobriu** o defeito — mecanismo primeiro, sintoma na terceira
cláusula, `arquivo:linha` no meio da frase, quarenta palavras por período. Quem vai decidir precisa
do contrário. Traduzir isso é o trabalho.

## Duas entradas, e elas mudam só onde se verifica

| Entrada | Como chega | Onde o fato se confirma |
|---|---|---|
| **Review no PR dele** | número, URL, ou o PR da branch atual | no **head do PR** (`gh api contents?ref=<headRefOid>`) |
| **Relatório de um comando** | ele cola o resumo, ou nomeia o comando que acabou de rodar | no **working tree**, mais `git diff` — o comando acabou de mexer ali |

O resto do procedimento é o mesmo, e é de propósito: o que trava a leitura é idêntico nos dois
casos. Um relatório de fim de execução tende a ser **pior** que um review, porque a parte com
template — contagens, status de gate — é justamente a que não pede decisão, enquanto os pontos que
exigem escolha saem em prosa livre. **Densidade tem que ser inversa à necessidade de decisão:** onde
ele só precisa saber, tabela apertada serve; onde ele precisa decidir, cada item ganha espaço.

No relatório, separe antes de qualquer coisa duas naturezas que costumam vir misturadas:

- **Fato consumado** — o que o comando já aplicou. Vira **uma linha cada**: arquivo, sintoma, o que
  mudou. Mecanismo só se ele pedir, ou se a correção mexeu em comportamento.
- **Pendente de decisão** — flag, achado não aplicado, pergunta em aberto. É aqui que mora o
  trabalho, e cada um vira card com a faixa de decisão.

Uma pergunta por decisão, via `AskUserQuestion` — nunca um parágrafo terminando em "quer que eu
aplique isso ou trate aquilo?", que funde escolhas independentes numa frase e obriga ele a responder
em prosa.

## Colete tudo antes de ler qualquer coisa

**Se a entrada é um review no PR:**

```bash
gh pr view <N> --json reviews,reviewDecision,comments,body,headRefOid,headRefName
gh api repos/{owner}/{repo}/pulls/<N>/reviews          # corpos dos reviews
gh api repos/{owner}/{repo}/pulls/<N>/comments         # inline, com path e linha
gh api repos/{owner}/{repo}/issues/<N>/comments        # thread geral
```

- **Agrupe as threads** por `in_reply_to_id`. Um ponto discutido em cinco respostas é um ponto.
- **Separe os autores `[bot]`** — não descarte: bot repetitivo é ruído, mas às vezes acerta. Marque
  a origem e siga.
- **Guarde o `headRefOid`.** Toda verificação é contra o **head do PR**, nunca contra a working tree
  local, que pode estar em outra branch. Ler o arquivo errado e concluir que o revisor errou é o
  pior resultado possível daqui.

**Se a entrada é um relatório de comando:**

```bash
git status --porcelain          # o que o comando mexeu
git diff                        # e como — é a sua fonte de fato
git diff --cached
```

O relatório nomeia arquivos e linhas do estado **de agora**, então aqui a working tree é a fonte
certa — o oposto do caso do PR. Confira também o que ele afirma sobre gate: contagem de testes,
typecheck, lint. Relatório que diz "995/995 ✓" e uma suíte que diz outra coisa é o primeiro achado.

**Meça antes de reescrever** — palavras, frases, referências inline, e quantos pontos pedem decisão.
É isso que você relata como o custo de leitura que a peça tirou do caminho.

## Cada ponto vira mecanismo, e o mecanismo se verifica

O ciclo, por ponto do review:

1. **Nomeie o sintoma.** O que o usuário final vê, numa linha. Se você não consegue dizer isso, você
   ainda não entendeu o ponto — volte ao texto antes de seguir.
2. **Ache o gatilho.** Em que condição acontece: que dado, que ordem de cliques, que estado.
3. **Explique em prosa.** Dois a quatro períodos: o que o sistema faz hoje, o que deveria fazer, e
   por que a diferença importa. Com conector causal — `porque`, `então`, `mas` —, que é exatamente
   o que fragmento telegráfico não tem. Se esses três períodos não saem, você ainda não entendeu o
   ponto, e nenhum bloco de evidência vai cobrir esse buraco.
4. **Reconstrua o traço, se houver traço.** Quando o mecanismo é ordem de execução ou estado, a
   sequência do gatilho ao sintoma em linhas curtas é insubstituível — metade dos achados de review
   é disso, e isso é ilegível em prosa por construção. Quando o achado é uma contradição entre dois
   textos, uma convenção sem precedente ou uma contagem que não fecha, **não há sequência**: ali o
   bloco mono vira saída de `grep` empilhada, que prova o achado e não explica nada. Nesse caso a
   prosa carrega sozinha, e a evidência vira citação de duas linhas de cada lado.
5. **Verifique no código do head**, arquivo por arquivo:
   `gh api repos/{owner}/{repo}/contents/<path>?ref=<headRefOid> --jq .content | base64 -d`
   Confirme a assinatura, a linha, a ordem das chamadas. **O texto do revisor é a hipótese; o código
   é o fato.**
6. **Classifique** com `arquivo:linha`: **procede** · **procede em parte** — o que sobra ·
   **não procede** — o que o código mostra · **[não verificado]** — e por quê.
7. **Escreva a correção, não a tarefa.** Defeito em texto — doc, skill, `CLAUDE.md`, comentário,
   mensagem de UI — sai como **o texto substituto escrito, em bloco, pronto pra colar**. Defeito em
   código sai como **diff mínimo**; em config, o valor novo e onde vai. "Reescrever para o que a
   cláusula quer mesmo dizer" **não é correção**: é o problema repetido em imperativo, e devolve
   justamente o trabalho que a página existe pra fazer. Diga também o que **não** resolve, quando
   existe um conserto óbvio e errado.
8. **Se o ponto pede decisão dele**, monte a faixa: qual é a escolha, o que muda de cada lado, e a
   sua recomendação — que é recomendação, não veredito. Ponto sem os dois lados escritos é ponto que
   empurra a decisão de volta pra ele sem material. **Faixa de decisão é pra escolha real**, não pra
   fugir de escrever o texto: se só há um caminho defensável, ele se escreve.

**Frase longa é mais de um fato — no texto que chegou.** Ponto do review com quarenta palavras num
período costuma empacotar dois ou três achados com pesos diferentes. Separe antes de classificar: cada fato ou é
verificável, ou é opinião do revisor — e as duas coisas merecem tratamento diferente.

## Não repassar é a regra

- **Ponto não verificado não vira prioridade.** Fica listado, marcado, e explicitamente fora da
  ordem de ataque.
- **Discordar do revisor é legítimo, com evidência.** Mostre as duas leituras, com `arquivo:linha`
  dos dois lados, e **deixe a decisão com o usuário**. Ter revisado não é evidência; nem ter
  implementado.
- **Não maquie o que procede.** Achado que confere é achado que confere — apresentar como "parcial"
  o que o código confirma é fazer o usuário decidir com dado torto.
- **Não invente achado que o review não fez.** Se você notar algo de passagem, isso vai numa lista
  separada, nomeada como sua, não misturada ao que o time pediu.

## A ordem de ataque

Ordene assim, e mostre o critério junto:

1. **Regressão** — funcionava antes desta mudança e parou.
2. **O que envenena trabalho futuro** — doc, `CLAUDE.md` ou skill afirmando o que é falso; padrão
   recém-documentado com a lacuna dentro. Custa em todo trabalho seguinte, inclusive de agente.
3. **Barato e certo** — fix de uma linha, predicado que volta, guard que retorna.
4. **O resto**, com o alcance real de cada um.

**Se o revisor deu a ordem dele, ela ganha** — e quando você discordar, diga isso numa linha em vez
de reordenar em silêncio. Bloqueante é palavra dele: se ele disse que nada bloqueia, não promova.

## A entrega

**Uma página local, e três linhas na tela.** Dois arquivos governam o que sai, e os dois se leem
antes de escrever: a régua de prosa em `${CLAUDE_SKILL_DIR}/prosa.md` — que vale pra todo texto
deste toolkit — e o formato da página em `${CLAUDE_SKILL_DIR}/format.md`, que é a versão
especializada dela pra cá.

**Onde o arquivo mora:** `<root>/thoughts/board/triage/<alvo>-<origem>.html`

```
<root>/thoughts/board/triage/pr-465-review.html         # o review que chegou no PR 465
<root>/thoughts/board/triage/pr-465-fullreview.html     # o fullreview rodado nessa mesma branch
<root>/thoughts/board/triage/feat-estorno-fullreview.html   # sem PR aberto ainda: slug da branch
```

- **`<alvo>`** é `pr-<N>` quando existe PR pra branch atual (`gh pr view --json number`), senão o
  slug da branch. É ele que identifica o trabalho.
- **`<origem>`** é de onde o denso veio: `review`, ou o nome do comando que rodou.

**O alvo vem primeiro porque é ele que discrimina.** `<root>` é o repositório **principal**
(`git worktree list | head -1`), então **todas as worktrees escrevem neste mesmo diretório** — nomear
pelo comando faria dois `fullreview` em worktrees diferentes colidirem, e o segundo apagaria o
primeiro em silêncio. Nome pelo alvo permite quantas rodadas simultâneas ele quiser, e ainda deixa
tudo de um mesmo trabalho junto quando ordenado por nome.

`thoughts/board/` é onde as views derivadas deste toolkit já moram — longe do dado, e gitignored.

**Mesma origem no mesmo alvo sobrescreve**, e isso é o certo: rodar o `fullreview` de novo na mesma
branch produz o estado de agora, não uma segunda opinião. O cabeçalho carrega data e hora da geração
— é o que diz se o que está na tela é da rodada de agora. Nunca crie `-v2` nem sufixo de timestamp:
o caminho é o que se fixa no navegador.

**Nada é publicado.** Não use a tool `Artifact`, e não mande a página pra serviço nenhum: review de
código e relatório de execução carregam caminho de arquivo, trecho de código e defeito não corrigido
de um repositório privado. A página é `file://`, fica na máquina, e é isso.

Na tela, só três linhas: quantos pontos e quantos pedem decisão, os **três** primeiros da ordem de
ataque com uma frase cada, e o caminho absoluto em `file://` pra abrir. Repetir a página no terminal
desfaz o ponto da peça.

```
7 pontos · 4 pedem decisão · página em
file:///home/você/projeto/thoughts/board/triage/pr-465-fullreview.html
```

## Depois, e isto não é seu

Termine dizendo qual caminho cada grupo segue — sem invocar nada, porque nenhuma peça deste toolkit
invoca outra:

| O que | Vai pra onde |
|---|---|
| Correção pequena, com o texto já escrito na página | ele cola, e a checagem de "o pedido foi atendido?" é do **`/tk7:imp-review`** |
| Ponto que muda comportamento | `tasks.md` da mudança, e **`/tk7:implement`** — comportamento sem teste é o que o ciclo existe pra impedir |
| Ponto que procede e ninguém vai tocar agora | roadmap, como item com dono |
| Relatório que sai denso **toda vez** | é a fonte que precisa de conserto, não a tradução. Diga qual arquivo gera o resumo e o que faltou nele — template pro que pede decisão, `AskUserQuestion` no lugar da pergunta aberta — e deixe a edição pro usuário: comando de projeto é versionado e revisado pelo time |

**Você nunca posta no PR.** Ler via `gh` é livre; responder ao revisor é do usuário — e o rascunho
de resposta nasce depois da correção, no `imp-review`, não aqui.

## Sempre

- **Nunca poste, comente ou resolva thread no PR.**
- **Nunca diga que o revisor errou sem `arquivo:linha`** do head.
- **Nunca decida o que aceitar.** Você entrega o que é fato e o que é opinião, separados. O corte é
  do usuário.
- **Nunca aplique a correção que você escreveu.** Escrever o conserto é o trabalho; editar o arquivo
  do projeto, não — quem cola é o usuário, ou o `implement` depois.
