---
name: test-plan
description: Fecha o que a mudança garante. A skill propõe a matriz de cobertura com o motivo de cada caso escrito — o que quebra sem ele — e você revisa caso a caso, cortando o que não quer. Três lentes criticam a proposta depois. Não escreve teste nenhum.
disable-model-invocation: true
argument-hint: <pasta da mudança em thoughts/changes/, ou nada pra usar a mais recente>
allowed-tools: Read Grep Glob Write Edit Agent AskUserQuestion Bash(ls *) Bash(git log*) Bash(git worktree list*) Bash(structure-cache *) Bash(structure-cache)
---

# test-plan

Fecha **o que esta mudança garante** — antes de qualquer tarefa ser quebrada e antes de qualquer
teste existir. Você não escreve teste aqui; escreve a decisão sobre quais vão existir.

**A ordem é: você propõe, ele corta.** Escrever a lista do zero custava a ele o trabalho que esta
skill existe pra fazer — mas revisar lista pronta só é revisão de verdade se cada linha disser
**por que existe**. Sem isso vira carimbo, e carimbo é pior que a lista que ele escreveria.

**Por isso a regra que sustenta todo o resto: nenhum caso entra na matriz sem a linha do que
quebra sem ele** — concreta, no sistema dele, não "garante o comportamento". Caso cujo motivo
você não consegue escrever não é caso: é volume, e some antes de chegar à tela.

É também o filtro que substitui a antiga trava. A suíte não incha porque o inchaço não passa
pelo motivo escrito.

**Leia `${CLAUDE_SKILL_DIR}/../triage/prosa.md` antes da Tela 1.** Ela governa como se escreve o
motivo, e é o que separa revisão de carimbo. A seção "A pergunta" dela governa **cada caso que
você leva a ele** — na revisão da Tela 1, nos achados da Tela 2, na pergunta do requisito sem
verificação. "Abate", "terreno", "matriz", "lente" e "ambiente" são o vocabulário desta peça, pra
você; na tela ele vê "já existe no código", "o que o projeto já testa hoje", "a lista de casos",
"um revisor olhando só X" e "o que precisa estar de pé pra rodar".

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

## Tela 1 — o terreno, e a matriz proposta

O terreno primeiro, a proposta depois — ele precisa do que já existe pra julgar o que você sugere:

1. **O que temos hoje** — componente, quem testa, o que cobre, contagem. Baseline total.
2. **O que já cobre esta mudança** — teste existente que ataca comportamento que esta mudança toca,
   com `arquivo:linha`. É o abate: comportamento que aparece aqui não precisa de caso novo.
3. **O que dá pra reusar** — fixtures, factories, helpers e o arquivo onde caso novo caberia, com
   paths. Cada linha com uma nota do que ela poupa.
4. **A matriz proposta** — um caso por linha, cada um com **o que quebra sem ele**.

Marque também as lacunas pré-existentes, separadas — não são desta mudança e não entram no escopo
a menos que ele peça.

Números reais, vindos do inventário. Sem dado, escreva `?` em vez de estimar.

### A linha do "sem ele, quebra"

É a coluna que faz a revisão ser possível, e a única difícil de escrever. Ela diz **o que passa a
acontecer no sistema** se o caso não existir — no vocabulário de quem usa, com o dado concreto:

```
❌ "garante o cálculo de estorno"          ← repete o título do caso
❌ "cobre o caminho de erro"               ← não diz o erro nem o que ele causa
❌ "boa prática, aumenta a confiança"      ← não é consequência, é opinião

✅ "estorno de 150 num pedido de 100 passa e vira saldo credor no cliente"
✅ "gateway cai, o pedido fica pago e sem refund registrado — ninguém percebe até o fechamento"
```

Se só sai a versão da esquerda, **o caso não entra**. Não force: some da proposta e, se você achar
mesmo que falta, ele reaparece pela crítica, onde a lente precisa provar a consequência.

### O que você não pode fazer

- **Desdobrar um comportamento em três casos "pra ficar completo".** Um comportamento, um caso,
  salvo quando os dois motivos escritos são de fato diferentes.
- **Promover a tipo mais caro** do que o comportamento exige — e2e onde unit resolve infla o gate
  e a chance de flake.
- **Propor caso pra comportamento que a spec não promete.** Isso é lacuna da spec, vai como aviso,
  e não vira linha da matriz.

Requisito ambíguo demais pra virar caso ("o fluxo de reembolso funciona") não vira três chutes:
pergunte o que especificamente deve dar certo ou errado. Uma pergunta, não um questionário.

## A revisão dele, um caso por vez

A matriz nasce **dentro**, e ele corta. É o inverso dos achados da crítica, que nascem fora — a
diferença é que a proposta já passou pelo filtro do motivo escrito, e o achado de lente ainda não.

- **Recusar não pede justificativa.** "Não quero" fecha o caso e vira linha de dívida. Exigir
  motivo pra não cobrir é o atrito que faz a suíte inchar por cansaço.
- **A escolha dele vence**, inclusive contra o motivo que você escreveu. Registre o risco aceito
  numa linha e siga, sem reabrir.
- **Caso que ele adiciona entra sem passar pelo seu crivo** — só traduza tipo, ambiente e gate, e
  peça a ele a linha do "sem ele, quebra" se não estiver óbvia.
- **Um por vez, em ordem de impacto.** Lista inteira de uma vez é o carimbo de volta.
- **Cada caso chega como escolha, não como linha de tabela.** O que quebra sem ele primeiro, o
  que custa escrever depois, e a sua recomendação — mantém ou corta. O tipo vai traduzido:

  ```
  ❌ R3 · timeout do gateway · integração · sandbox. Mantém?

  ✅ Se o gateway cair no meio do estorno, o pedido fica pago e sem estorno
     registrado — ninguém percebe até o fechamento do mês.
     Cobrir custa um teste que sobe um gateway de mentira (uns 10s a mais na
     suíte). Recomendo manter.
  ```

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

Só agora as lentes entram, e entram **sobre a matriz já revisada por ele** — com os cortes dele
dentro, nunca sobre a spec crua nem sobre a sua proposta original. O que ele tirou, tirou. Lance três
subagentes **numa única resposta** (turnos separados serializam), `subagent_type: general-purpose`,
`model: opus`, cada um com este prompt:

> Leia `${CLAUDE_SKILL_DIR}/lenses.md` e assuma a lente **<Produto/QA | Engenharia | Adversarial>**.
> Você critica uma matriz de cobertura já aprovada pelo usuário — não reescreve uma nova, e não
> reabre caso que ele cortou. Todo achado seu carrega **o que quebra na prática se ficar de fora**,
> concreto; sem isso ele não chega à tela.
> A spec está em `<caminho>`. A matriz, com os cortes dele: `<matriz>`.
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
**todo achado nasce fora da matriz** — entra só com um sim explícito. É o contrário da proposta
da Tela 1, e de propósito: aquela já passou pelo filtro do motivo escrito, esta ainda não.

Três blocos, cada um ordenado por impacto:

- **Descoberto** — comportamento sem verificação nenhuma. Cada linha diz **o que quebra na prática**
  se ficar de fora, e o custo de cobrir. É o único bloco que aumenta a suíte.
- **Redundante** — caso da matriz que teste existente já cobre (`arquivo:linha`), ou dois casos
  que verificam a mesma coisa. Aqui você recomenda **tirar** — inclusive caso que você propôs.
- **Caro** — caso da matriz que sai mais salgado do que parece: ambiente novo, risco de flakiness,
  setup pesado. Sempre com a alternativa mais barata ao lado, quando existir.

Resolva **um por vez**, em ordem de impacto, com o trade-off numa linha e **sua recomendação
explícita**. Opções discretas vão em `AskUserQuestion` com a recomendação primeiro; pergunta aberta
vai em texto. Nos dois casos, as quatro linhas da régua: a escolha, o que acontece se entra, o que
acontece se fica de fora, a recomendação — e nenhuma palavra que só este toolkit usa.

Valem aqui as mesmas regras da revisão da Tela 1 — a escolha dele vence, recusar não pede
justificativa, e o que ele cortar vira dívida registrada. Além delas:
- **Requisito caminhando pra ficar sem verificação** dispara a pergunta da regra acima.
- Se a decisão abrir tipo ou ambiente que nenhuma lente avaliou, rode **só a lente de Engenharia**
  de novo pra conferir custo e mock. Não repita o trio por isso.

## Onde escrever

Seção `## Testes` de `<root>/thoughts/changes/<NNN>-<slug>/plan.md` — crie o arquivo com apenas essa
seção se ele ainda não existe. **`root` é o repositório principal** (`git worktree list | head -1`),
porque `thoughts/` é gitignored e não existe dentro da worktree.

Todo caso carrega a origem: `[agente]` pro que você propôs e ele manteve, `[usuário]` pro que ele
acrescentou, `[lente]` pro que veio da crítica e ele aceitou. Registre também **quantos casos ele
cortou** — é o número que diz se a revisão está acontecendo ou se virou carimbo.

```markdown
## Testes

Baseline: <N> testes nos componentes tocados → <M> depois (+<K>)
Ambiente exigido: <none | server-local | browser-playwright | sandbox>
Origem: <X> [agente] · <Y> [usuário] · <Z> [lente] · <W> já cobertos (abatidos) · <C> cortados por ele

| Req | Caso | Tipo · Ambiente | Sem ele, quebra | Origem |
|---|---|---|---|---|
| R1 | estorno maior que o pedido | unit · none | estorno de 150 num pedido de 100 passa e vira saldo credor | agente |
| R2 | — | — | já coberto por `test/refund.spec.ts:40` | — |
| R3 | timeout do gateway | integração · sandbox | pedido fica pago e sem refund registrado até o fechamento | lente |

Gate: `npm test refund` (unit) · `npm run test:int` (integração)

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

Uma tela curta: cobertura antes → depois por tipo, ambiente exigido, **quantos casos você propôs,
quantos ele cortou e quantos ele acrescentou**, o que foi abatido por já existir, e a dívida que
ficou. O número de cortes é o que mostra se ele revisou de fato. Depois:

> Vou passar isto pro `plan`, e cada tarefa herda daqui tipo, ambiente e gate.

A quebra de tarefas **não reinventa** a estratégia de teste — ela herda esta matriz.
