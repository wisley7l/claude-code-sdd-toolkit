---
description: Modo rapido — mudanca pequena sem PRD nem SPEC formal (bug fix, config, tweak)
allowed-tools: Read, Edit, Write, Glob, Grep, Agent, Skill, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(git fetch*), Bash(git add*), Bash(git commit*), Bash(gh *), Bash(npm *), Bash(npx *), Bash(bun *), Bash(bunx *), Bash(pnpm *), Bash(node *), Bash(go *), Bash(ls *), Bash(mkdir *), WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs
# Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe Rodrigues
# https://github.com/tech-leads-club/agent-skills
# Conceitos adaptados: Quick mode com safety valve
---

# Quick Task — Modo Rapido

Voce executa **mudancas pequenas** sem rodar SPEC formal. Use quando:
- ≤3 arquivos alterados
- Descricao cabe em 1 frase
- Sem decisao arquitetural nova
- Sem dependencia entre passos
- Bug fix, ajuste de config, typo, rename simples

**Se o escopo crescer durante a execucao, voce sobe para o fluxo formal.**

## Principios

- **Baixa ceremonia**: 1 arquivo de input (`TASK.md`) + 1 de output (`SUMMARY.md`)
- **Safety valve**: se passos passarem de 5 OU surgir decisao arquitetural OU dependencia nao obvia, PARE e sugira `/sdd-plan`
- **TDD quando aplicavel**: codigo de lib/dominio = TDD obrigatorio. Config/typo = nao
- **Memoria persistente leve**: leia memoria de sessoes anteriores (vault `CLAUDE_VAULT_PATH` ou `thoughts/STATE.md`) para nao repetir blockers conhecidos. Detalhes: skill `vault-memory`
- **Zero Inferencia**: API externa = verifique antes (Context7/WebFetch). Sem verificacao = pare
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` mesmo no quick mode

## Resolucao do diretorio root

```bash
git worktree list | head -1 | awk '{print $1}'
```

Use esse caminho como base para `thoughts/`.

## Configuracao Inicial

### 1. Receber a Demanda
Se nao descreveu:
```
O que voce quer fazer? (1 frase)
Lembre: quick mode e para mudanca pequena. Se for feature, use /sdd-plan.
```

### 2. Validar se cabe em quick mode

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

### 3. Ler context minimo
- `CLAUDE.md`
- `ARCHITECTURE.md`
- Memoria persistente — so blockers conhecidos. Modo vault (`CLAUDE_VAULT_PATH`): `state/blockers/*.md`. Modo legacy: `thoughts/STATE.md`. Ver skill `vault-memory`.
- Skills aplicaveis em `.claude/skills/`

### 4. Decidir o numero da task

Liste `thoughts/quick/`:
```bash
ls thoughts/quick/ 2>/dev/null | grep -E '^[0-9]+' | sort -n | tail -1
```

Use o proximo numero (3 digitos: 001, 002, ...).

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

```
Quick Task NNN criada:

[Resumo do TASK.md]

Posso executar?
```

Aguarde aprovacao.

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
3. Continuamos no fluxo SPEC + executor

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

```
Quick task verificada. Posso passar code-simplifier antes do commit?
[Arquivos: lista]
```

Se aprovado, reexecute o Gate apos simplifier.

### Passo 8 — Commit

Commit atomico. Mensagem clara descrevendo a mudanca.

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
- Padrao novo → tipo `decisao` ou `licao`
- Blocker resolvido (importante para futuro) → tipo `blocker`
- Licao aprendida → tipo `licao`

Pergunte:
```
Identifiquei algo util como memoria:

[Item]
[Tipo: decisao | blocker | licao]
[Por que importa]

Salvar? (s/n)
```

Se aprovado:
- **Modo vault**: nota atomica em `$CLAUDE_VAULT_PATH/<org>/<projeto>/state/<tipo>s/<YYYY-MM-DD>-<slug>.md` (formato no skill `vault-memory`).
- **Modo legacy**: entrada em `thoughts/STATE.md` na secao correspondente.

### Passo 11 — Informar ao usuario

```
Quick Task NNN concluida.

Resumo: thoughts/quick/NNN-slug/SUMMARY.md
Commit: [hash]
Gate: PASSOU
[Memoria: K entradas adicionadas / nao alterada]
```

---

## Guardrails

- **Safety valve obrigatorio**: ao detectar crescimento, escale para fluxo formal. Nunca force quick mode em algo medio
- **TDD em codigo de lib**: typo/config = pode pular. Codigo de dominio/lib = sempre TDD
- **Test count check se TDD**: silent deletion e bloqueante mesmo em quick mode
- **Gate obrigatorio**: toda quick task tem um comando de verificacao. Sem gate = nao e quick task, e ajuste manual nao reproduzivel
- **Constitution mesmo aqui**: CLAUDE.md + ARCHITECTURE.md
- **Commit atomico**: 1 quick task = 1 commit (ou 2 se houver passada do simplifier)
- **Nunca invente API**: verifique em doc oficial ou codigo existente
- **Memoria sob confirmacao**: nunca escreva (vault ou STATE.md) sem perguntar
- **Skills nao opcionais**: se a task tem skills, ative
- **GitHub via `gh` CLI**: nunca tokens manuais
