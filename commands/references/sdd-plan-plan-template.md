# Reference: template do PLAN tecnico (/sdd-plan)

> Carregado sob demanda pelo `/sdd-plan` no momento de escrever o doc (Passo 11+).
> Caminho do output: `thoughts/plans/PLAN-DD-MM-YYYY-NNN-[slug].md`
> O PLAN e o COMO (pesquisa + tarefas). O QUE (comportamento) vive na SPEC referenciada.

```markdown
---
date: DD-MM-YYYY (UTC-3)
scope: Medium | Large | Complex
spec: thoughts/specs/spec-<ts>-<slug>.md   # SPEC de comportamento que originou este plano
issue: [link se aplicavel]
skills: [lista]
---

# PLAN: [Titulo]

## Resumo Executivo

> Escreva por ultimo. Cada bullet deve corresponder a conteudo real das secoes.

**O que vamos implementar**: [2-3 linhas]
**Estrategia geral**: [2-3 linhas]
**Tarefas (visao de cima)**:
- Foundation: [T1 — entrega, T2 — entrega]
- Core: [T3 [P] — entrega, T4 [P] — entrega]
- Integration: [T5 — entrega]
**Riscos principais**: [bullets]
**Pre-requisitos**: [decisoes tecnicas resolvidas, dependencias externas]

---

## 1. SPEC de Referencia

**SPEC**: `thoughts/specs/spec-<ts>-<slug>.md`

> Resumo do comportamento especificado (1 paragrafo). RFs e ATs que este PLAN implementa.
> Se nao houve SPEC formal, registre aqui: "Sem SPEC formal — entendimento derivado da conversa + codebase".

| RF/AT da SPEC | O que exige |
|---|---|
| RF1 | [comportamento] |
| AT1 | [cenario de aceite] |

---

## 2. Decisoes Tecnicas

> Decisoes de implementacao resolvidas no planejamento (NAO comportamento — isso e da SPEC).

| Questao tecnica | Decisao | Justificativa | Fonte |
|---|---|---|---|
| [pergunta] | [resposta] | [por que] | [Fonte: ...] |

---

## 3. Analise Local

### 3.1 Componentes envolvidos
[Arquivos, modulos, funcoes — com paths e linhas]

### 3.2 Dependencias e padroes existentes
[Libs ja instaladas + padroes reusaveis]

### 3.3 Design docs existentes (reconciliacao)

| Doc | Status | Como o PLAN se relaciona |
|---|---|---|
| [path] | RELEVANTE | [referencia/respeita/atualiza] |
| [path] | DESATUALIZADO | [conflito resolvido, ver Decisoes Tecnicas] |

---

## 4. Referencias Externas

**[Omita esta secao se escopo Medium sem pesquisa externa.]**

| Tema | Fonte | Resumo |
|---|---|---|
| [tema] | [Fonte: url] | [insight relevante para o design] |

---

## 5. Diagrama

[Mermaid — arquitetura das mudancas; obrigatorio para Large/Complex, opcional para Medium]

---

## 6. Plano de Testes

> Fechado **em par com o usuario** no Passo 7.5 do /sdd-plan (Mapa de Testes em tela → discussao → decisoes). Precede e guia a quebra de tarefas — cada tarefa herda seu tipo, ambiente e casos daqui.

### 6.1 Convencoes do projeto

- **Framework/runner**: [jest, vitest, go test, playwright...] + comando de cada tipo
- **Estrutura e naming**: [describe/it, table-driven, AAA...]
- **Mocking**: [o que mocka vs usa real]
- **Fixtures/factories**: [disponiveis a reusar]
- **Onde ficam**: [co-location vs pasta] por tipo
- **Ambiente por tipo**: [server local + porta / browser-playwright / sandbox-DB / nenhum]

### 6.2 Cobertura existente (baseline)

| Componente tocado | Ja testado por | O que cobre hoje | Testes |
|---|---|---|---|
| `path/to/x.ts` | `x.spec.ts` | happy path de ... | 6 |
| `path/to/y.ts` | — | sem teste | 0 |

Baseline: [N] testes nos componentes tocados.

### 6.3 Matriz de testes novos (fechada em par)

| RF/AT | Comportamento a exercitar | Tipo | Casos (happy/edge/negativo/erro) | Como / Ambiente | Prio | Ja coberto? |
|---|---|---|---|---|---|---|
| RF1 | ... | unit | happy + valor zero + negativo | mock do repo X / none | critico | nao |
| AT2 | ... | e2e | login valido + credencial invalida `[fonte: usuario]` | server-local :3000 + Playwright | importante | parcial |

> **Tipo por necessidade**, nao default unit: logica pura → unit; interacao entre modulos/DB → integracao; fluxo de usuario/tela/rota → e2e.
> `[fonte: usuario]` marca caso que o usuario adicionou no pair — conhecimento de produto que as lentes nao tinham.

### 6.4 Gaps

[RF/AT que a SPEC exige e hoje NAO tem teste — cada um vira teste novo numa tarefa.]

### 6.5 Decisoes do pair de testes

| # | Ponto | Decisao | Quem decidiu | Motivo / risco aceito |
|---|---|---|---|---|
| 1 | RF3: tipo (integracao vs e2e) | integracao | usuario | e2e ficaria flaky no gateway |
| 2 | AT2: 2 casos de borda | cortados | usuario | nao acontece na pratica |

### 6.6 Divida e risco aceito

- **Casos cortados**: [caso — motivo dado pelo usuario]
- **RF/AT sem teste**: [ancora — justificativa; a tarefa nasce com `Tests: none` justificado]
- **Lacunas pre-existentes (fora de escopo)**: [componente — sugestao: item separado no roadmap]
- **Risco que sobra apos este PR**: [o que continua sem rede de protecao]

### 6.7 Pra onde caminhamos

- Cobertura: [N] testes hoje → [M] depois (+[K]) — [a unit / b integracao / c e2e]
- Ambiente novo exigido: [sandbox / Playwright / nenhum]
- Custo de suite: [sinal de tempo — e2e novo pesa no CI]

---

## 7. Tarefas

### Phase 1: Foundation (Sequencial)

T1 → T2

### Phase 2: Core (Parallel-friendly)

```
T2 ──┬─→ T3 [P]
     ├─→ T4 [P]
     └─→ T5 [P]
```

### Phase 3: Integration (Sequencial)

T3, T4, T5 → T6

---

#### T1: [Titulo]

- [ ] **What**: [1 frase — entrega exata]
- **Covers**: RF1, AT1
- **Where**: `path/to/file.ext`
- **Depends on**: None
- **Reuses**: [path:line]
- **Skills**: [lista]
- **Riscos**: [se aplicavel, senao omita]
- **Tests**: unit | integration | e2e | none  (herdado da matriz 6.3; justifique se none)
- **Test env**: none | server-local | browser-playwright | sandbox  (herdado da matriz; o que o executor sobe antes do gate)
- **Test count**: N tests
  - [descricao do teste 1]
  - [descricao do teste 2]
- **Gate**: `comando exato`
- **Done when**:
  - [ ] [criterio especifico testavel]
  - [ ] Gate passa: N tests pass (no silent deletions)
- **Commit**: `feat(escopo): descricao`

#### T2: [Titulo] [P]

[mesma estrutura]

---

## 8. Parallel Execution Map

```
Phase 1 (Sequencial): T1 → T2
Phase 2 (Paralelo apos T2):
  ├── T3 [P]
  ├── T4 [P]
  └── T5 [P]
Phase 3 (Sequencial): T3, T4, T5 → T6
```

[Omita se nao houver paralelizacao — apenas declare "Sem paralelizacao" em 1 linha.]

---

## 9. Cobertura da SPEC

| RF/AT da SPEC | Coberto por | Status |
|---|---|---|
| RF1 | T1 | OK |
| RF2 | T3 | OK |
| AT1 | T1 | OK |
| AT2 | T4 | OK |

[Todo RF/AT da SPEC tem ≥1 tarefa. Lacuna aqui = plano incompleto.]

---

## 10. Simplificacao

Ao executar este plano, `/executor-plan`:
- Ao fim de cada tarefa (apos testes verdes, antes do commit): pergunta se passa o subagent `code-simplifier`
- Apos todas as tarefas: oferece passada final do simplifier

Confirmacao a cada vez — usuario decide tarefa a tarefa.

---

## 11. Validacao Pre-Aprovacao (4 checks)

| Check | Status |
|---|---|
| Granularity | PASS |
| Diagram-Definition Cross-Check | PASS |
| Test Co-location | PASS |
| SPEC Coverage | PASS |

[Se houve VIOLACAO em alguma tabela, mostre o detalhe da reestruturacao aqui.]

---

## 12. Duvidas Pendentes

[Itens `[NEEDS VERIFICATION]` e claims sem fonte que nao bloqueiam mas precisam ser validados durante execucao]

---

## 13. Verificacao de Links

| URL | Status |
|---|---|
| [url] | OK |
```
