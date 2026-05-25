# claude-code-sdd-toolkit

> **[Read in English](./README-en.md)**

Uma colecao de slash commands para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) que implementam um workflow de **Pair Programming com TDD**.

Esses commands transformam o Claude Code em um par de programacao que segue um processo disciplinado: **Pesquisar -> Entender -> Codar com TDD**.

## O que tem aqui

### Workflow Principal v7 (auto-sizing, single-doc spec)

| Fase | Command | Modelo | Descricao |
|------|---------|--------|-----------|
| Plan | `/sdd-plan` | **Opus** | Pesquisa + entendimento + tarefas em **1 doc auto-sized** (Medium/Large/Complex). Mapeia design docs, reconcilia conflitos, classifica escopo, quebra tarefas com Phases + `[P]`/`Depends on:`/`Gate:`. 3 checks pre-aprovacao (Granularity, Diagram-Definition Cross-Check, Test Co-location). Detecta Quick e delega pra `/quick-task` |
| Codar | `/executor-plan` | **Sonnet** | Pair programming com TDD em **modo autonomo** (sem pausa entre tarefas). Passo 1 forca `/model sonnet` + `/compact` (libera contexto inflado vindo do `/sdd-plan` em Opus). Sub-agents paralelos para `[P]`. Test count protection (bloqueia silent deletion). Staging (`git add`) por tarefa — **commits sob aprovacao humana no fim**. `--step` ativa pausa antiga + commits atomicos imediatos |
| Quick | `/quick-task` | **Opus** | Modo rapido para mudanca pequena (≤3 arquivos, 1 frase). Pula SPEC formal. Safety valve sobe para fluxo formal se escopo crescer. Suporta modos invocados (`autonomo-invocado`/`step-invocado`) quando chamado por `/sdd-review` |
| Aprender | `/sdd-learning` | **Opus** | Tipicamente rodado apos PR fechar. Le IMPs, reviews internos **e consulta GitHub PR** (body, reviews, threads de discussao humanas). Auto-detecta ultimo PR fechado da branch ou aceita `--pr <N>`. Extrai aprendizado nao-obvio via 5 filtros duros + decisao emergente de threads, propoe registro no auto-memory via skill `memory-keeper` (9 tipos). Confirma por item. Atualiza > cria. **Substitui o antigo `/sdd-confirm`** (deprecated). |
| Manutencao | `/memory-organize` | **Sonnet** | Reorganiza o auto-memory do projeto: detecta orfas/links quebrados/duplicatas, propoe sub-sumarios quando `MEMORY.md` cresce (>150 linhas). Aplica sob confirmacao por bloco. Sonnet pelos pontos de julgamento semantico (duplicatas, guardrail diluido, conteudo inline anti-pattern) |
| Roadmap | `/roadmap` | **Haiku** | Gerencia `thoughts/ROADMAP.md`. Adiciona entradas, importa de issues GH, sincroniza status com SPEC/IMP existentes. Fluxo mecanico — Haiku suficiente |

> **Modelos por command** (todos forcam o modelo no frontmatter):
> - **Opus** — raciocinio profundo: `/sdd-plan`, `/sdd-review`, `/sdd-learning`, `/quick-task`
> - **Sonnet** — execucao + analise leve: `/executor-plan`, `/modo-livre`, `/worktree-detect`, `/busca` (main), `/memory-organize`
> - **Haiku** — operacoes mecanicas: `/git-worktree`, `/git-remove-worktree`, `/git-prune-branches`, `/sync-tests`, `/roadmap`, `/busca --rapido`
>
> Commands em Opus tem passo 1 explicito (`/model opus`). Commands em Sonnet tem passo 1 (`/model sonnet` + `/compact` em `/executor-plan` e `/modo-livre`, que tipicamente recebem contexto inflado de Opus). Commands em Haiku confiam apenas no frontmatter — nao precisam de passo de troca explicito porque sao tao curtos que se o usuario invocar em outro modelo, o desperdicio eh marginal.

### Utilitarios

| Command | Modelo | Descricao |
|---------|--------|-----------|
| `/sdd-review` | **Opus** + delega 6 subagents `code-reviewer` | Analisa PR, branch ou diff e gera relatorio privado. **Independente do `/executor-plan`** (Sonnet): roda em Opus + delega analise pra subagents `code-reviewer` (built-in, isolam contexto da implementacao) |
| `/busca [--rapido\|--profundo] [--save] <query>` | **Sonnet** (main) + Haiku/Sonnet/Opus (subagent por flag) | Pesquisa web via subagent isolado. `--rapido` = Haiku (lookup factual). default = Sonnet (exploracao media). `--profundo` = Opus (comparacao com nuance). `--save` persiste em `thoughts/research/`. **Zero impacto no contexto principal** — subagent nao herda historico |
| `/git-worktree` | **Haiku** | Cria uma worktree isolada para trabalho paralelo |
| `/git-remove-worktree` | **Haiku** | Remove uma worktree de forma segura (chama `/sync-tests` antes) |
| `/sync-tests` | **Haiku** | Sincroniza testes TDD entre worktree e root, mostrando diffs antes de agir |
| `/git-prune-branches` | **Haiku** | Remove branches locais cujas remotas ja foram deletadas |
| `/pr-report [--mes\|--de --ate\|--semana\|anual]` | **Haiku** | Relatorio de PRs do user no repo atual. **Semanal** so inline (3 visoes: abri/mergeei/revisei). **Mensal** com quantitativo (taxa de merge) + qualitativo (lead time, engajamento) + opt-in salvar em `thoughts/reports/`. **Anual** consolida mensais ja salvos via bloco YAML machine-readable. Desconsidera PRs `closed` sem merge |
| `/worktree-detect` | **Sonnet** | Analisa branches/PRs e detecta oportunidades de split em worktrees (classificacao por dominio + score de complexidade + ordem de merge — exige sintese) |
| `/modo-livre [on\|off\|update\|status]` | **Sonnet** | Toggle do modo autônomo. Passo 1 forca `/model sonnet` + `/compact`. `on` faz backup do `.claude/settings.local.json` e instala um com allow amplo + deny dos perigosos (commit/push/rm/etc). `off` restaura o backup. `update` reescreve só o settings com a versão atual do JSON canônico (preserva backup). Quando ativo, agente opera sem prompts pra leitura/edição/internet/MCPs/git-read e respeita guardrails negativos absolutos. Requer recarregar a sessão após toggle/update. Por-worktree: cada worktree precisa do seu próprio toggle |

### Versoes anteriores

- **Split v7 (gerador-prd + gerador-spec)** — versao anterior do workflow tinha 2 fases separadas (PRD em `thoughts/research/` + SPEC em `thoughts/plans/`). Foram fundidas em `/sdd-plan` (1 doc auto-sized) por causar ~40-50% de duplicacao entre os 2 outputs. Arquivos preservados em `commands/deprecated/gerador-prd.v7.md` e `commands/deprecated/gerador-spec.v7.md`
- **`/sdd-confirm` (v7)** — gerenciava ciclo "criar draft em `thoughts/decisions-draft/` -> aguardar merge -> mover pro auto-memory". Substituido nesta iteracao pelo `/sdd-learning` ampliado, que extrai aprendizado direto do PR no GitHub apos o merge (body + reviews + threads humanas). Arquivo preservado em `commands/deprecated/sdd-confirm.v7.md` como fallback pra projetos legados com drafts pendentes
- **v1-v6** — versoes historicas em `commands/deprecated/` com sufixo `.vN.md` (ex: `executor-plan.v6.md`, `gerador-prd.v5.md`). Pra usar uma versao antiga como fallback, copie o `.vN.md` desejado pra `~/.claude/commands/<nome>.md` (sem o sufixo)
- **Commands promovidos a skill** — `sdd-review.v1.md`, `vault-memory.v7.md` e `worktree-detect.v1.md` em `commands/deprecated/` sao versoes antigas (eram commands) de artefatos que hoje vivem como skill ou continuam como command mas foram reescritos

## Principios

- **Zero Inferencia** — Nunca assume comportamento de APIs ou padroes. Verifica na documentacao oficial (via [Context7](https://context7.com/)) ou no codigo existente
- **Constitution-first** — Commands leem `CLAUDE.md` e `ARCHITECTURE.md` antes de qualquer acao
- **TDD como contrato** — Testes unitarios sao escritos antes do codigo. Se quebram, paramos e discutimos
- **Memoria persistente** — auto-memory nativo do Claude Code (`~/.claude/projects/<projeto>/memory/`) guarda decisoes/blockers/licoes/etc entre sessoes, gerenciado pela skill `memory-keeper`. Escrita sempre sob confirmacao
- **Auto-sizing** — Complexidade determina profundidade: Quick (`/quick-task`), Medium/Large/Complex (1 SPEC em `/sdd-plan`)
- **Modelo certo pra cada fase** — Opus pra planejar/revisar (raciocinio profundo), Sonnet pra executar (custo/velocidade), Haiku pra lookup factual. Cada command forca o modelo no frontmatter + passo 1 explicito (`/model <modelo>` + `/compact` quando troca pra modelo menor). Review independente de execucao: `/sdd-review` (Opus) usa subagent `code-reviewer` pra nao herdar contexto do `/executor-plan` (Sonnet)
- **Test count protection** — Toda tarefa declara `Test count: N tests pass`. Cair = bloqueio (previne silent deletion)
- **Paralelismo seguro** — Tarefas `[P]` rodam em sub-agents simultaneos, com checagem de conflito de arquivos
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
Quick — mudanca pequena (≤3 arquivos, 1 frase):
  /quick-task     -> Opus. Executa direto com TDD onde aplicavel
                     (safety valve: se crescer, sugere fluxo formal)

Medium/Large/Complex — feature normal:
  /sdd-plan       -> Opus. Pesquisa + entendimento + tarefas em 1 doc auto-sized
                     (Mapeia design docs, classifica escopo, quebra tarefas com [P],
                      3 checks pre-aprovacao: Granularity, Diagram, Test Co-location)
  /executor-plan  -> Sonnet. Passo 1 ja roda /model sonnet + /compact (libera contexto
                     inflado do /sdd-plan). MODO AUTONOMO (default): codar com TDD em
                     cadeia, sub-agents paralelos para [P], staging por tarefa
                     (sem commit). --step volta ao comportamento antigo
  /sdd-review     -> Opus + subagents code-reviewer. Independente do executor:
                     analise feita por "cerebro" diferente (modelo + contexto isolado).
                     Classifica issues (CRITICAL/MAJOR/MINOR), oferece gerar fixes
                     via /quick-task. Fixes ficam staged junto.
    voce revisa o diff completo no VSCode -> commit + push manualmente

A qualquer momento (busca otimizada):
  /busca <query>            -> Sonnet (subagent). Exploracao media, conceito tecnico
  /busca --rapido <query>   -> Haiku (subagent). Lookup factual (versao, comando, sintaxe)
  /busca --profundo <query> -> Opus (subagent). Comparacao com nuance, trade-offs
  /busca --save <query>     -> + salva em thoughts/research/

Apos PR fechar (mergeado ou nao):
  /sdd-learning   -> Opus. Auto-detecta ultimo PR fechado da branch (ou aceita --pr <N>).
                     Le IMPs + reviews internos + body/reviews/threads humanas do PR.
                     Aplica 5 filtros duros + decisao emergente de threads de discussao.
                     Propoe candidatos um por um -> auto-memory via memory-keeper.
                     Substitui o antigo /sdd-confirm (deprecated).

Manutencao periodica:
  /memory-organize  -> arruma o auto-memory (orfas, links quebrados, sub-sumarios)

Multi-feature (visao de cima):
  /roadmap                       -> sincroniza status com SPECs/IMPs
  /roadmap add "<descricao>"     -> adiciona ao Backlog
  /roadmap add #123              -> importa de issue GH
```

> **Por que `/compact` automatico no `/executor-plan` e `/modo-livre`?** O `/sdd-plan` roda em Opus e infla o contexto com pesquisa + 3 checks + reconciliacao de docs. Ao trocar pra Sonnet no `/executor-plan` (passo 1), rodamos `/compact` em seguida — o resumo eh gerado em Sonnet (mais barato que Opus) e libera espaco pra implementacao. Sessao nova sem command previo: pula o `/compact`, nao ha o que compactar.

> **Por que modo autonomo no executor**: o usuario relatou dificuldade de revisar mudancas no VSCode depois que cada tarefa virava commit (diff fica preso no historico do git). Com staging acumulado, o VSCode Source Control panel mostra todo o diff continuo, facilitando revisao humana antes do commit final.

> Limpe a sessao entre commands grandes (PRD -> SPEC -> Executor) para maximizar a janela de contexto. Os artefatos em `thoughts/` servem como handoff entre sessoes.

### 4. Memoria persistente (auto-memory)

Os commands recuperam contexto entre sessoes via **auto-memory nativo do Claude Code** (`~/.claude/projects/<projeto>/memory/`), gerenciado pela skill `memory-keeper`. O harness carrega `MEMORY.md` automaticamente no system prompt no inicio de cada sessao (limite 200 linhas ou 25KB).

**Estrutura** (convencao flat — sem subpastas):

```
~/.claude/projects/<projeto>/memory/
├── MEMORY.md                          # Indice carregado automaticamente — tabela agrupada por tipo
├── feedback_bash_permission_syntax.md # Notas individuais (carregadas sob demanda)
├── decision_<slug>.md
├── blocker_<slug>.md
├── lesson_<slug>.md
├── _summary_<tipo>.md                 # Sub-sumarios (criados pelo /memory-organize)
└── ...
```

**9 tipos** (4 nativos do harness + 5 SDD):

| Tipo | Captura |
|---|---|
| `user` | Perfil, preferencias do usuario |
| `feedback` | Regra de colaboracao (faca X / nunca Y) |
| `project` | Decisao/contexto/deadline nao-obvio sobre o trabalho |
| `reference` | Ponteiro pra sistema externo (Linear, Grafana, etc) |
| `decision` | Decisao arquitetural/tecnica do projeto |
| `blocker` | Bloqueio conhecido + workaround |
| `lesson` | Aprendizado de execucao/review |
| `idea` | Ideia pra explorar depois |
| `preference` | Preferencia especifica deste projeto |

**Convencao**: arquivo flat `<tipo>_<slug>.md`. Frontmatter minimo: `name`, `description`, `metadata.type`. Veja `skills/memory-keeper/SKILL.md` para o protocolo completo e `references/nota-template.md` para os 9 templates de corpo.

**Aprendizado pos-merge**: durante o desenvolvimento, os commands SDD anotam decisoes/blockers/licoes no proprio relatorio (IMP, SUMMARY) ou oferecem salvar direto na memoria via opcao `(m)` quando a decisao ja eh definitiva. Apos o PR fechar, `/sdd-learning` extrai aprendizado lendo IMPs, reviews internos **e o PR no GitHub** (body, reviews formais, threads de discussao humana). A decisao emergente das threads vira candidato — voce aprova caso a caso. (Antes desta iteracao, o fluxo usava drafts em `thoughts/decisions-draft/` + `/sdd-confirm`; ambos foram substituidos pela fonte GitHub no `/sdd-learning`.)

**Manutencao**: rode `/memory-organize` quando `MEMORY.md` crescer (>150 linhas) ou quando suspeitar de orfas/duplicatas. O command propoe sub-sumarios por tipo (`_summary_<tipo>.md`, carregados sob demanda) pra manter o indice principal enxuto.

**Escrita sempre sob confirmacao do usuario** — o command propoe entradas, voce aprova caso a caso.

### 5. Testes

- **Testes unitarios**: Sempre em `thoughts/tests/`, escritos antes do codigo (TDD). Nao sao commitados, sao nosso andaime de trabalho
- **Test count protection**: Toda tarefa declara `Test count: N tests pass`. Se cair durante execucao = parada obrigatoria (previne silent deletion)
- **Testes de integracao/e2e**: Quando o projeto usa, vao onde o projeto manda e sao commitados
- **Test co-location**: Testes vao na MESMA tarefa que cria o codigo. Defer = anti-pattern bloqueado pelo sdd-plan
- Se testes que passavam comecam a falhar: parada obrigatoria para discutir

### 6. Statusline com contexto, rate limits e indicador de modo-livre (opcional)

Configure uma barra no rodape do Claude Code que mostra **modelo + pasta + barra colorida de contexto + rate limits da Anthropic (5h e 7d) com tempo ate o reset + estado do `/modo-livre`**. Util pra saber quando dar `/clear` ou `/compact` (barra vermelha em ≥85%), pra acompanhar consumo das janelas de uso e pra confirmar a olho se o `/modo-livre` esta ativo no projeto.

> Nota: este layout NAO mostra branch git, partindo do princípio que o terminal/PS1 ja exibe. Se voce quiser a branch, adicione " (branch-do-git *)" entre `<pasta>` e a barra de contexto na frase abaixo.

Dentro do Claude Code, rode `/statusline` colando este prompt:

```
mostre [nome-do-modelo] entre colchetes, depois nome da pasta atual (basename de .workspace.current_dir), depois uma barra de progresso de 10 blocos usando █ pra preenchido e ░ pra vazio seguida da porcentagem de contexto e da palavra "ctx", depois " • 5h XX% (HhMm)" usando .rate_limits.five_hour.used_percentage e tempo ate .rate_limits.five_hour.resets_at (epoch), depois " • 7d XX% (Dd Hh)" com .rate_limits.seven_day.* na mesma logica; omita as secoes 5h/7d se rate_limits nao existir. e no fim adicione (ML 🟢) quando o arquivo <workspace>/thoughts/modo-livre/active existir ou (ML 🔴) quando nao existir. formato do tempo ate reset (diff = resets_at - now em segundos): se diff <= 0 omita o parentese; se diff < 60 mostre (<1m); se diff < 3600 mostre (Ym); se diff < 86400 mostre (XhYm) sem espaco; se diff >= 86400 mostre (Xd Yh) com espaco entre d e h. cor por threshold (aplicada na barra de contexto e nos numeros dos rate limits, NAO no resto do texto): verde se < 60%, amarelo se 60-84%, vermelho se >= 85%. salve em ~/.claude/statusline.sh com chmod +x e atualize ~/.claude/settings.json
```

Resultado:

```
[Claude Sonnet 4.5] gopay ████░░░░░░ 42% ctx • 5h 8% (5h30m) • 7d 18% (5d 12h) (ML 🟢)
```

Componentes (da esquerda pra direita):

- `[Claude Sonnet 4.5]` — modelo ativo na sessao
- `gopay` — basename da pasta atual
- `████░░░░░░ 42% ctx` — barra de 10 blocos e porcentagem da janela de contexto. Colorida por threshold: **verde** < 60%, **amarelo** 60-84%, **vermelho** ≥ 85%
- `• 5h 8% (5h30m)` — consumo da janela de 5 horas da Anthropic + tempo restante ate o reset (formato `XhYm`). Numero colorido na mesma escala da barra de contexto. Omitido se o campo `rate_limits` nao vier no JSON
- `• 7d 18% (5d 12h)` — consumo da janela de 7 dias + tempo ate o reset (formato `Xd Yh`)
- `(ML 🟢)` ou `(ML 🔴)` — `/modo-livre` **ATIVO** (verde) ou **INATIVO** (vermelho) no projeto atual, detectado via marker em `thoughts/modo-livre/active`

Recarregue a sessao apos configurar: `Ctrl+C` e `claude` de novo.

## Estrutura

### Toolkit

```
CLAUDE.md                   # Constituicao do repo (regras pro agente que edita o toolkit)
commands/                   # Slash commands (invocação manual via /)
  sdd-plan.md               # v7+ — Pesquisar + Entender + Tarefas (1 doc auto-sized) [Opus]
  executor-plan.md          # v7 — Codar com TDD + paralelismo [Sonnet + /compact]
  quick-task.md             # v7 — Modo rapido [Opus]
  sdd-review.md             # Review independente com subagents code-reviewer [Opus]
  busca.md                  # Pesquisa via subagent isolado [Sonnet main + Haiku/Sonnet/Opus subagent]
  sdd-learning.md           # Colher aprendizado de IMPs+reviews+PR GitHub -> auto-memory [Opus]
  roadmap.md                # v7 — Gerenciar ROADMAP.md
  memory-organize.md        # Reorganizar auto-memory (orfas, links quebrados, sub-sumarios)
  modo-livre.md             # Modo autonomo com guardrails negativos [Sonnet + /compact]
  git-worktree.md           # Criar worktree
  git-remove-worktree.md    # Remover worktree
  sync-tests.md             # Sincronizar testes TDD
  git-prune-branches.md     # Limpar branches
  pr-report.md              # Relatorio semanal/mensal/anual de PRs (do user, no repo atual) [Haiku]
  worktree-detect.md        # Analisar worktrees
  deprecated/               # Versoes antigas — fallback (sufixo .vN.md)
    executor-plan.v1.md ... v6.md
    gerador-prd.v1.md ... v7.md      # v1-v6 + v7 (split PRD+SPEC substituido por sdd-plan)
    gerador-spec.v1.md ... v7.md     # idem
    sdd-review.v1.md
    vault-memory.v7.md      # Promovido para skill, depois substituido por memory-keeper (v7+)
    worktree-detect.v1.md
skills/                     # Skills (auto-trigger via descrição)
  memory-keeper/            # Auto-memory: 9 tipos (4 nativos + 5 SDD), convencao flat, MEMORY.md em tabela
    SKILL.md
    references/
      nota-template.md
      memory-md-template.md
  conciso/                  # Modo conciso de resposta em pt-BR (lite/full/ultra)
    SKILL.md
  deprecated/               # Skills antigas — fallback
    vault-memory/           # Substituida por memory-keeper (v7+)
```

**Por que skills/ e commands/ separados** (convenção Anthropic):
- **`commands/`** — slash commands invocados manualmente (`/sdd-plan`, `/executor-plan`, etc). O usuário decide quando rodar.
- **`skills/`** — auto-trigger pela descrição. O agente decide invocar quando o contexto bate. `memory-keeper` é skill porque precisa estar "sempre disponível" pra ler/escrever memórias persistentes sem o usuário precisar lembrar de chamar.

A integração entre as duas pontas: os commands SDD (`/sdd-plan`, `/executor-plan`, `/quick-task`, `/sdd-learning`, `/sdd-confirm`) referenciam a skill `memory-keeper` para o protocolo de leitura/escrita no auto-memory — todos os 9 tipos (4 nativos + 5 SDD) seguem o mesmo contrato. O command `/memory-organize` faz a manutencao periodica (sub-sumarios, orfas, links quebrados).

**Skills disponíveis:**

| Skill | Função |
|---|---|
| `memory-keeper` | Lê/escreve memórias persistentes no auto-memory nativo do Claude Code. 9 tipos (4 nativos + 5 SDD), convenção flat, MEMORY.md em formato tabela |
| `conciso` | Modo de resposta enxuto em pt-BR com 3 níveis (`/conciso lite\|full\|ultra`) — corta enchimento, mantém precisão técnica. Inspirado no [caveman](https://github.com/JuliusBrussee/caveman). Economia ~25-70% nos tokens de saída |

### Outputs em `thoughts/` (no projeto onde os commands rodam)

```
thoughts/
  ROADMAP.md                  # Visao multi-feature (opcional)
  plans/
    SPEC-DD-MM-YYYY-slug.md   # Output do /sdd-plan (1 doc auto-sized)
  history/
    IMP-DD-MM-YYYY-slug.md    # Output do /executor-plan
  reviews/
    (output do /sdd-review)
  research/
    YYYY-MM-DD-slug.md        # Output do /busca quando invocado com --save (ou opt-in pos-busca profunda)
  reports/
    prs-YYYY-MM.md            # Output mensal do /pr-report (opt-in)
    prs-YYYY-anual.md         # Output anual do /pr-report (consolida mensais via bloco YAML)
  quick/
    NNN-slug/
      TASK.md                 # Input do /quick-task
      SUMMARY.md              # Output do /quick-task
  tests/                      # Andaime TDD (NAO commitado)
  decisions-draft/            # [LEGADO] Drafts de memoria. Pasta NAO eh mais criada pelos commands novos —
                              # /sdd-learning extrai aprendizado direto do PR/IMP/review. Mantida no diagrama
                              # apenas pra projetos legados com drafts pendentes processaveis via
                              # commands/deprecated/sdd-confirm.v7.md
```

> Antes da v7, os artefatos ficavam em `thoughts/shared/`. A v7 simplifica removendo `shared/` — testes TDD continuam isolados em `thoughts/tests/`. A pasta `thoughts/research/` voltou nesta iteracao, mas com proposito diferente: agora eh output opt-in do `/busca` (pesquisa via subagent), nao mais do antigo `gerador-prd` (cujo conteudo foi fundido em `/sdd-plan`).
>
> **`thoughts/decisions-draft/` foi descontinuada nesta iteracao.** O fluxo "criar draft -> aguardar merge -> /sdd-confirm" foi substituido por: anotacao no proprio IMP/SUMMARY do command + extracao pelo `/sdd-learning` apos PR fechar (que agora consulta o PR no GitHub). Projetos legados com drafts pendentes podem rodar `commands/deprecated/sdd-confirm.v7.md` uma ultima vez pra processar o backlog.

## Inspiracoes

- **[spec-kit](https://github.com/github/spec-kit)** — Toolkit oficial do GitHub para Spec-Driven Development
- **[tlc-spec-driven (Tech Lead's Club)](https://github.com/tech-leads-club/agent-skills/blob/main/packages/skills-catalog/skills/(development)/tlc-spec-driven/SKILL.md)** — Skill de Spec-Driven Development com 4 fases adaptativas (Specify, Design, Tasks, Execute), auto-sizing por complexidade, STATE.md persistente, Test Co-location Validation e formalizacao de paralelismo (`[P]`, `Depends on:`, `Gate:`). Autor: Felipe Rodrigues. A partir da v7 deste toolkit, varios conceitos sao adaptados desta skill — veja [Atribuicoes](#atribuicoes-e-licencas-de-terceiros)
- **[HumanLayer — Advanced Context Engineering](https://www.humanlayer.dev/blog/advanced-context-engineering)** — Padroes de context engineering para agentes de IA
- **[HumanLayer Claude Commands](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands)** — Exemplos praticos de commands
- **[Como eu uso o Claude Code — Workflow SDD](https://dfolloni.substack.com/p/como-eu-uso-o-claude-code-workflow)** — Walkthrough de um workflow SDD real
- **[caveman](https://github.com/JuliusBrussee/caveman)** — Skill que reformata respostas pra cortar tokens de saida (~65-75%) sem perder substancia tecnica. Inspirou conceitualmente o skill `conciso` deste toolkit (implementacao independente em pt-BR). Autor: Julius Brussee. Veja [Atribuicoes](#atribuicoes-e-licencas-de-terceiros)
- Extreme Programming (XP) — Pair programming, TDD, small releases

## Atribuicoes e Licencas de Terceiros

Este toolkit incorpora conceitos adaptados de obras de terceiros. As licencas originais sao preservadas e atribuicao e dada conforme exigido.

### tlc-spec-driven

- **Autor**: Felipe Rodrigues — https://github.com/felipfr
- **Fonte**: https://github.com/tech-leads-club/agent-skills/tree/main/packages/skills-catalog/skills/(development)/tlc-spec-driven
- **Licenca original**: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- **Status**: adaptado (nao copiado literalmente). Conceitos incorporados a partir da v7 deste toolkit: auto-sizing por complexidade (Quick/Medium/Large/Complex), memoria persistente entre sessoes, marcadores `[P]` / `Depends on:` / `Gate:` em tarefas, Granularity Check, Diagram-Definition Cross-Check, Test Co-location Validation, agrupamento em Phases (Foundation/Core/Integration), `Test count: N tests pass (no silent deletions)`

A CC-BY-4.0 e uma licenca permissiva e compativel com a MIT — permite uso, modificacao e redistribuicao desde que se atribua o autor original e se indiquem modificacoes feitas. Esta secao cumpre essa exigencia.

### caveman

- **Autor**: Julius Brussee — https://github.com/JuliusBrussee
- **Fonte**: https://github.com/JuliusBrussee/caveman
- **Licenca original**: [MIT](https://github.com/JuliusBrussee/caveman/blob/main/LICENSE)
- **Status**: inspirado conceitualmente (nao copiado). O skill `conciso` deste toolkit (`skills/conciso/SKILL.md`) usa o mesmo principio de cortar tokens de saida via reformatacao de estilo, mas a implementacao foi escrita do zero em pt-BR. Conceito incorporado: niveis ajustaveis de compressao (caveman tem `lite`/`full`/`ultra`/`wenyan`; `conciso` adapta para `lite`/`full`/`ultra` em pt-BR sem o estilo "caveman speak" telegrafico quebrado). Detalhes completos de atribuicao no proprio `SKILL.md` da skill.

A MIT e uma licenca permissiva e compativel com a MIT deste toolkit. Como nao houve copia literal de codigo ou texto, basta a atribuicao acima. Esta secao cumpre essa boa pratica.

## Licenca

[MIT](./LICENSE) — codigo proprio deste toolkit. Trechos adaptados de obras de terceiros mantem suas licencas originais (ver [Atribuicoes](#atribuicoes-e-licencas-de-terceiros)).
