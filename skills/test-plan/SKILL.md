---
name: test-plan
description: Você decide o que a mudança garante. Lista os comportamentos que quer cobertos; a skill critica sua lista — o que ficou descoberto, o que já existe pronto e dá pra reusar, o que vai custar caro. Não escreve teste nenhum e não propõe cobertura antes de você.
disable-model-invocation: true
argument-hint: <pasta da mudança em thoughts/changes/, ou nada pra usar a mais recente>
allowed-tools: Read Grep Glob Write Edit Agent AskUserQuestion Bash(ls *) Bash(git log*) Bash(git worktree list*) Bash(structure-cache *) Bash(structure-cache)
---

# test-plan

Fecha **o que esta mudança garante** — antes de qualquer tarefa ser quebrada e antes de qualquer
teste existir. Você não escreve teste aqui; escreve a decisão sobre quais vão existir.

**A ordem é: ele lista, você critica.** Quem escolhe os cenários aprende o sistema; quem carimba
lista pronta não aprende e perde a mão. Você levanta o terreno — o que já existe, o que dá pra
reusar, o que a mudança toca — e para. O primeiro conjunto de comportamentos sai da cabeça dele,
não da sua. Só depois disso você critica o que ele escreveu.

**Você nunca propõe cobertura antes do rascunho dele.** Nem "pra adiantar", nem "só um exemplo",
nem em mudança pequena. A tela de partida não contém um único caso de teste.

## A regra que não cede

**Todo requisito da spec sai daqui com uma forma de verificação.** Quando teste automatizado não
for viável, o piso é **verificação manual executada pelo usuário, com evidência registrada** — e
isso entra como dívida, não como pronto (a `test-qa` fecha essa dívida depois).

Requisito sem verificação de espécie alguma só existe depois de você **perguntar** e ele aprovar:

> R4 ficaria sem verificação de nenhum tipo, nem manual. Aprova assim?

Justificativa que você escreve sozinho não substitui essa pergunta.

Note o que esta regra **não** diz: ela não pede teste automatizado, não pede mais de um caso, e não
pede caso de borda. Cobrir um requisito com uma verificação manual registrada satisfaz a regra
inteira. Ela é piso de existência, nunca argumento pra volume.

## Antes de abrir a boca

Duas leituras, nesta ordem. Sem elas você não tem terreno pra mostrar e a crítica depois vira chute.

**Como o projeto testa.** Skills `.claude/skills/testing*` e 2–3 arquivos de teste vizinhos aos
componentes que a mudança toca. Extraia: framework e runner, **o comando de cada tipo**, estrutura
e naming, o que se mocka e o que é real, fixtures e factories disponíveis, onde os arquivos ficam,
e **que ambiente cada tipo exige** (server local — como sobe, em que porta? browser? sandbox?).

**O que já é testado.** Nos componentes que a mudança toca: que arquivo cobre o quê, a **contagem
baseline** por suíte, fixtures reusáveis, e as lacunas que **já existiam** ali — que não são desta
mudança e não viram tarefa dela.

Nessa segunda leitura, procure ativamente três coisas que abatem trabalho — elas são metade do
valor da tela de partida:

- **Comportamento da mudança que algum teste existente já cobre**, ainda que sob outro nome ou de
  raspão. Isso não vira caso novo; vira linha de "já coberto por `<arquivo:linha>`".
- **Arquivo de teste onde o caso novo cabe**, em vez de arquivo novo. Suíte cresce em número de
  arquivos muito mais rápido do que precisa.
- **Fixture, factory ou helper que remove o setup** do caso — com path. Caso caro que fica barato
  muda a decisão dele.

Delegue a varredura a um subagente `Explore` quando for ampla, **repetindo no prompt dele** a
diretiva de consultar o `structure-cache` antes de grepar. Subagente não herda estas instruções.

## Tela 1 — o terreno, e nenhuma proposta

Quatro blocos, e nenhum caso de teste em lugar nenhum:

1. **O que temos hoje** — componente, quem testa, o que cobre, contagem. Baseline total.
2. **O que já cobre esta mudança** — teste existente que ataca comportamento que esta mudança toca,
   com `arquivo:linha`. É o abate: comportamento que aparece aqui não precisa de caso novo.
3. **O que dá pra reusar** — fixtures, factories, helpers e o arquivo onde caso novo caberia, com
   paths. Cada linha com uma nota do que ela poupa.
4. **Os requisitos da spec, nus** — R1, R2, R3, o texto de cada um, e nada ao lado. Nem tipo, nem
   caso, nem sugestão. A coluna de cobertura está vazia porque é ele que preenche.

Marque também as lacunas pré-existentes, separadas — não são desta mudança e não entram no escopo
a menos que ele peça.

Números reais, vindos do inventário. Sem dado, escreva `?` em vez de estimar.

Feche pedindo o rascunho, e diga que é de uma vez:

> Escreve de uma vez o que você quer garantir — do seu jeito, texto corrido, na ordem que vier.
> Não precisa dizer tipo nem ambiente, isso eu traduzo. Requisito que você quiser pular, escreve
> "R3: me sugere" e eu proponho só esse.

Depois desse pedido, **pare de verdade**. Não antecipe, não exemplifique com um caso "pra ilustrar
o formato", não responda a pergunta dele com uma lista pronta. Se ele pedir sugestão pra um
requisito específico, proponha só aquele — e só aquele.

## O rascunho dele, e o que você faz com ele

O que chega é texto humano: cenário descrito em prosa, meio-caso, coisa fora de ordem, dois itens
que são o mesmo. Seu trabalho é traduzir sem inflar.

**O que você pode fazer:** dar nome ao caso, escolher o tipo pela natureza do comportamento,
determinar o ambiente e o comando do gate, apontar o arquivo onde ele cai, ligar o caso ao
requisito, e apontar a fixture que o barateia.

**O que você não pode fazer:** acrescentar caso que ele não pediu, desdobrar um caso dele em três
"pra ficar completo", ou promover a tipo mais caro do que o comportamento exige. Caso que você acha
que falta não entra agora — vai pra crítica, no bloco certo, e volta a ele como decisão.

Se um item dele estiver ambíguo demais pra virar caso ("testar o fluxo de reembolso"), pergunte o
que especificamente deve dar certo ou errado. Uma pergunta, não um questionário.

### Tipo por necessidade

`unit` não é resposta automática. O tipo sai da natureza do comportamento:

| Sinal do requisito | Tipo |
|---|---|
| Lógica pura, função isolável, regra de cálculo | unit |
| Interação entre módulos, DB, fila, contrato de API interna | integração |
| Fluxo de usuário ponta a ponta, tela, rota HTTP completa | e2e |

Todo tipo carrega o **ambiente** que o gate exige (`none`, `server-local`, `browser-playwright`,
`sandbox`) — é o que diz à execução o que precisa subir antes de rodar.

## A crítica

Só agora as lentes entram, e entram **sobre a lista dele** — nunca sobre a spec crua. Lance três
subagentes **numa única resposta** (turnos separados serializam), `subagent_type: general-purpose`,
`model: opus`, cada um com este prompt:

> Leia `${CLAUDE_SKILL_DIR}/lenses.md` e assuma a lente **<Produto/QA | Engenharia | Adversarial>**.
> Você critica uma lista de cobertura que o usuário escreveu — não propõe uma nova.
> A spec está em `<caminho>`. A lista dele, já traduzida: `<matriz>`.
> Convenções de teste do projeto: `<sua síntese>`. Cobertura existente: `<inventário, com contagens
> e os abates que você achou>`. Componentes tocados: `<paths>`.

Antes de levar à tela, **verifique você mesmo** o que elas afirmam — a fixture existe mesmo? o teste
que a lente diz que já cobre cobre de verdade? o ambiente é mesmo exigido? Lente erra; descarte o
inválido registrando o motivo.

Duas coisas que a crítica **não** produz. Achado sem consequência concreta — "seria bom ter
cobertura de X" sem dizer o que quebra na prática — não chega à tela; devolva ou descarte.
E comportamento que a spec não promete não é buraco de cobertura: é **lacuna da spec**, vai como
aviso, e não vira caso.

## Tela 2 — os achados, e o default é fora

Sem teto de quantidade: ele vê tudo que a crítica achou, porque o panorama do risco é dele. Mas
**todo achado nasce fora da matriz** — entra só com um sim explícito. Ele não corta de uma lista
pronta; ele escolhe o que puxar pra dentro.

Três blocos, cada um ordenado por impacto:

- **Descoberto** — comportamento sem verificação nenhuma. Cada linha diz **o que quebra na prática**
  se ficar de fora, e o custo de cobrir. É o único bloco que aumenta a suíte.
- **Redundante** — caso dele que teste existente já cobre (`arquivo:linha`), ou dois casos dele que
  verificam a mesma coisa. Aqui você recomenda **tirar**.
- **Caro** — caso dele que sai mais salgado do que parece: ambiente novo, risco de flakiness, setup
  pesado. Sempre com a alternativa mais barata ao lado, quando existir.

Resolva **um por vez**, em ordem de impacto, com o trade-off numa linha e **sua recomendação
explícita**. Opções discretas vão em `AskUserQuestion` com a recomendação primeiro; pergunta aberta
vai em texto.

O que governa a discussão:

- **A escolha dele vence**, inclusive contra as três lentes. Registre o risco aceito numa linha e
  siga — sem reabrir o ponto.
- **Recusar achado não pede justificativa.** "Não quero" fecha o item e vira linha de risco aceito.
  Exigir motivo pra não cobrir é o atrito que fez a suíte inchar.
- **Caso cortado vira dívida registrada**, com o motivo se ele deu.
- **Requisito caminhando pra ficar sem verificação** dispara a pergunta da regra acima.
- Se a decisão abrir tipo ou ambiente que nenhuma lente avaliou, rode **só a lente de Engenharia**
  de novo pra conferir custo e mock. Não repita o trio por isso.

## Onde escrever

Seção `## Testes` de `<root>/thoughts/changes/<NNN>-<slug>/plan.md` — crie o arquivo com apenas essa
seção se ele ainda não existe. **`root` é o repositório principal** (`git worktree list | head -1`),
porque `thoughts/` é gitignored e não existe dentro da worktree.

Todo caso carrega a origem: `[usuário]` pro que veio do rascunho dele, `[lente]` pro que veio da
crítica e ele aceitou. As duas marcas juntas mostram, PR a PR, quanto da suíte ele decidiu e quanto
a máquina empurrou.

```markdown
## Testes

Baseline: <N> testes nos componentes tocados → <M> depois (+<K>)
Ambiente exigido: <none | server-local | browser-playwright | sandbox>
Origem: <X> casos [usuário] · <Y> casos [lente] · <Z> comportamentos já cobertos (abatidos)

| Req | Tipo | Casos | Ambiente | Gate |
|---|---|---|---|---|
| R1 | unit | happy, valor negativo `[usuário]` | none | `npm test refund` |
| R2 | — | já coberto por `test/refund.spec.ts:40` | — | — |
| R3 | integração | timeout do gateway `[lente]` | sandbox | `npm run test:int` |

### Decisões
| # | Ponto | Decisão | Quem decidiu | Motivo / risco aceito |
|---|---|---|---|---|
| 1 | R3: tipo | integração | usuário | e2e ficaria flaky no gateway |

### Dívida e risco aceito
- <achado que ele recusou, com o motivo se deu>
- <caso cortado por redundância>
- <lacuna pré-existente que continua sem rede>
```

A contagem `+K` é **piso, não meta**. Ela existe pra que a suíte não encolha em silêncio rio abaixo
— nunca pra medir se o plano foi bom. Plano bom é o que ele consegue defender caso a caso.

## Ao terminar

Uma tela curta: cobertura antes → depois por tipo, ambiente exigido, quantos casos vieram dele e
quantos da crítica, o que foi abatido por já existir, e a dívida que ficou. Depois:

> Vou passar isto pro `plan`, e cada tarefa herda daqui tipo, ambiente e gate.

A quebra de tarefas **não reinventa** a estratégia de teste — ela herda esta matriz.
