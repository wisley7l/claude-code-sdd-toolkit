---
description: Prepara um projeto pro toolkit SDD — audita pré-requisitos (CLAUDE.md, ARCHITECTURE.md, thoughts/, Context7, references) e cria o que falta sob confirmação por bloco.
model: claude-sonnet-4-6
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion, Bash(ls *), Bash(mkdir *), Bash(find *), Bash(test *), Bash(pwd), Bash(cp *), Bash(git status*), Bash(git worktree list*), Bash(git remote*), Bash(grep *)
---

# SDD Init — preparar o projeto pro toolkit

Você audita os pré-requisitos do workflow SDD no projeto atual e cria o que falta — **um bloco por vez, sob confirmação**. Roda uma vez por projeto (ou de novo quando algo quebrar/faltar).

## Fluxo

### 1. Auditoria

Cheque cada item e monte a tabela:

| Item | Como checar | Status |
|---|---|---|
| `CLAUDE.md` | existe na raiz? declara comandos de gate (test/typecheck/lint)? | ✓ / ⚠ sem gates / ✗ |
| `ARCHITECTURE.md` | existe na raiz (ou doc equivalente referenciado pelo CLAUDE.md)? | ✓ / ✗ |
| `thoughts/` | subpastas `plans/ history/ reviews/ research/ quick/ tests/` | ✓ / parcial / ✗ |
| `.gitignore` | cobre `thoughts/tests/` e `.worktrees/` | ✓ / ✗ |
| Context7 MCP | `.mcp.json` (projeto) ou config global com `context7` | ✓ / ✗ |
| References SDD | `.claude/sdd-references/` no projeto ou `~/.claude/sdd-references/` | ✓ / ✗ |
| Commands SDD | `/sdd-plan` etc. em `.claude/commands/` ou `~/.claude/commands/` | ✓ / ✗ |
| Auto-memory | `~/.claude/projects/<root-encoded>/memory/` existe | ✓ / ✗ (harness cria) |
| Modo livre | `thoughts/modo-livre/active` | ATIVO / inativo (opcional) |

Apresente a tabela. Se tudo ✓: "Projeto pronto pro SDD" e encerre.

### 2. Criar o que falta — bloco a bloco, com confirmação

Pra cada ✗/⚠, na ordem abaixo, proponha e **aguarde OK antes de criar**:

**a) `CLAUDE.md` ausente** — gere um draft analisando o codebase. Delegue a leitura a um subagente (`Agent`, `subagent_type: Explore`): stack e versões (manifests), comandos reais de build/test/lint/typecheck (scripts declarados), estrutura de pastas, convenções visíveis (naming, testes). Draft mínimo:

```markdown
# CLAUDE.md — [nome]

## Stack
[linguagem, framework, runtime — do manifest, não chute]

## Comandos
- Test: `[comando real]`
- Typecheck: `[comando real]`
- Lint: `[comando real]`
- Dev: `[comando real]`

## Convenções
[2-5 bullets observados no código — marcar [NEEDS REVIEW] no que for inferência]

## Branch base
[main/dev — de `git remote show origin`]
```

Todo item inferido leva `[NEEDS REVIEW]` — o draft é rascunho, o humano valida.

**b) `CLAUDE.md` existe mas sem gates (⚠)** — proponha **adicionar** a seção de comandos (nunca reescrever o arquivo). Os commands SDD dependem dos gates declarados.

**c) `ARCHITECTURE.md` ausente** — mesmo protocolo do (a): subagente mapeia camadas/módulos/fluxos principais e gera draft com diagrama mermaid simples, tudo `[NEEDS REVIEW]`. Se o projeto for pequeno demais (ex: script único), sugira pular com nota no CLAUDE.md.

**d) `thoughts/`** — `mkdir -p thoughts/{plans,history,reviews,research,quick,tests}`.

**e) `.gitignore`** — adicione (sem duplicar): `thoughts/tests/` e `.worktrees/`.

**f) Context7** — proponha criar `.mcp.json` (ou mostrar o bloco pra config global):

```json
{
  "mcpServers": {
    "context7": { "command": "npx", "args": ["-y", "@upstash/context7-mcp@latest"] }
  }
}
```

Avise que MCP novo exige reload da sessão.

**g) References/commands SDD ausentes** — você não instala o toolkit daqui (não sabe onde o repo dele está). Instrua:

```bash
cd <repo do claude-code-sdd-toolkit>
cp commands/*.md ~/.claude/commands/
mkdir -p ~/.claude/sdd-references && cp commands/references/* ~/.claude/sdd-references/
```

**h) Modo livre inativo** — apenas sugira `/modo-livre on` (acelera execução autônoma). Não rode.

### 3. Resumo final

```
SDD Init concluído.

Criados: [lista]
Já existiam: [lista]
Pendentes de ação sua: [reload p/ MCP, revisar [NEEDS REVIEW], instalar toolkit, /modo-livre on]

Próximo passo: /sdd-spec pra especificar a primeira feature (ou /quick-task pra mudança pequena).
```

## Guardrails

- **Nunca sobrescreva `CLAUDE.md`/`ARCHITECTURE.md` existentes** — só proponha adições pontuais
- **Draft é rascunho**: tudo que foi inferido do código leva `[NEEDS REVIEW]`; o humano é quem valida a constitution
- **Confirmação por bloco**: nada é criado em lote sem OK
- **Zero Inferência**: stack/comandos vêm de manifests e scripts reais — sem chute
- **Nunca commita** — os arquivos criados ficam no working tree pro usuário revisar e commitar
