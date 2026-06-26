---
description: Modo rapido — mudanca pequena sem PLAN formal (bug fix, config, tweak). Suporta modos invocados por /sdd-review que NUNCA commitam, so fazem `git add`.
model: claude-sonnet-4-6
allowed-tools: Read, Edit, Write, Glob, Grep, Agent, Skill, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(git fetch*), Bash(git add*), Bash(git commit*), Bash(gh *), Bash(npm *), Bash(npx *), Bash(bun *), Bash(bunx *), Bash(pnpm *), Bash(node *), Bash(go *), Bash(ls *), Bash(mkdir *), WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs
# Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe Rodrigues
# https://github.com/tech-leads-club/agent-skills
# Conceitos adaptados: Quick mode com safety valve
---

# Quick Task — Modo Rapido

Voce executa **mudancas pequenas** sem rodar PLAN formal. Use quando:
- ≤3 arquivos alterados
- Descricao cabe em 1 frase
- Sem decisao arquitetural nova
- Sem dependencia entre passos
- Bug fix, ajuste de config, typo, rename simples

**Se o escopo crescer durante a execucao, voce sobe para o fluxo formal.**

## Modos de execucao

| Modo | Quando | Comportamento |
|---|---|---|
| **manual** (default) | Invocado pelo usuario direto via `/quick-task` | Confirmacoes interativas; commit atomico ao final |
| **autonomo-invocado** | Chamado por outro command (ex: `/sdd-review` Etapa 6) com flag de autonomia | Pula confirmacoes nao-bloqueantes; **so faz `git add`, NUNCA commita** — staging fica acumulado para o caller resolver |
| **step-invocado** | Chamado por outro command com flag de pausa | Mantem confirmacoes; **so faz `git add`, NUNCA commita** |

**Como detectar o modo**: o prompt do subagent que invoca o quick-task declara explicitamente o modo (`mode: autonomo-invocado` ou `mode: step-invocado`). Se o prompt nao declara modo, assuma `manual`.

**Paradas duras (sempre param em qualquer modo)**: safety valve (>5 passos, decisao arquitetural, nova lib, >3 arquivos), test count drop, gate falhando, sem fonte verificavel para claim externa.

## Principios

- **Baixa ceremonia**: 1 arquivo de input (`TASK.md`) + 1 de output (`SUMMARY.md`)
- **Safety valve**: se passos passarem de 5 OU surgir decisao arquitetural OU dependencia nao obvia, PARE e sugira `/sdd-plan`. **Vale em todos os modos.**
- **TDD quando aplicavel**: codigo de lib/dominio = TDD obrigatorio. Config/typo = nao
- **Memoria persistente leve**: leia `MEMORY.md` (ja carregado pelo harness) para nao repetir blockers conhecidos. Detalhes: skill `memory-keeper`
- **Zero Inferencia**: API externa = verifique antes (Context7/WebFetch). Sem verificacao = pare
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` mesmo no quick mode
- **Modos invocados nunca commitam**: em `autonomo-invocado` e `step-invocado`, `git add` ao final substitui `git commit`. O caller decide quando/como commitar.

## Resolucao do diretorio root

```bash
git worktree list | head -1 | awk '{print $1}'
```

Use esse caminho como base para `thoughts/`.

## Configuracao Inicial

### 1. Modelo

Quick mode roda na **base Sonnet** (sem `model: opus` no topo). Mudanca pequena (≤3 arquivos, 1 frase, sem decisao arquitetural) nao justifica Opus — e se o escopo crescer a ponto de exigir julgamento profundo, o safety valve (Passo 3) ja manda pro `/sdd-plan`. **Nao rode `/model opus`**: trocar de modelo invalida o cache de prompt e gasta token a toa. Em modo `autonomo-invocado` ou `step-invocado`, respeite o modelo que o caller ja definiu (nao force troca).

### 2. Receber a Demanda
Se nao descreveu:
```
O que voce quer fazer? (1 frase)
Lembre: quick mode e para mudanca pequena. Se for feature, use /sdd-plan.
```

### 3. Validar se cabe em quick mode

Antes de criar TASK.md, avalie:

| Sinal | OK quick mode? |
|---|---|
| Descricao cabe em 1 frase | Sim |
| Imagina ≤3 arquivos afetados | Sim |
| Sem decisao arquitetural | Sim |
| Sem nova lib/dependencia | Sim |
| Sem migracao de schema | Sim |
| Sem decisao de design | Sim |
| >3 dos sinais acima negativos | Use `/sdd-plan` |

Se duvidoso:
```
Esta mudanca parece [pequena/media]. Confirmar quick mode ou prefere fluxo formal (/sdd-plan)?
```

### 4. Ler context minimo
- `CLAUDE.md`
- `ARCHITECTURE.md`
- Memoria persistente — so blockers conhecidos. Pelo `MEMORY.md` ja carregado, identifique linhas da secao `## Blocker` e abra so as relevantes. Ver skill `memory-keeper`.
- Skills aplicaveis em `.claude/skills/`

### 5. Decidir o numero da task

Liste `thoughts/quick/`:
```bash
ls thoughts/quick/ 2>/dev/null | grep -E '^[0-9]+' | sort -n | tail -1
```

Use o proximo numero (3 digitos: 001, 002, ...).

### 6. Detectar agente especializado (opcional, conservador)

**So sugira delegar se TODAS estas condicoes baterem** (threshold mais alto que `/executor-plan` porque quick-task ja e pequeno e o overhead anula o ganho):

- Match forte: a `description` de algum agente em `~/.claude/agents/` ou `.claude/agents/` contem **≥4 termos especificos** do contexto da task (stack + dominio + ferramenta/integracao). Termos genericos como "implementacao", "codigo", "feature" nao contam.
- Tarefa nao-trivial: `TDD aplicavel: Sim` no TASK.md OU ≥2 passos com logica de negocio (nao typo/config/rename simples).
- Modo livre ATIVO no projeto (`thoughts/modo-livre/active` existe) — senao o subagent vai pedir prompt do zero.

**Se as 3 condicoes baterem:**

```
Achei um subagente que bate fortemente com esta task:

  `dev-backend-ts` (model: sonnet)
  Match: TypeScript + backend + payment gateway + e-commerce (4 termos)

Aviso: ganho marginal em tarefas pequenas. Para typo/config simples,
executar no main agent costuma ser mais rapido.

Delegar a execucao [s/N]?
```

**Default: nao delegar.** Em `autonomo-invocado` (chamado por `/sdd-review`), pule essa etapa por completo — o caller ja decidiu o agente.

**Se aprovar:** invoque via Agent tool, repassando contexto-chave (constitution lida, modo do quick-task, modo-livre ATIVO) + path do TASK.md. O subagente continua a partir do Passo 1 do Fluxo de Execucao.

**Se rejeitar ou nao houver match:** prossiga no main agent.

**Cuidados** (mesmos do `/executor-plan` mas reforcados pra quick):
- Subagent so herda permissoes via arquivo. Decisoes runtime do main nao se propagam.
- Pra tarefa pequena, overhead de spawn + perda de estado runtime costumam superar o ganho de expertise.

---

## Fluxo de Execucao

### Passo 1 — Criar TASK.md

Em `thoughts/quick/NNN-slug/TASK.md`:

```markdown
# Quick Task NNN: [Titulo]

Data: DD-MM-YYYY
Issue/PR: [link se aplicavel]

## Descricao
[1 frase clara do que mudar]

## Por que
[1 linha do motivo — bug, request, etc]

## Passos
1. [acao concreta]
2. [acao concreta]
3. [...]

## Arquivos esperados
- `path/to/file1.ext`
- `path/to/file2.ext`

## TDD aplicavel?
[Sim/Nao + justificativa em 1 linha]

## Gate
[Comando exato de verificacao — ex: `bun test src/foo.test.ts` ou `bun typecheck` ou `npm run lint`]

## Skills
[Skills aplicaveis ou "nenhuma"]
```

### Passo 2 — Apresentar para aprovacao

**Em modo `manual` ou `step-invocado`**:
```
Quick Task NNN criada:

[Resumo do TASK.md]

Posso executar?
```
Aguarde aprovacao.

**Em modo `autonomo-invocado`**: pule a aprovacao. Mostre o TASK.md brevemente e avance direto:
```
Quick Task NNN (autonomo-invocado): [titulo]
Executando...
```

### Passo 3 — Safety Valve (apos passos detalhados)

Antes de tocar codigo, conte os passos REAIS necessarios (nao os otimistas):

| Sinal | Sobe para fluxo formal? |
|---|---|
| >5 passos atomicos | Sim |
| Dependencia nao obvia entre passos | Sim |
| Decisao arquitetural surgiu | Sim |
| Mais de 3 arquivos afetados | Sim |
| Surgiu nova lib/dependencia | Sim |

Se algum, PARE:
```
Esta task cresceu alem do quick mode:
- [motivo]

Sugiro converter para fluxo formal:
1. Apago thoughts/quick/NNN-slug/
2. Voce roda /sdd-plan
3. Continuamos no fluxo PLAN + executor

Confirma escalonamento?
```

### Passo 4 — Executar

Para cada passo:

**Se TDD aplicavel**:
- Escreva teste em `thoughts/tests/`
- Execute — FALHA
- Implemente o codigo minimo
- Execute — PASSA
- Refatore se necessario

**Se nao TDD** (config, typo, rename):
- Faca a mudanca direto
- Execute o `Gate` para validar

### Passo 5 — Verificar Gate

Execute o `Gate` do TASK.md. **Deve passar**.

Se falhar:
- Investigue
- Se simples: corrija
- Se complexo: PARE, mostre o problema, discuta

### Passo 6 — Test count check (se TDD)

Compare contagem de testes antes/depois. Se caiu, **PARE** — silent deletion.

### Passo 7 — Simplificar (opcional, com confirmacao)

**Em modo `manual` ou `step-invocado`**:
```
Quick task verificada. Posso passar code-simplifier antes do commit?
[Arquivos: lista]
```
Se aprovado, reexecute o Gate apos simplifier.

**Em modo `autonomo-invocado`**: pule o simplifier. O caller (`/sdd-review`) decide se aplica simplifier no conjunto consolidado de fixes ao final.

### Passo 8 — Commit (manual) ou Staging (modos invocados)

**Em modo `manual`**:
- Commit atomico. Mensagem clara descrevendo a mudanca.

**Em modo `autonomo-invocado` ou `step-invocado`**:
- **Nao commite.** Execute `git add <arquivos da task>` apenas.
- O caller (ex: `/sdd-review`) decide quando/como commitar.
- Anote no SUMMARY.md: "Staged, aguardando aprovacao do caller para commit."

### Passo 9 — Criar SUMMARY.md

Em `thoughts/quick/NNN-slug/SUMMARY.md`:

```markdown
# Quick Task NNN — Concluida

Data: DD-MM-YYYY
Commit: [hash + mensagem]

## O que foi feito
[1-2 linhas]

## Arquivos alterados
- `path/to/file1.ext` — [o que mudou]
- `path/to/file2.ext` — [o que mudou]

## Gate
- Comando: [comando]
- Resultado: PASSOU
- Test count: [se TDD: antes/depois]

## Observacoes
[Se algo surgiu fora do escopo previsto, registre aqui]
```

### Passo 10 — Propor Memoria (se aplicavel)

Se durante a execucao apareceu:
- Padrao novo → tipo `decision` ou `lesson`
- Blocker resolvido (importante para futuro) → tipo `blocker`
- Licao aprendida → tipo `lesson`

Pergunte:
```
Identifiquei algo util como memoria:

[Item]
[Tipo: decision | blocker | lesson]
[Por que importa]

Salvar?
  (m) MEMORY direto — definitiva agora (decisao independente de revisao de PR)
  (l) Deixar pro /sdd-learning extrair pos-merge — recomendado se a quick-task vira PR e pode ter feedback do review
  (n) Nao salvar
```

**Default sugerido**: `(l) pendente pro /sdd-learning` se ha PR aberto na branch atual ou voce sabe que a quick-task vai virar PR. Detecte com `gh pr list --head $(git branch --show-current) --state open --json number 2>/dev/null` — se ha PR, sugira (l). Se nao ha PR e nao vai virar PR (ex: ajuste local que nao vai pra remoto), `(m) memory direto` funciona quando voce esta certo da decisao.

Se `(l)` pendente pro /sdd-learning:
- **Nao crie arquivo** agora. Apenas anote a decisao + por que no `SUMMARY.md` da quick-task (secao "Observacoes" ou crie uma secao "Memoria pendente"). O /sdd-learning le o SUMMARY/PR/review depois e usa essa anotacao como pista, combinada com comentarios do review humano.
- Isso elimina drafts orfas em `thoughts/decisions-draft/` (pasta nao precisa mais existir nos projetos novos; projetos legados com drafts pendentes podem usar o command deprecated em `commands/deprecated/sdd-confirm.v7.md`).

Se `(m)` MEMORY direto:
- Resolva o path do auto-memory (via root do worktree pra centralizar memorias):
  ```bash
  ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
  PROJ_ENC=$(echo "${ROOT:-$(pwd)}" | sed 's|/|-|g')
  MEM_DIR="$HOME/.claude/projects/$PROJ_ENC/memory"
  ```
- Crie `$MEM_DIR/<tipo>_<slug>.md` no formato da skill `memory-keeper`.
- Atualize o `MEMORY.md` (secao `## <Type capitalizado>`, adicionar linha na tabela).

Se `(n)`: pule.

### Passo 11 — Informar (manual) ou Retornar resultado (modos invocados)

**Em modo `manual`** — informe ao usuario:
```
Quick Task NNN concluida.

Resumo: thoughts/quick/NNN-slug/SUMMARY.md
Commit: [hash]
Gate: PASSOU
[Memoria: K entradas adicionadas / nao alterada]
```

**Em modo `autonomo-invocado` ou `step-invocado`** — retorne estruturado para o caller (`/sdd-review` ou outro):
```
status: Complete | Blocked | Partial
files_staged: [lista]
gate_result: pass | fail
test_count: [antes / depois / esperado]
spec_deviation: [se aplicavel]
issues: [se aplicavel]
summary_path: thoughts/quick/NNN-slug/SUMMARY.md
```
Nao escreva mensagem ao usuario final — o caller agrega.

---

## Guardrails

- **Safety valve obrigatorio**: ao detectar crescimento, escale para fluxo formal. Nunca force quick mode em algo medio
- **TDD em codigo de lib**: typo/config = pode pular. Codigo de dominio/lib = sempre TDD
- **Test count check se TDD**: silent deletion e bloqueante mesmo em quick mode
- **Gate obrigatorio**: toda quick task tem um comando de verificacao. Sem gate = nao e quick task, e ajuste manual nao reproduzivel
- **Constitution mesmo aqui**: CLAUDE.md + ARCHITECTURE.md
- **Estilo de codigo (sempre)**: sem linhas em branco dentro do corpo de funcoes/metodos (entre funcoes, ok) — codigo compacto
- **Commit so em modo manual**: em `manual`, 1 quick task = 1 commit. Em `autonomo-invocado` e `step-invocado`, **NUNCA commite** — so `git add`. Caller decide o commit.
- **Nunca invente API**: verifique em doc oficial ou codigo existente
- **Memoria sob confirmacao**: nunca escreva no `memory/` (ou em draft) sem perguntar
- **Skills nao opcionais**: se a task tem skills, ative
- **GitHub via `gh` CLI**: nunca tokens manuais
