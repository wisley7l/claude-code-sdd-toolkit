# Créditos — skill `triage`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

**Nenhuma fonte externa.** A peça nasceu de um caso real em 02-09-2026: um review de 2.083 palavras
recebido num PR, que o usuário não conseguia ler.

*"to recebendo uns review e eles tão ficando muito denso na leitura, talvez pq eu precise ver esse
erros em pseudo codigo, tem hora que não estou entendendo nada"* — e depois, fechando o endereço:
*"eu preciso da peca quando o time fizer um review pra mim"*.

O diagnóstico não foi qualidade: o review estava certo — os pontos checados no head do PR conferiam.
Era **forma de entrega**. Medido: 91 frases, média de 23 palavras, 9 frases com 40+ palavras, e
**40 referências `arquivo:linha` dentro da prosa**, num corpo único sem cabeçalho por item.

## As três descobertas que viraram desenho

- **⭐ Metade dos achados de review é sobre ordem de execução e estado**, e isso é ilegível em prosa
  por construção. O caso que provou: três fatos que só fazem sentido juntos (o campo está desmontado,
  o erro é escrito antes de montar, a escrita substitui a lista inteira). Em parágrafo, o leitor
  reconstrói a sequência de cabeça; em cinco linhas indentadas o defeito salta e a correção aparece
  sozinha. Daí o **traço** ser faixa obrigatória de todo achado.
- **A referência dentro da frase é o que trava a leitura.** Cada `arquivo:linha` no meio do texto é
  uma decisão de abrir ou continuar. Elas são prova, não mensagem — foram pro pé do card.
- **Sintoma antes do mecanismo.** Review é escrito por quem descobriu (mecanismo → sintoma) e lido
  por quem vai corrigir (sintoma → mecanismo). Inverter a ordem é a mudança mais barata e a de maior
  efeito.

## Por que peça própria, e não branch do `imp-review`

Pela Parte C.4, separar exige ganho por invocação ou por sequência. Tem os dois:

- **Por invocação** — é **model-invoked**, como `glossary` e `grilling`. O usuário sempre abre a conversa
  dizendo *"recebemos um review"*, e pediu explicitamente o gatilho. Habilitar model-invocation no
  `imp-review` custaria context load de uma description que já cobre três trabalhos, e dispararia
  torto; uma description curta e ancorada em "review recebido no meu PR" custa pouco e acerta.
- **Por sequência** — entender e decidir vem **antes** de corrigir. O `imp-review` já cobre "o time
  comentou", mas no momento seguinte: `Pediu / No código / Leitura`, que pressupõe correção feita.
  Misturar os dois é confundir dois momentos com contratos diferentes.

## A fronteira com as peças vizinhas

| Peça | Papel |
|---|---|
| `triage` | review **recebido**: entende, verifica no head, prioriza. Não corrige, não responde |
| `imp-review` | depois da correção: o comentário humano é o contrato, e checa se foi atendido. É de lá que sai o rascunho de resposta |
| `pr-review` | o outro lado: revisar o PR **de alguém**. Ganhou a régua de forma no mesmo dia, pro problema não nascer |

Nenhuma invoca a outra (I.27): cada uma termina nomeando a seguinte.

## O que o usuário decidiu (02-09-2026)

- **A peça é pra review recebido**, não pro review que ele escreve.
- **Gatilho por linguagem natural** — model-invoked, contra o padrão de todo o resto do toolkit,
  porque o custo real dele é lembrar que a peça existe no momento em que ela serve.
- **A entrega é página publicada**, não despejo no terminal — mesma decisão que a auto-memory já
  registra pra doc denso (`doc-humano-view-html-gerada`). Um review de 2.000 palavras relido no
  terminal continua sendo 2.000 palavras.
- **`pr-review` exibe no mesmo formato** — *"e sim pode fazr o pr-review exibir nesse formato que me
  mandou"*. Lá a página não serve (o destinatário é o GitHub), então o que atravessou foram as quatro
  faixas e a régua de densidade, aplicadas ao corpo do review.

## Limite declarado

A verificação é contra o **head do PR**, lido via `gh api contents?ref=<sha>` — não contra a working
tree, que costuma estar em outra branch. Ler o arquivo errado e concluir que o revisor errou é o pior
resultado possível da peça, e por isso o `headRefOid` é coletado antes de qualquer leitura.

## Segunda entrada: relatório de comando (02-09-2026, mesmo dia)

*"da para ter tbm quando eu executar um comando do projeto ele devolve as resposta geralmente assim
[…] de ser menos densa?"* — e, quando eu comecei a desenhar um formato novo: *"gostei do que vc
apresentou no triage não daria para ser igual?"*

**Ele estava certo e eu ia errar.** Meu caminho era escrever um template de flags dentro do
`fullreview.md` do projeto — arquivo versionado, revisado pelo time, num repo de trabalho — quando a
peça que faz exatamente esse trabalho já existia. Virou **branch de entrada** (Parte C: caminhos
diferentes conforme o gatilho), não peça nova e não formato duplicado.

**O que muda entre as duas entradas é só a fonte de verificação:** review de PR confere contra o
head (`gh api contents?ref=<sha>`), relatório de comando confere contra o **working tree**, porque o
comando acabou de mexer ali. O resto é idêntico, e é o ponto: o que trava a leitura é o mesmo.

**⭐ A descoberta deste caso — densidade inversa à decisão.** No relatório real que ele colou
(`fullreview`, 7 fases), o que tinha template era o bloco de contagens e o status de gate: a parte
que **não** pede decisão. As 7 flags — a única coisa que exigia ação dele — não tinham template
nenhum, porque a spec só dizia "liste cada um e ofereça a ação ao usuário". Improviso sai em prosa.
Densidade tem que ser inversa: contagem no cabeçalho, decisão em card com os dois custos escritos.

Daí a **faixa de decisão** (a escolha · se A · se B · recomendo), obrigatória nos quatro campos.
Escolha sem os dois lados é decisão devolvida sem material — que é o que a memória
`decisao-de-produto-e-do-usuario` já registrava, aplicado à forma.

**Fonte densa toda vez é a fonte que se conserta, não a tradução.** A peça diz qual arquivo gera o
resumo e o que faltou nele, e para aí: comando de projeto é versionado e revisado pelo time, e essa
edição é do usuário.

## O nome do arquivo é pelo alvo, não pelo comando (02-09-2026)

*"/fullreview.html impede de fazer mais de um fullreview por vez"* — correção dele sobre o esquema
que eu havia escrito.

Estava errado por confundir **origem** com **alvo**. `fullreview` é de onde o denso veio; o que
identifica o trabalho é o PR ou a branch. E o efeito não era só colisão: como `<root>` é o
repositório principal, **todas as worktrees escrevem no mesmo diretório** — duas rodadas paralelas
se apagariam sem aviso, que é o pior tipo de bug de arquivo derivado, porque parece ter funcionado.

Esquema final: `<alvo>-<origem>.html`. Alvo primeiro para ordenar junto o que é do mesmo trabalho.
