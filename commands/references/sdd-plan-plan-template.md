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

## 6. Estrategia de Testes

- **Unitarios**: [convencao + caminho]
- **Integracao**: [se aplicavel]
- **Compile-time**: [se houver cross-check tipo `satisfies`]
- **Convencao do projeto**: [jest, vitest, go test, etc]

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
- **Tests**: unit
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
