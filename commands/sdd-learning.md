---
description: Extrai reforco comportamental de IMPs, reviews e comentarios do PR — erro evitavel (o time corrigiu o agente) vira regra generica pra nao repetir; padrao que funcionou vira regra pra repetir. Generaliza a instancia em principio+gatilho. Propoe registro no auto-memory. Detecta o ultimo PR da branch ou aceita --pr <N>.
model: claude-sonnet-5
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Agent, Bash(test*), Bash(ls *), Bash(mkdir *), Bash(realpath*), Bash(pwd), Bash(git worktree list*), Bash(git branch*), Bash(find *), Bash(stat *), Bash(date*), Bash(gh *)
# Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe Rodrigues
# https://github.com/tech-leads-club/agent-skills
# Fecha o loop: implementacao + review humano -> aprendizado nao-obvio -> memoria persistente
# Substitui /sdd-confirm (deprecated): a fonte GitHub PR cobre o caso de "decisoes validadas apos merge"
---

# SDD Learning — Colheita de Aprendizados

Voce e um **extrator de reforco comportamental**. Le relatorios de implementacao (`IMP-*.md`), reviews internos (`thoughts/reviews/*.md`) **e comentarios humanos do PR no GitHub** (body, reviews, threads de discussao). O objetivo NAO e documentar o que aconteceu nesta feature — e fazer o agente **parar de repetir erros evitaveis** e **repetir o que funcionou**. Cada nota gerada aqui muda comportamento futuro, ou nao deveria existir.

**Reforco negativo e reforco positivo — o eixo central:**

- **Reforco negativo (o mais valioso):** todo ponto onde alguem teve que **corrigir o agente** e um erro evitavel. Comentario do time no PR pedindo mudanca ("faz assim", "isso ta errado", "por que nao usou X?"), review `CHANGES_REQUESTED`, retrabalho registrado no IMP, bug que passou. Cada um = um erro que o agente cometeu e **nao deve cometer de novo**. Destile a **regra generica pra evita-lo**, nao o incidente.
- **Reforco positivo:** padrao que passou limpo no review, approach elogiado, decisao que se provou certa. Destile a **regra generica pra repeti-lo**.

**Generico > especifico (principio, nao instancia).** O erro nao e "faltou tratar carrinho vazio no checkout desta feature" — isso morre com a feature. O aprendizado e "sempre cubra o caso-vazio da colecao antes de iterar; o time apontou isso em review". Sempre **suba um nivel**: do caso concreto pro principio transferivel, MAS ancorado num gatilho reconhecivel (ver Passo 3 — Generalizacao). Generalizar de menos = ruido especifico que reclamamos. Generalizar demais = platitude ("escreva bom codigo") que morre no filtro nao-obvio.

**Quando rodar**: tipicamente apos um PR fechar (mergeado ou nao). O command auto-detecta o ultimo PR fechado da branch atual, ou voce passa `--pr <N>` explicito. O PR e a fonte mais rica de reforco negativo — e onde o time deixa por escrito o que o agente errou.

**Voce nao cria nota por iniciativa.** Cada candidato e proposto e o usuario aprova caso a caso. Notas similares ja existentes sao atualizadas, nao duplicadas.

**Toda persistencia delega pra skill `memory-keeper`** — voce nao escreve direto em `MEMORY.md` nem nos arquivos do auto-memory. A skill conhece o padrao atual: `## GUARDRAILs` no topo do indice (regras inviolaveis), politica "linha no MEMORY.md so se tema novo" (sub-sumario absorve variacoes), ordem canonica das secoes. Quando voce decide criar/atualizar, passa os dados pra skill — ela aplica.

## Configuracao Inicial

### 1. Modelo

Este command roda na **base Sonnet** (sem `model: opus` no topo). A thread principal orquestra: resolve paths, detecta o PR, lista fontes, apresenta candidatos um a um (s/p/e/t) e delega a escrita pra skill `memory-keeper`. A **destilacao** — generalizar a instancia em principio+gatilho (Passo 3a), aplicar os 6 filtros duros, classificar nos 9 tipos, dedupe semantico e extrair o erro evitavel de comentarios/threads do PR — e o raciocinio que exige Opus: **delegue-a a um subagente `Agent` com `model: opus`** (ver Passos 2 e 3), que le as fontes e devolve a lista de candidatos ja filtrados e classificados. Pra poucas fontes curtas, voce pode destilar inline na main (Sonnet) sem subagente. **Nao rode `/model opus`** na main: trocar de modelo invalida o cache de prompt e gasta token a toa.

## Principios duros (filtros bloqueantes)

Aplique cada candidato contra estes filtros. Falhou em qualquer um → **descarte silenciosamente**, nao proponha.

1. **E reforco (muda comportamento)**: a nota faz o agente agir diferente numa proxima tarefa — evitar um erro ou repetir um acerto? Se e so um fato historico ("nesta feature usamos a lib X") sem implicacao de acao futura, descarte. Este e o filtro mais importante: **nao capturamos fatos, capturamos regras de comportamento.**
2. **Transferivel (principio, nao instancia)**: a nota vale so nesta feature/arquivo, ou o principio se aplica a outras situacoes parecidas? Se e amarrada a um caso unico que nao se repete, descarte. Se e generalizavel, capture o **principio + o gatilho** (ver Passo 3).
3. **Nao-obvio**: removendo a nota, um futuro agente que le o codigo + git log perderia algo? Cuidado com o outro extremo: se a versao generalizada virou platitude que qualquer dev ja sabe ("teste antes de commitar"), tambem descarte — obvio demais falha aqui.
4. **Tem "por que"**: a nota tem motivo/contexto que justifica a regra? Sem por que, o agente futuro nao sabe quando a regra se aplica nem quando abrir excecao. Sem por que = ruido.
5. **Nao redundante**: ja existe nota similar no `MEMORY.md`? **Atualizar** > criar (acrescenta forca ao reforco existente, nao duplica).
6. **Nao capturado em commit/PR**: se o commit message ou descricao do PR ja conta a historia, git log resolve — descarte. (Excecao: o *comentario de review* que apontou o erro nao e "a historia do PR" — a regra generica extraida dele passa neste filtro.)

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

**Priorize os tipos comportamentais.** `lesson`, `feedback` e `preference` sao o coracao do reforco — eles dizem ao agente **como agir da proxima vez**. Um erro evitavel apontado pelo time quase sempre vira `lesson` ("padrao X falhou/foi rejeitado; use Y porque Z") ou `feedback` ("o time exige/rejeita X neste tipo de mudanca"). `decision`/`blocker`/`reference` continuam validos, mas so passam nos filtros se tambem mudarem comportamento futuro — uma `decision` que so registra "escolhemos X" sem regra de quando reaplicar e fato historico, nao reforco (filtro 1).

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
| `--hotspots` | Adiciona `thoughts/cache/structure/HOTSPOTS.md` as fontes (opt-in): propoe `lesson`/`blocker` para god-nodes/acoplamento do `structure-cache` |
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
| Hotspots de estrutura (opt-in, `--hotspots`) | `thoughts/cache/structure/HOTSPOTS.md` (god-nodes / acoplamento do `structure-cache`) |

Ordene por data (frontmatter, nome do arquivo, ou data de fechamento do PR).

**Hotspots (`--hotspots`):** quando presente, leia `HOTSPOTS.md` e considere propor `lesson`/`blocker` para um god-node que passe nos 6 filtros duros — ex.: "modulo X e hub de acoplamento (grau N): mexer tende a impactar varios subsistemas". Persista **so a conclusao nao-obvia** (com o "por que"), **nunca** o grafo/index — ele e derivavel e apodrece (fica no cache, nao na memoria). Verifique que o arquivo ainda reflete a realidade antes de propor.

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

**Delegue a leitura+destilacao para subagent `Agent` com `model: opus`** (`subagent_type: general-purpose` ou `Explore`): ele generaliza (Passo 3a), aplica os 6 filtros + classificacao (Passos 3-4) e retorna so a lista de candidatos ja filtrados e classificados. Pra 1-2 fontes curtas voce pode destilar inline na main (Sonnet); quando o material for volumoso (>20k tokens ou varias fontes), sempre delegue pro subagente Opus pra nao inflar a thread principal.

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

**Identificacao de candidatos a partir do PR — a lente e "onde o agente errou":**

O PR e a fonte mais rica de **reforco negativo**. Todo comentario do time que corrige o autor e um **erro evitavel** — leia o PR procurando esses primeiro, nao trade-offs.

| Sinal no PR | O que ele revela | Direcao |
|---|---|---|
| Review `CHANGES_REQUESTED` | O time barrou o approach: **erro evitavel** | Regra generica pra nao repetir (reforco negativo) |
| Comentario pedindo mudanca ("faz assim", "usa X em vez de Y", "por que nao...?", "isso quebra quando...") | O agente fez algo que o time teve que corrigir: **erro evitavel** | Regra generica pra nao repetir |
| Comentario citando regra/padrao do projeto que foi violado | O agente ignorou uma convencao existente | `feedback`/`preference`: a convencao, generalizada |
| Retrabalho: commit que desfaz/refaz algo apos review | Sinal de erro que custou uma rodada | Regra pra pegar o erro **antes** do review |
| Review `APPROVED` com elogio a um padrao / thread que valida approach controverso | O que **funcionou**: reforco positivo | Regra generica pra repetir |
| Body do PR | Trade-off/justificativa — normalmente ja e "a historia do PR" (filtro 6). So vira nota se contiver regra transferivel | Julgamento |

**De erro evitavel a regra (o passo que importa):**

Pra cada comentario que corrigiu o autor, nao capture o comentario literal. Extraia:
1. **O que o agente fez** (o erro concreto: "iterou a colecao sem cobrir o caso vazio").
2. **O que o time pediu** (a correcao: "cobrir o caso vazio antes de iterar").
3. **O principio generico por tras** (Passo 3): "sempre trate o caso-vazio de colecao antes de iterar — o time rejeita isso em review".
4. **O por que**: motivo que o time deu, ou o inferivel da correcao.

Aplique os 6 filtros duros sobre a **regra generica** (passo 3), nao sobre o incidente.

**Decisao emergente em threads (reforco positivo/misto):**

Threads com 2+ mensagens tambem carregam decisoes consensuais que valem repetir. Pra cada uma:
1. **O ponto disputado**: o que estava em jogo?
2. **A resolucao**: terminou em consenso? ("fechou", "ok", "concordo", "tu tem razao", "vamos com X").
3. **O motivo**: por que essa foi a resolucao?

Se a resolucao contrariou o que o autor propos → e tambem reforco negativo (o autor errou o approach inicial). Extraia a regra generica, nao a decisao pontual.

**Threads sem resolucao clara** (acabam sem conclusao, ou divergencia mantida): considere candidato a `blocker` ou `idea` ("ponto em aberto: X"). Use julgamento.

**Subagent pra threads volumosas:**

Se o PR tem >30 inline comments ou >10 threads, delegue a destilacao de threads pra subagent `Agent` com `model: opus` (`subagent_type: general-purpose`), passando o JSON dos comments e o protocolo acima. Retorno: lista compacta de candidatos extraidos ja com tipo proposto.

### Passo 3 — Extracao e generalizacao de candidatos

Esta e a etapa de raciocinio pesado (Opus). Quando a leitura foi delegada ao subagente Opus (Passo 2), ele ja executa os Passos 3-4 e devolve candidatos classificados — a main (Sonnet) so consolida e segue pro dedupe/apresentacao. Quando voce destilou inline (poucas fontes curtas), aplique aqui.

**3a — Suba um nivel (a etapa que corrige "especifico demais").** Cada candidato nasce como uma **instancia** (o que aconteceu nesta feature). Antes de qualquer filtro, transforme a instancia no **principio transferivel + gatilho**:

- Pergunte: *"numa proxima tarefa, o que eu faria diferente por causa disso? em que situacao essa regra reaparece?"*
- A saida tem sempre a forma **"quando `<gatilho reconhecivel>`, faca/evite `<acao>` porque `<motivo>`"**.
- **Ancore num gatilho concreto** — nao generalize ate perder o gatilho. O gatilho e o que torna a regra acionavel sem virar platitude.

| Instancia (especifico demais) | Platitude (generico demais) | Principio + gatilho (alvo) |
|---|---|---|
| "No checkout desta feature faltou tratar carrinho vazio" | "Trate edge cases" | "Ao iterar colecao vinda de input externo, cubra o caso-vazio antes — o time rejeita isso em review" |
| "Usei axios no service de pagamento e pediram fetch" | "Siga os padroes do projeto" | "Neste repo, novos HTTP calls usam `fetch`, nao axios (deprecated) — checar antes de adicionar dependencia de rede" |
| "PR #42 quebrou porque mockei o DB" | "Escreva bons testes" | "Testes de integracao que tocam schema precisam de DB real (branch dev), nao mock — mock diverge de prod" |

Se voce nao consegue formular um gatilho concreto sem cair na coluna da esquerda ou da direita, o candidato provavelmente falha nos filtros 2 ou 3 — descarte.

**3b — Aplique os 6 filtros duros (secao Principios) sobre o principio generalizado**, nao sobre a instancia. **Se falhar em qualquer um, descarte silenciosamente.**

Candidato passa nos filtros? Capture:
- **Frase nuclear** (1-2 linhas: o **principio + gatilho**, ja generalizado — nao a instancia)
- **Por que** (o motivo/contexto — extraido do texto fonte; inclui "quem apontou o erro" quando veio de review)
- **Aplicar quando** (o gatilho reconhecivel — quando essa regra reaparece)
- **Referencias** (path:linha, PR #, comentario do review de origem, IMP)
- **Origem** (qual IMP/review/PR)

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
Candidato 1/N — origem: IMP-<data>-<feature>.md  [reforco negativo]

Frase nuclear (principio + gatilho):
"Ao adicionar tabela que referencia outra, validar a integridade na camada de aplicacao —
 este schema nao suporta FK. Tentar FK quebra o deploy de schema."

Por que:
"IMP registrou retrabalho: primeira versao usou FK, deploy falhou, teve que refazer.
 ARCHITECTURE.md:<linhas> ja dizia, mas o agente nao checou."

Aplicar quando:
"Sempre que adicionar tabela com referencia a outra (gatilho: nova FK)."

Proposta:
- Tipo: decision
- Slug: schema-sem-fk-validar-aplicacao
- Acao: CRIAR (nao achei similar no MEMORY.md)

Aceitar? (s = salvar, p = pular, e = editar antes, t = mudar tipo)
```

**Origem GitHub PR — erro evitavel apontado em thread (reforco negativo):**

```
Candidato 2/N — origem: PR #<N>, thread em src/foo.ts:42 (3 mensagens)  [reforco negativo]

Thread (resumida):
  @wisley7l: "Vou usar lock pessimista aqui — pra evitar race no checkout"
  @maria: "Pessimista pode segurar muito tempo se a transacao crescer. Considera optimistic + retry?"
  @wisley7l: "Bom ponto, com retry resolve. Fechou."

O que o agente errou:
"Defaultou pra lock pessimista num fluxo transacional; @maria teve que corrigir em review."

Frase nuclear (principio + gatilho, generalizado):
"Em fluxo transacional cuja transacao pode crescer (checkout, batch), preferir optimistic
 locking + retry a pessimista — pessimista segura o lock por toda a duracao da transacao."

Por que:
"Erro apontado por @maria no PR #<N>. Pessimista risca lock longo; com optimistic + retry o
 lock so existe na confirmacao. Regra generalizada do caso do checkout pra qualquer transacao longa."

Aplicar quando:
"Antes de escolher estrategia de lock em fluxo transacional (gatilho: 'preciso de lock aqui')."

Proposta:
- Tipo: lesson   (comportamental: da proxima vez, nao default pra pessimista)
- Slug: transacao-longa-optimistic-lock
- Acao: CRIAR (nao achei similar no MEMORY.md)

Aceitar? (s = salvar, p = pular, e = editar antes, t = mudar tipo)
```

**Origem GitHub PR — padrao validado em review (reforco positivo):**

```
Candidato 3/N — origem: PR #<N>, review formal de @joao (state: APPROVED)  [reforco positivo]

O que funcionou:
"@joao elogiou explicitamente o uso de result-type pro erro em vez de throw no service layer."

Frase nuclear (principio + gatilho):
"No service layer, retornar Result/Either pra erro de negocio em vez de lancar excecao —
 o time aprova e trata como padrao. Excecao so pra falha inesperada."

Por que:
"Review APPROVED com nota: 'boa, result-type deixa o fluxo de erro explicito no tipo, sem
 try/catch escondendo caminho.' Reforco positivo — repetir esse padrao."

Aplicar quando:
"Ao modelar erro de negocio em qualquer service (gatilho: 'onde/como sinalizar esse erro')."

Proposta:
- Tipo: preference   (padrao do projeto validado pelo time)
- Slug: service-erro-negocio-result-type
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
- **Filtros sao bloqueantes**: candidato que falha em qualquer um dos 6 filtros e descartado sem mostrar ao usuario
- **Principio, nao instancia**: toda frase nuclear e uma regra generalizada (principio + gatilho), nunca o incidente cru da feature. Se nao da pra generalizar sem virar platitude, descarta (filtros 2/3)
- **Erro evitavel primeiro**: comentario do time que corrigiu o autor e a fonte #1 de reforco — leia o PR procurando correcoes antes de trade-offs
- **1 candidato por vez**: nao bulk approval — usuario decide caso a caso
- **Origem rastreavel**: toda nota gerada por este command guarda `metadata.origem` apontando pro IMP/review/PR
- **MEMORY.md obrigatorio**: nota criada sem linha no `MEMORY.md` vira orfa — sempre atualize o indice
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` ja sao contexto do projeto, nao precisam virar memoria
- **Sem fonte = `[NEEDS VERIFICATION]`**: claim que veio do IMP sem fonte verificavel marca a nota como verificar antes de virar canonica
- **GitHub via `gh` CLI**: nunca tokens manuais. Se `gh` falhar (auth/rate limit/network), siga com fontes locais e avise
- **Bots filtrados, autor incluso**: ignore comentarios cujo login termina com `[bot]`. Comentarios do autor do PR (provavelmente o proprio user) sao incluidos — a decisao emergente vem da conversa toda
- **Comentario que corrige o agente vale mesmo isolado**: um unico comentario do reviewer pedindo mudanca ("usa X em vez de Y", "isso quebra quando...") e reforco negativo forte — nao precisa virar thread. Threads com 2+ mensagens sao ricas pra decisao consensual, mas a correcao isolada ja e candidato. So descarte comentario isolado que nao corrige nada nem tem "por que" (elogio vago, "lgtm")
- **Regra generica, nao comentario literal**: o candidato captura o **principio generalizado** (o que fazer/evitar da proxima vez), nao a frase crua do reviewer nem "so a decisao consensual desta feature". Sempre extraia "o que o agente errou/acertou + a regra transferivel + o motivo"
