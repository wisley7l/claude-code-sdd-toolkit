---
description: Busca otimizada via subagent isolado. Default Sonnet, --rapido (Haiku), --profundo (Opus). Inline + opt-in salvar em thoughts/research/. Zero impacto no contexto principal.
model: claude-sonnet-5
argument-hint: [--rapido|--profundo] [--save] <query>
allowed-tools: Agent, Read, Write, WebFetch, WebSearch, Bash(git worktree list*), Bash(mkdir *), Bash(date *), mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# /busca — Pesquisa via subagent isolado

Voce delega uma pesquisa pra subagent rodando no modelo apropriado. Subagent **nao herda** o contexto da sessao atual — pesquisa do zero, sintese volta inline. Zero impacto no contexto principal.

## Quando usar

- Duvida que precisa olhar na internet ou doc oficial de lib
- Lookup factual rapido (versao, comando, sintaxe)
- Comparacao tecnica (X vs Y)
- Sintese de multiplas fontes
- Voce nao quer parar o trabalho atual pra pesquisar

## Quando NAO usar

- Pergunta sobre o codigo do projeto atual → use `Grep`, `Read` ou subagent `Explore` diretamente
- Pergunta cuja resposta voce ja tem no contexto → responda direto
- Pesquisa complexa que vai virar feature → use `/sdd-plan` (que ja faz Knowledge Verification Chain)

## Parse de $ARGUMENTS

Parseie a string de argumentos (case-insensitive, trim espacos):

1. **--rapido** ou **-r** → modo Haiku
2. **--profundo** ou **-p** → modo Opus
3. **--save** ou **-s** → flag pra salvar em `thoughts/research/`
4. **Sem flag de modo** → modo Sonnet (default)
5. **Resto da string** → query a pesquisar

Exemplos:

| Invocacao | Modo | Save | Query |
|---|---|---|---|
| `/busca qual a versao atual do node 22 LTS` | Sonnet | nao | `qual a versao atual do node 22 LTS` |
| `/busca --rapido comando pra ver disk usage no linux` | Haiku | nao | `comando pra ver disk usage no linux` |
| `/busca --profundo vitest vs jest pra monorepo TS` | Opus | nao | `vitest vs jest pra monorepo TS` |
| `/busca --save best practices prompt caching anthropic` | Sonnet | sim | `best practices prompt caching anthropic` |
| `/busca -p -s arquitetura SSE vs WebSocket producao` | Opus | sim | `arquitetura SSE vs WebSocket producao` |

## Modelo por modo

| Modo | Modelo | Quando usar | Custo relativo |
|---|---|---|---|
| `--rapido` | `claude-haiku-4-5-20251001` | Lookup factual, comando exato, versao, sintaxe — resposta cabe em 1-3 linhas | $ |
| **default** | `claude-sonnet-5` | Exploracao media, conceito tecnico, best practices, doc oficial — resposta cabe em 1 paragrafo + bullets | $$ |
| `--profundo` | `claude-opus-4-8` | Comparacao com nuance, trade-offs arquiteturais, sintese de 3+ fontes — resposta exige raciocinio | $$$ |

> Se errou o modo (Haiku trouxe resposta rasa demais), refaca com modo superior. Nunca "promova" o modo internamente sem refazer o spawn — Haiku-rodando-com-prompt-de-Opus ainda eh Haiku.

---

## Fluxo

### 1. Validar query

Se query vazia depois de remover flags, mostre:

```
Voce nao me deu o que pesquisar. Tente:
  /busca <pergunta>
  /busca --rapido <pergunta>
  /busca --profundo <pergunta>
  /busca --save <pergunta>
  /busca --profundo --save <pergunta>
```

E pare. Nao chute o que o user quis.

### 2. Lancar subagent

Use `Agent` tool com:

- `subagent_type`: `general-purpose`
- `model`: conforme tabela de modelo por modo
- `description`: 3-5 palavras com a query truncada (ex: "Buscar vitest vs jest")
- `prompt`: o template abaixo (substitua placeholders entre `<>`)

**Template do prompt do subagent:**

```
Voce e um pesquisador independente. Sua unica missao: responder a pergunta abaixo usando WebSearch, WebFetch e (se aplicavel) Context7 MCP. Voce NAO tem o contexto da sessao principal — pesquise do zero.

Pergunta: <query do user>

Modo: <rapido | medio | profundo>

Diretrizes por modo:

- **rapido**: 1-3 fontes maximo. Resposta direta em 1-3 linhas. Sem narrativa, sem disclaimer.
- **medio**: 3-5 fontes. Resposta em 1 paragrafo + bullets com pontos chave. Cite fontes inline.
- **profundo**: 5+ fontes. Sintese estruturada com sub-secoes (Visao geral, Comparacao, Trade-offs, Recomendacao). Sempre cite fonte na sub-secao em que aparece.

Ferramentas (escolha conforme a query):
- **WebSearch**: pra exploracao ampla, termos sem URL conhecida
- **WebFetch**: pra ler URL especifica (doc oficial, RFC, blog tecnico, repo GitHub)
- **mcp__context7__resolve-library-id** + **mcp__context7__query-docs**: pra doc oficial de lib quando a query menciona biblioteca/framework. Preferir Context7 sobre WebSearch quando a query e sobre uma lib conhecida (mais atualizado que web cache).

Output OBRIGATORIO (sem desviar do formato):

## Resposta
<resposta conforme o modo definido acima>

## Fontes consultadas
1. <titulo da pagina/doc> — <url> — <2-5 palavras do que essa fonte contribuiu>
2. ...

## Confiabilidade
<alta | media | baixa> — <1 frase justificando, ex: "doc oficial atualizada em 2025" ou "fonte secundaria, recomendo validar com a doc oficial">

NAO inclua:
- Narrativa do processo ("eu busquei X, depois Y, encontrei...")
- Disclaimers genericos ("baseado nos resultados...")
- Trechos longos copiados das fontes (cite, nao parafraseie)
- Recomendacao alem do escopo da pergunta
```

### 3. Apresentar resposta no main agent

Mostre o output do subagent INTEGRAL na sessao principal, com header curto:

```
🔍 Busca [<modo>]: "<query>"
Modelo: <modelo usado>
---
<output integral do subagent>
```

Nao reformate, nao resuma — o subagent ja entregou no formato certo. Se vier fora do formato (sem "## Resposta" / "## Fontes consultadas" / "## Confiabilidade"), informe o user que o output veio quebrado e ofereca refazer.

### 4. Salvar (se --save OU se profundo)

**Sempre salvar quando**:
- Flag `--save` ou `-s` presente

**Oferecer salvar quando**:
- Modo `--profundo` sem `--save` explicito (vale o esforco persistir): ao final da resposta, pergunte:
  ```
  Foi uma busca profunda — vale persistir em thoughts/research/?
  [s/N]
  ```

**Nunca oferecer salvar** quando o modo eh rapido/medio sem `--save` — mantem o command leve.

**Como salvar:**

Resolva o root do projeto principal:
```bash
git worktree list | head -1 | awk '{print $1}'
```

Crie diretorio se nao existir:
```bash
mkdir -p <root>/thoughts/research
```

Gere o slug a partir da query: primeiras 4-5 palavras, lowercase, sem stopwords (de/da/do/o/a/em/pra/que/the/of/in/for/to), separadas por hifen, sem caracteres especiais.

Exemplo: `"vitest vs jest pra monorepo TS"` → `vitest-vs-jest-monorepo-ts`

Escreva `<root>/thoughts/research/<YYYY-MM-DD>-<slug>.md`:

```markdown
---
date: YYYY-MM-DD
mode: <rapido | medio | profundo>
modelo: <modelo usado>
query: <query original literal>
---

# Busca: <query original>

<output integral do subagent>
```

Use `date +%Y-%m-%d` pra YYYY-MM-DD.

Informe ao user no fim da resposta:
```
💾 Salvo em thoughts/research/<YYYY-MM-DD>-<slug>.md
```

### 5. Encerrar

Nao continue conversa apos a apresentacao da busca, a menos que o user faca followup. O command e auto-contido — entregou, terminou.

---

## Padroes de uso comuns

**Dvida factual rapida durante codigo**:
```
/busca --rapido comando pra ver tamanho de pasta no linux
```

**Entender conceito tecnico**:
```
/busca o que sao Server-Sent Events e quando usar
```

**Comparacao com nuance pra decidir tech stack**:
```
/busca --profundo --save bun vs node vs deno pra api typescript em producao
```

**Verificar versao/changelog de lib**:
```
/busca --rapido versao atual e suporte LTS do node 22
```

**Best practices de feature**:
```
/busca prompt caching anthropic API best practices
```

---

## Guardrails

- **Subagent isolado obrigatorio**: nunca rode WebSearch/WebFetch direto no main agent. O ponto do command eh isolar contexto
- **Modelo por modo, sem sobrescrita interna**: rapido = Haiku, default = Sonnet, profundo = Opus. Se o resultado vier raso, **refaca com modo superior** — nao tente "fortalecer" o prompt
- **Fontes obrigatorias**: subagent SEMPRE cita fontes (url ou referencia de doc). Resposta sem fonte = output quebrado, refaca
- **Sem poluir contexto principal**: o output do subagent ja vem filtrado pelo template. Se vier longo demais, o subagent nao seguiu o protocolo — flagar
- **Context7 pra lib**: doc oficial de biblioteca = preferencia Context7 sobre WebSearch (mais atualizado que cache da web)
- **Confiabilidade explicita**: toda busca declara nivel (alta/media/baixa) — user decide se age sobre o resultado
- **--save respeita root do projeto**: nunca salvar dentro de worktree, sempre no repo principal via `git worktree list | head -1`
- **Query vazia = abort**: nao chute o que o user quis pesquisar
- **Nao mistura com memoria persistente**: este command nao consulta nem escreve no auto-memory. Pra registrar aprendizado de pesquisa, use `/sdd-learning` ou pergunte ao memory-keeper
- **Followup vira nova busca**: se o user fizer pergunta de followup, sugira `/busca` novamente — nao tente continuar a pesquisa no main agent (perde isolamento)
