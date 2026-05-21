---
name: memory-keeper
description: Lê e escreve memórias persistentes no auto-memory nativo do Claude Code (`~/.claude/projects/<projeto>/memory/`). Cobre 9 tipos — 4 nativos (user, feedback, project, reference) + 5 SDD (decision, blocker, lesson, idea, preference). Use sempre que o usuário pedir "lembra disso" / "anota" / "salva na memória", ou quando um command SDD precisar persistir aprendizado/decisão. Convenção flat (sem subpastas), MEMORY.md em formato tabela agrupada por tipo. Substitui a skill `vault-memory` (deprecated).
---

# memory-keeper — Memórias persistentes no auto-memory

Skill responsável por todo o ciclo de memória persistente do Claude Code: leitura, escrita e atualização do índice `MEMORY.md`. Usa **apenas** o sistema de auto-memory nativo (`~/.claude/projects/<projeto>/memory/`) — não toca vault Obsidian, não cria estrutura paralela.

## 1. Localização

Path do auto-memory por projeto (gerenciado pelo harness):

```
~/.claude/projects/<projeto-encoded>/memory/
```

`<projeto-encoded>` é o cwd com `/` substituído por `-`. Pra descobrir o path real:

```bash
PROJ_ENC=$(pwd | sed 's|/|-|g')
echo "$HOME/.claude/projects/$PROJ_ENC/memory/"
```

O harness já carrega `MEMORY.md` no system prompt no início de cada sessão (primeiras 200 linhas ou 25KB). Topic files (notas individuais) **não** são carregados automaticamente — só sob demanda via Read.

**Escopo global** (`~/.claude/memory/`) não tem suporte nativo confirmado. Esta skill opera **só per-projeto**. Notas que valem em qualquer projeto vão pro `~/.claude/CLAUDE.md` global (não auto-memory).

## 2. Tipos (9 no total)

**Sabor geral** (uso amplo, regras de colaboração):

| Tipo | Captura | Exemplo |
|---|---|---|
| `user` | Perfil, papel, conhecimento, preferências do usuário | "Wisley usa statusline com barra de contexto" |
| `feedback` | Regra de colaboração ("faça X" / "nunca Y") | "Bash perm precisa de espaço antes do `*`" |
| `project` | Decisão/contexto não-óbvio sobre o projeto | "Commands ficam em `commands/`, não `.claude/commands/`" |
| `reference` | Ponteiro pra sistema externo | "Linear INGEST rastreia bugs de pipeline" |

**Sabor SDD** (gerado pelos commands `/sdd-plan`, `/executor-plan`, `/quick-task`, `/sdd-learning`):

| Tipo | Captura | Exemplo |
|---|---|---|
| `decision` | Decisão arquitetural/técnica tomada com contexto | "Adotar X em vez de Y porque..." |
| `blocker` | Bloqueio conhecido + workaround reutilizável | "API Z falha com payload > 10KB — chunkar" |
| `lesson` | Aprendizado de execução/review | "Testes E2E precisam de DB real, não mock" |
| `idea` | Ideia pra explorar depois | "Cachear resultado de F() pode reduzir N queries" |
| `preference` | Preferência específica do projeto | "Neste repo: 1 PR por feature, não bundled" |

**Quando o tipo não é óbvio**, pergunte ao usuário. Default mais usado: `feedback`.

## 3. Convenção de nome

- **Arquivo**: `<tipo>_<slug>.md` — underscore separa tipo do slug (ex: `feedback_bash_permission_syntax.md`, `decision_vault_deprecation.md`)
- **Slug**: snake_case ou kebab — preserve o estilo do que já existe no projeto. Se vazio, use snake_case.
- **`name:` interno** (frontmatter): kebab-case correspondente (`feedback-bash-permission-syntax`)
- **Sem subpastas** — auto-memory nativo é flat. Não criar `memory/feedback/foo.md`.

## 4. Frontmatter

Mínimo obrigatório:

```yaml
---
name: <tipo>-<slug-kebab>
description: 1 linha — usada por agentes pra decidir se vale abrir
metadata:
  type: user | feedback | project | reference | decision | blocker | lesson | idea | preference
---
```

Opcionais (use quando fizer sentido):

```yaml
metadata:
  type: ...
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  topic: <agrupamento>           # ex: "bash-permissions", "statusline"
  pr: <número>                   # pra notas ligadas a PR específico
  branch: <nome>                 # pra notas ligadas a branch
```

O harness adiciona automaticamente `metadata.node_type: memory` e `metadata.originSessionId: <uuid>` — **não remover esses campos** se já existirem.

## 5. Corpo da nota

**Para `feedback`, `project`, `decision`, `blocker`, `lesson`, `preference`** — incluir:

```markdown
<descrição da regra / decisão / contexto>

**Why:** <a razão — incidente passado, constraint, preferência forte>

**How to apply:** <quando/onde aplicar — gatilhos concretos>
```

**Para `user`** — descrição livre + `**Why:**` opcional (geralmente "preferência confirmada").

**Para `reference`** — formato:

```markdown
<URL ou identificador do sistema>

**O que tem lá:** <conteúdo/dado disponível>

**Quando usar:** <gatilho pra consultar>
```

**Nunca incluir credenciais, tokens ou secrets** em notas `reference`.

**Para `idea`** — formato livre, com motivação curta.

## 6. Algoritmo de leitura

```
1. MEMORY.md já está no system prompt — agent já tem o índice.
2. Pelo hook/description de cada linha, identificar notas relevantes pro task atual.
3. Abrir apenas as relevantes via Read.
4. Se existirem sub-sumários (_summary_<tipo>.md), abrir só quando o tipo for relevante.
5. NUNCA varrer todas as notas. Índice (MEMORY.md) é o filtro primário.
```

## 7. Algoritmo de escrita

**Regra dura**: NÃO salvar por iniciativa. Só com pedido claro do usuário: *"lembra disso"*, *"anota aí"*, *"salva na memória"*, *"guarda isso"*, ou equivalente — OU quando um command SDD invoca a skill pra persistir output.

Quando autorizado:

1. **Decidir tipo + slug** com o usuário se ambíguo. Default: tipo mais comum (`feedback`).
2. **Procurar nota similar primeiro** — atualizar > duplicar:
   ```bash
   ls "$MEM_DIR" | grep -i "<keyword>"
   ```
   Se achou, atualizar a existente (frontmatter `updated:` e corpo) em vez de criar nova.
3. **Criar/atualizar `<MEM_DIR>/<tipo>_<slug>.md`** com frontmatter + corpo conforme template.
4. **Atualizar `MEMORY.md`**:
   - Se já existe seção `## <Tipo>`, adicionar linha na tabela.
   - Senão, criar seção nova respeitando a ordem canônica (seção 9).
   - Linha do índice (formato tabela):
     ```
     | [<slug-curto>](<arquivo>) | <hook curto, ≤90 chars> |
     ```
5. **Não anunciar verbosamente** — a tool call já é visível ao usuário. Frase única tipo "Salvei como `feedback_bash_permission_syntax.md`" basta.

## 8. Formato do MEMORY.md

Índice em **tabela markdown** agrupado por tipo. Cada tipo é uma seção `## <Tipo>` com tabela `| Slug | Hook |`.

Exemplo:

```markdown
# Memory Index

## User
| Slug | Hook |
|---|---|
| [statusline-layout](user_statusline_layout.md) | modelo + pasta + barra de contexto colorida |

## Feedback
| Slug | Hook |
|---|---|
| [bash-permission-syntax](feedback_bash_permission_syntax.md) | patterns precisam de espaço antes do `*` |
| [bash-compound-pitfalls](feedback_bash_compound_pitfalls.md) | newlines/subshells quebram pattern matching |
| [guardrails-negativos](feedback_guardrails_negativos.md) | "NUNCA X" > "pedir autorização antes de X" |

## Project
| Slug | Hook |
|---|---|
| [commands-path](project_commands_path.md) | slash commands ficam em `commands/` na raiz |

## Sub-sumários
| Tipo | Arquivo |
|---|---|
| (vazio até `/memory-organize` criar) | |
```

A seção `## Sub-sumários` só existe se `/memory-organize` já criou sub-sumários (ver seção 10).

## 9. Ordem canônica das seções

Em `MEMORY.md`, sempre nesta ordem:

1. `## User`
2. `## Feedback`
3. `## Project`
4. `## Reference`
5. `## Decision`
6. `## Blocker`
7. `## Lesson`
8. `## Idea`
9. `## Preference`
10. `## Sub-sumários` (se existir)

Seções vazias são omitidas. Mantenha a ordem mesmo após adições.

## 10. Sub-sumários (`_summary_<tipo>.md`)

Quando `MEMORY.md` cresce a ponto de ameaçar o limite de 200 linhas / 25KB, o comando `/memory-organize` propõe criar sub-sumários por tipo.

- **Nome**: `_summary_<tipo>.md` (underscore prefix pra ficar no topo do `ls`).
- **Conteúdo**: índice completo das notas daquele tipo (mesmo formato tabela), com mais detalhe que cabia no MEMORY.md.
- **Carregamento**: sob demanda. O `MEMORY.md` passa a referenciar o sub-sumário em vez de listar notas individuais:
  ```markdown
  ## Feedback
  Ver [[_summary_feedback.md]] — 24 notas.
  ```
- **Quando abrir um sub-sumário**: quando o task atual pode usar notas daquele tipo.

A skill **não cria sub-sumários sozinha**. Só `/memory-organize` faz, sob confirmação do usuário.

## 11. Migração e legados

- Notas antigas com convenções diferentes (sem underscore separando tipo, sem campo `metadata.type` rico) são **preservadas como estão**. Normalizar apenas quando tocadas (update natural).
- Hub `Comecar-aqui.md` ou similar **não existe** no auto-memory — só `MEMORY.md`. Se encontrar referência a hub em nota legada, deixar (não causa erro).
- Wikilinks `[[outra-nota]]` no corpo são tolerados mas não funcionam como navegação automática — preferir links markdown `[texto](arquivo.md)`.

## 12. Fallback gracioso

- Path do auto-memory não existe? Reportar uma vez: *"Auto-memory não detectado em `<path>`. Pode estar em diretório diferente — confirma `pwd`."* Não criar diretório automaticamente.
- Escrita falhou (permissão, disco)? Reportar e continuar a tarefa principal sem persistir.

## 13. Invocação direta pelo usuário

Quando o usuário invocar este skill explicitamente, reporte:

- Path resolvido do auto-memory deste projeto.
- Contagem total de notas e distribuição por tipo.
- Tamanho atual do `MEMORY.md` em linhas / KB (e se está próximo do limite).
- Sub-sumários existentes (se houver).
- Inconsistências detectadas: notas sem linha no `MEMORY.md`, linhas no `MEMORY.md` apontando pra arquivo inexistente, frontmatter inválido.

---

**Regra de ouro**: leitura via `MEMORY.md` (já carregado), escrita sob pedido explícito ou via command SDD, atualizar > duplicar, sub-sumários só via `/memory-organize`.
