# CLAUDE.md — claude-code-sdd-toolkit

## O que é este repo

Coleção de slash commands e skills para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) que implementa um workflow de **Pair Programming com TDD** (SDD = Spec-Driven Development). Não é uma aplicação — é um **toolkit** que distribui artefatos (`.md`) para serem instalados em `~/.claude/commands/` e `~/.claude/skills/`.

Versão atual: **v9** (pipeline de 2 docs: SPEC de comportamento via `/sdd-spec` → PLAN técnico via `/sdd-plan`; + progressive disclosure + knowledge cache na memória). Detalhes completos em [`README.md`](./README.md).

## Estrutura

```
commands/             # Slash commands distribuídos (.md). FONTE CANÔNICA.
  references/         # Templates/blocos carregados sob demanda pelos commands (progressive disclosure)
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

5. **Progressive disclosure:** o corpo de um command grande mantém só o protocolo (princípios, fluxo, guardrails). Templates de output e blocos usados num único passo vão pra `commands/references/<command>-<tema>.md`, carregados via `Read` no passo que os usa. Todo ponteiro pra reference inclui: busca em `.claude/sdd-references/` do projeto → `~/.claude/sdd-references/` → fallback inline resumido (2-4 linhas com as seções). **Instalação fica FORA de `.claude/commands/`** (em `sdd-references/`): o scanner do Claude Code registra todo `.md` dentro de `commands/` como command namespaced, o que poluiria a lista de skills de toda sessão. Exceção: conteúdo de segurança (JSON de permissões do `/modo-livre`) não tem fallback improvisado — reference ausente = parar e avisar.

6. **Modelos:** frontmatter de command usa ID completo (`claude-sonnet-5` etc. — formato documentado); spawns de subagent usam **aliases** (`opus`/`sonnet`/`haiku` — garantidos pela doc do Agent SDK).

## Workflow principal (resumo)

- `/sdd-spec` → **especificação de comportamento** (o QUÊ): pesquisa o codebase e escreve a SPEC (histórias de usuário, critérios de sucesso, requisitos funcionais, testes de aceitação) em `thoughts/specs/spec-<ts>-<slug>.md`. **Nunca escreve código, plano ou tarefas** — antecede o `/sdd-plan`. Inspirado na gist "Formação da especificação" por @parruda
- `/sdd-plan` → consome a SPEC de comportamento e gera o **plano técnico** (o COMO): pesquisa + tarefas TDD num doc auto-sized (Medium/Large/Complex) em `thoughts/plans/PLAN-<...>.md`, com cada tarefa rastreável a um RF/AT da SPEC (4º check de Cobertura). `/sdd-plan-eco` é a variante econômica pra Medium (main em Sonnet, quebra de tarefas + checks num subagente Opus)
- `/pr-draft` → abre PR inicial em draft a partir do plano (branch + empty commit + title/body derivados da **SPEC de comportamento**), devolve o root pra branch default e cria worktree via `/git-worktree`. Bloqueado pra criar PR → instrui o usuário comando-por-comando. `/pr-draft sync` reescreve o body pós-implementação como prévia pro reviewer (O quê / Por quê / Como / Test plan, rastreável a SPEC/PLAN/IMP/diff). **Nunca commita código nem sai de draft sozinho**
- `/executor-plan` → executa TDD autônomo, faz `git add` por tarefa, **nunca commita sozinho**
- `/pair-review` → companheiro interativo do review manual, em **sessão nova**: re-hidrata do staged + PLAN/IMP, perguntas de julgamento vão pra subagentes Opus focados, ajustes com gate + test count protection. Com PR sob review do time, valida cada fix contra o comentário humano de origem (modo `r`). **Nunca commita sem escolha explícita, nunca posta no PR**
- `/quick-task` → atalho pra mudança pequena (≤3 arquivos), sem SPEC/PLAN formal
- `/pr-ready` → entrega de PR ponta a ponta: avalia via `/sdd-review`; se reprovado → loop de correção via `/quick-task` **até convergir** (loop nativo no protocolo, não o builtin `/goal`; para se uma rodada não reduz os must-fix); aprovado → commit/push humano → `/pr-draft sync` no body → handoff. **Tirar de draft e marcar reviewer são gates `AskUserQuestion` (cada um com "agora não"), nunca automáticos.** Nunca commita/pusha sozinho; saída só com PR aprovado E código pushado
- `/sdd-review` → review de PR/branch/diff, oferece gerar fixes via `/quick-task`
- `/sdd-learning` → extrai aprendizados não-óbvios de IMPs/reviews e propõe registro em memória
- `/sdd-confirm` → move drafts de `thoughts/decisions-draft/` pra memória após merge do PR
- `/memory-organize` → reorganiza auto-memory: detecta órfãs/links quebrados, propõe sub-sumários quando MEMORY.md cresce
- `/verifica` → verificação comportamental: roda o app, exercita os fluxos tocados, registra evidência no IMP. Nunca produção; side effects só com confirmação
- `/investiga` → root cause de bug não-óbvio: hipóteses com mecanismo causal → evidência em subagents paralelos → causa com fonte → handoff. Alimenta blockers/lessons
- `/sdd-init` → audita/prepara projeto-alvo (constitution, thoughts/, Context7, references) sob confirmação por bloco
- `/git-rebase-seguro` → atualiza branch com a base: baseline de testes, conflitos sob confirmação, test count protection, rollback garantido. Nunca pusha

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
