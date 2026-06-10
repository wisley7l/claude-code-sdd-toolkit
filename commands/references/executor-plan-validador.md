# Reference: prompt do validador independente (/executor-plan, Verificação Final)

> Carregado sob demanda pelo `/executor-plan` apenas quando modo-livre ATIVO + modo autônomo.
> Spawn: `Agent` com `subagent_type: general-purpose`, `model: haiku`, `description: "Validar conclusao do plano"`.

Template do prompt (substitua placeholders):

```
Voce e um validador independente. NAO execute codigo. NAO leia arquivos alem dos
explicitamente listados abaixo. Sua tarefa: confirmar se a execucao do plano abaixo
terminou com sucesso, com base na evidencia que listo.

Plano: <path absoluto do SPEC>
Tarefas esperadas: <N>

Checagem 1 — Marcacoes [x] no SPEC:
- Leia o arquivo do plano (so esse).
- Conte linhas `- [x]` em secao de tarefas vs total.
- Esperado: <N>/<N> tarefas marcadas.

Checagem 2 — Test count:
- Baseline inicial declarado: <X> testes
- Test count esperado pos-execucao: <Y> testes
- Test count reportado pelo executor no ultimo passo: extrair da transcript ("Test count: ...").
- Esperado: atual >= Y. Cair = falha.

Checagem 3 — Gate (typecheck/lint):
- Comando do gate (declarado em CLAUDE.md): <comando>
- Ultimo resultado reportado pelo executor: extrair da transcript.
- Esperado: green/passou.

Checagem 4 — Staging:
- `git diff --cached --stat` ja foi reportado na transcript pelo executor?
- Esperado: lista arquivos coerentes com os declarados nas tarefas.

Checagem 5 — Sinais de parada dura:
- A transcript mostra SPEC_DEVIATION, blocker nao resolvido, ou test count drop?
- Esperado: nenhum.

Retorne JSON estrito (sem markdown, sem narrativa):

{
  "complete": true | false,
  "checks": {
    "spec_marks": "ok" | "missing N tasks",
    "test_count": "ok" | "dropped from X to Y",
    "gate": "ok" | "failed" | "not reported",
    "staging": "ok" | "missing files" | "not reported",
    "hard_stops": "none" | "<descricao>"
  },
  "reason": "<1-2 frases>"
}
```

## Mensagem ao usuário quando `complete: false`

```
⚠️ Validador independente reportou execucao incompleta.

Checks:
  spec_marks: <status>
  test_count: <status>
  gate:       <status>
  staging:    <status>
  hard_stops: <status>

Razao: <reason>

O que fazer?
  (a) Voltar e tentar resolver o que falta (eu identifico e retomo a execucao)
  (b) Aceitar como esta e seguir pro review humano (assumindo risco)
  (c) Marcar como parada dura e finalizar com aviso

[a/b/c]
```
