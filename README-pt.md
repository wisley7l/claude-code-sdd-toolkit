# claude-code-sdd-toolkit

> **[Read in English](./README.md)**

Uma coleção de slash commands para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) que implementam um workflow de **Specification-Driven Development (SDD)**.

Esses commands transformam o Claude Code em um parceiro de desenvolvimento estruturado que segue um processo disciplinado: **Pesquisa → Spec → Plano → Execução → Review**.

## O que tem aqui

### Workflow SDD (pipeline de 3 fases)

| Fase | Command | Descrição |
|------|---------|-----------|
| 0 — Pesquisa | `/gerador-prd` | Explora o codebase e documentações externas, produzindo um PRD (Preliminary Design Research) sem prescrever soluções |
| 1 — Spec + Plano | `/gerador-spec` | Lê o PRD e produz um documento em duas partes: **Part A** (o quê e por quê) e **Part B** (como — micro-tarefas atômicas) |
| 2 — Execução | `/executor-plan` | Executa micro-tarefas uma por vez, pausando para aprovação do usuário após cada passo |
| Review | `/sdd-review` | Analisa um PR, branch ou diff e gera um relatório privado de review com pontuação de confiança |

### Utilitários Git

| Command | Descrição |
|---------|-----------|
| `/git-worktree` | Cria uma worktree isolada a partir da branch default para trabalho paralelo |
| `/git-remove-worktree` | Remove uma worktree de forma segura, verificando mudanças não commitadas |
| `/git-prune-branches` | Remove branches locais cujas remotas já foram deletadas |
| `/worktree-detect` | Analisa branches/PRs e detecta oportunidades de split em worktrees focadas |

### Depreciados (v1)

Versões anteriores dos commands SDD estão em `deprecated/commands/` para referência. Funcionam independentemente, mas não têm alguns recursos das versões atuais (integração com worktree, rastreamento de checkpoints, geração de diagramas).

## Princípios Fundamentais

Esses commands aplicam algumas regras inegociáveis:

- **Zero Inferência** — Nunca assume comportamento de APIs ou padrões. Sempre verifica na documentação oficial (via [Context7](https://context7.com/) MCP) ou no código existente do projeto. Se nenhuma fonte verificável for encontrada, marca como `[NEEDS VERIFICATION]`
- **Constitution-first** — Commands sempre leem `CLAUDE.md` e `ARCHITECTURE.md` antes de qualquer ação, tornando-os agnósticos de stack
- **Execução atômica** — O executor nunca avança para a próxima tarefa sem aprovação explícita do usuário
- **Transparência de fontes** — Toda referência externa usada por subagentes deve aparecer no documento final com link verificável

## Como Usar

### 1. Instalação

Copie os arquivos de command para o diretório de commands do Claude Code:

```bash
# Commands globais (disponíveis em todos os projetos)
cp commands/*.md ~/.claude/commands/

# Ou commands por projeto
cp commands/*.md /seu-projeto/.claude/commands/
```

### 2. Pré-requisitos

**Arquivos do projeto** — Esses commands esperam que seu projeto tenha:

- **`CLAUDE.md`** — Regras do projeto, stack, convenções (a "constituição")
- **`ARCHITECTURE.md`** — Decisões estruturais e padrões

Os commands leem esses arquivos primeiro e se adaptam a qualquer stack que você use. Nenhuma suposição de framework ou runtime hardcoded.

**MCP Server** — Os commands usam o [Context7](https://github.com/upstash/context7) para consultar documentação oficial de bibliotecas e frameworks. É assim que eles evitam inferência — consultam docs reais ao invés de adivinhar.

Para configurar, adicione ao seu MCP config do Claude Code (`~/.claude.json` ou `.mcp.json` do projeto):

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

> Os commands ainda funcionam sem o Context7, mas as consultas de documentação cairão para busca web, que é menos confiável.

### 3. Executar

No Claude Code, invoque qualquer command com `/`:

```
/gerador-prd
/gerador-spec
/executor-plan
/sdd-review
```

### Fluxo SDD Recomendado

```
/gerador-prd          → produz PRD em thoughts/shared/research/
/gerador-spec          → lê o PRD, produz SPEC em thoughts/shared/plans/
/executor-plan         → lê a SPEC, executa micro-tarefas com checkpoints do usuário
/sdd-review            → faz review do PR/branch resultante
```

## Estrutura de Diretórios

```
commands/
  gerador-prd.md            # Fase 0 — Pesquisa
  gerador-spec.md           # Fase 1 — Spec + Plano
  executor-plan.md          # Fase 2 — Execução
  sdd-review.md             # Review
  git-worktree.md           # Criar worktree
  git-remove-worktree.md    # Remover worktree
  git-prune-branches.md     # Limpar branches locais
  worktree-detect.md        # Analisar oportunidades de worktree
deprecated/
  commands/
    gerador-prd.v1.md       # Pesquisa legacy (v1)
    gerador-spec.v1.md      # Spec legacy (v1)
    executor-plan.v1.md     # Executor legacy (v1)
```

## Licença

[MIT](./LICENSE)
