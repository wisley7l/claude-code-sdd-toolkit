# claude-code-sdd-toolkit

> **[Read in English](./README-en.md)**

Uma colecao de slash commands para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) que implementam um workflow de **Pair Programming com TDD**.

Esses commands transformam o Claude Code em um par de programacao que segue um processo disciplinado: **Pesquisar -> Entender -> Codar com TDD**.

## O que tem aqui

### Workflow Principal (3 fases)

| Fase | Command | Descricao |
|------|---------|-----------|
| Pesquisar | `/gerador-prd` | Investiga o problema: analisa codebase, consulta docs, mapeia o terreno. Profundidade proporcional a tarefa |
| Entender | `/gerador-spec` | Le a pesquisa, entende o problema, divide em tarefas praticas com TDD. Pausa para aprovacao |
| Codar | `/executor-plan` | Pair programming: escreve testes antes do codigo, implementa, refatora. Pausa entre tarefas |

### Utilitarios

| Command | Descricao |
|---------|-----------|
| `/sdd-review` | Analisa PR, branch ou diff e gera relatorio privado de review |
| `/git-worktree` | Cria uma worktree isolada para trabalho paralelo |
| `/git-remove-worktree` | Remove uma worktree de forma segura |
| `/git-prune-branches` | Remove branches locais cujas remotas ja foram deletadas |
| `/worktree-detect` | Analisa branches/PRs e detecta oportunidades de split em worktrees |

### Depreciados

Versoes anteriores dos commands estao em `deprecated/commands/` para referencia:
- `v1` — versoes iniciais independentes
- `v2` — versoes SDD com pipeline formal (PRD -> Spec -> Executor -> Review)

## Principios

- **Zero Inferencia** — Nunca assume comportamento de APIs ou padroes. Verifica na documentacao oficial (via [Context7](https://context7.com/)) ou no codigo existente
- **Constitution-first** — Commands leem `CLAUDE.md` e `ARCHITECTURE.md` antes de qualquer acao
- **TDD como contrato** — Testes unitarios sao escritos antes do codigo. Se quebram, paramos e discutimos
- **Adaptavel ao projeto** — Segue convencoes, skills e estrutura de cada projeto
- **Pair programming** — Estilo colaborativo, nao pipeline burocratico

## Como Usar

### 1. Instalacao

```bash
# Commands globais (disponiveis em todos os projetos)
cp commands/*.md ~/.claude/commands/

# Ou commands por projeto
cp commands/*.md /seu-projeto/.claude/commands/
```

### 2. Pre-requisitos

**Arquivos do projeto** — Os commands esperam que seu projeto tenha:

- **`CLAUDE.md`** — Regras do projeto, stack, convencoes
- **`ARCHITECTURE.md`** — Decisoes estruturais e padroes

**MCP Server** — Os commands usam o [Context7](https://github.com/upstash/context7) para consultar documentacao oficial:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

### 3. Fluxo Recomendado

```
Tarefa complexa/desconhecida:
  /gerador-prd    -> pesquisa e entendimento
    limpar sessao
  /gerador-spec   -> entender + dividir em tarefas
    limpar sessao
  /executor-plan  -> codar com TDD, tarefa por tarefa

Tarefa clara:
  /gerador-spec   -> dividir em tarefas (ou pular)
  /executor-plan  -> codar direto
```

> Limpe a sessao entre commands para maximizar a janela de contexto. Os artefatos em `thoughts/` servem como handoff entre sessoes.

### 4. Testes

- **Testes unitarios**: Sempre em `thoughts/tests/`, escritos antes do codigo (TDD). Nao sao commitados, sao nosso andaime de trabalho
- **Testes de integracao/e2e**: Quando o projeto usa, vao onde o projeto manda e sao commitados
- Se testes que passavam comecam a falhar: parada obrigatoria para discutir

## Estrutura

```
commands/
  gerador-prd.md            # Pesquisar
  gerador-spec.md           # Entender + Tarefas
  executor-plan.md          # Codar com TDD
  sdd-review.md             # Review
  git-worktree.md           # Criar worktree
  git-remove-worktree.md    # Remover worktree
  git-prune-branches.md     # Limpar branches
  worktree-detect.md        # Analisar worktrees
deprecated/
  commands/
    gerador-prd.v1.md       # Pesquisa v1
    gerador-spec.v1.md      # Spec v1
    executor-plan.v1.md     # Executor v1
    gerador-prd.v2.md       # Pesquisa v2 (SDD formal)
    gerador-spec.v2.md      # Spec v2 (SDD formal)
    executor-plan.v2.md     # Executor v2 (SDD formal)
```

## Inspiracoes

- **[spec-kit](https://github.com/github/spec-kit)** — Toolkit oficial do GitHub para Spec-Driven Development
- **[HumanLayer — Advanced Context Engineering](https://www.humanlayer.dev/blog/advanced-context-engineering)** — Padroes de context engineering para agentes de IA
- **[HumanLayer Claude Commands](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands)** — Exemplos praticos de commands
- **[Como eu uso o Claude Code — Workflow SDD](https://dfolloni.substack.com/p/como-eu-uso-o-claude-code-workflow)** — Walkthrough de um workflow SDD real
- Extreme Programming (XP) — Pair programming, TDD, small releases

## Licenca

[MIT](./LICENSE)
