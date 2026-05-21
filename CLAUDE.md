# CLAUDE.md — claude-code-sdd-toolkit

## O que é este repo

Coleção de slash commands e skills para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) que implementa um workflow de **Pair Programming com TDD** (SDD = Spec-Driven Development). Não é uma aplicação — é um **toolkit** que distribui artefatos (`.md`) para serem instalados em `~/.claude/commands/` e `~/.claude/skills/`.

Versão atual: **v7** (auto-sizing, single-doc spec). Detalhes completos em [`README.md`](./README.md).

## Estrutura

```
commands/             # Slash commands distribuídos (.md). FONTE CANÔNICA.
  deprecated/         # Versões antigas de commands (.vN.md) — fallback
skills/               # Skills distribuídas
  deprecated/         # Versões antigas de skills — fallback (mesma lógica)
README.md             # Visão geral em pt-BR
README-en.md          # Versão em inglês
LICENSE
```

**Não existe `src/`, `tests/`, `package.json` etc.** — os artefatos são markdown puro, consumidos pelo Claude Code em runtime.

## Convenções deste repo (importantes)

1. **Slash commands ficam em `commands/` na raiz**, NÃO em `.claude/commands/`. Este repo é o "fonte" — `.claude/commands/` é onde o Claude Code procura quando instalado em outros projetos. Aqui mantemos versionados em `commands/` e copiamos pra `~/.claude/commands/` na instalação.

2. **Skills ficam em `skills/` na raiz**, mesma lógica.

3. **Versões antigas vão pra subpasta `deprecated/` do tipo correspondente:**
   - Command antigo → `commands/deprecated/<nome>.vN.md`
   - Skill antiga → `skills/deprecated/<nome>/` (mesma estrutura da skill original)

   Não deletamos versões antigas — servem de fallback se uma versão nova regredir.

4. **Idioma:** documentação e instruções de command em **pt-BR**. Termos técnicos e identificadores ficam em inglês.

## Workflow principal (resumo)

- `/sdd-plan` → pesquisa + planejamento em 1 doc auto-sized (Medium/Large/Complex)
- `/executor-plan` → executa TDD autônomo, faz `git add` por tarefa, **nunca commita sozinho**
- `/quick-task` → atalho pra mudança pequena (≤3 arquivos), sem SPEC formal
- `/sdd-review` → review de PR/branch/diff, oferece gerar fixes via `/quick-task`
- `/sdd-learning` → extrai aprendizados não-óbvios de IMPs/reviews e propõe registro em memória
- `/sdd-confirm` → move drafts de `thoughts/decisions-draft/` pra memória após merge do PR
- `/memory-organize` → reorganiza auto-memory: detecta órfãs/links quebrados, propõe sub-sumários quando MEMORY.md cresce

### Memória persistente

O toolkit usa o **auto-memory nativo do Claude Code** (`~/.claude/projects/<projeto>/memory/`) — sem dependências externas. A skill `memory-keeper` define o contrato (9 tipos, convenção flat, formato tabela do MEMORY.md). A skill `vault-memory` foi depreciada em favor desse modelo (ver `skills/deprecated/vault-memory/` como referência histórica).

Detalhes e fluxo recomendado: [`README.md`](./README.md).

## Princípios não-negociáveis

- **Zero Inferência** — Nunca assumir comportamento de API ou padrão. Verificar via Context7 MCP ou no código existente.
- **Constitution-first** — Commands leem `CLAUDE.md` e `ARCHITECTURE.md` do projeto-alvo antes de agir.
- **TDD como contrato** — Testes antes do código. Se quebram, paramos.
- **Commit sob aprovação humana** — Commands podem fazer `git add`, mas `git commit` e `git push` sempre precisam de OK explícito do usuário.
- **Atualizar > criar** — Em memória, em docs, em commands: prefira atualizar artefato existente a criar duplicado.

## O que NÃO fazer aqui

- Não criar `.claude/commands/` neste repo — usar `commands/` na raiz.
- Não criar `.claude/skills/` neste repo — usar `skills/` na raiz.
- Não deletar arquivos de `commands/deprecated/` ou `skills/deprecated/` — são fallback intencional.
- Não inventar workflow novo sem antes ler como o atual funciona (`README.md` + um command/skill existente como modelo).
- Não commitar/pushar sem o usuário pedir explicitamente.

## Pré-requisitos pros commands rodarem (em projetos-alvo)

- `CLAUDE.md` e `ARCHITECTURE.md` no projeto-alvo
- MCP Context7 configurado pra consultar documentação oficial
- `thoughts/` pra outputs persistentes (specs, IMPs, reviews, ROADMAP, drafts em `decisions-draft/`)
- Auto-memory do Claude Code (nativo, em `~/.claude/projects/<projeto>/memory/`) — gerenciado pela skill `memory-keeper`
