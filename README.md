# claude-code-sdd-toolkit

> **[Read in English](./README-en.md)**

Coleção de slash commands para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) que transformam o agente num par de programação com TDD, seguindo um processo disciplinado: **Pesquisar → Entender → Codar com TDD**.

## Commands

### Workflow principal

**`/sdd-plan`** — pesquisa, entende e quebra a feature em tarefas num único doc auto-sized (Medium/Large/Complex). Detecta escopo Quick e delega pra `/quick-task`.

**`/sdd-plan-eco`** — variante econômica do `/sdd-plan` pra escopo Medium: main em Sonnet, quebra de tarefas + 3 checks delegadas a um único subagente Opus de contexto focado.

**`/pr-draft`** — abre o PR inicial em draft a partir do plano (branch + empty commit + title/body do SPEC) e cria a worktree pra implementação isolada.

**`/executor-plan`** — executa as tarefas com TDD em modo autônomo, sub-agents paralelos pras tarefas marcadas `[P]`, staging por tarefa. Commits sob aprovação humana; `--step` volta ao modo pausado.

**`/quick-task`** — mudança pequena (≤3 arquivos) sem SPEC formal. Sobe pro fluxo formal se o escopo crescer.

**`/pair-review`** — companheiro interativo do review manual pós-executor. Roda em **sessão nova** (`/clear`): re-hidrata do staged + SPEC/IMP (~3-4k tokens, sem o ruído da execução), responde perguntas factuais direto e delega julgamento a subagentes Opus escopados nos arquivos da pergunta, aplica ajustes pequenos com gate + test count protection. Walkthrough por tarefa e hotspots opcionais. Nunca commita sem escolha.

**`/sdd-learning`** — após o PR fechar, extrai aprendizado não-óbvio de IMPs, reviews e do PR no GitHub e propõe registro na memória, caso a caso.

**`/memory-organize`** — reorganiza o auto-memory: órfãs, links quebrados, duplicatas e sub-sumários quando `MEMORY.md` cresce.

**`/roadmap`** — gerencia `thoughts/ROADMAP.md`: entradas, import de issues do GitHub, sync com SPEC/IMP.

### Utilitários

**`/sdd-review`** — review de PR, branch ou diff via subagents isolados; oferece gerar fixes via `/quick-task`.

**`/busca`** — pesquisa web via subagent isolado, sem impacto no contexto principal. Flags `--rapido`, `--profundo` e `--save`.

**`/pr-report`** — relatório de PRs do usuário no repo (semanal inline, mensal e anual salvos).

**`/complexidade`** — mede complexidade ciclomática **só nos arquivos alterados** (vs base ou `--staged`), threshold 10 (ou o do `CLAUDE.md` do projeto). Detecta a ferramenta na ordem linter do projeto → `lizard` → `fta`. Com `--fix`, oferece refactor via `code-simplifier`. O mesmo gate roda embutido no `/sdd-review` (vira issue MINOR/MAJOR) e no `/executor-plan` (correção automática na Verificação Final, parada dura após 2 tentativas).

**`/worktree-detect`** — detecta oportunidades de isolar branches/PRs em worktrees.

**`/modo-livre`** — toggle do modo autônomo (allow amplo + deny dos perigosos). Requer reload da sessão.

**`/git-worktree`, `/git-remove-worktree`, `/sync-tests`, `/git-prune-branches`** — utilitários de git e worktree.

**Modelo por command**: a thread principal roda leve (Sonnet base, ou Haiku nos utilitários de git) e só sobe pra Opus **dentro de subagentes**, na etapa que realmente exige raciocínio — assim o modelo caro processa só o contexto focado, sem queimar token nas etapas mecânicas (git, leitura de arquivo, escrita de doc). Trocar de modelo na thread principal (`/model`) invalida o cache de prompt, então os commands evitam isso. Exceção: `/sdd-plan` roda em Opus na main (planejamento é raciocínio interativo denso e espalhado, não isolável num subagente) e delega só as leituras volumosas a subagentes — pra escopo Medium, o `/sdd-plan-eco` derruba esse custo. Nos frontmatters os modelos são IDs completos (formato documentado pra slash commands); nos spawns de subagent são **aliases** (`opus`/`sonnet`/`haiku`), garantidos pela doc do Agent SDK — acompanham o melhor modelo de cada tier sem manutenção.

**Progressive disclosure**: os commands grandes mantêm no corpo só o protocolo; templates e blocos de uso pontual vivem em `commands/references/` (instalados em `~/.claude/sdd-references/` — fora de `commands/`, pra não serem registrados como commands namespaced) e são carregados via `Read` apenas no passo que os usa. Isso corta o custo fixo por invocação (~30-40% nos commands pesados) e evita arrastar template de relatório por dezenas de turnos de execução.

### Fluxo recomendado

```
Feature normal:   /sdd-plan → /pr-draft → (cd <worktree> && claude) → /executor-plan → /sdd-review
                                                                                          ↓
                                                              você revisa o diff e commita/pusha
Review manual:    /clear → /pair-review   (companheiro interativo sobre o staged, sem ruído da execução)
Mudança pequena:  /quick-task
Após PR fechar:   /sdd-learning
Quando precisar:  /busca · /complexidade · /roadmap · /memory-organize
```

`/pr-draft` é opcional, mas recomendado: isola a implementação numa worktree e sinaliza o kickoff ao time. Os artefatos em `thoughts/` servem de handoff entre sessões — limpe a sessão (`/clear`) entre commands grandes pra maximizar a janela de contexto. O custo de re-hidratação é baixo (SPEC + `MEMORY.md` ≈ 2-3k tokens), então limpar é quase sempre ganho: o estado durável vive em arquivo, não na conversa.

## Como usar

### 1. Instalação

```bash
# Commands globais (todos os projetos)
cp commands/*.md ~/.claude/commands/
mkdir -p ~/.claude/sdd-references && cp commands/references/* ~/.claude/sdd-references/

# Ou por projeto
cp commands/*.md /seu-projeto/.claude/commands/
mkdir -p /seu-projeto/.claude/sdd-references && cp commands/references/* /seu-projeto/.claude/sdd-references/
```

A pasta `references/` é necessária: os commands grandes carregam templates dela sob demanda (progressive disclosure). Sem ela os commands ainda funcionam via fallback inline, mas com templates resumidos.

### 2. Pré-requisitos

No projeto onde os commands rodam:

- **`CLAUDE.md`** — regras, stack e convenções do projeto
- **`ARCHITECTURE.md`** — decisões estruturais e padrões
- **MCP [Context7](https://github.com/upstash/context7)** — pra consultar documentação oficial (princípio Zero Inferência):

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

## Princípios

- **Zero Inferência** — nunca assume comportamento de API ou padrão; verifica na doc oficial (Context7) ou no código existente
- **Constitution-first** — lê `CLAUDE.md` e `ARCHITECTURE.md` antes de qualquer ação
- **TDD como contrato** — testes antes do código; se quebram, paramos e discutimos
- **Test count protection** — toda tarefa declara `Test count: N tests pass`; cair = bloqueio (previne silent deletion)
- **Test co-location** — testes na MESMA tarefa que cria o código; defer é anti-pattern
- **Commit sob aprovação humana** — commands fazem `git add`, nunca `git commit`/`push` sozinhos
- **Memória persistente** — auto-memory nativo guarda decisões/blockers/lições entre sessões; escrita sempre sob confirmação
- **Pair programming** — estilo colaborativo, não pipeline burocrático

## Memória persistente (auto-memory)

Os commands recuperam contexto entre sessões via **auto-memory nativo do Claude Code** (`~/.claude/projects/<projeto>/memory/`), gerenciado pela skill `memory-keeper`. O harness carrega `MEMORY.md` no system prompt no início de cada sessão (limite 200 linhas / 25KB); notas individuais são abertas sob demanda.

Convenção **flat** (sem subpastas): `MEMORY.md` como índice + arquivos `<tipo>_<slug>.md`. São **9 tipos** — 4 nativos do harness e 5 SDD:

- **Nativos** — `user` (perfil/preferências), `feedback` (regra de colaboração), `project` (contexto/deadline não-óbvio), `reference` (ponteiro pra sistema externo)
- **SDD** — `decision` (decisão arquitetural/técnica), `blocker` (bloqueio + workaround), `lesson` (aprendizado de execução/review), `idea` (explorar depois), `preference` (preferência do projeto)

Escrita **sempre sob confirmação**. Rode `/memory-organize` quando `MEMORY.md` crescer (>150 linhas) ou suspeitar de órfãs/duplicatas. Protocolo completo em `skills/memory-keeper/SKILL.md`.

Dois usos que aumentam o retorno por token:

- **Cache de conhecimento** — claims de API verificados via Context7/web viram notas `reference` (claim + fonte + data + versão da lib). O `/sdd-plan` consulta esse cache como **Step 0** da Knowledge Verification Chain e só re-pesquisa quando o cache venceu (>90 dias ou major version diferente). Em stack estável, corta pesquisa externa repetida entre features.
- **Hooks autossuficientes** — a linha no `MEMORY.md` carrega a **regra aplicável**, não só o tema (ex: `schema sem FK; validar referência na aplicação`). Como o índice é carregado de graça em toda sessão, na maioria dos usos o agente age sem abrir a nota individual.

## Testes

- **Unitários** em `thoughts/tests/`, escritos antes do código (TDD). Não commitados — são andaime de trabalho
- **Integração/e2e** vão onde o projeto manda e são commitados
- Se testes que passavam começam a falhar, ou a contagem cai: parada obrigatória pra discutir

## Statusline (opcional)

Barra no rodapé com modelo, pasta, contexto colorido, rate limits (5h/7d) e estado do `/modo-livre` — útil pra saber quando dar `/clear` (barra vermelha em ≥85%) e acompanhar consumo. Rode `/statusline` colando:

```
mostre [nome-do-modelo] entre colchetes, depois nome da pasta atual (basename de .workspace.current_dir), depois uma barra de progresso de 10 blocos usando █ pra preenchido e ░ pra vazio seguida da porcentagem de contexto e da palavra "ctx", depois " • 5h XX% (HhMm)" usando .rate_limits.five_hour.used_percentage e tempo ate .rate_limits.five_hour.resets_at (epoch), depois " • 7d XX% (Dd Hh)" com .rate_limits.seven_day.* na mesma logica; omita as secoes 5h/7d se rate_limits nao existir. e no fim adicione (ML 🟢) quando o arquivo <workspace>/thoughts/modo-livre/active existir ou (ML 🔴) quando nao existir. formato do tempo ate reset (diff = resets_at - now em segundos): se diff <= 0 omita o parentese; se diff < 60 mostre (<1m); se diff < 3600 mostre (Ym); se diff < 86400 mostre (XhYm) sem espaco; se diff >= 86400 mostre (Xd Yh) com espaco entre d e h. cor por threshold (aplicada na barra de contexto e nos numeros dos rate limits, NAO no resto do texto): verde se < 60%, amarelo se 60-84%, vermelho se >= 85%. salve em ~/.claude/statusline.sh com chmod +x e atualize ~/.claude/settings.json
```

Resultado: `[Claude Sonnet 4.5] gopay ████░░░░░░ 42% ctx • 5h 8% (5h30m) • 7d 18% (5d 12h) (ML 🟢)`. Recarregue a sessão após configurar (`Ctrl+C` e `claude`). O layout não mostra branch git (assume que o PS1 já exibe).

## Estrutura

```
commands/                   # Slash commands — FONTE CANÔNICA (copiada pra ~/.claude/commands/)
  sdd-plan.md · sdd-plan-eco.md · pr-draft.md · executor-plan.md · pair-review.md
  quick-task.md · sdd-review.md · sdd-learning.md · memory-organize.md · roadmap.md
  busca.md · pr-report.md · complexidade.md · worktree-detect.md · modo-livre.md
  git-worktree.md · git-remove-worktree.md · sync-tests.md · git-prune-branches.md
  references/               # Templates carregados sob demanda (progressive disclosure)
  deprecated/               # Versões antigas — fallback (sufixo .vN.md). Não deletar
skills/
  memory-keeper/            # Auto-memory: 9 tipos, convenção flat, MEMORY.md como índice
  conciso/                  # Modo de resposta enxuto em pt-BR (lite/full/ultra)
  deprecated/               # Skills antigas — fallback
```

**`commands/` vs `skills/`** (convenção Anthropic): commands são invocados manualmente (`/sdd-plan`); skills auto-disparam pela descrição quando o contexto bate. `memory-keeper` é skill porque precisa estar sempre disponível pra ler/escrever memória sem o usuário pedir.

### Outputs em `thoughts/` (no projeto-alvo)

```
thoughts/
  ROADMAP.md                  # Visão multi-feature (opcional)
  plans/SPEC-DD-MM-YYYY-slug.md      # /sdd-plan
  history/IMP-DD-MM-YYYY-slug.md     # /executor-plan
  reviews/                    # /sdd-review
  research/YYYY-MM-DD-slug.md        # /busca --save
  reports/prs-YYYY-MM.md             # /pr-report (opt-in)
  quick/NNN-slug/             # /quick-task (TASK.md + SUMMARY.md)
  tests/                      # Andaime TDD (NÃO commitado)
```

## Inspirações

- **[spec-kit](https://github.com/github/spec-kit)** — toolkit oficial do GitHub para Spec-Driven Development
- **[tlc-spec-driven (Tech Lead's Club)](https://github.com/tech-leads-club/agent-skills/blob/main/packages/skills-catalog/skills/(development)/tlc-spec-driven/SKILL.md)** — skill SDD com fases adaptativas, auto-sizing e formalização de paralelismo. Autor: Felipe Rodrigues. Vários conceitos da v7 são adaptados dela — ver [Atribuições](#atribuições-e-licenças-de-terceiros)
- **[HumanLayer — Advanced Context Engineering](https://www.humanlayer.dev/blog/advanced-context-engineering)** e **[Claude Commands](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands)**
- **[Como eu uso o Claude Code — Workflow SDD](https://dfolloni.substack.com/p/como-eu-uso-o-claude-code-workflow)**
- **[caveman](https://github.com/JuliusBrussee/caveman)** — inspirou conceitualmente a skill `conciso`. Autor: Julius Brussee
- Extreme Programming (XP) — pair programming, TDD, small releases

## Atribuições e Licenças de Terceiros

Este toolkit incorpora conceitos adaptados de terceiros. As licenças originais são preservadas e a atribuição é dada conforme exigido.

### tlc-spec-driven

- **Autor**: Felipe Rodrigues — https://github.com/felipfr
- **Fonte**: https://github.com/tech-leads-club/agent-skills/tree/main/packages/skills-catalog/skills/(development)/tlc-spec-driven
- **Licença original**: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- **Status**: adaptado (não copiado). Conceitos incorporados na v7: auto-sizing por complexidade, memória persistente entre sessões, marcadores `[P]`/`Depends on:`/`Gate:`, Granularity Check, Diagram-Definition Cross-Check, Test Co-location Validation, Phases (Foundation/Core/Integration), `Test count: N tests pass`

A CC-BY-4.0 é permissiva e compatível com a MIT — permite uso, modificação e redistribuição mediante atribuição e indicação de modificações. Esta seção cumpre essa exigência.

### caveman

- **Autor**: Julius Brussee — https://github.com/JuliusBrussee
- **Fonte**: https://github.com/JuliusBrussee/caveman
- **Licença original**: [MIT](https://github.com/JuliusBrussee/caveman/blob/main/LICENSE)
- **Status**: inspirado conceitualmente (não copiado). A skill `conciso` usa o mesmo princípio de cortar tokens via reformatação de estilo, com implementação escrita do zero em pt-BR e níveis ajustáveis de compressão (`lite`/`full`/`ultra`). Detalhes no próprio `SKILL.md` da skill.

## Licença

[MIT](./LICENSE) — código próprio deste toolkit. Trechos adaptados de terceiros mantêm suas licenças originais (ver [Atribuições](#atribuições-e-licenças-de-terceiros)).
