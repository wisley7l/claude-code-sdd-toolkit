---
name: test-plan
description: Decide o que a mudança vai garantir — quais comportamentos ganham teste, de que tipo, em que ambiente, e o que fica sem rede de proteção. Sessão interativa em que você corta e prioriza. Não escreve teste nenhum.
disable-model-invocation: true
argument-hint: <pasta da mudança em thoughts/changes/, ou nada pra usar a mais recente>
allowed-tools: Read Grep Glob Write Edit Agent AskUserQuestion Bash(ls *) Bash(git log*) Bash(git worktree list*) Bash(structure-cache *) Bash(structure-cache)
---

# test-plan

Fecha **o que esta mudança garante** — antes de qualquer tarefa ser quebrada e antes de qualquer
teste existir. Você não escreve teste aqui; escreve a decisão sobre quais vão existir.

Teste é a codificação do comportamento esperado. Escolher sozinho quais cenários importam, o que
vale o custo e o que fica de fora é decidir produto sozinho. **O trabalho pesado é seu — inventário,
propostas, trade-offs. O corte, a prioridade e o risco aceito são do usuário.**

## A regra que não cede

**Todo requisito da spec sai daqui com uma forma de verificação.** Quando teste automatizado não
for viável, o piso é **verificação manual executada pelo usuário, com evidência registrada** — e
isso entra como dívida, não como pronto.

Requisito sem verificação de espécie alguma só existe depois de você **perguntar** e ele aprovar:

> R4 ficaria sem verificação de nenhum tipo, nem manual. Aprova assim?

Justificativa que você escreve sozinho não substitui essa pergunta.

## Antes de propor

Duas leituras, nesta ordem — sem elas a proposta é chute:

**Como o projeto testa.** Skills `.claude/skills/testing*` e 2–3 arquivos de teste vizinhos aos
componentes que a mudança toca. Extraia: framework e runner, **o comando de cada tipo**, estrutura
e naming, o que se mocka e o que é real, fixtures e factories disponíveis, onde os arquivos ficam,
e **que ambiente cada tipo exige** (server local — como sobe, em que porta? browser? sandbox?).

**O que já é testado.** Nos componentes que a mudança toca: que arquivo cobre o quê, a **contagem
baseline** por suíte (é ela que alimenta a proteção de contagem nas tarefas), fixtures reusáveis,
e as lacunas que **já existiam** ali — que não são desta mudança e não viram tarefa dela.

Delegue a varredura a um subagente `Explore` quando for ampla, **repetindo no prompt dele** a
diretiva de consultar o `structure-cache` antes de grepar. Subagente não herda estas instruções.

## As três lentes

Uma perspectiva só enxerga um recorte. Lance três subagentes **numa única resposta** (turnos
separados serializam), `subagent_type: general-purpose`, `model: opus`, cada um com este prompt:

> Leia `${CLAUDE_SKILL_DIR}/lenses.md` e assuma a lente **<Produto/QA | Engenharia | Adversarial>**.
> A spec está em `<caminho>`. Convenções de teste do projeto: `<sua síntese>`.
> Cobertura existente: `<inventário, com contagens>`. Componentes tocados: `<paths>`.

Antes de levar à tela: agrupe por requisito, deduplique casos equivalentes, e **verifique você
mesmo** o que elas afirmam — a fixture existe mesmo? o ambiente é mesmo exigido? Lente erra;
descarte o inválido registrando o motivo. Se as lentes apontarem comportamento que a spec não
cobre, isso é **lacuna da spec**, não teste novo: leve como aviso, não invente requisito.

## O mapa vai pra tela antes da discussão

Mostre o quadro inteiro antes de discutir qualquer ponto. É o que dá a visão de onde se está e
pra onde se caminha — e é o passo que não tem atalho, em nenhum tamanho de mudança.

Quatro blocos:

1. **O que temos hoje** — componente, quem testa, o que cobre, contagem. Baseline total.
2. **O que não temos** — separando *desta mudança* (vira teste novo) de *lacuna pré-existente*
   (fora de escopo, a menos que ele peça).
3. **O que esta mudança adiciona** — por requisito: tipo, casos, ambiente, prioridade, custo,
   marcado ✅ consenso · ⚠️ lentes divergem · ❓ precisa da decisão dele.
4. **Pra onde caminhamos** — cobertura antes → depois, ambiente novo exigido, peso no CI, o que
   fica de dívida e **qual risco sobra depois deste PR**.

Números reais, vindos do inventário. Sem dado, escreva `?` em vez de estimar.

Feche a tela perguntando se o quadro representa o que ele tem em mente. Se a resposta reenquadrar
a mudança ("esse fluxo nem é o principal"), isso é lacuna da spec — trate antes de seguir.

## Tipo por necessidade

`unit` não é resposta automática. O tipo sai da natureza do comportamento:

| Sinal do requisito | Tipo |
|---|---|
| Lógica pura, função isolável, regra de cálculo | unit |
| Interação entre módulos, DB, fila, contrato de API interna | integração |
| Fluxo de usuário ponta a ponta, tela, rota HTTP completa | e2e |

Todo tipo carrega o **ambiente** que o gate exige (`none`, `server-local`, `browser-playwright`,
`sandbox`) — é o que diz à execução o que precisa subir antes de rodar.

## A discussão

Os pontos ⚠️/❓ já estão visíveis. Resolva **um por vez**, em ordem de impacto, mostrando as
posições das lentes quando divergiram, o trade-off numa linha, e **sua recomendação explícita**.
Opções discretas vão em `AskUserQuestion` com a recomendação primeiro; pergunta aberta vai em
texto.

O que governa a discussão:

- **A escolha dele vence**, inclusive contra as três lentes. Registre o risco aceito numa linha e
  siga — sem reabrir o ponto.
- **Caso cortado vira dívida registrada**, com o motivo dele. Nada some em silêncio.
- **Caso que ele adiciona** e nenhuma lente propôs ganha `[fonte: usuário]` — é conhecimento de
  produto que você não tinha.
- **Requisito caminhando pra ficar sem verificação** dispara a pergunta da regra acima.
- Se a decisão abrir tipo ou ambiente que nenhuma lente avaliou, rode **só a lente de Engenharia**
  de novo pra conferir custo e mock. Não repita o trio por isso.

## Onde escrever

Seção `## Testes` de `<root>/thoughts/changes/<NNN>-<slug>/plan.md` — crie o arquivo com apenas essa
seção se ele ainda não existe. **`root` é o repositório principal** (`git worktree list | head -1`),
porque `thoughts/` é gitignored e não existe dentro da worktree.

```markdown
## Testes

Baseline: <N> testes nos componentes tocados → <M> depois (+<K>)
Ambiente exigido: <none | server-local | browser-playwright | sandbox>

| Req | Tipo | Casos | Ambiente | Gate |
|---|---|---|---|---|
| R1 | unit | happy, zero, valor negativo | none | `npm test refund` |
| R3 | integração | 4 casos `[fonte: usuário]` | sandbox | `npm run test:int` |

### Decisões
| # | Ponto | Decisão | Quem decidiu | Motivo / risco aceito |
|---|---|---|---|---|
| 1 | R3: tipo | integração | usuário | e2e ficaria flaky no gateway |

### Dívida e risco aceito
- <caso cortado, com o motivo dele>
- <lacuna pré-existente que continua sem rede>
```

## Ao terminar

Uma tela curta: cobertura antes → depois por tipo, ambiente exigido, quantos pontos ele decidiu
(quantos cortes, quantos casos que ele adicionou), e a dívida que ficou. Depois:

> Vou passar isto pro `plan`, e cada tarefa herda daqui tipo, ambiente e gate.

A quebra de tarefas **não reinventa** a estratégia de teste — ela herda esta matriz.
