# Reference: template do SPEC (/sdd-plan)

> Carregado sob demanda pelo `/sdd-plan` no momento de escrever o doc (Passo 11+).
> Caminho do output: `thoughts/plans/SPEC-DD-MM-YYYY-NNN-[slug].md`

```markdown
---
date: DD-MM-YYYY (UTC-3)
scope: Medium | Large | Complex
issue: [link se aplicavel]
skills: [lista]
---

# SPEC: [Titulo]

## Resumo Executivo

> Escreva por ultimo. Cada bullet deve corresponder a conteudo real das secoes.

**O que vamos implementar**: [2-3 linhas]
**Estrategia geral**: [2-3 linhas]
**Tarefas (visao de cima)**:
- Foundation: [T1 — entrega, T2 — entrega]
- Core: [T3 [P] — entrega, T4 [P] — entrega]
- Integration: [T5 — entrega]
**Riscos principais**: [bullets]
**Pre-requisitos**: [decisoes resolvidas, dependencias externas]

---

## 1. Entendimento

[O que entendi do problema e como vou resolver — 1 paragrafo]

---

## 2. Decisoes Resolvidas

| Questao | Decisao | Justificativa | Fonte |
|---|---|---|---|
| [pergunta] | [resposta] | [por que] | [Fonte: ...] |

**[Apenas para escopo Complex]**: incluir transcricao curta da sessao de discussao se houve gray areas resolvidas com usuario.

---

## 3. Analise Local

### 3.1 Componentes envolvidos
[Arquivos, modulos, funcoes — com paths e linhas]

### 3.2 Dependencias e padroes existentes
[Libs ja instaladas + padroes reusaveis]

### 3.3 Design docs existentes (reconciliacao)

| Doc | Status | Como o spec se relaciona |
|---|---|---|
| [path] | RELEVANTE | [referencia/respeita/atualiza] |
| [path] | DESATUALIZADO | [conflito resolvido, ver Decisoes] |

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

## 9. Simplificacao

Ao executar este plano, `/executor-plan`:
- Ao fim de cada tarefa (apos testes verdes, antes do commit): pergunta se passa o subagent `code-simplifier`
- Apos todas as tarefas: oferece passada final do simplifier

Confirmacao a cada vez — usuario decide tarefa a tarefa.

---

## 10. Validacao Pre-Aprovacao (3 checks)

| Check | Status |
|---|---|
| Granularity | PASS |
| Diagram-Definition Cross-Check | PASS |
| Test Co-location | PASS |

[Se houve VIOLACAO em alguma tabela, mostre o detalhe da reestruturacao aqui.]

---

## 11. Duvidas Pendentes

[Itens `[NEEDS VERIFICATION]` e claims sem fonte que nao bloqueiam mas precisam ser validados durante execucao]

---

## 12. Verificacao de Links

| URL | Status |
|---|---|
| [url] | OK |
```
