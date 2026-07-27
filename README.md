# claude-code-sdd-toolkit

> **[Read in English](./README-en.md)**

Coleção de slash commands para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) que transformam o agente num par de programação com TDD, seguindo um processo disciplinado: **Especificar comportamento → Planejar → Codar com TDD**.

O planejamento é dividido em dois documentos: a **SPEC de comportamento** (o QUÊ, via `/sdd-spec`) e o **PLAN técnico** (o COMO, via `/sdd-plan`).

## Commands

### Workflow principal

**`/sdd-spec`** — escreve a **especificação de comportamento** (o QUÊ): pesquisa o codebase e produz a SPEC com histórias de usuário, critérios de sucesso, requisitos funcionais/não funcionais, fora de escopo e testes de aceitação em `thoughts/specs/spec-<ts>-<slug>.md`. **Não escreve código, plano nem tarefas** — descreve comportamento, não implementação. Detecta escopo trivial e delega pra `/quick-task`. (Inspirado na gist ["Formação da especificação"](https://gist.github.com/parruda/85bf3d6ee2e8adee5c0dd9429afd76b3) por @parruda.)

**`/sdd-plan`** — consome a SPEC de comportamento e produz o **plano técnico** (o COMO): pesquisa + quebra em tarefas TDD num único doc auto-sized (Medium/Large/Complex) em `thoughts/plans/PLAN-<...>.md`. Cada tarefa rastreia a um requisito funcional (RF) ou teste de aceitação (AT) da SPEC — um 4º check de **Cobertura** garante que nada da SPEC fique sem tarefa. **Antes de quebrar tarefas, os testes são planejados em par com você** (Passo 7.5, interativo por design): lê as convenções de teste do projeto na largada, inventaria o que **já é testado**, e **3 lentes paralelas** (Produto/QA, Engenharia de teste, Adversarial) propõem a cobertura por RF/AT. O resultado vai **pra tela como um Mapa de Testes** — o que temos hoje, o que **não** temos (desta feature e lacunas pré-existentes), o que a feature adiciona (tipo/casos/ambiente/prioridade/custo, marcado ✅ consenso / ⚠️ lentes divergem / ❓ decisão sua) e **pra onde caminhamos** (cobertura antes→depois, ambiente novo exigido, dívida que fica, risco que sobra). Aí a discussão vai ponto a ponto, com recomendação explícita: **a IA propõe, você corta, prioriza e aceita risco.** Caso cortado vira dívida registrada no PLAN, não esquecimento; caso que você adicionou entra marcado `[fonte: usuário]`. A quebra de tarefas herda a matriz fechada — nenhuma tarefa nasce sem saber que teste a cobre, e o painel de review (abaixo) não reabre o que você decidiu. Ao finalizar, **registra no ROADMAP 1 item por PR previsto** (`backlog/`): PLAN que o Check 5 divide em N PRs sequenciais gera N itens (com `Depende de:` ligando os slices), pra nenhum PR ficar esquecido. Detecta escopo Quick e delega pra `/quick-task`.

**`/sdd-plan-eco`** — variante econômica do `/sdd-plan` pra escopo Medium: main em Sonnet, quebra de tarefas + 4 checks delegadas a um único subagente Opus de contexto focado. **O pair de testes continua** (lentes em Sonnet em vez de Opus) — o modo eco corta custo de modelo, nunca a sua mão no produto.

**`/pr-draft`** — abre o PR inicial em draft a partir do plano (branch + empty commit + title/body derivados da **SPEC de comportamento** — histórias de usuário e critérios são a melhor prévia pro reviewer) e cria a worktree pra implementação isolada. **Promove o item do slice no ROADMAP** (`backlog/` → `em-progresso/` + `#PR`) no vault local — nunca no body. **`/pr-draft sync`** (pós-implementação) reescreve o body como prévia pro reviewer em 4 seções — **O quê · Por quê · Como · Test plan** (incluindo desvios do plano e como testar manualmente) — tudo rastreável a SPEC/PLAN/IMP/diff. Nunca tira o PR de draft.

**`/executor-plan`** — executa as tarefas com TDD em modo autônomo, sub-agents paralelos pras tarefas marcadas `[P]`, staging por tarefa. TDD com **red verificável**: roda o teste e confirma que ele **falha pelo motivo certo** antes de implementar — **falso-verde** (teste que passa sem o código) é parada dura, e a evidência do red vai pro log/IMP (o validador Haiku audita). O tipo de teste **vem do PLAN** (não default unit) e, quando o PLAN pede integração/e2e, sobe **ambiente real** pra rodar o red→green: server local em background, Playwright pra telas, sandbox/DB de teste. Exceção ao red só quando a tarefa declara `Tests: none` justificado. Commits sob aprovação humana; `--step` volta ao modo pausado.

**`/verifica`** — verificação comportamental pós-implementação: sobe a aplicação, exercita os fluxos que a mudança tocou e registra **evidência real** no IMP (testes verdes ≠ feature funcionando). Nunca aponta pra produção; pagamentos sempre em test mode; side effects externos só com confirmação.

**`/pr-ready`** — entrega de PR de ponta a ponta. **Avalia** se o PR segue os padrões do projeto (delega ao `/sdd-review` — subagentes Opus independentes); se passar, atualiza o body (`/pr-draft sync`) e faz o handoff pro review humano. **Tirar de draft e marcar reviewer são gates `AskUserQuestion`** (cada um com a opção de "agora não") — nunca automáticos; o handle do reviewer nunca é hardcode. Se não passar, **loop de correção** via `/quick-task` (staging only) → re-avalia → **repete até zero must-fix** ("continue até tudo ok"), quando aprova roda o **gate de verde** (CI passou — deploy incluído — ou, sem CI, a suíte local completa: unit + integração + e2e, **todos** os testes, não só os do PR = regressão; consulta a memória do projeto pra subir o server local), PARA e te entrega os comandos de commit+push, **aguarda o push**, confirma o CI, e só então faz o handoff. O loop é nativo no protocolo (reproduz o builtin `/goal` sem depender dele) e tem circuit-breaker por progresso: rodada que não reduz os must-fix → para e escala (`/sdd-plan`). **Nunca commita/pusha sozinho; só tira de draft com PR aprovado E código pushado.**

**`/quick-task`** — mudança pequena (≤3 arquivos) sem SPEC/PLAN formal. Sobe pro fluxo formal se o escopo crescer.

**`/pair-review`** — companheiro interativo do review manual. Roda em **sessão nova** (`/clear`): re-hidrata do staged + PLAN/IMP (~3-4k tokens, sem o ruído da execução), responde perguntas factuais direto e delega julgamento a subagentes Opus escopados nos arquivos da pergunta, aplica ajustes pequenos com gate + test count protection. Com PR sob review do time, o modo `(r)` valida cada fix **contra o comentário humano que o originou** (detecta não-endereçados, escopa o diff à rodada de fixes, gera rascunhos de resposta pras threads). Walkthrough por tarefa e hotspots opcionais. Nunca commita sem escolha, nunca posta no PR.

**`/sdd-learning`** — após o PR fechar, extrai **reforço comportamental** de IMPs, reviews e do PR no GitHub: onde o time corrigiu o agente é um **erro evitável** que vira regra genérica pra não repetir (reforço negativo); o que passou limpo/foi elogiado vira regra pra repetir (reforço positivo). Sempre generaliza a instância em **princípio + gatilho** (não o caso pontual da feature) e propõe registro na memória, caso a caso. O propósito é o agente ir melhorando — parar de cometer os mesmos erros.

**`/memory-organize`** — reorganiza o auto-memory: órfãs, links quebrados, duplicatas e sub-sumários quando `MEMORY.md` cresce. Modo `revisar` reescreve o **conteúdo** de notas antigas presas ao caso pontual pra **princípio + gatilho** (mesmo padrão que `/sdd-learning` já aplica nas novas), caso a caso, sem inventar motivo que a nota não registrou.

**`/roadmap`** — gerencia o roadmap como **vault Obsidian** em `thoughts/roadmap/`: cada item é um `.md`, dependência é wikilink `[[...]]` e o grafo é nativo (sem mermaid). Status = pasta (`backlog/` · `em-progresso/` · `concluido/`); dependência via `/roadmap dep NNN <- MMM`; sync por status de PR; `migrar` converte o formato antigo (arquivo único). O hub lista 🔴 Próximos e 🔓 Desbloqueados agora (o que um merge liberou).

**`/sdd-close`** — arquiva o par **SPEC+PLAN concluído** (PR **mergeado**): move os docs de `thoughts/specs/` e `thoughts/plans/` pra `closed/` em cada pasta e move o item do roadmap pra `concluido/` (recalculando o que isso desbloqueou). Só age sob PR MERGED, confirmação individual, par junto (detecta o PLAN→SPEC pela linha `SPEC:` do topo). Distinto de `old/` (specs/planos **descartados**, geridos à mão). Nunca commita (`thoughts/` é gitignored).

### Utilitários

**`/sdd-review`** — review de PR, branch ou diff via subagents isolados; oferece gerar fixes via `/quick-task`.

**`/investiga`** — root cause de bug não-óbvio via protocolo de hipóteses: sintoma estruturado → hipóteses com mecanismo causal → evidência em subagents paralelos → eliminação → causa **com fonte** + handoff (`/quick-task` ou `/sdd-plan`). É a maior fábrica de `blocker`/`lesson` pra memória.

**`/sdd-init`** — prepara um projeto novo pro toolkit: audita os pré-requisitos (CLAUDE.md, ARCHITECTURE.md, `thoughts/`, Context7, references) e cria o que falta sob confirmação por bloco — drafts de constitution marcados `[NEEDS REVIEW]`.

**`/git-rebase-seguro`** — atualiza branch longa com a base sem comer código: baseline de testes antes, conflito sempre mostrado (dois lados + proposta), test count protection depois, SHA de rollback garantido. Recomenda merge (não rebase) quando o PR já tem review do time. Nunca pusha.

**`/busca`** — pesquisa web via subagent isolado, sem impacto no contexto principal. Flags `--rapido`, `--profundo` e `--save`.

**`/pr-report`** — relatório de PRs do usuário no repo (semanal inline, mensal e anual salvos).

**`/complexidade`** — mede complexidade ciclomática **só nos arquivos alterados** (vs base ou `--staged`), threshold 10 (ou o do `CLAUDE.md` do projeto). Detecta a ferramenta na ordem linter do projeto → `lizard` → `fta`. Com `--fix`, oferece refactor via `code-simplifier`. O mesmo gate roda embutido no `/sdd-review` (vira issue MINOR/MAJOR) e no `/executor-plan` (correção automática na Verificação Final, parada dura após 2 tentativas).

**`/worktree-detect`** — detecta oportunidades de isolar branches/PRs em worktrees.

**`/status-deps`** — checa o status das dependências externas (Cloudflare, GitHub, PlanetScale/Vitess, AWS) via status pages oficiais. Read-only; resumo com nível por serviço + veredito geral. AWS filtrado por recência (eventos >7d não contam). Pra monitorar em intervalo: `/loop <intervalo> /status-deps`.

**`/modo-livre`** — toggle do modo autônomo em três camadas: allow amplo (flui), **`ask` pra `git commit`/`git push`** (humano no loop garantido pelo harness — prompta em **qualquer** permission mode, inclusive `auto`) e deny dos perigosos (force push, `reset --hard`, `rm -rf`, publishes — bloqueados sempre). Compatível com o permission mode `auto`. Requer reload da sessão. O `/git-worktree` **ativa este modo por default** na worktree que cria (a sessão nova aberta lá já nasce autônoma, sem reload) — use `/git-worktree <branch> --ml-off` pra criar sem.

**`/git-worktree`, `/git-remove-worktree`, `/sync-tests`, `/git-prune-branches`** — utilitários de git e worktree.

**Modelo por command**: a thread principal roda leve (Sonnet base, ou Haiku nos utilitários de git) e só sobe pra Opus **dentro de subagentes**, na etapa que realmente exige raciocínio — assim o modelo caro processa só o contexto focado, sem queimar token nas etapas mecânicas (git, leitura de arquivo, escrita de doc). Trocar de modelo na thread principal (`/model`) invalida o cache de prompt, então os commands evitam isso. Exceção: `/sdd-spec` e `/sdd-plan` rodam em Opus na main (especificar comportamento e planejar são raciocínio interativo denso e espalhado, não isolável num subagente) e delegam só as leituras volumosas a subagentes — pra escopo Medium, o `/sdd-plan-eco` derruba o custo do planejamento. Nos frontmatters os modelos são IDs completos (formato documentado pra slash commands); nos spawns de subagent são **aliases** (`opus`/`sonnet`/`haiku`), garantidos pela doc do Agent SDK — acompanham o melhor modelo de cada tier sem manutenção.

**Progressive disclosure**: os commands grandes mantêm no corpo só o protocolo; templates e blocos de uso pontual vivem em `commands/references/` (instalados em `~/.claude/sdd-references/` — fora de `commands/`, pra não serem registrados como commands namespaced) e são carregados via `Read` apenas no passo que os usa. Isso corta o custo fixo por invocação (~30-40% nos commands pesados) e evita arrastar template de relatório por dezenas de turnos de execução.

### Fluxo recomendado

```
Feature normal:   /sdd-spec → /sdd-plan → /pr-draft → (cd <worktree> && claude) → /executor-plan → /verifica → /pr-ready
                                                                                                    ↓
                                                    avalia → corrige em loop → você commita/pusha → handoff
Entregar um PR:   /pr-ready   (avalia, corrige, sync do body; tira de draft e marca reviewer só se você confirmar — commit/push é seu)
Review manual:    /clear → /pair-review   (companheiro interativo sobre o staged, sem ruído da execução)
Mudança pequena:  /quick-task
Bug misterioso:   /investiga → root cause com fonte → /quick-task ou /sdd-plan
Após PR fechar:   /sdd-learning → /sdd-close (arquiva SPEC+PLAN + move item do ROADMAP)
Projeto novo:     /sdd-init (uma vez)
Quando precisar:  /busca · /verifica · /complexidade · /git-rebase-seguro · /roadmap · /memory-organize
```

`/pr-draft` é opcional, mas recomendado: isola a implementação numa worktree e sinaliza o kickoff ao time. Os artefatos em `thoughts/` servem de handoff entre sessões — limpe a sessão (`/clear`) entre commands grandes pra maximizar a janela de contexto. O custo de re-hidratação é baixo (SPEC/PLAN + `MEMORY.md` ≈ 2-3k tokens), então limpar é quase sempre ganho: o estado durável vive em arquivo, não na conversa.

## Como usar

### 1. Instalação

```bash
# Commands globais (todos os projetos)
cp commands/*.md ~/.claude/commands/
mkdir -p ~/.claude/sdd-references && cp commands/references/* ~/.claude/sdd-references/
cp -r skills/*/ ~/.claude/skills/          # skills (memory-keeper, conciso, structure-cache…)

# Ou por projeto
cp commands/*.md /seu-projeto/.claude/commands/
mkdir -p /seu-projeto/.claude/sdd-references && cp commands/references/* /seu-projeto/.claude/sdd-references/
cp -r skills/*/ /seu-projeto/.claude/skills/
```

> A skill `structure-cache` chama o script `scripts/structure-cache/build.py`. Para usá-la como comando (`structure-cache …`), deixe-o no PATH — via alias ou instalando em `~/.local/bin` (extra opt-in, ver `scripts/`).

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
- **TDD como contrato, red verificável** — teste antes do código; roda e confirma que **falha pelo motivo certo** antes de implementar (falso-verde = parada dura). Se quebram depois, paramos e discutimos
- **Tipo de teste por necessidade** — unit não é default; o tipo (unit/integração/e2e) sai do que o RF/AT exige, planejado na matriz do `/sdd-plan` e executado contra ambiente real quando preciso (server local, Playwright, sandbox)
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

- **Testes se planejam em par** — o `/sdd-plan` lê as convenções do projeto na largada, inventaria o que já é testado, e traz o **Mapa de Testes pra tela** (o que temos / o que não temos / pra onde caminhamos) pra você decidir cortes, prioridade e risco **antes** de qualquer tarefa ser quebrada. Testes codificam comportamento: essa decisão é de produto, não da IA
- **Tipo por necessidade** — unit não é default: lógica pura → unit; interação entre módulos/DB → integração; fluxo de usuário/tela → e2e
- **Red verificável** — o `/executor-plan` roda o teste e confirma que falha antes de implementar; falso-verde é parada dura, evidência do red vai pro IMP
- **Unitários** em `thoughts/tests/`, escritos antes do código. Não commitados — são andaime de trabalho
- **Integração/e2e** vão onde o projeto manda e são commitados; rodam contra **ambiente real** (server local em background, Playwright pra telas, sandbox/DB de teste)
- Se testes que passavam começam a falhar, ou a contagem cai: parada obrigatória pra discutir

## Statusline (opcional)

Barra no rodapé com modelo, pasta, contexto colorido, rate limits (5h/7d) e estado do `/modo-livre` — útil pra saber quando dar `/clear` (barra vermelha em ≥85%) e acompanhar consumo. Rode `/statusline` colando:

```
mostre [nome-do-modelo] entre colchetes, depois nome da pasta atual (basename de .workspace.current_dir), depois uma barra de progresso de 10 blocos usando █ pra preenchido e ░ pra vazio seguida da porcentagem de contexto e da palavra "ctx", depois " • 5h XX% (HhMm)" usando .rate_limits.five_hour.used_percentage e tempo ate .rate_limits.five_hour.resets_at (epoch), depois " • 7d XX% (Dd Hh)" com .rate_limits.seven_day.* na mesma logica; omita as secoes 5h/7d se rate_limits nao existir. e no fim adicione (ML 🟢) quando o arquivo <workspace>/thoughts/modo-livre/active existir ou (ML 🔴) quando nao existir. formato do tempo ate reset (diff = resets_at - now em segundos): se diff <= 0 omita o parentese; se diff < 60 mostre (<1m); se diff < 3600 mostre (Ym); se diff < 86400 mostre (XhYm) sem espaco; se diff >= 86400 mostre (Xd Yh) com espaco entre d e h. cor por threshold (aplicada na barra de contexto e nos numeros dos rate limits, NAO no resto do texto): verde se < 60%, amarelo se 60-84%, vermelho se >= 85%. salve em ~/.claude/statusline.sh com chmod +x e atualize ~/.claude/settings.json
```

Resultado: `[Claude Sonnet 4.5] meu-projeto ████░░░░░░ 42% ctx • 5h 8% (5h30m) • 7d 18% (5d 12h) (ML 🟢)`. Recarregue a sessão após configurar (`Ctrl+C` e `claude`). O layout não mostra branch git (assume que o PS1 já exibe).

## Estrutura

```
commands/                   # Slash commands — FONTE CANÔNICA (copiada pra ~/.claude/commands/)
  sdd-spec.md · sdd-plan.md · sdd-plan-eco.md · pr-draft.md · executor-plan.md · pair-review.md
  quick-task.md · pr-ready.md · sdd-review.md · sdd-learning.md · verifica.md · investiga.md
  sdd-init.md · memory-organize.md · roadmap.md · busca.md · pr-report.md
  complexidade.md · worktree-detect.md · status-deps.md · modo-livre.md · git-worktree.md
  git-remove-worktree.md · git-rebase-seguro.md · sync-tests.md · git-prune-branches.md
  references/               # Templates carregados sob demanda (progressive disclosure)
  deprecated/               # Versões antigas — fallback (sufixo .vN.md). Não deletar
skills/
  memory-keeper/            # Auto-memory: 9 tipos, convenção flat, MEMORY.md como índice
  conciso/                  # Modo de resposta enxuto em pt-BR (lite/full/ultra)
  structure-cache/          # [protótipo] Consulta estrutura do código do cache (importadores/defs/hotspots) sem reler
  deprecated/               # Skills antigas — fallback
scripts/                    # Extras opt-in. Ver scripts/README.md
  ouvir                     # Fala a última resposta via TTS local (pt-BR)
  structure-cache/build.py  # [protótipo] Cache shallow de estrutura de código (TS) invalidado por hash — acelera a pesquisa do /sdd-spec e /sdd-plan sem reler código. Ver "Cache de estrutura" abaixo
```

**`commands/` vs `skills/`** (convenção Anthropic): commands são invocados manualmente (`/sdd-plan`); skills auto-disparam pela descrição quando o contexto bate. `memory-keeper` é skill porque precisa estar sempre disponível pra ler/escrever memória sem o usuário pedir.

### Outputs em `thoughts/` (no projeto-alvo)

```
thoughts/
  roadmap/                    # Visão multi-feature — vault Obsidian (opcional)
    ROADMAP.md                #   hub + backlog/ · em-progresso/ · concluido/
  specs/spec-<ts>-slug.md            # /sdd-spec (comportamento — o QUÊ)
  plans/PLAN-DD-MM-YYYY-slug.md      # /sdd-plan (técnico — o COMO)
  history/IMP-DD-MM-YYYY-slug.md     # /executor-plan
  reviews/                    # /sdd-review
  research/YYYY-MM-DD-slug.md        # /busca --save
  reports/prs-YYYY-MM.md             # /pr-report (opt-in)
  quick/NNN-slug/             # /quick-task (TASK.md + SUMMARY.md)
  tests/                      # Andaime TDD (NÃO commitado)
  cache/structure/            # [protótipo] index.json + manifest.json + HOTSPOTS.md (regenerável, gitignored)
```

### Cache de estrutura (protótipo)

Um índice *shallow* da estrutura do código — quem importa quem, definições por arquivo, god-nodes — pra acelerar a fase de pesquisa do `/sdd-spec` e `/sdd-plan` **sem reler código a cada consulta**. Não é memória: é um **cache regenerável** invalidado por hash (`scripts/structure-cache/build.py`).

- `build [--full]` — extrai defs + imports → `index.json`. **Incremental automático** (reaproveita os arquivos sem hash divergente — sem flag pra lembrar); `--full` força rebuild completo. Determinístico, sem LLM.
- `check` — compara hash atual vs `manifest.json`; é o **backstop de correção** que pega `rebase`/`checkout`/`stash` que os hooks perderam (exit `0`=fresco, `1`=stale).
- **Worktree-safe** e sem digitação: `--root` é **auto-detectado** via `git rev-parse --show-toplevel` — rode `structure-cache build` de qualquer subdir do repo/worktree. De dentro de um worktree linkado o git devolve o root *daquele* worktree, então o cache cai em `<worktree>/thoughts/cache/structure/`, nunca compartilhado, sem thrashing entre branches.
- `query` — consulta sem reler código: `structure-cache query --importers/--imports/--defs/--hotspots [--json]` (exit `3` = sem cache → o caller cai no fallback de reler código).
- `export` — gera `graph.html` **local e self-contained** (força-dirigido em canvas, sem CDN; abre via `file://`). Nós = arquivos coloridos por diretório, tamanho por acoplamento; zoom/pan/hover/filtro. Nada sobe pra fora da máquina. `open` gera e **abre no navegador padrão**; `help` lista tudo.
- **Git hooks opt-in** (`scripts/structure-cache/install-hooks.sh`) — instala `post-commit`/`post-checkout` no hooks-dir **comum** (uma vez, vale pra todos os worktrees) que mantêm o cache morno via build incremental **destacado** (nunca bloqueia o git). `--uninstall` remove só o bloco.
- **Claude Code hook (uso)** — `scripts/structure-cache/pretooluse-cache-nudge.py` é um hook `PreToolUse` (matcher `Grep|Glob`) que lembra o modelo de consultar o cache **antes** de grepar/ler código, mas **só quando o projeto tem cache** (senão sai mudo, custo zero) e sem bloquear o Grep. Registre em `~/.claude/settings.json`: `hooks.PreToolUse[].matcher="Grep|Glob"` → `hooks[].command="python3 <path>/pretooluse-cache-nudge.py"`. Requer reload da sessão.
- Consumido por `/sdd-plan` e `/sdd-spec` na fase de pesquisa (com fallback gracioso) e por `/sdd-learning` (`--hotspots`): o `HOTSPOTS.md` derivado alimenta propostas de `lesson`/`blocker` — o grafo fica no cache, só a **conclusão não-óbvia** vai pra memória.

> Estado atual: motor + `query` + skill wrapper + hooks opt-in + consumo em `/sdd-plan`/`/sdd-spec`/`/sdd-learning`, validados em fixture TS. Falta: extração via **tree-sitter** (hoje regex) e **multi-linguagem** (hoje só TS/JS).

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
