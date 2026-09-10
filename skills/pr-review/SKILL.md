---
name: pr-review
description: Revisa o PR de outra pessoa. Explica a mudança antes de julgá-la, confere o que o PR prometeu contra o que entregou, passa as lentes, sabatina você sobre o que só você decide, e monta um submit review único — comentários inline, revisados por você antes de sair.
disable-model-invocation: true
argument-hint: [número do PR | URL | vazio = escolher entre os que aguardam você]
allowed-tools: Read Write Grep Glob Agent Skill AskUserQuestion Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git show*) Bash(git branch*) Bash(git fetch*) Bash(git worktree list*) Bash(gh *) Bash(ls *) Bash(structure-cache *) Bash(structure-cache)
---

# pr-review

O PR é de outra pessoa e quem assina a revisão é você. A skill faz o trabalho de leitura, traz o
que achou, e sabatina você sobre o que só você decide. **O veredito é seu, e o texto que vai pro
GitHub passa pelos seus olhos antes de sair.**

Isto é o oposto do `imp-review`: lá você é o autor procurando o próprio furo, e a regra é jamais
escrever no PR. Aqui você é o revisor, e o produto final é justamente o comentário.

## Delimitar

Sem argumento, liste o que espera por você e pergunte qual:

```bash
gh pr list --search "review-requested:@me state:open" --json number,title,author,additions,deletions
```

Com o PR escolhido, capture tudo de uma vez — e guarde o **`headRefOid`**, que é o SHA em que sua
leitura se apoia:

```bash
gh pr view <N> --json number,title,body,author,headRefOid,baseRefName,files,commits,reviews,comments
gh pr diff <N>
```

**PR seu próprio** → é o `imp-review` que serve, e o GitHub recusa aprovação do próprio PR. Diga e
pare. **Rascunho ainda em draft** → confirme com o usuário antes de gastar análise.

## 1. Briefing — entender antes de julgar

Nada de achado nesta fase. O objetivo é você terminar de ler sabendo do que o PR trata.

Leia a issue vinculada (`Closes #`, `Fixes #` no body, ou referência no título), a mensagem dos
commits, e os **arquivos completos** que o diff toca — mais quem chama o que mudou
(`grep` pelos símbolos alterados). Diff sozinho esconde o contexto que decide se algo é bug.

Entregue na tela:

- **O que se propõe** — em duas ou três linhas, em suas palavras, do body e da issue.
- **O que de fato toca** — por área, separando a mudança real do arrasto (lockfile, gerado,
  formatação em massa). Se o PR é grande, diga qual arquivo é o coração dele.
- **Por onde ler** — a ordem em que os arquivos fazem sentido, começando pelo que estabelece o
  comportamento novo e terminando nos que apenas o consomem.
- **O que mudou de comportamento** — o que o código fazia antes e passa a fazer, para quem chama.
- **O que não consegui determinar** — declare. Se alguma dessas lacunas mudaria a análise inteira
  (qual ambiente roda isso, se esse caminho é alcançável em produção, se essa tabela tem volume),
  pergunte aqui, poucas e diretas. O resto espera a fase 4.

## 2. Promessa × entrega

O contrato é o que o PR declarou: body, issue vinculada, critérios de aceite se houver. Extraia
item por item e confronte com o diff:

| Estado | Significa |
|---|---|
| **Entregue** | está no diff — cite `arquivo:linha` |
| **Parcial** | parte está, e falta o quê |
| **Não encontrei** | prometido e ausente do diff |
| **Não prometido** | está no diff e ninguém anunciou |

A última linha é a que quase todo review pula, e costuma ser a mais cara: mudança de comportamento
que entra de carona, sem ninguém ter pedido, e que ninguém vai procurar depois. Refactor amplo,
troca de default, campo removido de resposta — traga tudo, mesmo que pareça inofensivo.

Body vazio ou genérico ("ajustes", "fix") é um achado em si: sem contrato declarado não há o que
conferir, e vale pedir a descrição antes de revisar o resto.

## 3. As lentes

Reaproveitam integralmente as do `imp-review` — foram escritas na voz de quem não implementou o
código, que é exatamente a sua posição aqui. Lance **numa única resposta**,
`subagent_type: general-purpose`, `model: opus` para bugs, segurança, queries e testes, `sonnet`
para conformidade e nomenclatura:

> Leia `${CLAUDE_SKILL_DIR}/../imp-review/lenses.md` e assuma a lente **<nome>**. Diff e arquivos
> completos: `<conteúdo>`. Constitution: `<CLAUDE.md e ARCHITECTURE.md>`. Você é read-only, não
> aprova nada, e o código é de outra pessoa.

**Pule a lente cujo escopo não aparece no diff.** Lente sem matéria-prima inventa achado.

Os achados voltam com `arquivo:linha` numa string única. Para virarem comentário inline você
precisa dos campos separados — **quebre em `path` e `line` ao consolidar**, e confira que a linha
está mesmo num hunk do diff (`gh pr diff <N>`).

**Nem todo achado ancora.** "Isso quebra `src/legacy/handler.ts`, que o PR não toca" é legítimo e
não tem linha no diff onde pousar. Separe os dois baldes já aqui: o que vai inline e o que vai no
corpo do review. Um comentário inline apontando para linha fora do diff faz o POST inteiro falhar.

## 4. Sabatina — antes do veredito

Aqui a skill segue a disciplina do `grilling`, aplicada ao que um review decide. **Uma pergunta por
vez, cada uma com sua recomendação e o motivo dela.** Espere a resposta antes da próxima.

**Fato você busca; decisão é do usuário.** Se dá para descobrir no código, no git ou na doc, vá
buscar em vez de perguntar — a atenção dele é o recurso escasso da conversa. Perguntas que valem a
pena são as que só ele responde:

- **Este furo bloqueia ou vira follow-up?** Você trouxe a evidência; o apetite de risco do time é
  dele. Um `REQUEST_CHANGES` tem custo social que a análise não enxerga.
- **Este padrão é aceito aqui?** O que parece divergência pode ser convenção viva que o
  `CLAUDE.md` nunca registrou.
- **Quanto de porquê o autor precisa junto?** Muda o texto de cada comentário, não o conteúdo.
- **O que ficou em aberto na fase 1** e agora pesa no veredito.

**Discorde quando tiver motivo.** Se ele quer aprovar por cima de algo que você acha que bloqueia,
diga qual é a consequência — uma vez, sem insistir. Se ele reafirmar, é decisão dele: registre no
corpo do review, se ele quiser, e siga.

Feche a sabatina com o veredito escolhido e o que o sustenta:

- **`APPROVE`** — segue sem alteração pedida.
- **`REQUEST_CHANGES`** — há ponto que precisa mudar antes do merge.
- **`COMMENT`** — observação sem travar, e sem carimbar.

## 5. Montar o review

**Todo pedido de alteração vai inline.** Comentário inline chega no arquivo e na linha de quem vai
consertar; a mesma frase no corpo do review vira caça ao tesouro. O corpo carrega o que não tem
linha: o resumo, o contexto do veredito, e os achados sem âncora.

Cada comentário inline, em duas ou três linhas: o que está errado, por que importa, e o ajuste
concreto — com a base que o sustenta (`arquivo:linha` de um padrão do projeto, o trecho do
`CLAUDE.md`, ou doc oficial). Sugestão de código cabe em bloco `suggestion`, que o autor aplica com
um clique. Nit vai marcado como nit, para o autor saber o que é opcional.

### O corpo é onde o review engorda

O inline tem limite natural — duas ou três linhas, um arquivo, uma linha. O corpo não tem nenhum, e
é ali que o review viaja: mecanismo antes do sintoma, `arquivo:linha` no meio da frase, quarenta
palavras por período. Quem recebe é quem paga, e paga na hora de consertar.

**Cada achado do corpo tem quatro faixas, nesta ordem:**

```
### <o que quebra, na língua de quem usa o sistema — não o nome da função>

Quem sente: <uma linha>  ·  Gatilho: <uma linha>  ·  Alcance: <uma linha>

    <traço: a sequência do gatilho até o sintoma, uma chamada ou decisão por linha,
     com setas mostrando causa e indentação mostrando aninhamento>

Correção: <uma frase — e o que não resolve, quando alguém tentaria o óbvio>
Refs: arquivo:linha · arquivo:linha
```

A régua, que vale pro corpo inteiro:

- **Frase de até ~25 palavras.** Passou disso, provavelmente são dois fatos — quebre em dois.
- **Um aparte por frase.** Aparte dentro de subordinada é o que faz perder o sujeito antes do verbo.
- **Nenhuma referência dentro de frase.** Cada `arquivo:linha` no meio do texto é uma decisão de
  abrir ou continuar; elas são a prova, não a mensagem, e moram na linha de `Refs`.
- **O achado abre pelo sintoma.** Mecanismo primeiro é como escreve quem descobriu; sintoma
  primeiro é como lê quem vai corrigir. Você está escrevendo pro segundo.
- **Sub-achados do mesmo mecanismo** entram como `a.` `b.` `c.` sob um achado só, não como quatro
  itens soltos que parecem quatro problemas.

O traço não é enfeite: metade dos achados de review é sobre **ordem de execução e estado**, e isso é
ilegível em prosa por construção. Três fatos que só fazem sentido juntos — o campo está desmontado,
o erro é escrito antes de montar, a escrita substitui a lista inteira — em parágrafo obrigam o leitor
a reconstruir a sequência de cabeça. Em cinco linhas indentadas, o defeito salta e a correção
aparece sozinha.

**Dois mil caracteres de corpo já pedem revisão da forma.** Rigor não é densidade: o mesmo achado
cabe em menos, e o que sobra de espaço vira achado que ninguém teria lido.

Monte o JSON num arquivo de trabalho — ancorado no `headRefOid` capturado lá no início:

```json
{
  "commit_id": "<headRefOid>",
  "event": "REQUEST_CHANGES",
  "body": "<resumo, veredito e achados sem âncora>",
  "comments": [
    { "path": "src/refund/calc.ts", "line": 88, "side": "RIGHT", "body": "<o ponto>" }
  ]
}
```

`side: RIGHT` para linha adicionada ou de contexto, `LEFT` para removida. Trecho de várias linhas
usa `start_line` com `start_side`.

## 6. Preview e envio

**Mostre tudo na tela antes de qualquer chamada de escrita**: o veredito, o corpo, e cada
comentário inline com seu `arquivo:linha`. O usuário altera, remove, suaviza, acrescenta — quantas
rodadas ele quiser. Só quando ele fechar é que sai.

Um POST, um review, todos os comentários juntos:

```bash
gh api --method POST repos/{owner}/{repo}/pulls/<N>/reviews --input <arquivo.json>
```

Sempre como **submit review**. Comentário solto (`gh pr comment`) fica fora da thread de revisão,
não pode ser resolvido pelo autor e não carrega veredito — o que quebra o próprio propósito.

**Se o POST falhar:**

- **422 em um comentário** → a linha caiu fora do diff. Mova aquele ponto para o corpo e repita.
- **SHA desatualizado** → o autor pushou depois da sua leitura. Recarregue o PR: comentário
  ancorado em código que mudou aponta para o lugar errado.

Confirme com a URL do review publicado, e diga o que ficou de fora — as lentes puladas e por quê.
Sem isso o usuário não sabe o tamanho do silêncio que ele assinou.

## Limites

- **O veredito é do usuário.** A skill recomenda com evidência; carimbar é dele.
- **Escrever no GitHub acontece uma vez, depois do preview aprovado.** Ler é livre.
- **Zero achado é resultado legítimo** — diga isso e diga onde olhou. Inflar afoga o achado bom.
- **Problema pré-existente que o PR não introduziu fica fora**, por pior que seja. Se for grave,
  ofereça abrir issue à parte em vez de pendurar no PR de quem passou por perto.
