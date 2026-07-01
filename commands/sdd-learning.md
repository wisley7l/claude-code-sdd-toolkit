---
description: Extrai aprendizados de IMPs, reviews e comentarios do PR no GitHub — propoe registro no auto-memory. Detecta o ultimo PR da branch ou aceita --pr <N>.
model: claude-sonnet-5
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Agent, Bash(test*), Bash(ls *), Bash(mkdir *), Bash(realpath*), Bash(pwd), Bash(git worktree list*), Bash(git branch*), Bash(find *), Bash(stat *), Bash(date*), Bash(gh *)
# Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe Rodrigues
# https://github.com/tech-leads-club/agent-skills
# Fecha o loop: implementacao + review humano -> aprendizado nao-obvio -> memoria persistente
# Substitui /sdd-confirm (deprecated): a fonte GitHub PR cobre o caso de "decisoes validadas apos merge"
---

# SDD Learning — Colheita de Aprendizados

Voce e um **destilador de aprendizado**. Le relatorios de implementacao (`IMP-*.md`), reviews internos (`thoughts/reviews/*.md`) **e comentarios humanos do PR no GitHub** (body, reviews, threads de discussao). Identifica o que vale virar memoria persistente, e propoe registro no auto-memory via skill `memory-keeper` — sempre sob confirmacao por item.

**Quando rodar**: tipicamente apos um PR fechar (mergeado ou nao). O command auto-detecta o ultimo PR fechado da branch atual, ou voce passa `--pr <N>` explicito.

**Voce nao cria nota por iniciativa.** Cada candidato e proposto e o usuario aprova caso a caso. Notas similares ja existentes sao atualizadas, nao duplicadas.

**Toda persistencia delega pra skill `memory-keeper`** — voce nao escreve direto em `MEMORY.md` nem nos arquivos do auto-memory. A skill conhece o padrao atual: `## GUARDRAILs` no topo do indice (regras inviolaveis), politica "linha no MEMORY.md so se tema novo" (sub-sumario absorve variacoes), ordem canonica das secoes. Quando voce decide criar/atualizar, passa os dados pra skill — ela aplica.

## Configuracao Inicial

### 1. Modelo

Este command roda na **base Sonnet** (sem `model: opus` no topo). A thread principal orquestra: resolve paths, detecta o PR, lista fontes, apresenta candidatos um a um (s/p/e/t) e delega a escrita pra skill `memory-keeper`. A **destilacao** — aplicar os 5 filtros duros, classificar nos 9 tipos, dedupe semantico e extrair decisao emergente de threads do PR — e o raciocinio que exige Opus: **delegue-a a um subagente `Agent` com `model: opus`** (ver Passos 2 e 3), que le as fontes e devolve a lista de candidatos ja filtrados e classificados. Pra poucas fontes curtas, voce pode destilar inline na main (Sonnet) sem subagente. **Nao rode `/model opus`** na main: trocar de modelo invalida o cache de prompt e gasta token a toa.

## Principios duros (filtros bloqueantes)

Aplique cada candidato contra estes filtros. Falhou em qualquer um → **descarte silenciosamente**, nao proponha.

1. **Nao-obvio**: removendo a nota, um futuro agente que le o codigo + git log perderia algo? Se nao, descarte.
2. **Tem "por que"**: a nota tem motivo/contexto que justifica o registro? Sem por que = ruido futuro.
3. **Persiste**: vale alem da feature atual? Se for so detalhe operacional de uma sessao, descarte.
4. **Nao redundante**: ja existe nota similar no `MEMORY.md`? **Atualizar** > criar.
5. **Nao capturado em commit/PR**: se o commit message ou descricao do PR ja conta a historia, git log resolve — descarte.

## Tipos (9 no total, ver skill `memory-keeper`)

**Sabor SDD** (gerados durante execucao/review):

| Tipo | Captura | Exemplo |
|---|---|---|
| `decision` | Decisao arquitetural que persiste alem da feature | "Schema sem FK; validar referencias em camada de aplicacao" |
| `blocker` | Problema conhecido com sintoma e workaround | "Tool externa falha local sem secret <X>; rodar `<tool> login` antes" |
| `lesson` | Abordagem testada que nao funcionou OU padrao que provou valor | "Mock de DB divergiu de prod; usar branch dev real em testes" |
| `idea` | Algo que apareceu fora de escopo, pra retomar | "Migrar webhook sincrono pra fila assincrona quando tiver tempo" |
| `preference` | Estilo de trabalho do usuario neste projeto | "Confirmar com user antes de stage de migracao de schema" |

**Sabor geral** (regras transversais):

| Tipo | Captura |
|---|---|
| `user` | Perfil, papel, conhecimento do usuario |
| `feedback` | Regra de colaboracao ("faca X / nunca Y") |
| `project` | Decisao/contexto/deadline nao-obvio sobre o trabalho |
| `reference` | Ponteiro para sistema externo (URL, dashboard, tracker) |

**Quando e SDD vs geral?**

- Especifico do estado tecnico do projeto (decisao, blocker, licao de implementacao) → SDD
- Regra de colaboracao entre user e agente → `feedback`
- Decisao de produto/deadline/contexto de negocio → `project`
- Link para Linear/Grafana/dashboard externo → `reference`

Em duvida: SDD para coisa tecnica especifica; geral para coisa transversal.

## Args

| Forma | Comportamento |
|---|---|
| Sem args | **Auto-detecta** o ultimo PR fechado da branch atual via `gh pr list --head <branch> --state closed --limit 1`. Se achar, propoe processar IMP+review+PR. Se nao achar PR, cai no fallback: lista os 5 IMPs+reviews mais recentes. |
| `--pr <N>` | Processa o PR `<N>` explicitamente (alem dos IMPs/reviews ligados a ele) |
| `--no-pr` | Forca fonte local apenas (ignora GitHub). Util quando voce ja revisou comentarios manualmente |
| `<arquivo.md>` | Processa 1 arquivo especifico (`thoughts/history/IMP-...md` ou `thoughts/reviews/...md`) |
| `--since=YYYY-MM-DD` | Processa todos os IMPs+reviews desde a data |
| `--imp` | Filtra so IMPs |
| `--review` | Filtra so reviews |
| `--include-insights` | Adiciona `thoughts/insights/*.md` as fontes (opt-in) |
| `--all` | Processa tudo. **Alerta o user antes**: pode gerar muitos candidatos. Pergunta confirmacao. |

### 2. Resolver paths

```bash
ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
PROJ_ENC=$(echo "${ROOT:-$(pwd)}" | sed 's|/|-|g')
MEM_DIR="$HOME/.claude/projects/$PROJ_ENC/memory"
```

Use `$ROOT` como base para `thoughts/`. Use `$MEM_DIR` para escrever memoria — o encoded do **root** garante que worktrees compartilhem o mesmo `memory/` (sem fragmentacao).

### 3. Validar auto-memory

```bash
test -d "$MEM_DIR" || { echo "Auto-memory nao existe. O harness cria na primeira sessao."; exit 0; }
```

### 4. Ler MEMORY.md (para contexto + dedupe)

O `MEMORY.md` ja esta carregado pelo harness no system prompt. Use ele como indice primario pra detectar duplicacao antes de propor criar.

Se houver sub-sumarios (`_summary_<tipo>.md`), abra apenas os relevantes pros tipos que voce vai propor.

### 5. Detectar PR alvo

A nova fonte principal eh o **PR fechado** da branch — ele tem o body, reviews humanos do time e threads de discussao (decisao emergente). Logica de deteccao:

**Caso `--pr <N>` explicito:**
```bash
gh pr view <N> --json state,mergedAt,closedAt
```
Use esse PR direto.

**Caso `--no-pr`:** pule esta etapa. Fonte = local apenas.

**Caso sem args (auto-detect):**

```bash
BRANCH=$(git branch --show-current)
gh pr list --head "$BRANCH" --state closed --json number,state,mergedAt,closedAt,title --limit 1
```

- Se retornou 1 PR fechado: confirme com o user antes de processar:
  ```
  Detectei PR #<N> ("<title>") fechado em <data> (state: <merged|closed>).
  Processar este PR junto com IMPs/reviews locais? [S/n]
  ```
- Se nao retornou PR: avise e siga so com fontes locais ("Sem PR fechado pra branch `<branch>`. Seguindo so com IMP/review locais.").

**Se `gh` falhar (auth/network/rate limit):** avise mas nao bloqueie — siga com fontes locais.

### 6. Listar fontes disponiveis (segundo os args + PR detectado)

| Fonte | Caminho / origem |
|---|---|
| IMPs | `thoughts/history/IMP-*.md` |
| Reviews internos | `thoughts/reviews/*.md`, `thoughts/shared/reviews/*.md` (legacy) |
| **PR GitHub** | `gh pr view <N>` (body, reviews, comments) + `gh api repos/.../pulls/<N>/comments` (inline + threads) |
| Insights (opt-in) | `thoughts/insights/*.md` |

Ordene por data (frontmatter, nome do arquivo, ou data de fechamento do PR).

---

## Fluxo de execucao

### Passo 1 — Selecao das fontes

**Sem args**: liste os 5 mais recentes (IMP + review combinados, ordenados por data desc):

```
IMPs e reviews recentes:
1. IMP-<data>-<feature-a>.md (5 dias)
2. review-pr-<N>.md (8 dias)
3. IMP-<data>-<feature-b>.md (10 dias)
...

Quais processar? (numeros separados por virgula, `all`, ou `--since=YYYY-MM-DD`)
```

**Com `<arquivo>`**: confirme o path e avance.

**Com `--since=` ou `--all`**: liste o que entrou no filtro e pergunte confirmacao:

```
Filtro retornou [N] arquivos. Processar todos? (s/n)
```

### Passo 2 — Leitura das fontes

#### 2.1 — Fontes locais (IMP + reviews internos + insights opt-in)

Para cada arquivo selecionado:
1. Leia o conteudo completo
2. Identifique secoes que costumam concentrar aprendizado:
   - "Licoes aprendidas", "O que aprendi", "Takeaways"
   - "Decisoes tomadas", "Decisoes"
   - "Blockers encontrados", "Problemas"
   - "Surpresas", "Achados inesperados"
   - "Para a proxima vez", "Next time"
   - "Trade-offs"
3. Tambem leia o corpo geral procurando paragrafos com "decidimos", "descobrimos que", "ja tentamos", "nao funciona quando", "tem que ser X porque Y"

**Delegue a leitura+destilacao para subagent `Agent` com `model: opus`** (`subagent_type: general-purpose` ou `Explore`): ele aplica os 5 filtros + classificacao (Passos 3-4) e retorna so a lista de candidatos ja filtrados e classificados. Pra 1-2 fontes curtas voce pode destilar inline na main (Sonnet); quando o material for volumoso (>20k tokens ou varias fontes), sempre delegue pro subagente Opus pra nao inflar a thread principal.

#### 2.2 — Fonte GitHub PR (se detectado no Passo 5 da Configuracao)

**Captura completa:**

```bash
# PR body, top-level reviews, top-level issue-comments
gh pr view <N> --json title,body,author,reviews,comments,mergedAt,closedAt,state

# Inline comments (review comments por arquivo:linha — agrupados em threads)
gh api repos/{owner}/{repo}/pulls/<N>/comments
```

Substitua `{owner}/{repo}` pelo retorno de `gh repo view --json owner,name -q '.owner.login + "/" + .name'`.

**Estrutura esperada:**

- `body` — descricao do PR (pode conter trade-offs, contexto, justificativa)
- `reviews[]` — reviews formais com `state` (APPROVED / CHANGES_REQUESTED / COMMENTED), `body` e `author.login`
- `comments[]` — comentarios gerais soltos (nao atrelados a linha)
- inline comments (do `gh api`) — atrelados a arquivo:linha, e podem ter `in_reply_to_id` formando **threads**

**Filtros antes da analise:**

1. **Filtrar bots automaticamente**: ignore qualquer entrada cujo `author.login` (ou `user.login`) termine com `[bot]` (ex: `dependabot[bot]`, `github-actions[bot]`).
2. **NAO filtrar o autor do PR**: o autor (provavelmente o proprio user que rodou este command) participa das discussoes. Comentarios dele sao tao relevantes quanto os do time — a **decisao emergente** vem do conjunto.
3. **Agrupar inline comments em threads**: use `in_reply_to_id` pra reconstruir threads. Comentario raiz + replies = 1 thread.

**Identificacao de candidatos a partir do PR:**

| Fonte no PR | O que procurar |
|---|---|
| Body do PR | Trade-offs explicitos, justificativa de approach ("optamos por X porque Y") |
| Reviews formais (CHANGES_REQUESTED / COMMENTED) | Sugestao de padrao, correcao de approach, citacao de regra do projeto |
| Reviews formais (APPROVED) | Validacao explicita de decisao controversa ("ok pode seguir assim porque...") |
| Threads inline com 2+ mensagens | **Mais ricas**: discussao -> decisao consensual. Foco aqui. |
| Comentario isolado (1 unica mensagem, sem reply) | Considere SE tem "por que" explicito; senao, descarte (alta probabilidade de ruido) |

**Decisao emergente em threads:**

Pra cada thread com 2+ mensagens, identifique:
1. **O ponto disputado**: o que esta sendo discutido?
2. **A resolucao**: a thread terminou com consenso? Padrao linguistico: "fechou", "ok", "vai assim mesmo", "concordo", "tu tem razao", "vamos com X".
3. **O motivo do consenso**: por que a resolucao foi essa? (extrair da propria thread)

A **decisao emergente** da thread = ponto disputado + resolucao + motivo. Isso vira o candidato. Aplique os 5 filtros duros sobre ela.

**Threads sem resolucao clara** (acabam sem conclusao, ou divergencia mantida): considere candidato a `blocker` ou `idea` ("ponto em aberto: X"). Use julgamento.

**Subagent pra threads volumosas:**

Se o PR tem >30 inline comments ou >10 threads, delegue a destilacao de threads pra subagent `Agent` com `model: opus` (`subagent_type: general-purpose`), passando o JSON dos comments e o protocolo acima. Retorno: lista compacta de candidatos extraidos ja com tipo proposto.

### Passo 3 — Extracao de candidatos

Esta e a etapa de raciocinio pesado (Opus). Quando a leitura foi delegada ao subagente Opus (Passo 2), ele ja executa os Passos 3-4 e devolve candidatos classificados — a main (Sonnet) so consolida e segue pro dedupe/apresentacao. Quando voce destilou inline (poucas fontes curtas), aplique aqui.

Para cada paragrafo/secao identificada, aplique os 5 filtros duros (secao Principios). **Se falhar em qualquer um, descarte silenciosamente.**

Candidato passa nos filtros? Capture:
- **Frase nuclear** (1-2 linhas: o que e a licao/decisao/etc)
- **Por que** (o motivo/contexto — extraido do texto fonte)
- **Aplicar quando** (quando essa informacao se torna relevante de novo)
- **Referencias** (path:linha, PR #, POC, etc — extraido do texto fonte)
- **Origem** (qual IMP/review)

### Passo 4 — Classificacao

Para cada candidato:

1. **Tipo** (conforme tabelas acima): decision/blocker/lesson/idea/preference (SDD) ou feedback/project/reference (geral). `user` raramente sai de aprendizado de IMP/review.
2. **Slug proposto**: kebab-case curto da frase nuclear (ex: `schema-sem-fk-validar-aplicacao`)

### Passo 5 — Dedupe contra MEMORY.md

Para cada candidato classificado:

1. Pelo `MEMORY.md` (ja carregado), busque na secao do tipo por slug similar ou hook que cubra o tema.
2. Se houver `_summary_<tipo>.md` para o tipo do candidato, abra-o tambem.
3. Se encontrar similar:
   - **Atualizar** a nota existente (acrescentar referencias, refinar "por que", adicionar contexto)
   - **Nao duplicar**
4. Se nao encontrar: candidato vira proposta de **criar**.

### Passo 6 — Apresentacao + confirmacao por item

Para cada candidato, mostre **uma proposta por vez** (nao bulk). O formato muda ligeiramente conforme a origem:

**Origem local (IMP / review interno):**

```
Candidato 1/N — origem: IMP-<data>-<feature>.md

Frase nuclear:
"Schema nao suporta FK; integridade de referencia precisa ser validada na camada de aplicacao."

Por que:
"PR #<N> inline comment de reviewer + ARCHITECTURE.md:<linhas>. Tentar usar FK quebra deploy de schema."

Aplicar quando:
"Sempre que adicionar tabela com referencia a outra (FKs de aplicacao)."

Proposta:
- Tipo: decision
- Slug: schema-sem-fk-validar-aplicacao
- Acao: CRIAR (nao achei similar no MEMORY.md)

Aceitar? (s = salvar, p = pular, e = editar antes, t = mudar tipo)
```

**Origem GitHub PR — thread de discussao:**

```
Candidato 2/N — origem: PR #<N>, thread em src/foo.ts:42 (3 mensagens)

Thread (resumida):
  @wisley7l: "Vou usar lock pessimista aqui — pra evitar race no checkout"
  @maria: "Pessimista pode segurar muito tempo se a transacao crescer. Considera optimistic + retry?"
  @wisley7l: "Bom ponto, com retry resolve. Fechou."

Decisao emergente:
"Em fluxo de checkout, preferir optimistic locking + retry sobre pessimistic. Pessimista risca lock longo."

Por que:
"Discussao em thread do PR #<N> com @maria. Pessimista segura transacao por toda duracao; com optimistic + retry o lock so existe na confirmacao."

Aplicar quando:
"Qualquer fluxo transacional onde a transacao pode crescer (checkout, batch, etc)."

Proposta:
- Tipo: decision
- Slug: checkout-optimistic-locking-retry
- Acao: CRIAR (nao achei similar no MEMORY.md)

Aceitar? (s = salvar, p = pular, e = editar antes, t = mudar tipo)
```

**Origem GitHub PR — body / review formal:**

```
Candidato 3/N — origem: PR #<N>, review formal de @joao (state: APPROVED)

Frase nuclear:
"OK seguir com axios mesmo sendo deprecated — migracao pra fetch fica pro PR de housekeeping."

Por que:
"Review APPROVED com nota: 'sei que axios ta deprecated mas a refac pra fetch e fora do escopo deste PR. Aprovado pra nao bloquear feature; abre issue pra fazer depois.'"

Aplicar quando:
"Decisao escopada a esta feature. Nao replicar — proximo PR deve avancar a migracao."

Proposta:
- Tipo: idea (housekeeping pendente)
- Slug: migrar-axios-para-fetch
- Acao: CRIAR (nao achei similar no MEMORY.md)

Aceitar? (s = salvar, p = pular, e = editar antes, t = mudar tipo)
```

**Edicao** (e): permitir editar frase nuclear, por que, aplicar quando, slug. Reapresentar.

**Mudar tipo** (t): permitir mudar classificacao. Reapresentar.

**Atualizar** (quando dedupe acha similar):

```
Candidato 2/N — origem: review-pr-<N>.md

Frase nuclear:
"Cross-check entre lib X e lib Y evita drift de schema."

Encontrei nota similar:
  $MEM_DIR/decision_<tema-similar>.md
  "Pattern para evitar drift entre schemas (lib X / lib Y)"

Diff proposto:
- Acrescentar referencia: review-pr-<N>.md
- Adicionar contexto: "padrao replicado em outra feature (PR #..)"
- Atualizar metadata.updated: <hoje>

Acao: ATUALIZAR (s = salvar, p = pular, c = criar nova mesmo assim)
```

### Passo 7 — Aplicacao (sempre via skill `memory-keeper`)

**Toda escrita delega pra skill `memory-keeper`** — nao escreva direto nos arquivos. A skill aplica o padrao atual (frontmatter, convencoes de nome, politica "linha no MEMORY.md so se tema novo", `## GUARDRAILs` no topo do indice, ordem canonica das secoes).

**Para cada candidato aprovado:**

**CRIAR** — invoque a skill `memory-keeper` passando:

- `tipo`: decision | blocker | lesson | idea | preference | feedback | project | reference
- `slug`: kebab-case curto
- `description`: frase nuclear ≤120 chars
- `corpo`: frase nuclear no topo + `**Why:**` (motivo/contexto) + `**How to apply:**` (quando aplicar) + `**Referencias:**` (path:linha, PR #, IMP de origem)
- `origem`: IMP-... ou review-... (vai pro frontmatter `metadata.origem`)
- `guardrail`: true/false — se a regra e inviolavel e seu rompimento causa dano irreversivel (commit indevido, push, delete, vazamento), marque como guardrail. A skill move pro `## GUARDRAILs` do MEMORY.md em vez da secao do tipo.

A skill decide:
- Se o tema ja tem linha no MEMORY.md → cria arquivo individual mas **nao adiciona linha duplicada** (sub-sumario absorve).
- Se e tema novo → cria arquivo + adiciona linha no MEMORY.md.
- Se e guardrail → vai pra secao `## GUARDRAILs` no topo (formato `| Regra | Detalhe (link) |`).

**ATUALIZAR** — passe pra skill `memory-keeper` em modo update:

- `slug-existente`: path da nota encontrada no dedupe (Passo 5)
- `acrescentar-referencias`: lista de refs novas (origem do IMP/review atual)
- `refinar-why`: contexto novo (opcional)

A skill preserva o conteudo existente, so adiciona/refina — nunca reescreve do zero.

**Importante**: nunca escreva diretamente em `MEMORY.md` neste passo. A skill cuida do indice. Isso garante que a politica "linha so se tema novo" e a saliencia de `## GUARDRAILs` sejam respeitadas.

### Passo 8 — Resumo final

```
SDD Learning concluido.

Fontes processadas:
- IMPs: N arquivos
- Reviews internos: M arquivos
- PR GitHub: #<N> (<X> threads inline, <Y> reviews formais)  [omita se --no-pr ou sem PR detectado]

Candidatos detectados: K (locais: KL, do PR: KP)
- Aprovados: A (criadas: X, atualizadas: Y)
- Pulados: P
- Descartados pelos filtros: D

Arquivos criados/atualizados em $MEM_DIR:
- decision_<tema-a>.md (novo)
- decision_<tema-b>.md (atualizado)
...

MEMORY.md atualizado.
```

Se o `MEMORY.md` cresceu muito (> 150 linhas), sugira rodar `/memory-organize` ao final.

---

## Relacao com outros commands

- `/sdd-spec` / `/sdd-plan` / `/quick-task` / `/executor-plan` / `/sdd-review` produzem os artefatos locais (SPEC, PLAN, IMP, review) que viram fonte deste command. Eles tambem oferecem `(m)` salvar memoria direto durante a execucao quando a decisao ja eh definitiva — nesse caso `/sdd-learning` so deduplica.
- `/sdd-learning` **substitui o antigo `/sdd-confirm`** (movido pra `commands/deprecated/`). A fonte GitHub PR (body + reviews + threads de discussao) cobre o caso de "decisoes validadas pelo merge" que o sdd-confirm tratava via drafts locais — agora extraidas direto do PR mergeado, com o contexto humano do review.
- `/memory-organize` arruma a memoria periodicamente (sub-sumarios, orfaos, links quebrados).

---

## Guardrails

- **Nunca crie por iniciativa**: cada candidato pede confirmacao do usuario (s/p/e/t)
- **Atualizar > criar**: se ha similar, sempre proponha atualizar primeiro
- **Filtros sao bloqueantes**: candidato que falha em qualquer um dos 5 filtros e descartado sem mostrar ao usuario
- **1 candidato por vez**: nao bulk approval — usuario decide caso a caso
- **Origem rastreavel**: toda nota gerada por este command guarda `metadata.origem` apontando pro IMP/review/PR
- **MEMORY.md obrigatorio**: nota criada sem linha no `MEMORY.md` vira orfa — sempre atualize o indice
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` ja sao contexto do projeto, nao precisam virar memoria
- **Sem fonte = `[NEEDS VERIFICATION]`**: claim que veio do IMP sem fonte verificavel marca a nota como verificar antes de virar canonica
- **GitHub via `gh` CLI**: nunca tokens manuais. Se `gh` falhar (auth/rate limit/network), siga com fontes locais e avise
- **Bots filtrados, autor incluso**: ignore comentarios cujo login termina com `[bot]`. Comentarios do autor do PR (provavelmente o proprio user) sao incluidos — a decisao emergente vem da conversa toda
- **Threads vs comentarios isolados**: prefira threads com 2+ mensagens (discussao -> consenso). Comentario isolado so vira candidato se tiver "por que" explicito; senao, descarte (alta chance de ruido)
- **Decisao emergente, nao comentario literal**: o candidato vindo de thread captura a **conclusao consensual** da discussao, nao o primeiro comentario. Sempre extraia o "ponto disputado + resolucao + motivo"
