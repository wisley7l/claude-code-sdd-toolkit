# Créditos — skill `test-plan`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

Extraída do **Passo 7.5 do `/sdd-plan` v9** e do seu reference `sdd-plan-testes.md` (311 linhas),
que são material do próprio repositório — mas o command que os hospedava declarava conceitos
adaptados de **tlc-spec-driven** (tech-leads-club/agent-skills) por Felipe Rodrigues,
**CC-BY-4.0**, cuja atribuição é obrigatória e permanente inclusive em reescrita.

Conceitos dessa fonte presentes aqui:

- **Test co-location** — a verificação pertence à mesma tarefa que cria o código.
- **Test count protection** — a contagem baseline levantada no inventário é o que alimenta o
  `N → M testes` das tarefas.

O restante do Passo 7.5 (as cinco etapas, as três lentes, o Mapa de Testes em quatro blocos, a
tabela de decisões com autoria) é construção nossa, sem equivalente em nenhuma das fontes
mapeadas — e foi a única parte do v9 em que o usuário decidia de verdade, o que explica
retroativamente por que sobreviveu inteira ao refactor.

## O que mudou do v9

- **Skill própria**, não passo dentro do `plan`. Ganho por sequência (critério b da Parte C do
  `REFACTOR-v10.md`): esconder a quebra de tarefas atrás do mapa fechado é o que impede conclusão
  prematura — no v9 isso dependia de um guardrail em prosa ("Etapa 3 não tem atalho") escrito no
  mesmo arquivo que descrevia a quebra.
- **A saída continua no `plan.md`**, como seção `## Testes`. Peça própria não implica arquivo
  próprio, e o usuário pediu explicitamente menos arquivos por mudança (31-07-2026).
- **Flags `--rapido` / `--solo` removidas.** Calibravam o número de lentes (3 / 2 / 0). Viraram
  ajuste que não muda decisão nenhuma — e `--solo` com 0 lentes já mantinha as etapas obrigatórias,
  o que denuncia que a flag cortava só diversidade de proposta.
- **⭐ `Tests: none` deixou de ser saída do agente.** No v9 um requisito podia ficar sem teste com
  "justificativa explícita", escrita pelo próprio agente e cobrada pelo Check 3. **Decisão do
  usuário em 31-07-2026:** *"para haver um plano sem teste tem que ser aprovado explicitamente por
  mim"* — com o agente perguntando, não assumindo. O piso passa a ser verificação manual executada
  por ele com evidência registrada; ausência total exige pergunta e OK.

## Divergência consciente com o OpenSpec

No OpenSpec **testes não são artefato formal**. Cenários são descritos como *"testable (you could
write an automated test for them)"*, mas a cobertura só é olhada **depois do código**, pelo
`/opsx:verify`, que reporta `"Scenario 'Respects the OS preference on first load' has no test
coverage"` como WARNING — e a doc afirma literalmente **"Does not block archive."**

Aqui é o oposto em três eixos: a cobertura é decidida **antes** da quebra de tarefas, é **decidida
pelo usuário** e não pelo agente, e **bloqueia**. Este é o ponto em que o toolkit é
deliberadamente mais forte que a referência, e o motivo está na Parte E.5 do `REFACTOR-v10.md`:
red verificável e test count protection são invariantes que nenhuma das fontes tem.

## Redesenho de 25-08-2026 — a ordem invertida

A skill escrita em 31-07 gerava a cobertura e pedia carimbo. O usuário voltou com a queixa que
motivou a inversão: *"tá crescendo demais os testes, talvez poderia aproveitar, e eu tô perdendo a
mão nos testes."*

Agora a skill levanta o terreno e para. Ele escreve o rascunho de uma vez; as três lentes viram
crítica da lista dele, com saída em `descoberto` / `redundante` / `caro` — dois dos três blocos
reduzem a suíte. Achado de crítica nasce fora da matriz e entra só com um sim dele.

O contrato de saída não mudou (`plan` e `implement` dependem dele). A regra da E.5 também ficou:
reexaminada, ela não é a causa da inflação — o piso dela é verificação manual, que comprime.

Análise completa em I.41 do `REFACTOR-v10.md`.
