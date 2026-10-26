# O formato da página

O que chegou denso vira **uma página local** — não um despejo no terminal. Um review de 2.000
palavras relido no terminal continua sendo 2.000 palavras: o ganho vem da estrutura, e estrutura
precisa de página.

**Arquivo local, nunca publicado.** Escreva em
`<root>/thoughts/board/triage/<alvo>-<origem>.html` — alvo é `pr-<N>` ou o slug da branch, origem é
`review` ou o comando — e entregue o caminho `file://`. Não use a tool `Artifact`: o conteúdo é caminho de arquivo, trecho de código e
defeito não corrigido de repositório privado, e isso não sai da máquina.

**Carregue a skill `artifact-design` antes de escrever** — a orientação de composição, tipografia e
tema vale igual fora do Artifact; só o publicar é que não se aplica.

### A casca, que agora é sua

Sem o Artifact não há skeleton envolvendo nada: o arquivo é HTML completo.

```html
<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Achados do PR 465</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'
  viewBox='0 0 16 16'><text y='14' font-size='14'>🧾</text></svg>">
<style> /* tudo embutido */ </style>
</head><body> … </body></html>
```

Três consequências de rodar em `file://`:

- **CSS sempre embutido.** Folha externa não é garantida — é a mesma razão pela qual os scripts de
  view deste toolkit embutem o estilo.
- **Fonte externa é bônus, não base.** `<link>` pro Google Fonts pode entrar (com `preconnect`), mas
  toda família precisa de stack de sistema atrás dela: aberto sem rede, a página tem que continuar
  bem composta.
- **Tema só por `prefers-color-scheme`.** `data-theme` é coisa do viewer do Artifact e aqui não
  existe: defina a paleta clara no `:root` e redefina os tokens dentro do media query. `body` com
  `background` de token, como sempre.

## As faixas de cada achado

| Faixa | O que carrega | Quando |
|---|---|---|
| **Título** | o que quebra, na língua de quem usa o sistema — não o nome da função | sempre |
| **Quem sente · Gatilho · Alcance** | três linhas curtas, em lista de definição | sempre |
| **O que está acontecendo** | prosa: o que o sistema faz hoje, o que deveria fazer, por que a diferença importa | sempre |
| **Traço** | bloco mono, do gatilho ao sintoma | só quando o mecanismo é ordem de execução ou estado |
| **Correção** | o texto novo ou o diff, escrito — e o que não resolve | sempre, salvo quando vira faixa de decisão |

E no pé do card, separada do texto: a **linha de referências** (`arquivo:linha · arquivo:linha`).
Toda referência sai da prosa e vem pra cá. Era isso que travava a leitura no original: cada
`arquivo:linha` no meio da frase é uma decisão de abrir ou continuar.

## A prosa, que é onde o achado se entende

**Dois a quatro períodos, em prosa de verdade.** Não é resumo do traço nem repetição do título: é o
parágrafo que um colega escreveria explicando o problema no quadro. Responde três coisas, nesta
ordem:

1. **O que o sistema faz hoje** — o comportamento real, afirmado.
2. **O que deveria fazer** — e é aqui que o defeito aparece, por contraste.
3. **Por que a diferença importa** — a consequência que justifica parar pra corrigir.

**Esta faixa é a exceção à régua de densidade.** Ela pode ter período longo, pode ter aparte, e
principalmente **precisa de conector causal** — `porque`, `então`, `mas`, `ou seja`. Fragmento
telegráfico prova; prosa ligada explica, e é a ligação que faltava. O que ela continua não podendo
ter é `arquivo:linha` no meio da frase: isso mora no pé do card, como no resto.

Se esses três períodos não saem, você ainda não entendeu o achado — e nenhum traço cobre esse
buraco.

## O traço, que é opcional

**Traço só quando o mecanismo é ordem de execução ou estado.** Aí ele é insubstituível: três fatos
que só fazem sentido juntos — o campo está desmontado, o erro é escrito antes de montar, a escrita
substitui a lista inteira — em parágrafo obrigam o leitor a reconstruir a sequência de cabeça.

**Quando o achado não tem sequência, o traço atrapalha.** Contradição entre dois parágrafos de um
doc, convenção sem precedente, contagem que não fecha, regra que nasce violada: nada disso é um
caminho de execução. Forçar o bloco mono ali empilha saída de `grep` e resultado de `gh api`, que
**provam** o achado sem **explicar** nada. Nesses casos a prosa carrega o achado sozinha, e a
evidência vira citação curta de duas ou três linhas de cada lado.

**A pergunta que decide:** dá pra numerar os passos do gatilho até o sintoma? Se dá, é traço. Se a
resposta é "não são passos, são dois lugares que se contradizem", não há traço — há uma citação de
cada lado.

Quando entra, as regras:

- **Uma chamada ou uma decisão por linha.** Nunca duas.
- **Setas de fluxo** (`→`, `⇒`, `│`, `└─`) mostrando causa, e indentação mostrando aninhamento.
- **`antes` × `head`** lado a lado quando o achado é uma regressão — a diferença de um caractere só
  aparece assim.
- **Estado concreto**, não abstrato: `[A, B, C]` e "remove A", não "considere uma lista".
- **Marque o ponto do defeito** (`<b>`) e comente o de apoio em tom apagado (`<i>`). Um destaque
  por traço; dois já é nenhum.
- **Sem `if`/`for` transcrito do código.** O traço é o caminho, não a implementação.

## A correção, que se escreve — não se encomenda

**A faixa entrega o conserto pronto, não a tarefa de achá-lo.** "Reescrever para o que a cláusula
quer mesmo dizer" não é correção: é o problema repetido em modo imperativo, e devolve pro usuário
exatamente o trabalho que a página existia pra fazer.

| Natureza do defeito | O que a faixa entrega |
|---|---|
| **Texto** — doc, skill, `CLAUDE.md`, comentário, mensagem de UI | **o texto substituto, escrito**, em bloco, pronto pra colar |
| **Código** | **o diff mínimo** — as linhas que mudam, e nada mais |
| **Config** | o valor novo e onde ele vai |
| **Escolha do usuário** | nenhuma: vira faixa de decisão, e a correção nasce depois que ele escolhe |

**Escrever a correção não é aplicá-la.** Você não edita arquivo, não commita, não posta. A página
mostra o texto pronto; colar é do usuário, ou do `implement` depois.

**Duas correções defensáveis viram faixa de decisão**, com os dois custos escritos. O que não vale
é fugir pra faixa de decisão porque escrever o texto dá trabalho: se o certo é óbvio, escreva o
certo.

**E continue dizendo o que não resolve**, uma linha, quando existe um conserto óbvio e errado que
alguém tentaria. É o que evita a segunda rodada.

## A página inteira

Nesta ordem:

1. **Cabeçalho** — repo e número do PR, o revisor, e a medida do original (palavras, frases,
   referências inline) contra o número de achados. Diga que a verificação foi contra o head.
2. **O que atacar antes** — três blocos, com o id do achado e uma frase. Se o revisor deu a ordem,
   é a dele.
3. **Tabela de todos os achados** — severidade, o que quebra (link pra âncora), alcance hoje.
4. **Os achados**, agrupados pela severidade que o **revisor** usou. Sub-achados do mesmo mecanismo
   entram como `a. b. c.` dentro do card, não como cards soltos.
5. **O que o review confirmou** — o que ele checou e está certo. Isso não é elogio: é o que o
   usuário não precisa revisitar, e economiza tanto quanto os achados.
6. **O que ficou de fora**, com o motivo (já tem PR, já tem item de roadmap, não verificado).

## Quando a entrada é relatório de comando, não review

A página é a mesma; muda o que entra em cada seção.

1. **Cabeçalho** — o comando que rodou, quantas fases, e o gate que ele afirma (typecheck, lint,
   contagem de testes, do jeito que ele reportou). Se você conferiu e divergiu, isso é a primeira
   coisa da página.
2. **O que já foi aplicado** — tabela, **uma linha por correção**: arquivo · o que quebrava ·
   o que mudou. Sem card, sem traço. É fato consumado, e fato consumado não precisa convencer
   ninguém — só precisa ser encontrável depois.
3. **O que espera decisão** — os cards, com a faixa de decisão. Esta é a seção principal, e a ordem
   dela é a ordem de ataque.
4. **Contagens por fase** — no fim, como apêndice. Vieram estruturadas da fonte e não pedem nada
   dele; ficam pra conferência, não pra leitura.
5. **O que a fonte errou sobre si mesma**, se houver: contagem que não fecha, ponto que o relatório
   declara como coberto e o código contradiz, gate afirmado que não confere. Vai separado, porque
   muda a confiança em todo o resto.

**A faixa de decisão** entra depois da correção, e substitui o "Correção" quando não há uma:

```html
<dl class="facts decision">
  <dt>A escolha</dt><dd>o teste fica, sai, ou vira teste de runtime real?</dd>
  <dt>Se ficar</dt><dd>o plano continua afirmando que é "o único detector" — e é falso</dd>
  <dt>Se sair</dt><dd>o memo segue necessário em runtime, sem nada protegendo</dd>
  <dt>Recomendo</dt><dd>manter o memo, corrigir o plano, marcar o caso como não-detector</dd>
</dl>
```

As quatro linhas são obrigatórias juntas. Escolha sem os dois custos escritos é a decisão devolvida
sem material — o que o relatório dele já fazia, e é o que a página existe pra consertar. E
`Recomendo` é recomendação: uma linha, sem insistir, e recusa não vira ponto a rebater.

**Contagem no cabeçalho, decisão em card.** Um relatório de execução chega com a densidade
invertida: a parte com template (contagens, status) é a que não pede nada, e a que pede escolha sai
em prosa. A página desfaz essa inversão — é a razão de ela existir pra este caso.

## Régua de densidade, que vale pra página inteira — menos numa faixa

- **Frase de até ~25 palavras.** Passou disso, quebre — provavelmente são dois fatos.
- **Um aparte por frase**, no máximo. Aparte dentro de subordinada é o que faz perder o sujeito.
- **Nenhuma referência dentro de frase.** Vão pro pé do card ou pra linha de meta.
- **Coluna de leitura em ~65 caracteres.** Prosa larga cansa antes de confundir.
- **Achado começa pelo sintoma.** Mecanismo primeiro é como quem descobriu escreve; sintoma
  primeiro é como quem corrige lê.

**A exceção é a faixa "O que está acontecendo".** A régua foi escrita pra desinflar prosa de quem
descobriu o defeito — e aplicada à escrita do zero ela produz fragmento, não explicação. Naquela
faixa, período longo e conector causal são o instrumento; em todo o resto, continuam sendo o
problema.

## Título e identidade

`<title>` é nome, não legenda: `Achados do PR 465`, não "Análise detalhada do review do PR 465". Ele
é o que aparece na aba, junto do favicon — e os dois ficam estáveis entre rodadas, senão a aba
aberta parece outra página.

**Mesmo alvo e mesma origem, mesmo arquivo.** A rodada seguinte sobrescreve
`pr-465-review.html` em vez de criar `-v2`: o caminho é o que se fixa no navegador. Alvos diferentes
nunca colidem, o que é o que permite duas worktrees rodando ao mesmo tempo. Marque no cabeçalho a
data e hora da geração — é o que diz se o que está na tela é da rodada de agora.

## Esqueleto

Ponto de partida, não gabarito a copiar — a identidade visual se decide na hora, com a
`artifact-design` na mão. O que **não** se negocia: tokens de cor no `:root` e redefinidos no media
query de tema escuro, `body` com `background` de token, mono nos traços e no bloco de correção,
`overflow-x:auto` em todo bloco largo, e âncora (`id`) em cada achado — em página longa, o link pra um achado específico é o
que faz a conversa sobre ele ser possível.

```html
<article class="finding" id="e1">
  <header>
    <span class="stamp s-struct">Estrutural 1</span>
    <h3>Um método sem nome derruba a única tela que podia apagá-lo</h3>
  </header>
  <dl class="facts">
    <dt>Quem sente</dt><dd>o lojista, que perde a tela por completo</dd>
    <dt>Gatilho</dt><dd>método escrito por fora do schema: SQL direto, seed, migration</dd>
    <dt>Alcance</dt><dd>regressão — antes o caso era coberto</dd>
  </dl>
  <p class="what">Hoje a linha chama <code>trim()</code> direto no <code>displayName</code>, que o
  schema deixa nulo. Deveria chamar com <code>?.</code>, como chamava antes desta mudança — o
  fallback "Método sem nome" logo ao lado só existe porque alguém previu o nulo. A diferença
  importa porque o erro estoura dentro de um computed, então não é o campo que fica vazio: é a
  página inteira que não renderiza, e ela é a única via de apagar o método defeituoso.</p>
  <pre class="trace">antes  method.displayName<b>?.</b>trim() || "Método sem nome"
head   method.displayName<b>  </b>trim() || "Método sem nome"
                          <i>↑ o ?. saiu, o fallback continua anunciado</i>

displayName = undefined
   └─ describeCustomPaymentRow → <b>TypeError dentro de um computed</b>
        └─ a página não renderiza
             └─ <b>morre a única via de apagar o método defeituoso</b></pre>
  <div class="fix">
    <b>Correção</b>
    <pre>- method.displayName  trim() || "Método sem nome"
+ method.displayName?.trim() || "Método sem nome"</pre>
    <p>Não resolve tratar no chamador: o computed roda antes.</p>
  </div>
  <footer class="refs">store-apps-state.ts:80 · store-apps-patch.ts:537</footer>
</article>
```
