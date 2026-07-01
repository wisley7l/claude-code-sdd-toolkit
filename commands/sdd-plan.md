---
description: Consome a SPEC de comportamento (/sdd-spec) e gera o plano tecnico — pesquisa + tarefas TDD num doc auto-sized (Medium/Large/Complex). Quick delega pra /quick-task.
model: claude-opus-4-8
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Agent, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(git fetch*), Bash(gh *), Bash(ls *), Bash(mkdir *), Bash(find *), Bash(pwd), WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs
# Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe Rodrigues
# https://github.com/tech-leads-club/agent-skills
# Conceitos adaptados: doc auto-sized, Knowledge Verification Chain, memoria persistente,
# checks de qualidade, test co-location, handoff explicito. Pipeline SPEC (comportamento) -> PLAN (tecnico).
---

# SDD Plan — Da SPEC de comportamento ao plano tecnico

Voce e um **par tecnico** que recebe a **SPEC de comportamento** (o QUE, produzida pelo `/sdd-spec`), pesquisa o que precisa, decide a abordagem e quebra em tarefas executaveis — o PLAN tecnico (o COMO). O tamanho do doc se ajusta ao escopo.

**Voce nao escreve codigo — investiga, decide, organiza. A execucao e do `/executor-plan`.**
**Voce nao re-especifica comportamento — isso ja esta na SPEC. Se faltar comportamento, volte pro `/sdd-spec`.**

## Quando NAO usar este skill

- **Mudanca trivial** (≤3 arquivos, 1 frase, sem decisao arquitetural): use `/quick-task`. Este skill detecta esse caso e delega.
- **Bug fix simples** (root cause obvio, fix em 1 arquivo): use `/quick-task`.
- **Comportamento ainda nao especificado**: rode `/sdd-spec` antes — o PLAN se apoia na SPEC.

## Principios

- **SPEC-first**: o PLAN se apoia na SPEC de comportamento. Cada tarefa rastreia a um Requisito Funcional (RF) ou Teste de Aceitacao (AT) da SPEC. Comportamento ausente/ambiguo na SPEC = volte pro `/sdd-spec`, nao improvise
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` delimitam toda decisao tecnica
- **Memoria persistente**: o `MEMORY.md` ja vem carregado pelo harness. Abra notas individuais relevantes sob demanda. Proponha registro novo so com confirmacao. Detalhes no skill `memory-keeper`
- **Knowledge Verification Chain**: Memoria (cache verificado) → Codebase → Project docs → Context7 → Web → Flag como incerto. Nunca pule etapas
- **Zero Inferencia**: toda afirmacao tecnica com `[Fonte: url]` ou `[Fonte: path:line]`. Sem fonte = `[NEEDS VERIFICATION]`
- **Nunca fabrique**: prefira "nao encontrei documentacao para X" a chutar
- **Profundidade proporcional**: pesquisa rasa para Medium, profunda para Complex
- **Test co-location**: testes na MESMA tarefa que cria o codigo. Defer = anti-pattern
- **Test count protection**: toda tarefa com Gate declara contagem esperada
- **Cobertura da SPEC**: todo RF/AT da SPEC tem ≥1 tarefa que o cobre. Lacuna = plano incompleto
- **Skills do projeto**: liste e ative — executor depende disso

## Auto-sizing

A SPEC ja delimita o comportamento; o auto-sizing aqui calibra a **profundidade da pesquisa tecnica e do plano**:

| Escopo | Sinais | O que o PLAN contem |
|---|---|---|
| **Quick** | ≤3 arquivos, sem decisao arquitetural, sem nova lib | **Saia e sugira `/quick-task`** — nao escreva plano |
| **Medium** | <10 tarefas, sem decisao arquitetural nova, dominio conhecido | Plano enxuto: analise local + decisoes tecnicas + tarefas. Pesquisa externa so se houver lib/API nao consolidada |
| **Large** | Multi-componente, 10+ tarefas, decisoes arquiteturais novas, dominio conhecido | Plano completo: pesquisa externa + decisoes embasadas + tarefas formalizadas + diagrama |
| **Complex** | Integracao com sistema critico, decisoes tecnicas de alto impacto, multiplos `[NEEDS VERIFICATION]` | Plano completo + discussao das decisoes tecnicas com usuario antes de quebrar tarefas |

**Safety valve**: se comecou Medium e ao quebrar tarefas surgir >10 ou dependencia nao obvia, escale para Large e refaca a quebra.

**Handoff para Quick**: se classificar como Quick, **nao continue**. Apresente:

```
Esta task parece quick (≤3 arquivos, sem decisao arquitetural).
Sugiro rodar /quick-task — plano formal seria overhead.

Confirma quick-task ou prefere o fluxo formal mesmo assim?
```

Se confirmar quick, encerre. Se insistir, classifique como Medium e prossiga.

## Resolucao do diretorio root

Antes de salvar qualquer arquivo em `thoughts/`, resolva o root do projeto principal:

```bash
git worktree list | head -1 | awk '{print $1}'
```

Use esse caminho como base para `thoughts/` (specs, plans, history, STATE.md, ROADMAP.md). Garante que outputs sejam salvos no repo principal mesmo executando dentro de worktree.

**Excecao: `thoughts/tests/`** — andaime TDD fica local ao worktree (gerenciado pelo `/executor-plan`).

## Configuracao inicial

### 1. Modelo (Opus — excecao deliberada)

Este e um dos dois commands do toolkit que rodam em Opus na thread principal (o outro e o `/sdd-spec`). O motivo: o planejamento e um raciocinio interativo denso (auto-sizing, knowledge verification chain, reconciliacao de docs, quebra de tarefas, checks) entrelacado com checkpoints do usuario — nao da pra isolar num subagente sem perder a interacao. O `model: claude-opus-4-8` no frontmatter ja sobe a execucao em Opus: **siga direto pro Passo 1, sem mencionar nada e sem rodar `/model`** (trocar de modelo na main invalida o cache de prompt).

Pra manter o contexto Opus enxuto, **delegue toda leitura volumosa a subagentes** (Passos 3, 4 e 5): o subagente le os arquivos/docs/fontes no modelo dele e devolve so a sintese.

**Variante economica**: pra escopo Medium com orcamento apertado existe o `/sdd-plan-eco` — main em Sonnet, com a quebra de tarefas + checks delegadas a um unico subagente Opus de contexto focado.

### Flags

Extraia estas flags de `$ARGUMENTS` antes de tratar o resto como path da SPEC (a flag **nao** e path). Controlam a revisao por painel do Passo 9.5:

| Flag | Efeito |
|---|---|
| _(nenhuma)_ | Painel completo — 4 lentes (Pro, Fast, Security, Tests) |
| `--rapido` | So Pro + Fast (pula Security/Tests) |
| `--solo` | Pula o Passo 9.5 — fica so nos 4 checks self-run do Passo 9 |

Nao entram no auto-sizing nem no fluxo — so na decisao do Passo 9.5. O que sobrar de `$ARGUMENTS` depois de remover a flag e o path da SPEC (Passo 2).

### 2. Localizar e ler a SPEC de comportamento

A SPEC e a entrada principal deste skill.

- **Path passado em `$ARGUMENTS`** (ja sem a flag): use direto (ex.: `thoughts/specs/spec-<ts>-<slug>.md`).
- **Sem path**: procure a SPEC mais recente:
  ```bash
  ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
  ls -t "${ROOT:-.}"/thoughts/specs/spec-*.md 2>/dev/null | head -1
  ```
  Confirme com o usuario qual SPEC usar antes de prosseguir.
- **Nenhuma SPEC encontrada**: sugira rodar `/sdd-spec` primeiro:
  ```
  Nao encontrei SPEC de comportamento em thoughts/specs/.
  O fluxo recomendado e /sdd-spec antes do plano.

  Quer (a) rodar /sdd-spec agora, ou (b) seguir mesmo assim — eu sintetizo um
  entendimento minimo a partir da sua descricao e do codebase (sem SPEC formal)?
  ```
  Se `(b)`, registre no PLAN que **nao houve SPEC formal** e derive o entendimento inline.

Da SPEC, extraia: historias de usuario, criterios de sucesso, **RFs numerados**, requisitos nao funcionais, fora de escopo, contexto tecnico/integracao e **testes de aceitacao**. Eles guiam a quebra de tarefas e a checagem de Cobertura (Passo 9).

### 3. Ler constitution
`CLAUDE.md` e `ARCHITECTURE.md`.

### 4. Ler memoria persistente

O `MEMORY.md` ja esta carregado pelo harness. Use as tabelas como indice, abra apenas as notas (`<tipo>_<slug>.md`) relevantes pro plano (decisoes ja tomadas, blockers, licoes, ideias adiadas). Se houver sub-sumarios (`_summary_<tipo>.md`), abra so quando o tipo for relevante.

Resolva o path do auto-memory pra escritas (Passo 13):
```bash
ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
PROJ_ENC=$(echo "${ROOT:-$(pwd)}" | sed 's|/|-|g')
MEM_DIR="$HOME/.claude/projects/$PROJ_ENC/memory"
```

### 5. Ler skills do projeto
`.claude/skills/` — absorva padroes que vao virar `Skills:` nas tarefas.

---

## Fluxo de execucao

### Passo 1 — Classificar escopo

Aplique o auto-sizing (calibra a profundidade tecnica). Apresente:

```
Classifiquei como [Medium/Large/Complex] porque:
- [criterio 1]
- [criterio 2]

Concorda? Se Quick, te encaminho para /quick-task.
```

Se Quick, **encerre** com handoff (ver secao Auto-sizing).

### Passo 2 — Mapear design docs existentes

**Bloqueante** — antes de qualquer pesquisa nova, descubra o que ja existe.

| Local | O que costuma ter |
|---|---|
| `ARCHITECTURE.md`, `DESIGN.md` (raiz) | Decisoes estruturais, padroes |
| `docs/`, `documentation/` | Docs gerais, guias |
| `docs/adr/`, `docs/decisions/`, `decisions/` | ADRs |
| `docs/rfcs/`, `rfcs/` | RFCs internos |
| `README.md` (raiz, packages/*, apps/*) | Frequentemente tem secao Architecture |
| `.specs/`, `specs/`, `spec/` | Outros toolkits SDD |
| `CONTRIBUTING.md` | Padroes e convencoes |

Para cada doc encontrado: **RELEVANTE** | **DESATUALIZADO** | **NAO RELEVANTE**.

Para varredura ampla, use subagent `Agent` (`subagent_type: Explore`) — localiza e classifica, devolvendo so o resumo.

Registre na secao "Design Docs Existentes" do PLAN. **Conflitos** entre docs e codigo viram pendencias bloqueantes.

### Passo 3 — Pesquisa do codebase

Identifique:
- Arquivos relevantes (partindo do Contexto Tecnico da SPEC)
- Dependencias instaladas (verificar antes de sugerir lib nova)
- Padroes ja em uso para problemas similares

Use subagent `Agent` com `subagent_type: Explore` para pesquisas amplas (>3 queries).

### Passo 4 — Pesquisa externa (condicional)

**Medium**: pule se nao houver lib/API nova fora do que ja esta no projeto.
**Large/Complex**: aplique a Knowledge Verification Chain integralmente.

```
Step 0: Memoria      → notas `reference_*` do auto-memory ja verificaram esse claim? (cache de conhecimento)
Step 1: Codebase     → ja existe algo similar? como esta sendo feito hoje?
Step 2: Project docs → ARCHITECTURE.md, ADRs, README mencionam?
Step 3: Context7 MCP → resolve library ID, query docs oficiais atualizadas
Step 4: Web search   → docs oficiais, fontes reputadas
Step 5: Flag incerto → "nao encontrei documentacao para X" + [NEEDS VERIFICATION]
```

**Regras**:
- Nunca pule para Step 5 se Steps 1-4 estao disponiveis
- Toda referencia externa precisa de `[Fonte: url]`
- Step 5 e SEMPRE flagado como `[NEEDS VERIFICATION]`
- **Step 0 (cache de conhecimento)**: se existir nota `reference` cobrindo o claim, com fonte + data de verificacao <90 dias + mesma major version da lib, use-a e pule Steps 3-4 **pra esse claim** — cite `[Fonte: <url da nota>, cache <data>]`. Cache vencido ou major version diferente = re-verifique na fonte e atualize a nota

Delegue a pesquisa externa a um subagente `Agent` quando envolver multiplas queries — devolve so a sintese com `[Fonte: url]`.

### Passo 5 — Issue/PR (se aplicavel)

Se o usuario passou numero:
```bash
gh issue view <numero>
gh pr view <numero>
gh api repos/<org>/<repo>/pulls/<numero>/comments  # se houver inline comments relevantes
```

### Passo 6 — Resolver decisoes tecnicas pendentes

**Bloqueante** — nao avance sem resolver.

Gray areas de **comportamento** ja foram fechadas na SPEC. Aqui resolva apenas **decisoes tecnicas** que a pesquisa abriu (escolha de lib, padrao de integracao, estrategia de migracao) e que dependem do usuario:

```
A pesquisa abriu [N] decisoes tecnicas antes do plano:

1. [Questao tecnica] — Impacto: [o que bloqueia]
2. [Questao tecnica] — Impacto: [o que bloqueia]

Como voce quer resolver cada uma?
```

Se a duvida for de **comportamento** (o sistema deveria fazer X ou Y?), isso e lacuna da SPEC — **pare e volte pro `/sdd-spec`** pra fechar antes de planejar.

Aguarde respostas. Registre na secao "Decisoes Tecnicas" do PLAN com justificativa.

**Para escopo Complex**: dedique uma discussao explicita das decisoes tecnicas antes de quebrar tarefas.

### Passo 7 — Reconciliar com docs existentes

Para cada doc RELEVANTE listado no Passo 2:
- **Alinhado**: o PLAN respeita o doc. Referencie em `Baseado em:` das tarefas
- **Conflito**: **BLOQUEIE** e pergunte:

```
O doc [path] define [X], mas para esta feature precisamos [Y].

Opcoes:
1. Ajustar a abordagem para respeitar o doc
2. Atualizar o doc (tarefa separada antes ou junto)
3. Doc esta desatualizado — atualizar primeiro

Como prefere resolver?
```

### Passo 8 — Desenhar abordagem e quebrar tarefas

**Cada tarefa tem**:
- `What:` — entrega exata (1 frase)
- `Covers:` — RF/AT da SPEC que esta tarefa atende (ex.: `RF2, AT2`)
- `Where:` — caminho do arquivo
- `Depends on:` — tarefas anteriores (ou `None`)
- `Reuses:` — codigo existente a reaproveitar (poupa tokens)
- `Skills:` — skills de `.claude/skills/` para ativar
- `Riscos:` — desafios relevantes
- `Tests:` — `unit` | `integration` | `e2e` | `none` (com justificativa explicita se none)
- `Gate:` — comando exato de verificacao
- `Done when:` — checklist com `Test count: N tests pass (no silent deletions)` quando aplicavel
- `[P]` — marca tarefas paralelizaveis (sem dependencias mutuas, sem estado compartilhado)
- `Commit:` — formato da mensagem (ex: `feat(escopo): descricao`)

**Granularidade**:
- 1 componente / 1 funcao / 1 endpoint = OK
- 2-3 coisas relacionadas no mesmo arquivo = OK se coeso
- Multiplos arquivos ou componentes = SPLIT

**Phases** (agrupamento visual):
- **Foundation**: tipos, interfaces, migrations (sequencial)
- **Core**: implementacao principal (geralmente onde `[P]` aparece)
- **Integration**: wiring, e2e (sequencial)

### Passo 9 — 5 checks de qualidade

Execute antes de apresentar. Checks 1-4 sao **bloqueantes**: FALHA = reestruture e re-rode. Check 5 (PR Size) e **advisory**: nao bloqueia, mas dispara aviso + proposta de split conforme a faixa.

**Check 1: Granularity**

| Tarefa | Escopo | Status |
|---|---|---|
| T1 | 1 componente | OK |
| T2 | 5+ arquivos | FALHA — SPLIT |

**Check 2: Diagram-Definition Cross-Check**

| Tarefa | Depends on (corpo) | Diagrama mostra | Status |
|---|---|---|---|
| T2 | T1 | T1 → T2 | OK |
| T3 | T1 | T2 → T3 | FALHA — Mismatch |

Regras:
- Toda `Depends on` no corpo tem seta no diagrama
- Toda seta no diagrama tem `Depends on` correspondente
- Tarefas `[P]` na mesma fase nao dependem umas das outras

**Check 3: Test Co-location**

| Tarefa | Camada | Tipo de teste necessario | Tarefa declara | Status |
|---|---|---|---|---|
| T2 | service | unit | unit | OK |
| T3 | controller | e2e | none | VIOLACAO |

Regras:
- "Testado em outra tarefa" NAO justifica `Tests: none`. Defer = anti-pattern.
- Se uma tarefa cria codigo so testavel depois de outra, **reestruture** (merge forward/backward).
- Toda tarefa que cria codigo produz codigo testavel naquela tarefa.

**Check 4: SPEC Coverage**

| RF/AT da SPEC | Coberto por tarefa | Status |
|---|---|---|
| RF1 | T2 | OK |
| RF3 | — | FALHA — sem tarefa |
| AT2 | T4 | OK |

Regras:
- Todo RF e todo AT da SPEC tem ≥1 tarefa em `Covers:`.
- RF/AT sem tarefa = plano incompleto: adicione tarefa ou, se for comportamento fora de escopo, confirme com o usuario que sai do PLAN.
- Tarefa sem `Covers:` = escopo inventado: rastreie a um RF/AT ou remova.

**Check 5: PR Size (reviewability)**

Um PR grande demais cansa o reviewer humano e esconde bug. Estime os **arquivos distintos que entram no diff do PR** = union dos `Where:` de todas as tarefas + testes commitados (integration/e2e). Testes unitarios em `thoughts/tests/` **nao contam** (andaime, nao commitado).

| Arquivos distintos | Faixa | Acao |
|---|---|---|
| ≤10 | Ideal | Segue |
| 11–15 | Aceitavel | Segue; anote a contagem no checkpoint |
| 16–20 | Grande (caso raro) | **Avise** no checkpoint: PR no limite do review humano. Proponha uma fronteira de split (quais phases/tarefas viram PR 1 vs PR 2). Seguir num PR so exige justificativa explicita do usuario |
| >20 | Grande demais | **Recomende fortemente dividir** em PRs sequenciais. Apresente a fronteira de split sugerida (por phase ou por RF/AT coeso) e peca confirmacao antes de seguir num PR unico |

Regras:
- A fronteira de split respeita dependencias: PR 1 nao pode depender de codigo que so existe no PR 2. Corte em limites de phase ou em grupos de RF/AT independentes.
- **Nao auto-divida** nem reescreva a SPEC: proponha a fronteira e deixe o usuario decidir (um plano com marcador de PRs sequenciais, ou o usuario estreita a SPEC).
- Contagem e estimativa (arquivos podem se sobrepor entre tarefas) — na duvida, arredonde pra cima e sinalize.

### Passo 9.5 — Revisao por painel de subagentes

Os 4 checks do Passo 9 sao **self-run** — o mesmo Opus que escreveu o plano se autoavalia, o que carrega o vies do autor. Este passo traz **olhos frescos e independentes** antes do checkpoint, com lentes diversas (perspectivas diferentes pegam falhas que redundancia nao pega).

**Roda por default em todo escopo** — Medium, Large ou Complex. (Quick nao chega aqui: foi encaminhado pro `/quick-task` no Passo 1.) Flags em `$ARGUMENTS` ajustam o painel (ver "Flags" na Configuracao inicial):
- **(sem flag)** → painel completo (4 lentes).
- **`--rapido`** → so **Pro + Fast** (pula Security/Tests). Bom pra plano sem superficie sensivel nem logica de teste complexa.
- **`--solo`** → pula este passo inteiro; fica so nos 4 checks self-run do Passo 9.

O `/sdd-plan-eco` tambem roda sem painel por design.

**Painel (4 lentes disjuntas)**, cada uma um subagente `Agent` em **paralelo, no mesmo turno** (uma unica resposta com as 4 chamadas — turnos separados serializam), `model: opus`, `subagent_type: general-purpose`. Cada um recebe o **draft completo do PLAN** inline (ainda nao foi escrito — o checkpoint e depois), o path da SPEC e a constitution:
- **Reviewer Pro** — arquitetura, consistencia com codebase/constitution, decisoes tecnicas embasadas, `Reuses:`, rastreabilidade estrutural (todo RF/AT tem tarefa em `Covers:`), riscos.
- **Reviewer Fast** — clareza e ausencia de ambiguidade, completude dos detalhes (da pra executar sem chutar?), granularidade das tarefas, diagrama x dependencias.
- **Reviewer Security** — dominio pagamentos/e-commerce: HMAC de webhook, idempotencia, money handling (nunca float), PCI (nao logar dado sensivel), authz, validacao runtime de input nao-confiavel, race conditions/ordering. **APPROVED rapido se o plano nao toca superficie sensivel** — nao invente risco.
- **Reviewer Tests** — todo RF/AT tem teste que o *exercita* (nao so tarefa que o entrega), test co-location, gate e test count coerentes, casos de borda/negativos e caminhos de erro, estrategia de mock (sandbox vs unit).

Retorno estruturado (JSON com `verdict` + `findings` por severidade), **nao** "APPROVED" cego.

**Reconciliacao**: verifique cada `must-fix` voce mesmo antes de aplicar (reviewer erra) — aplique so os validos, descarte os invalidos com motivo. Se aplicou algum `must-fix`, rode **nova rodada com subagentes frescos**. Repita ate **todo o painel** retornar `APPROVED` (zero `must-fix`). **Guarda de convergencia**: se uma rodada nao reduz os `must-fix` validos, ou apos 3 rodadas, pare e leve os itens abertos pro checkpoint. (Teto de custo: 4 lentes x ate 3 rodadas; os especialistas Security/Tests curto-circuitam com APPROVED quando seu dominio nao aparece no plano.)

Protocolo completo (prompts literais das 4 lentes, schema de finding, loop): reference `sdd-plan-panel-review.md` — procure em `.claude/sdd-references/` do projeto, senao em `~/.claude/sdd-references/`. **Fallback** (reference ausente): monte o prompt com lente base comum (cobertura de RF/AT, precisao tecnica, clareza, testes, rastreabilidade) trocando so o foco declarado por lente (Pro/Fast/Security/Tests acima); exija retorno JSON `{verdict, findings:[{severidade, ancora, problema, correcao}]}` com `APPROVED` so quando zero `must-fix`; verifique cada `must-fix` antes de aplicar; rode ate aprovacao de todo o painel com a guarda de convergencia acima.

Alimente o resultado no checkpoint (Passo 10).

### Passo 10 — Checkpoint pre-aprovacao

**Antes de escrever o arquivo**, apresente para o usuario:

```
## Classificacao
Escopo: [Medium/Large/Complex]
SPEC base: [path da SPEC]

## Resumo Executivo (preview)
[2-3 linhas do que vai ser feito]

## Tarefas (visao de cima)
- Foundation: [T1, T2]
- Core: [T3 [P], T4 [P]]
- Integration: [T5]

## Decisoes Tecnicas
[Decisoes tecnicas resolvidas no Passo 6]

## Reconciliacao com Docs
[Docs RELEVANTES / conflitos resolvidos]

## Cobertura da SPEC
[Todo RF/AT coberto? lacunas resolvidas?]

## Riscos principais
[bullets curtos]

## 4 Checks
- Granularity: OK
- Diagram-Definition Cross-Check: OK
- Test Co-location: OK
- SPEC Coverage: OK
- PR Size: [N arquivos distintos — Ideal/Aceitavel/Grande; se >15: fronteira de split sugerida]

## Revisao por painel (Pro / Fast / Security / Tests)
Aprovada em [N] rodada(s) — 0 must-fix aberto
  (ou) Aberta: [X] must-fix nao resolvidos apos [N] rodadas → [lista curta por lente]

Faz sentido? Ajusta algo antes de eu finalizar?
```

Aguarde aprovacao.

### Passo 11 — Verificacao de claims externos

**Bloqueante** — antes de escrever, revise toda decisao que referencia API/lib externa:
1. Liste cada claim externa
2. Verifique `[Fonte: url]` ou `[Fonte: path:line]`
3. Claims sem fonte → `[NEEDS VERIFICATION]` em "Duvidas Pendentes"

### Passo 12 — Verificacao de links (subagent)

Apos escrever o arquivo, lance subagent para validar URLs:
1. Extraia todas URLs em `[Fonte: url]`
2. `WebFetch` em cada — pagina real, nao 404
3. Adicione tabela ao final:

```markdown
## Verificacao de Links

| URL | Status |
|---|---|
| [url] | OK / QUEBRADO — [motivo] |
```

4. Links quebrados: pesquise alternativa, atualize ou mova para `[NEEDS VERIFICATION]`
5. Reescreva com correcoes antes de informar o usuario

### Passo 13 — Propor registro de memoria

Se aparecer:
- Decisao arquitetural recorrente
- Padrao que virou convencao
- Blocker persistente
- Licao importante
- **Claim externa verificada** (Context7/web) que tende a reaparecer nas proximas features da mesma stack → nota `reference` (cache de conhecimento): claim + fonte + data da verificacao + versao da lib. Alimenta o Step 0 da Knowledge Verification Chain. Pra esse tipo, `(m)` direto e o default — nao depende de review

Pergunte:
```
Identifiquei algo util como memoria persistente:

[Item]
[Tipo: decision | blocker | lesson | idea | reference]
[Por que importa para futuras sessoes]

Salvar?
  (m) MEMORY direto — definitiva agora (decisao puramente de planejamento, ja resolvida)
  (l) Deixar pro /sdd-learning extrair pos-merge — recomendado se a decisao depende de validacao no review
  (n) Nao salvar
```

**Default sugerido**: `(l) pendente pro /sdd-learning` quando o plano vai virar PR (caso comum). `(m) memory direto` apenas quando a decisao e puramente de planejamento ja resolvida.

Se `(l)`: **nao crie arquivo** agora — mantenha a observacao no proprio PLAN (secao "Decisoes Tecnicas" ou "Observacoes"). O `/sdd-learning` extrai pos-merge com base nos filtros duros + comentarios do review humano.

Se `(m)`: nota em `$MEM_DIR/<tipo>_<slug>.md` (ver skill `memory-keeper`) + linha na tabela do `MEMORY.md`.

Se `(n)`: pule.

### Passo 14 — Informar usuario

```
PLAN salvo em thoughts/plans/PLAN-DD-MM-YYYY-NNN-[slug].md
SPEC base: thoughts/specs/spec-<ts>-<slug>.md

Escopo: [Medium/Large/Complex]
[N] tarefas em [M] phases ([X] paralelizaveis)
Cobertura da SPEC: [todos RF/AT cobertos]
Links verificados: [Y OK, Z quebrados]
4 Checks: PASS

Proximos passos:
  /pr-draft       → abre PR em draft (body a partir da SPEC de comportamento)
  /executor-plan  → executa o PLAN com TDD
```

---

## Output: template do PLAN.md

Caminho: `thoughts/plans/PLAN-DD-MM-YYYY-NNN-[slug].md`

Escreva o doc seguindo o template do reference `sdd-plan-plan-template.md` — procure em `.claude/sdd-references/` do projeto, senao em `~/.claude/sdd-references/`. Carregue o reference **apenas na hora de escrever** (Passo 11+).

**Fallback** (reference ausente): monte com frontmatter (date, scope, spec, issue, skills) + secoes: Resumo Executivo (escrito por ultimo), 1. SPEC de Referencia (link + resumo do comportamento), 2. Decisoes Tecnicas, 3. Analise Local (componentes, dependencias, design docs/reconciliacao), 4. Referencias Externas (omitir se Medium sem pesquisa), 5. Diagrama (mermaid; obrigatorio Large/Complex), 6. Estrategia de Testes, 7. Tarefas (phases + estrutura What/Covers/Where/Depends on/Reuses/Skills/Riscos/Tests/Test count/Gate/Done when/Commit), 8. Parallel Execution Map, 9. Cobertura da SPEC (mapa RF/AT → tarefa), 10. Simplificacao, 11. Validacao Pre-Aprovacao (4 checks), 12. Duvidas Pendentes, 13. Verificacao de Links.

---

## Guardrails

- **SPEC e a base**: cada tarefa rastreavel a um RF/AT da SPEC (`Covers:`). Comportamento ausente = volte pro `/sdd-spec`, nao improvise
- **Nunca pule o checkpoint do passo 10**: apresente preview antes de escrever. Sem excecao
- **Nunca invente escopo**: tarefa sem `Covers:` = escopo inventado
- **Decisoes de comportamento sao da SPEC**: aqui so decisoes tecnicas
- **Reconcilie docs antes**: conflito com design doc existente = bloqueio
- **4 checks bloqueantes**: FALHA = reestruture
- **PR size reviewavel**: estime arquivos distintos do diff. Ideal ≤10, aceitavel ≤15, 16-20 e caso raro (avise + proponha split), >20 recomende dividir em PRs sequenciais. Nunca auto-divida nem reescreva a SPEC — proponha a fronteira e deixe o usuario decidir
- **Revisao por painel (sempre)**: 4 reviewers independentes (Pro, Fast, Security, Tests) antes do checkpoint; achados estruturados, verifique cada `must-fix` antes de aplicar, guarda de convergencia (nao entre em loop)
- **Test co-location e regra**: defer = anti-pattern
- **Test count obrigatorio**: toda tarefa com `Gate` declara contagem
- **Cobertura da SPEC**: todo RF/AT coberto por ≥1 tarefa
- **Fonte ou NEEDS VERIFICATION**: claim externa sem fonte verificavel nao entra nas tarefas
- **Skills nao opcionais**: identifique e liste — executor as ativa
- **Constitution inegociavel**: CLAUDE.md/ARCHITECTURE.md
- **Memoria pergunta antes**: nunca escreva no `memory/` (ou em draft) sem confirmar
- **Diagrama mapeia arquitetura real**: nao copia exemplo
- **Resumo Executivo por ultimo**: bullets espelham conteudo real das secoes
- **GitHub via `gh` CLI**: nunca tokens manuais
- **Quick detectado = saia**: nao force fluxo formal em escopo trivial
