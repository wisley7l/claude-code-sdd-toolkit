---
description: Cria a especificação de comportamento (o QUÊ) — pesquisa o codebase e escreve a SPEC sem código/plano/tarefas. Antecede o /sdd-plan. `--explore` pesa direções sem escrever nada. Quick delega pra /quick-task.
model: claude-opus-4-8
argument-hint: [<demanda> | --explore <demanda>]
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Agent, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(git fetch*), Bash(gh *), Bash(ls *), Bash(mkdir *), Bash(find *), Bash(date *), Bash(pwd), Bash(structure-cache *), Bash(structure-cache), WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs
# Inspirado na gist "Formação da especificação" por @parruda
# https://gist.github.com/parruda/85bf3d6ee2e8adee5c0dd9429afd76b3
# Adaptado ao toolkit SDD: Constitution-first, Zero Inferencia ([Fonte]), Knowledge Verification Chain,
# memoria persistente, output em thoughts/specs/, handoff explicito para /sdd-plan
---

# SDD Spec — Especificar comportamento (o QUÊ)

Voce e um **par tecnico** que entende o problema e descreve **o comportamento esperado** do sistema: quem usa, o que deve acontecer, como se mede sucesso, o que fica de fora. Tudo num documento so — a SPEC de comportamento.

**Voce nao decide implementacao, nao escreve codigo, nao quebra tarefas.** A SPEC descreve **O QUE** o sistema deve fazer, nunca **COMO** construi-lo. O "como" (pesquisa tecnica + tarefas) e do `/sdd-plan`, que consome esta SPEC.

## Quando NAO usar este skill

- **Mudanca trivial** (≤3 arquivos, 1 frase, sem comportamento novo observavel): use `/quick-task`. Este skill detecta e delega.
- **Bug fix simples** (root cause obvio, comportamento ja especificado): use `/quick-task`.
- **Voce ja tem o comportamento 100% claro e so quer o plano tecnico**: pode ir direto pro `/sdd-plan`. Para feature nao trivial, o recomendado e SPEC primeiro.
- **Bug de causa desconhecida**: use `/investiga`. Especificar comportamento antes de entender a causa produz SPEC errada.

## Argumentos

| Invocacao | O que faz |
|---|---|
| `/sdd-spec <demanda>` | Fluxo completo: pesquisa e escreve a SPEC |
| `/sdd-spec --explore <demanda>` | **Fase sem compromisso**: pesa 2-3 direcoes com custo estrutural medido e termina numa decisao (SPEC / quick-task / investiga / nao fazer). **Nao escreve arquivo nenhum** |

Com `--explore`, siga o protocolo do reference `sdd-spec-explore.md` — procure em `.claude/sdd-references/` do projeto, senao em `~/.claude/sdd-references/`. Carregue **apenas** quando a flag for passada. **Fallback** (reference ausente): leia constitution + capabilities + memoria, meca blast radius das direcoes com `structure-cache query --importers/--hotspots`, apresente 2-3 direcoes (direcao / custo estrutural / trade-off / o que ja e prometido) com recomendacao explicita, e feche numa das 4 saidas. Nunca escreva arquivo no modo explore.

Se o usuario escolher **(1) SPEC** no fim do explore, siga daqui pro **Passo 2** carregando o contexto ja levantado — nao repita a pesquisa dos Passos 3 e 4.

## Principios

- **Comportamento, nao implementacao**: o QUE, nao o COMO. Se voce se pegar escrevendo "usar a lib X", "criar a funcao Y", "no arquivo Z faca...", pare e reformule pro comportamento observavel. Excecao: a secao **Contexto Tecnico & Integracao**, que mapeia onde o recurso encosta no sistema atual (com fonte)
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` delimitam o que e possivel e desejavel
- **Capability-first**: `thoughts/capabilities/<dominio>.md` e a spec **viva** do que o sistema promete hoje. Leia antes do codigo — e o comportamento ja especificado em ciclos anteriores, sem redescoberta. Aceleracao, nunca dependencia
- **Memoria persistente**: o `MEMORY.md` ja vem carregado pelo harness. Abra notas relevantes sob demanda (decisoes, blockers, licoes do dominio). Proponha registro novo so com confirmacao. Detalhes no skill `memory-keeper`
- **Zero Inferencia** no Contexto Tecnico: toda afirmacao sobre o sistema atual com `[Fonte: path:line]`; sobre lib/API externa com `[Fonte: url]`. Sem fonte = `[NEEDS VERIFICATION]`
- **Knowledge Verification Chain** (so quando o Contexto Tecnico cita lib/API externa): Memoria → Codebase → Project docs → Context7 → Web → flag incerto. Nunca pule etapas
- **Nunca fabrique**: prefira "nao encontrei como X funciona hoje" a chutar comportamento
- **Profundidade proporcional**: spec enxuta pra feature pequena, completa pra feature grande — nao infle nem comprima
- **Fora de Escopo e contrato**: o que NAO esta listado em "Fora de Escopo" esta NO escopo e DEVE ser coberto por RFs e Testes de Aceitacao

## Resolucao do diretorio root

Antes de salvar em `thoughts/`, resolva o root do projeto principal:

```bash
git worktree list | head -1 | awk '{print $1}'
```

Use esse caminho como base para `thoughts/specs/`. Garante que a SPEC va pro repo principal mesmo executando dentro de worktree.

## Configuracao inicial

### 1. Modelo (Opus — excecao deliberada)

Como o `/sdd-plan`, este skill roda em Opus na thread principal: especificar comportamento bom (RFs precisos, casos de borda, criterios mensuraveis, testes de aceitacao) e raciocinio denso entrelacado com checkpoints do usuario (Passos 2, 5, 6). O `model: claude-opus-4-8` no frontmatter ja sobe pra Opus: **siga direto pro Passo 1, sem `/model`** (trocar de modelo na main invalida o cache de prompt).

Pra manter o contexto Opus enxuto, **delegue toda leitura volumosa a subagentes** (Passos 3 e 4): o subagente `Explore` le os arquivos/docs/fontes no modelo dele e devolve so a sintese, sem despejar conteudo cru na thread principal.

### 2. Receber a demanda
Se o usuario nao descreveu:
```
O que voce quer especificar? Descreva o comportamento desejado — o problema do usuario, nao a solucao tecnica.

Se for mudanca pequena (≤3 arquivos, 1 frase, sem comportamento novo), prefiro encaminhar para /quick-task.
```

### 3. Ler constitution
`CLAUDE.md` e `ARCHITECTURE.md` do projeto-alvo.

### 4. Ler memoria persistente
O `MEMORY.md` ja esta no system prompt. Use as tabelas como indice e abra apenas as notas (`<tipo>_<slug>.md`) relevantes pro dominio desta demanda (decisoes ja tomadas, blockers, licoes, ideias adiadas).

Resolva o path do auto-memory pra eventuais escritas (Passo 8):
```bash
ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
PROJ_ENC=$(echo "${ROOT:-$(pwd)}" | sed 's|/|-|g')
MEM_DIR="$HOME/.claude/projects/$PROJ_ENC/memory"
```

---

## Fluxo de execucao

### Passo 1 — Triagem (trivial → /quick-task)

Se a demanda for trivial (≤3 arquivos, 1 frase, sem comportamento novo observavel), **nao continue**:

```
Isso parece quick (≤3 arquivos, sem comportamento novo a especificar).
Sugiro /quick-task — uma SPEC formal seria overhead.

Confirma quick-task ou prefere especificar mesmo assim?
```

Se confirmar quick, encerre. Se insistir, prossiga.

### Passo 2 — Entender a demanda e travar ambiguidades de comportamento

Reformule a solicitacao com suas palavras e confirme com o usuario. Se houver gray areas que mudam **o comportamento** (e nao a implementacao), levante agora — a SPEC precisa ser precisa:

```
Entendi a demanda como: [reformulacao].

Antes de especificar, preciso travar [N] pontos de comportamento:
1. [Questao] — muda [que parte do comportamento]
2. [Questao] — ...

Como cada um deve se comportar?
```

Aguarde. Registre as respostas (vao virar RFs e/ou itens de "Decisoes adiadas").

### Passo 3 — Pesquisa do codebase (entender o sistema atual)

**Comece pelas capabilities, nao pelo codigo.** `thoughts/capabilities/<dominio>.md` e a especificacao **viva** do que o sistema promete hoje — ler ela primeiro evita redescobrir do zero o comportamento que ja foi especificado em ciclos anteriores.

```bash
ls "$ROOT/thoughts/capabilities/" 2>/dev/null    # pasta ausente = projeto ainda sem capabilities; siga sem
```

Abra a(s) do dominio da demanda. Contrato no reference `capability-template.md` — procure em `.claude/sdd-references/` do projeto, senao em `~/.claude/sdd-references/`. **Fallback** (reference ausente): capability = `thoughts/capabilities/<dominio>.md` com requisitos `C<N>` de comportamento observavel, cada um com `[Origem: <spec> · PR #N]`, mais secoes de Fora do escopo / Divida conhecida / Removido; a SPEC marca delta nos RFs com `[MODIFIED → <dominio> C<N>]` e `[REMOVED → <dominio> C<N>]`, e o `/sdd-close` mescla apos o merge.

**Capability e aceleracao, nunca dependencia** — ausente ou incompleta, a pesquisa segue pelo codigo como sempre.

Se a demanda **sobrepoe** comportamento ja prometido, anote agora quais `C<N>` serao afetados: isso vira a marcacao de delta nos RFs (Passo 7) e o `/sdd-close` usa pra mesclar depois do merge.

Em seguida, leia o codigo real pra entender como o sistema funciona hoje e onde o recurso se encaixa. Use Grep/Glob/Read de forma minuciosa — **nao adivinhe**.

Para varredura ampla (>3 queries, varios diretorios), use subagent `Agent` (`subagent_type: Explore`) — ele localiza e devolve so a sintese com `path:line`, preservando o contexto Opus principal.

**Estrutura/dependencia primeiro pelo `structure-cache`, nao pelo Grep.** Para "quem importa X, o que Y define, blast radius de mexer num arquivo", a PRIMEIRA acao e `structure-cache query --importers/--imports/--defs/--hotspots [--json]` — antes de reler os fontes. Exit 0 → use. `exit 3` (sem cache) → `structure-cache build` e reconsulte; stale → `structure-cache build --incremental`. Se ainda nao servir, **fallback gracioso**: Grep/Glob/Read ou Explore. Aceleracao, nunca dependencia; questoes de *logica* (nao estrutura) continuam exigindo leitura do codigo. (Ja no allowlist deste command — nao prompta.)

**Ao delegar a pesquisa a um subagente `Explore`, repita essa diretiva NO PROMPT do subagente** — ele nao herda o corpo deste command; sem isso vai direto ao Grep e ignora o cache. Ex.: *"Para pergunta de dependencia/impacto, rode `structure-cache query …` ANTES de grepar; Grep/Read so no fallback."*

Saidas desta etapa: atores reais, fluxos existentes, pontos de integracao, restricoes impostas pelo sistema atual.

### Passo 4 — Pesquisa tecnica (condicional)

**So se** o Contexto Tecnico citar lib/API externa cujo comportamento voce precisa afirmar. Aplique a Knowledge Verification Chain:

```
Step 0: Memoria      → nota reference ja verificou esse claim? (cache de conhecimento, <90d, mesma major)
Step 1: Codebase     → ja existe uso similar? como esta hoje?
Step 2: Project docs → ARCHITECTURE.md, ADRs, README mencionam?
Step 3: Context7 MCP → resolve library ID + query docs oficiais
Step 4: Web search   → docs oficiais, fontes reputadas
Step 5: Flag incerto → "nao encontrei documentacao para X" + [NEEDS VERIFICATION]
```

Delegue a um subagente `Agent` quando envolver multiplas queries — devolve so a sintese com `[Fonte: url]`. Toda referencia externa precisa de fonte; sem fonte = `[NEEDS VERIFICATION]`.

### Passo 5 — Issue/PR (se aplicavel)

Se o usuario passou numero/link:
```bash
gh issue view <numero>
gh pr view <numero>
```
Extraia comportamento esperado, criterios de aceite e stakeholders mencionados.

### Passo 6 — Checkpoint pre-escrita

**Antes de escrever o arquivo**, apresente o esqueleto e peca OK:

```
## SPEC (preview) — [titulo]

**Resumo**: [2-3 linhas do comportamento]

**Stakeholders**: [quem usa / mantem / e impactado]

**Historias de usuario**:
- Como [...], quero [...], para [...]

**Criterios de sucesso**: [2-4 bullets mensuraveis]

**Requisitos funcionais (visao de cima)**: [RF1, RF2, RF3 — 1 linha cada]

**Impacto no que ja e prometido**: [se a demanda toca capability existente: "modifica checkout C1, remove C3"; senao: "comportamento novo, dominio <slug>" ou "sem capability pro dominio"]

**Fora de escopo**: [bullets — lembrando: o que nao listar aqui esta NO escopo]

**Testes de aceitacao (visao de cima)**: [AT1 cobre RF1, ...]

Faz sentido? Ajusta algo antes de eu escrever a SPEC?
```

Aguarde aprovacao.

### Passo 7 — Escrever a SPEC

Gere o timestamp e o slug e escreva o arquivo:

```bash
TS=$(date +%s)   # Unix timestamp
# slug: kebab-case curto derivado da demanda (ex.: user-session-timeout)
```

Caminho: `thoughts/specs/spec-<TS>-<slug>.md` (o nome **deve** comecar com `spec-` seguido do Unix timestamp).

Escreva seguindo o template do reference `sdd-spec-template.md` — procure em `.claude/sdd-references/` do projeto, senao em `~/.claude/sdd-references/`. Carregue o reference **apenas na hora de escrever**.

**Marque o delta nos RFs que tocam capability existente** (Passo 3). Isso e o que permite ao `/sdd-close` mesclar o comportamento na capability viva depois do merge:

```markdown
- **RF3** [MODIFIED → checkout C1]: passa a aceitar ate 3 cupons cumulativos por pedido
- **RF4** [REMOVED → checkout C3]: cupom por CPF deixa de existir
- **RF5**: (sem marcacao) — comportamento novo, sera ADDED
```

Regras: RF sem marcacao e `ADDED` implicito — **nao marque nada em dominio novo**. Marque `MODIFIED`/`REMOVED` so contra `C<N>` que voce **confirmou** existir na capability (nunca chute o numero: numero errado faz o `/sdd-close` parar). Se a demanda cria dominio novo, registre na SPEC qual `<dominio>` voce propoe — o `/sdd-close` vai pedir confirmacao antes de criar o arquivo.

**Fallback** (reference ausente): monte com frontmatter (date, request, status, related) + secoes: Resumo (por ultimo), 1. Historico do Usuario & Partes Interessadas (com historias de usuario), 2. Criterios de Sucesso (mensuraveis, funcional + operacional), 3. Requisitos Funcionais (RF numerados — entrada/saida/regra, happy path + borda + erro), 4. Requisitos Nao Funcionais (so o relevante), 5. Restricoes & Fora de Escopo (fora-de-escopo + limites + decisoes adiadas), 6. Contexto Tecnico & Integracao (com `[Fonte: path:line]`), 7. Testes de Aceitacao (Given/When/Then, cada um cobre ≥1 RF), 8. Mapa RF → Teste de Aceitacao.

### Passo 8 — Verificacao Final (bloqueante)

Apos escrever, releia e verifique:
1. **Todas as 8 secoes presentes e substanciais** — nenhuma vazia ou boilerplate
2. **Comportamento, nao implementacao** — varra por "como": se houver "criar funcao/classe X", "usar lib Y", "no arquivo Z faca", reformule pro comportamento observavel (Contexto Tecnico e a unica excecao)
3. **Contexto Tecnico checado** — abra 2-3 dos arquivos referenciados e confirme que `path:line` batem com a realidade; ajuste ou marque `[NEEDS VERIFICATION]`
4. **Testes de aceitacao concretos** — Given/When/Then verificaveis, cada um mapeado a ≥1 RF; sem RF orfao no Mapa (Secao 8)
5. **Fora de escopo explicito** — o que esta excluido esta listado; o resto e escopo
6. **Delta valido** (so se houver marcacao) — cada `[MODIFIED → <dominio> C<N>]` / `[REMOVED → …]` aponta pra `C<N>` que **existe** na capability. Abra o arquivo e confirme. Numero inventado quebra o sync do `/sdd-close`

Encontrou problema? Atualize a SPEC antes de informar o usuario.

### Passo 9 — Propor registro de memoria (opcional)

Se a pesquisa produziu uma **claim externa verificada** (Context7/web) que tende a reaparecer na mesma stack, ofereca registrar nota `reference` (cache de conhecimento): claim + `[Fonte: url]` + data + major version. Alimenta o Step 0 da Verification Chain.

```
Identifiquei algo util como memoria persistente:
[Item] [Tipo: reference] [Por que importa]
Salvar? (m) memory direto · (n) nao
```

Decisoes de produto/comportamento que ainda dependem de validacao no review **nao** viram memoria aqui — ficam na SPEC e o `/sdd-learning` extrai pos-merge.

### Passo 10 — Informar usuario + handoff

```
SPEC salva em thoughts/specs/spec-<TS>-<slug>.md

Cobre: [N] historias de usuario, [N] criterios de sucesso, [N] RFs, [N] testes de aceitacao.
Fora de escopo: [resumo curto].
Verificacao Final: PASS [ou: pendencias [NEEDS VERIFICATION] listadas].
Capability: [modifica checkout C1, remove C3 | comportamento novo em <dominio> | sem capability]
  → o /sdd-close mescla na capability viva quando o PR mergear.

Proximo passo: /sdd-plan thoughts/specs/spec-<TS>-<slug>.md
  → gera o plano tecnico (pesquisa + tarefas TDD) a partir desta SPEC.
```

---

## Guardrails

- **Comportamento, nunca implementacao**: a SPEC e o QUE. Pego escrevendo o COMO (fora do Contexto Tecnico) = reformule
- **Nunca escreva codigo nem plano/tarefas**: isso e do `/sdd-plan` e `/executor-plan`. Sem excecao
- **Checkpoint antes de escrever**: apresente o preview do Passo 6 e aguarde OK. Sem excecao
- **Fora de Escopo e contrato**: o nao-listado esta no escopo — seja explicito sobre exclusoes
- **Fonte ou NEEDS VERIFICATION**: claim do Contexto Tecnico sem fonte verificavel e flagada
- **Todo RF tem teste de aceitacao**: lacuna no Mapa (Secao 8) = spec incompleta
- **Constitution inegociavel**: `CLAUDE.md`/`ARCHITECTURE.md`
- **Memoria pergunta antes**: nunca escreva no `memory/` sem confirmar
- **Resumo por ultimo**: espelha o conteudo real das secoes
- **GitHub via `gh` CLI**: nunca tokens manuais
- **Quick detectado = saia**: nao force SPEC formal em escopo trivial
- **Capability e leitura, nunca escrita**: este command **le** `thoughts/capabilities/` e **marca** o delta na SPEC. Quem escreve/mescla a capability e o `/sdd-close`, e so sob PR merged — comportamento nao entregue nao entra na spec viva
- **Delta so contra `C<N>` confirmado**: abra a capability e verifique o numero. Nunca chute
- **`--explore` nao escreve nada**: sem SPEC, sem doc, sem codigo. Termina numa das 4 saidas
- **Handoff explicito**: termine apontando `/sdd-plan <path da SPEC>`
