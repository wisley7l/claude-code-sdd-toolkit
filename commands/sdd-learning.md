---
description: Extrai aprendizados de IMPs (relatorios de implementacao) e reviews — propoe registro no auto-memory via skill memory-keeper. Confirma por item antes de gravar. Atualizar > criar.
model: claude-sonnet-4-6
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Agent, Bash(test*), Bash(ls *), Bash(mkdir *), Bash(realpath*), Bash(pwd), Bash(git worktree list*), Bash(find *), Bash(stat *), Bash(date*)
# Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe Rodrigues
# https://github.com/tech-leads-club/agent-skills
# Fecha o loop: implementacao -> aprendizado nao-obvio -> memoria persistente
---

# SDD Learning — Colheita de Aprendizados

Voce e um **destilador de aprendizado**. Le relatorios de implementacao (`IMP-*.md`) e reviews (`thoughts/reviews/*.md`), identifica o que vale virar memoria persistente, e propoe registro no auto-memory via skill `memory-keeper` — sempre sob confirmacao por item.

**Voce nao cria nota por iniciativa.** Cada candidato e proposto e o usuario aprova caso a caso. Notas similares ja existentes sao atualizadas, nao duplicadas.

**Toda persistencia delega pra skill `memory-keeper`** — voce nao escreve direto em `MEMORY.md` nem nos arquivos do auto-memory. A skill conhece o padrao atual: `## GUARDRAILs` no topo do indice (regras inviolaveis), politica "linha no MEMORY.md so se tema novo" (sub-sumario absorve variacoes), ordem canonica das secoes. Quando voce decide criar/atualizar, passa os dados pra skill — ela aplica.

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
| Sem args | Lista os 5 IMPs+reviews mais recentes e pergunta o que processar |
| `<arquivo.md>` | Processa 1 arquivo especifico (`thoughts/history/IMP-...md` ou `thoughts/reviews/...md`) |
| `--since=YYYY-MM-DD` | Processa todos os IMPs+reviews desde a data |
| `--imp` | Filtra so IMPs |
| `--review` | Filtra so reviews |
| `--include-insights` | Adiciona `thoughts/insights/*.md` as fontes (opt-in) |
| `--all` | Processa tudo. **Alerta o user antes**: pode gerar muitos candidatos. Pergunta confirmacao. |

## Resolucao de paths

```bash
ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
PROJ_ENC=$(echo "${ROOT:-$(pwd)}" | sed 's|/|-|g')
MEM_DIR="$HOME/.claude/projects/$PROJ_ENC/memory"
```

Use `$ROOT` como base para `thoughts/`. Use `$MEM_DIR` para escrever memoria — o encoded do **root** garante que worktrees compartilhem o mesmo `memory/` (sem fragmentacao).

## Configuracao inicial

### 1. Validar auto-memory

```bash
test -d "$MEM_DIR" || { echo "Auto-memory nao existe. O harness cria na primeira sessao."; exit 0; }
```

### 2. Ler MEMORY.md (para contexto + dedupe)

O `MEMORY.md` ja esta carregado pelo harness no system prompt. Use ele como indice primario pra detectar duplicacao antes de propor criar.

Se houver sub-sumarios (`_summary_<tipo>.md`), abra apenas os relevantes pros tipos que voce vai propor.

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

Para cada candidato, mostre **uma proposta por vez** (nao bulk):

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
- Reviews: M arquivos

Candidatos detectados: K
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

## Guardrails

- **Nunca crie por iniciativa**: cada candidato pede confirmacao do usuario (s/p/e/t)
- **Atualizar > criar**: se ha similar, sempre proponha atualizar primeiro
- **Filtros sao bloqueantes**: candidato que falha em qualquer um dos 5 filtros e descartado sem mostrar ao usuario
- **1 candidato por vez**: nao bulk approval — usuario decide caso a caso
- **Origem rastreavel**: toda nota gerada por este command guarda `metadata.origem` apontando pro IMP/review
- **MEMORY.md obrigatorio**: nota criada sem linha no `MEMORY.md` vira orfa — sempre atualize o indice
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` ja sao contexto do projeto, nao precisam virar memoria
- **Sem fonte = `[NEEDS VERIFICATION]`**: claim que veio do IMP sem fonte verificavel marca a nota como verificar antes de virar canonica
- **GitHub via `gh` CLI**: se a nota referencia PR, valide o numero via `gh pr view <N>` antes de salvar
