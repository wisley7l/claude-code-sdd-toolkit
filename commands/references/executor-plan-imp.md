# Reference: template do relatório IMP (/executor-plan)

> Carregado sob demanda pelo `/executor-plan` ao final da execução.
> Caminho do output: `thoughts/history/IMP-DD-MM-YYYY-[slug].md`

```markdown
# Implementacao: [Nome]

Data: DD-MM-YYYY
PLAN: [caminho]
[DESIGN: caminho, se aplicavel]

## O que foi feito

[Resumo das tarefas executadas, agrupadas por phase]

## Diagrama

[Mermaid — o que foi adicionado/modificado e como conecta]

## Testes

- Unitarios: [N testes em thoughts/tests/]
- Integracao: [N testes, se aplicavel]
- Test count: [baseline X / esperado Y / final Z — PRESERVADO]
- Todos passando: sim/nao

## Complexidade

- Threshold: [10 default / N declarado no CLAUDE.md] — ferramenta: [linter do projeto / lizard / fta / nao rodou]
- Funcoes corrigidas pelo gate: [lista arquivo:funcao CC antes → depois, ou "nenhuma violacao"]
- Dividas aceitas pelo usuario: [lista + justificativa, ou "nenhuma"]

## Paralelismo Utilizado

- Tarefas executadas em paralelo: [N tarefas em phase Core]
- Tempo aproximado economizado vs. sequencial: [estimativa]

## Desvios do Plano

[Mudancas que surgiram durante e por que. Inclui SPEC_DEVIATION reportados por sub-agents]

## Memoria persistente

- Entradas adicionadas em $MEM_DIR: [N — listar tipos e slugs]
- Decisoes anotadas pra /sdd-learning pos-merge: [K — listar brevemente cada item + por que]

## Reconciliacao com Docs

- Docs do projeto atualizados: [lista, ou "nenhum precisou"]

## Observacoes

[Coisas que notei mas nao implementei — input para proxima iteracao]
```

## Verificação de links do relatório

Após escrever o IMP, lance subagente para verificar links (URLs em referências, docs):

1. Extraia URLs
2. `WebFetch` em cada, valide não-404
3. Adicione tabela final:

```markdown
## Verificacao de Links

| URL | Status |
|---|---|
| [url] | OK / QUEBRADO — [motivo] |
```

4. Para cada quebrado: pesquise alternativa, atualize ou remova com nota em "Observacoes"
5. Reescreva com correções
