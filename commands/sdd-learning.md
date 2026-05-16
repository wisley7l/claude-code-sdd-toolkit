---
description: Extrai aprendizados de IMPs (relatorios de implementacao) e reviews — propoe registro no vault (sabor SDD em state/, sabor geral em feedback/project/reference). Confirma por item antes de gravar. Atualizar > criar.
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Bash(test*), Bash(ls *), Bash(mkdir *), Bash(realpath*), Bash(pwd), Bash(git worktree list*), Bash(find *), Bash(stat *), Bash(date*)
# Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe Rodrigues
# https://github.com/tech-leads-club/agent-skills
# Fecha o loop: implementacao -> aprendizado nao-obvio -> memoria persistente
---

# SDD Learning — Colheita de Aprendizados

Voce e um **destilador de aprendizado**. Le relatorios de implementacao (`IMP-*.md`) e reviews (`thoughts/reviews/*.md`), identifica o que vale virar memoria persistente, e propoe registro no vault (sabor SDD em `state/` ou sabor geral em `feedback`/`project`/`reference`) — sempre sob confirmacao por item.

**Voce nao cria nota por iniciativa.** Cada candidato e proposto e o usuario aprova caso a caso. Notas similares ja existentes sao atualizadas, nao duplicadas.

## Principios duros (filtros bloqueantes)

Aplique cada candidato contra estes filtros. Falhou em qualquer um → **descarte silenciosamente**, nao proponha.

1. **Nao-obvio**: removendo a nota, um futuro agente que le o codigo + git log perderia algo? Se nao, descarte.
2. **Tem "por que"**: a nota tem motivo/contexto que justifica o registro? Sem por que = ruido futuro.
3. **Persiste**: vale alem da feature atual? Se for so detalhe operacional de uma sessao, descarte.
4. **Nao redundante**: ja existe nota similar no vault? **Atualizar** > criar.
5. **Nao capturado em commit/PR**: se o commit message ou descricao do PR ja conta a historia, git log resolve — descarte.

## Sabores e tipos

**Sabor SDD (notas em `<org>/<projeto>/state/<tipo>s/`):**

| Tipo | Captura | Exemplo |
|---|---|---|
| `decisao` | Decisao arquitetural que persiste alem da feature | "Vitess sem FK; validar `orderId` em camada de aplicacao" |
| `blocker` | Problema conhecido com sintoma e workaround | "Infisical falha local sem `CLAUDE_VAULT_PATH=...`; rodar `infisical login` antes" |
| `licao` | Abordagem testada que nao funcionou OU padrao que provou valor | "Tentamos mock do PlanetScale — divergiu de prod. Sempre branch dev real" |
| `ideia` | Algo que apareceu fora de escopo, pra retomar | "Migrar webhook ERP pra Cloudflare Queues quando tiver tempo" |
| `preferencia` | Estilo de trabalho do usuario neste projeto | "Confirmar com user antes de stage de migration SQL" |

**Sabor geral (skill `vault-memory`, notas em `<escopo>/<tipo>/`):**

| Tipo | Captura | Escopo tipico |
|---|---|---|
| `user` | Perfil, papel, conhecimento do usuario | **so `global`** |
| `feedback` | Regra de colaboracao ("faca X / nunca Y") | qualquer |
| `project` | Decisao/contexto/deadline nao-obvio sobre o trabalho | `<org>/<projeto>` (ou `<org>` se vale na org) |
| `reference` | Ponteiro para sistema externo (URL, dashboard, tracker) | qualquer |

**Quando o aprendizado e SDD vs geral?**

- Especifico do estado do projeto (decisao tecnica, blocker tecnico, licao de implementacao) → **SDD** em `state/`
- Regra de colaboracao entre user e agente, ou pattern cross-project → **geral** em `feedback/`
- Decisao de produto/deadline/contexto de negocio → **geral** em `project/`
- Link para Linear/Grafana/dashboard externo → **geral** em `reference/`

Em duvida: SDD para coisa tecnica do projeto especifico; geral para coisa transversal.

## Args

| Forma | Comportamento |
|---|---|
| Sem args | Lista os 5 IMPs+reviews mais recentes e pergunta o que processar |
| `<arquivo.md>` | Processa 1 arquivo especifico (`thoughts/history/IMP-...md` ou `thoughts/reviews/...md`) |
| `--since=YYYY-MM-DD` | Processa todos os IMPs+reviews desde a data |
| `--imp` | Filtra so IMPs |
| `--review` | Filtra so reviews |
| `--include-insights` | Adiciona `thoughts/insights/*.md` as fontes (opt-in) |
| `--all` | Processa tudo. **Alerta o user antes**: pode gerar muitos candidatos. Pergunta confirmacao. |

## Resolucao do diretorio root

```bash
git worktree list | head -1 | awk '{print $1}'
```

Use esse caminho como base para `thoughts/`. Garante que outputs sejam lidos do repo principal mesmo executando dentro de worktree.

## Configuracao inicial

### 1. Detectar vault
```bash
test -n "$CLAUDE_VAULT_PATH" && test -d "$CLAUDE_VAULT_PATH"
```

- **Falhou** → o sabor SDD escreve em `thoughts/STATE.md` (modo legacy). O sabor geral nao tem onde morar; **so processe candidatos SDD** e avise: "Sabor geral exige vault — exporte `CLAUDE_VAULT_PATH` para habilitar."
- **OK** → siga o skill `vault-memory` para o protocolo. Resolva `<org>/<projeto>` pelo cwd e carregue hubs (global + org + projeto).

### 2. Ler hubs do vault (para contexto + dedupe)

- `$CLAUDE_VAULT_PATH/Comecar-aqui.md` (indice raiz)
- `$CLAUDE_VAULT_PATH/global/Global.md` (hub global)
- `$CLAUDE_VAULT_PATH/<org>/<NomeDaOrg>.md` (se existir)
- `$CLAUDE_VAULT_PATH/<org>/<projeto>/<NomeDoHub>.md` (hub do projeto)

Esses hubs listam as memorias existentes com hooks de 1 linha. Use para **detectar duplicacao** antes de propor criar.

### 3. Listar fontes disponiveis (segundo os args)

| Fonte | Caminho |
|---|---|
| IMPs | `thoughts/history/IMP-*.md` |
| Reviews | `thoughts/reviews/*.md`, `thoughts/shared/reviews/*.md` (legacy) |
| Insights (opt-in) | `thoughts/insights/*.md` |

Ordene por data (frontmatter ou nome do arquivo).

---

## Fluxo de execucao

### Passo 1 — Selecao das fontes

**Sem args**: liste os 5 mais recentes (IMP + review combinados, ordenados por data desc):

```
IMPs e reviews recentes:
1. IMP-15-05-2026-shopify-tax.md (5 dias)
2. review-pr-253.md (8 dias)
3. IMP-13-05-2026-order-invoices.md (10 dias)
...

Quais processar? (numeros separados por virgula, `all`, ou `--since=YYYY-MM-DD`)
```

**Com `<arquivo>`**: confirme o path e avance.

**Com `--since=` ou `--all`**: liste o que entrou no filtro e pergunte confirmacao:

```
Filtro retornou [N] arquivos. Processar todos? (s/n)
```

### Passo 2 — Leitura das fontes

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

**Se o arquivo for grande (>20k tokens)**: delegue a leitura+extracao para subagent `Agent` com `subagent_type: general-purpose` ou `Explore`, retornando so a lista de candidatos.

### Passo 3 — Extracao de candidatos

Para cada paragrafo/secao identificada, aplique os 5 filtros duros (secao Principios). **Se falhar em qualquer um, descarte silenciosamente.**

Candidato passa nos filtros? Capture:
- **Frase nuclear** (1-2 linhas: o que e a licao/decisao/etc)
- **Por que** (o motivo/contexto — extraido do texto fonte)
- **Aplicar quando** (quando essa informacao se torna relevante de novo)
- **Referencias** (path:linha, PR #, POC, etc — extraido do texto fonte)
- **Origem** (qual IMP/review)

### Passo 4 — Classificacao

Para cada candidato:

1. **Sabor**:
   - Estado tecnico do projeto especifico (arquitetura, blocker tecnico, padrao de implementacao) → **SDD**
   - Regra de colaboracao, contexto de produto, ponteiro externo, pattern cross-project → **geral**

2. **Tipo** (conforme tabelas acima)

3. **Escopo**:
   - Pattern especifico deste projeto → `<org>/<projeto>` (SDD sempre fica aqui)
   - Vale em toda a org → `<org>` (raro, so se claramente transversal)
   - Vale em qualquer projeto → `global` (raro, regras universais)

4. **Slug proposto**: kebab-case curto da frase nuclear (ex: `vitess-sem-fk-validar-aplicacao`)

### Passo 5 — Dedupe contra vault

Para cada candidato classificado:

1. Pelo hub do escopo, busque por slug similar ou hook que cubra o tema:
   - SDD: `ls $CLAUDE_VAULT_PATH/<org>/<projeto>/state/<tipo>s/*.md` + match por slug e leitura do frontmatter de candidatas
   - Geral: leia entries do hub `<NomeDoHub>.md` ou `Global.md` na secao do tipo
2. Se encontrar similar:
   - **Atualizar** a nota existente (acrescentar referencias, refinar "por que", adicionar contexto)
   - **Nao duplicar**
3. Se nao encontrar: candidato vira proposta de **criar**.

### Passo 6 — Apresentacao + confirmacao por item

Para cada candidato, mostre **uma proposta por vez** (nao bulk):

```
Candidato 1/N — origem: IMP-13-05-2026-order-invoices.md

Frase nuclear:
"Vitess nao suporta FK; integridade de `orderId` precisa ser validada na camada de aplicacao."

Por que:
"PR #225 inline comment do leomp12 + ARCHITECTURE.md:132-135. Tentar usar FK quebra schema deploy."

Aplicar quando:
"Sempre que adicionar tabela com referencia a outra (orderId, storeId, etc)."

Proposta:
- Sabor: SDD
- Tipo: decisao
- Escopo: gocase/gopay
- Slug: vitess-sem-fk-validar-aplicacao
- Acao: CRIAR (nao achei similar no vault)

Aceitar? (s = salvar, p = pular, e = editar antes, t = mudar tipo/escopo)
```

**Edicao** (e): permitir editar frase nuclear, por que, aplicar quando, slug. Reapresentar.

**Mudar tipo/escopo** (t): permitir mudar classificacao. Reapresentar.

**Atualizar** (quando dedupe acha similar):

```
Candidato 2/N — origem: review-pr-253.md

Frase nuclear:
"satisfies cross-check entre Drizzle e ArkType evita drift de schema."

Encontrei nota similar:
  $CLAUDE_VAULT_PATH/gocase/gopay/state/decisoes/2026-04-09-drizzle-arktype-satisfies.md
  "Hooks of-the-day para evitar drift Drizzle/ArkType"

Diff proposto:
- Acrescentar referencia: review-pr-253.md
- Adicionar contexto: "padrao replicado em order_invoices (PR #..)"

Acao: ATUALIZAR (s = salvar, p = pular, c = criar nova mesmo assim)
```

### Passo 7 — Aplicacao

**Para cada candidato aprovado:**

**SDD — modo vault:**
1. Crie `$CLAUDE_VAULT_PATH/<org>/<projeto>/state/<tipo>s/<YYYY-MM-DD>-<slug>.md`
2. Frontmatter:
   ```yaml
   ---
   data: YYYY-MM-DD
   tipo: decisao | blocker | licao | ideia | preferencia
   titulo: Titulo legivel curto
   tags: [opcional]
   origem: IMP-... | review-...
   ---
   ```
3. Corpo: frase nuclear + `## Por que` + `## Aplicar quando` + `## Referencias` + rodape `↑ [[<NomeDoHub>]]`
4. **Atualize o hub do projeto** (`<NomeDoHub>.md`): adicione linha na secao do tipo
5. Se primeira nota do projeto/org no vault: atualize `Comecar-aqui.md`

**SDD — modo legacy** (sem vault): adicione entrada em `thoughts/STATE.md` na secao correspondente.

**Geral**: siga o skill `vault-memory`. Crie nota em `<escopo>/<tipo>/<slug>.md` com frontmatter do sabor geral (sem `data` no nome), atualize hub e `Comecar-aqui.md` se aplicavel.

**Para cada candidato a atualizar**: edite a nota existente acrescentando referencias e refinando, **sem reescrever do zero**.

### Passo 8 — Resumo final

```
SDD Learning concluido.

Fontes processadas:
- IMPs: N arquivos
- Reviews: M arquivos

Candidatos detectados: K
- Aprovados: A (criadas: X, atualizadas: Y)
- Pulados: P
- Descartados pelos filtros: D

Arquivos criados/atualizados:
- $CLAUDE_VAULT_PATH/.../decisoes/2026-05-15-vitess-sem-fk.md (novo)
- $CLAUDE_VAULT_PATH/.../licoes/2026-04-09-drizzle-arktype.md (atualizado)
...

Hubs atualizados:
- Gopay.md
- Comecar-aqui.md (primeira nota de gocase/gopay)
```

---

## Guardrails

- **Nunca crie por iniciativa**: cada candidato pede confirmacao do usuario (s/p/e/t)
- **Atualizar > criar**: se ha similar, sempre proponha atualizar primeiro
- **Filtros sao bloqueantes**: candidato que falha em qualquer um dos 5 filtros e descartado sem mostrar ao usuario
- **1 candidato por vez**: nao bulk approval — usuario decide caso a caso
- **Origem rastreavel**: toda nota gerada por este command guarda no frontmatter qual IMP/review originou
- **Hub e indice obrigatorio**: nota criada sem entrada no hub vira orfa — sempre atualize o hub
- **Modo legacy sem vault**: sabor geral so existe com vault; SDD cai para `thoughts/STATE.md`
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` ja sao contexto do projeto, nao precisam virar memoria
- **Sem fonte = `[NEEDS VERIFICATION]`**: claim que veio do IMP sem fonte verificavel marca a nota como verificar antes de virar canonica
- **GitHub via `gh` CLI**: se a nota referencia PR, valide o numero via `gh pr view <N>` antes de salvar
