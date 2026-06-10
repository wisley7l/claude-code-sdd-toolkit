# Reference: Action Plan — execução dos fixes (/sdd-review, Etapa 6)

> Carregado sob demanda pelo `/sdd-review` apenas quando há issues must-fix (CRITICAL/MAJOR) e o usuário escolheu gerar fixes.

## Execução por opção

**Se (a) autônomo em cadeia ou (b) pausando entre cada**: para cada must-fix selecionada (todas em a/b; subset em c):

1. Crie `<root>/thoughts/quick/NNN-fix-<slug>/TASK.md` com conteúdo derivado da issue:
   - Descrição: o "Descrição" + "Impacto" da issue
   - Por que: vem do contexto da issue
   - Passos: rascunho da sugestão de correção
   - Arquivos esperados: arquivo da issue
   - TDD aplicável: sim se for código de lib/domínio; não se for typo/config
   - Gate: comando do projeto (typecheck/lint/test conforme CLAUDE.md)
   - Skills: skills do projeto relevantes ao arquivo modificado

2. **Invoque o quick-task via Agent subagent**:
   - `subagent_type: general-purpose`
   - Prompt contém: o TASK.md, o conteúdo de `quick-task.md` (carregado via Read), o modo (`autonomo-invocado` ou `step-invocado`), instrução "não commite — só `git add` ao final" (em ambos os modos invocados)
   - Subagent segue o protocolo do quick-task com as adaptações do modo invocado
   - Subagent retorna: status (Complete/Blocked/Partial), files changed, gate result, test count, observações

3. **Acumule resultados**. Se uma fix bloquear (escopo cresceu, decisão arquitetural surgiu), pare a cadeia e mostre ao usuário:
   ```
   Fix [N/M] bloqueada: [motivo]
   Sugestão do quick-task: escalar para /sdd-plan
   Continuo com as próximas ([X] restantes) ou paro? [continuar/parar]
   ```

**Se (c)**: liste as must-fix com checkboxes, peça seleção, depois mesmo fluxo de (a) ou (b) — pergunte qual modo após a seleção.

**Se (d)**: só crie os `TASK.md` em `thoughts/quick/NNN-fix-<slug>/`. Liste paths ao final. Termine sem invocar quick-task.

**Se (e)**: termine sem ação.

## Regression check após aplicar fixes (opt-in se ≥3 fixes)

Se a cadeia (a/b/c) aplicou **3 ou mais fixes com sucesso**, ofereça regression check antes de concluir:

```
[N] fixes aplicadas (staged, não commitadas).

Rodar regression check pra garantir que nada quebrou?
  (a) Sim — rodar gate do projeto (typecheck/lint declarado em CLAUDE.md)
  (b) Sim — gate + reanalisar arquivos tocados com Agente 2 (Bugs) só
  (c) Não — confio nos fixes, segue pro resumo final

[a/b/c]
```

**Se (a)**: rode o comando declarado em CLAUDE.md. Se passar, ✅ no resumo. Se falhar, reporte qual passo introduziu o problema (use o tracking de arquivos por fix do quick-task) e pergunte se reverte ou pede `/quick-task` pra corrigir.

**Se (b)**: roda (a) + dispara **só o Agente 2 (Bugs)** com o diff atualizado (após fixes). Reporta novos achados se houver — eles entram como anexo no relatório, não substituem o original.

**Se (c)**: pula direto pro resumo.

**Se a cadeia aplicou <3 fixes**: pule o regression check (custo > benefício pra pouca mudança).
