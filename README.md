# claude-code-sdd-toolkit

> **[Read in English](./README-en.md)**

Uma colecao de slash commands para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) que implementam um workflow de **Pair Programming com TDD**.

Esses commands transformam o Claude Code em um par de programacao que segue um processo disciplinado: **Pesquisar -> Entender -> Codar com TDD**.

## O que tem aqui

### Workflow Principal v7 (auto-sizing, single-doc spec)

| Fase | Command | Descricao |
|------|---------|-----------|
| Plan | `/sdd-plan` | Pesquisa + entendimento + tarefas em **1 doc auto-sized** (Medium/Large/Complex). Mapeia design docs, reconcilia conflitos, classifica escopo, quebra tarefas com Phases + `[P]`/`Depends on:`/`Gate:`. 3 checks pre-aprovacao (Granularity, Diagram-Definition Cross-Check, Test Co-location). Detecta Quick e delega pra `/quick-task` |
| Codar | `/executor-plan` | Pair programming com TDD em **modo autonomo** (sem pausa entre tarefas). Sub-agents paralelos para `[P]`. Test count protection (bloqueia silent deletion). Staging (`git add`) por tarefa — **commits sob aprovacao humana no fim**. `--step` ativa pausa antiga + commits atomicos imediatos |
| Quick | `/quick-task` | Modo rapido para mudanca pequena (≤3 arquivos, 1 frase). Pula SPEC formal. Safety valve sobe para fluxo formal se escopo crescer. Suporta modos invocados (`autonomo-invocado`/`step-invocado`) quando chamado por `/sdd-review` |
| Aprender | `/sdd-learning` | Le IMPs e reviews, extrai aprendizado nao-obvio, propoe registro no vault (sabor SDD em `state/` ou geral em `feedback`/`project`/`reference`). Confirma por item. Atualiza > cria. |
| Roadmap | `/roadmap` | Gerencia `thoughts/ROADMAP.md`. Adiciona entradas, importa de issues GH, sincroniza status com SPEC/IMP existentes |

### Utilitarios

| Command | Descricao |
|---------|-----------|
| `/sdd-review` | Analisa PR, branch ou diff e gera relatorio privado de review |
| `/git-worktree` | Cria uma worktree isolada para trabalho paralelo |
| `/git-remove-worktree` | Remove uma worktree de forma segura (chama `/sync-tests` antes) |
| `/sync-tests` | Sincroniza testes TDD entre worktree e root, mostrando diffs antes de agir |
| `/git-prune-branches` | Remove branches locais cujas remotas ja foram deletadas |
| `/worktree-detect` | Analisa branches/PRs e detecta oportunidades de split em worktrees |
| `/modo-livre [on\|off\|update\|status]` | Toggle do modo autônomo. `on` faz backup do `.claude/settings.local.json` e instala um com allow amplo + deny dos perigosos (commit/push/rm/etc). `off` restaura o backup. `update` reescreve só o settings com a versão atual do JSON canônico (preserva backup) — útil quando o command é atualizado. Quando ativo, agente opera sem prompts pra leitura/edição/internet/MCPs/git-read e respeita guardrails negativos absolutos. Requer recarregar a sessão após toggle/update. Por-worktree: cada worktree precisa do seu próprio toggle |

### Versoes anteriores

- **Split v7 (gerador-prd + gerador-spec)** — versao anterior do workflow tinha 2 fases separadas (PRD em `thoughts/research/` + SPEC em `thoughts/plans/`). Foram fundidas em `/sdd-plan` (1 doc auto-sized) por causar ~40-50% de duplicacao entre os 2 outputs. Arquivos preservados em `commands/deprecated/gerador-prd.v7.md` e `commands/deprecated/gerador-spec.v7.md`
- **v1-v6** — versoes historicas em `commands/deprecated/` com sufixo `.vN.md` (ex: `executor-plan.v6.md`, `gerador-prd.v5.md`). Pra usar uma versao antiga como fallback, copie o `.vN.md` desejado pra `~/.claude/commands/<nome>.md` (sem o sufixo)
- **Commands promovidos a skill** — `sdd-review.v1.md`, `vault-memory.v7.md` e `worktree-detect.v1.md` em `commands/deprecated/` sao versoes antigas (eram commands) de artefatos que hoje vivem como skill ou continuam como command mas foram reescritos

## Principios

- **Zero Inferencia** — Nunca assume comportamento de APIs ou padroes. Verifica na documentacao oficial (via [Context7](https://context7.com/)) ou no codigo existente
- **Constitution-first** — Commands leem `CLAUDE.md` e `ARCHITECTURE.md` antes de qualquer acao
- **TDD como contrato** — Testes unitarios sao escritos antes do codigo. Se quebram, paramos e discutimos
- **Memoria persistente** — `thoughts/STATE.md` guarda decisoes/blockers/licoes entre sessoes. Escrita sempre sob confirmacao
- **Auto-sizing** — Complexidade determina profundidade: Quick (`/quick-task`), Medium/Large/Complex (1 SPEC em `/sdd-plan`)
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
  /quick-task     -> executa direto com TDD onde aplicavel
                     (safety valve: se crescer, sugere fluxo formal)

Medium/Large/Complex — feature normal:
  /sdd-plan       -> pesquisa + entendimento + tarefas em 1 doc auto-sized
                     (Mapeia design docs, classifica escopo, quebra tarefas com [P],
                      3 checks pre-aprovacao: Granularity, Diagram, Test Co-location)
    limpar sessao
  /executor-plan  -> MODO AUTONOMO (default): codar com TDD em cadeia (sem pausa),
                     sub-agents paralelos para [P], staging por tarefa (sem commit).
                     /executor-plan --step volta ao comportamento antigo (pausa
                     entre tarefas + commits atomicos imediatos)
    limpar sessao
  /sdd-review     -> revisa o diff staged, classifica issues (CRITICAL/MAJOR/MINOR)
                     e oferece gerar fixes via /quick-task (autonomo em cadeia OU
                     pausando entre cada). Fixes ficam staged junto.
    voce revisa o diff completo no VSCode -> commit + push manualmente

Apos a feature mergeada:
  /sdd-learning   -> colhe aprendizado de IMPs+reviews -> vault

Multi-feature (visao de cima):
  /roadmap                       -> sincroniza status com SPECs/IMPs
  /roadmap add "<descricao>"     -> adiciona ao Backlog
  /roadmap add #123              -> importa de issue GH
```

> **Por que modo autonomo no executor**: o usuario relatou dificuldade de revisar mudancas no VSCode depois que cada tarefa virava commit (diff fica preso no historico do git). Com staging acumulado, o VSCode Source Control panel mostra todo o diff continuo, facilitando revisao humana antes do commit final.

> Limpe a sessao entre commands grandes (PRD -> SPEC -> Executor) para maximizar a janela de contexto. Os artefatos em `thoughts/` servem como handoff entre sessoes.

### 4. Memoria persistente (STATE.md ou vault)

Os commands recuperam contexto entre sessoes via memoria persistente. **Dois modos**:

**Modo legacy (default)** — `thoughts/STATE.md` monolitico:
- **Decisoes arquiteturais** — decisoes que persistem alem de uma feature
- **Blockers conhecidos** — coisas que ja travaram trabalho, com sintoma para reconhecer
- **Licoes aprendidas** — abordagens testadas que nao funcionaram, padroes que provaram valor
- **Ideias adiadas** — coisas que apareceram mas nao entraram no escopo atual
- **Preferencias do usuario** — estilo de trabalho, ferramentas, padroes de comunicacao

**Modo vault (opcional)** — notas atomicas em vault central (segundo cerebro Obsidian):

```bash
export CLAUDE_VAULT_PATH=~/caminho/para/seu/vault
```

Se a variavel `$CLAUDE_VAULT_PATH` apontar para um diretorio existente, os commands passam a ler/escrever em:

```
$CLAUDE_VAULT_PATH/<org>/<projeto>/state/
├── decisoes/   # 1 nota por decisao, com frontmatter
├── blockers/
├── licoes/
├── ideias/
└── preferencias/
```

Vantagens do modo vault:
- **Versionamento independente** do projeto (state nao polui o repo)
- **Grafo unificado** entre projetos (Obsidian conecta decisoes cross-projeto)
- **Notas atomicas** (1 arquivo por decisao) — busca e filtragem melhores
- **Promocao** de decisoes para escopo de organizacao ou global

Convencao de path: o `<org>` e `<projeto>` sao derivados do `cwd` (heuristica `~/codigos/<org>/<projeto>/`). Se a heuristica falhar, o command pergunta. Ver o skill `vault-memory` para o protocolo completo.

**A integracao e completamente opt-in** — sem `CLAUDE_VAULT_PATH`, o toolkit funciona exatamente como antes (STATE.md monolitico). Voce pode adotar gradualmente.

Em qualquer modo: **escrita sempre sob confirmacao do usuario** — o command propoe entradas, voce aprova caso a caso.

### 5. Testes

- **Testes unitarios**: Sempre em `thoughts/tests/`, escritos antes do codigo (TDD). Nao sao commitados, sao nosso andaime de trabalho
- **Test count protection**: Toda tarefa declara `Test count: N tests pass`. Se cair durante execucao = parada obrigatoria (previne silent deletion)
- **Testes de integracao/e2e**: Quando o projeto usa, vao onde o projeto manda e sao commitados
- **Test co-location**: Testes vao na MESMA tarefa que cria o codigo. Defer = anti-pattern bloqueado pelo sdd-plan
- Se testes que passavam comecam a falhar: parada obrigatoria para discutir

### 6. Statusline com indicador de modo-livre e contexto (opcional)

Configure uma barra no rodape do Claude Code que mostra **modelo + pasta + branch git + barra colorida de contexto + estado do `/modo-livre`**. Util pra saber quando dar `/clear` ou `/compact` (barra fica vermelha em ≥85% de contexto) e pra confirmar a olho se o `/modo-livre` esta ativo no projeto.

Dentro do Claude Code, rode `/statusline` colando este prompt:

```
mostre [nome-do-modelo] entre colchetes, depois nome da pasta atual (basename de .workspace.current_dir), depois (branch-do-git) com asterisco antes do parentese de fechar se o working tree estiver dirty (omita se nao for repo git), depois uma barra de progresso de 10 blocos usando █ pra preenchido e ░ pra vazio seguida da porcentagem de contexto e da palavra "ctx", e no fim adicione (ML 🟢) quando o arquivo <workspace>/thoughts/modo-livre/active existir ou (ML 🔴) quando nao existir. cor da barra de progresso: verde se menor que 60%, amarelo se entre 60 e 84%, vermelho se 85% ou mais. salve em ~/.claude/statusline.sh com chmod +x e atualize ~/.claude/settings.json
```

Resultado:

```
[Claude Sonnet 4.5] gopay (main *) ████░░░░░░ 42% ctx (ML 🟢)
```

Componentes (da esquerda pra direita):

- `[Claude Sonnet 4.5]` — modelo ativo na sessao
- `gopay` — basename da pasta atual
- `(main *)` — branch git; `*` aparece quando ha mudancas locais nao commitadas
- `████░░░░░░` — barra de 10 blocos, colorida por threshold: **verde** < 60%, **amarelo** 60-84%, **vermelho** ≥ 85%
- `42% ctx` — porcentagem da janela de contexto consumida
- `(ML 🟢)` ou `(ML 🔴)` — `/modo-livre` **ATIVO** (verde) ou **INATIVO** (vermelho) no projeto atual, detectado via marker em `thoughts/modo-livre/active`

Recarregue a sessao apos configurar: `Ctrl+C` e `claude` de novo.

## Estrutura

### Toolkit

```
CLAUDE.md                   # Constituicao do repo (regras pro agente que edita o toolkit)
commands/                   # Slash commands (invocação manual via /)
  sdd-plan.md               # v7+ — Pesquisar + Entender + Tarefas (1 doc auto-sized)
  executor-plan.md          # v7 — Codar com TDD + paralelismo
  quick-task.md             # v7 — Modo rapido
  roadmap.md                # v7 — Gerenciar ROADMAP.md
  sdd-review.md             # Review
  sdd-learning.md           # Colher aprendizado de IMPs+reviews -> vault
  modo-livre.md             # Modo autonomo com guardrails negativos
  git-worktree.md           # Criar worktree
  git-remove-worktree.md    # Remover worktree
  sync-tests.md             # Sincronizar testes TDD
  git-prune-branches.md     # Limpar branches
  worktree-detect.md        # Analisar worktrees
  deprecated/               # Versoes antigas — fallback (sufixo .vN.md)
    executor-plan.v1.md ... v6.md
    gerador-prd.v1.md ... v7.md      # v1-v6 + v7 (split PRD+SPEC substituido por sdd-plan)
    gerador-spec.v1.md ... v7.md     # idem
    sdd-review.v1.md
    vault-memory.v7.md      # Promovido para skill (atualmente em skills/vault-memory/)
    worktree-detect.v1.md
skills/                     # Skills (auto-trigger via descrição)
  vault-memory/             # Sabor geral: user/feedback/project/reference no vault
    SKILL.md
    references/
      hub-template.md
      nota-template.md
  conciso/                  # Modo conciso de resposta em pt-BR (lite/full/ultra)
    SKILL.md
  deprecated/               # Skills antigas — fallback (vazio por ora, .gitkeep)
```

**Por que skills/ e commands/ separados** (convenção Anthropic):
- **`commands/`** — slash commands invocados manualmente (`/sdd-plan`, `/executor-plan`, etc). O usuário decide quando rodar.
- **`skills/`** — auto-trigger pela descrição. O agente decide invocar quando o contexto bate. `vault-memory` é skill porque precisa estar "sempre disponível" pra ler/escrever memórias gerais sem o usuário precisar lembrar de chamar.

A integração entre as duas pontas: os commands SDD (`sdd-plan`, `executor-plan`, `quick-task`, `sdd-learning`) referenciam o skill `vault-memory` para o protocolo de leitura/escrita no vault — eles cuidam do sabor "SDD persistente" (`state/`) e o skill cuida do sabor "geral" (`feedback`/`project`/`reference`/`user`).

**Skills disponíveis:**

| Skill | Função |
|---|---|
| `vault-memory` | Lê/escreve memórias gerais (user/feedback/project/reference) em vault Obsidian central (`$CLAUDE_VAULT_PATH`) |
| `conciso` | Modo de resposta enxuto em pt-BR com 3 níveis (`/conciso lite\|full\|ultra`) — corta enchimento, mantém precisão técnica. Inspirado no [caveman](https://github.com/JuliusBrussee/caveman). Economia ~25-70% nos tokens de saída |

### Outputs em `thoughts/` (no projeto onde os commands rodam)

```
thoughts/
  ROADMAP.md                  # Visao multi-feature (opcional)
  STATE.md                    # Memoria persistente (opcional, criado sob confirmacao)
  plans/
    SPEC-DD-MM-YYYY-slug.md   # Output do /sdd-plan (1 doc auto-sized)
  history/
    IMP-DD-MM-YYYY-slug.md    # Output do /executor-plan
  reviews/
    (output do /sdd-review)
  quick/
    NNN-slug/
      TASK.md                 # Input do /quick-task
      SUMMARY.md              # Output do /quick-task
  tests/                      # Andaime TDD (NAO commitado)
```

> Antes da v7, os artefatos ficavam em `thoughts/shared/`. A v7 simplifica removendo `shared/` — testes TDD continuam isolados em `thoughts/tests/`. A pasta `thoughts/research/` (usada pelo `gerador-prd`) foi removida — `/sdd-plan` salva direto em `thoughts/plans/`.

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
- **Status**: adaptado (nao copiado literalmente). Conceitos incorporados a partir da v7 deste toolkit: auto-sizing por complexidade (Quick/Medium/Large/Complex), `STATE.md` persistente, marcadores `[P]` / `Depends on:` / `Gate:` em tarefas, Granularity Check, Diagram-Definition Cross-Check, Test Co-location Validation, agrupamento em Phases (Foundation/Core/Integration), `Test count: N tests pass (no silent deletions)`

A CC-BY-4.0 e uma licenca permissiva e compativel com a MIT — permite uso, modificacao e redistribuicao desde que se atribua o autor original e se indiquem modificacoes feitas. Esta secao cumpre essa exigencia.

### caveman

- **Autor**: Julius Brussee — https://github.com/JuliusBrussee
- **Fonte**: https://github.com/JuliusBrussee/caveman
- **Licenca original**: [MIT](https://github.com/JuliusBrussee/caveman/blob/main/LICENSE)
- **Status**: inspirado conceitualmente (nao copiado). O skill `conciso` deste toolkit (`skills/conciso/SKILL.md`) usa o mesmo principio de cortar tokens de saida via reformatacao de estilo, mas a implementacao foi escrita do zero em pt-BR. Conceito incorporado: niveis ajustaveis de compressao (caveman tem `lite`/`full`/`ultra`/`wenyan`; `conciso` adapta para `lite`/`full`/`ultra` em pt-BR sem o estilo "caveman speak" telegrafico quebrado). Detalhes completos de atribuicao no proprio `SKILL.md` da skill.

A MIT e uma licenca permissiva e compativel com a MIT deste toolkit. Como nao houve copia literal de codigo ou texto, basta a atribuicao acima. Esta secao cumpre essa boa pratica.

## Licenca

[MIT](./LICENSE) — codigo proprio deste toolkit. Trechos adaptados de obras de terceiros mantem suas licencas originais (ver [Atribuicoes](#atribuicoes-e-licencas-de-terceiros)).
