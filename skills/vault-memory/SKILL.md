---
name: vault-memory
description: Lê e escreve memórias gerais em vault Obsidian central (tipos user, feedback, project, reference) com escopo global, por org ou por projeto. Use sempre que houver vault detectado via $CLAUDE_VAULT_PATH — no início da sessão pra carregar contexto rico (perfil do usuário, regras de colaboração, decisões de projeto, referências externas), e quando o usuário pedir explicitamente "lembra disso" / "anota aí" / "salva na memória" pra registrar nota nova. NÃO cobre memórias persistentes do workflow SDD (decisao/blocker/licao/ideia/preferencia em `<org>/<projeto>/state/`) — essas são geradas pelos commands `/sdd-plan`, `/executor-plan`, `/quick-task`, `/sdd-learning` do `claude-code-sdd-toolkit`.
---

# Vault Memory — Memórias Gerais

Skill responsável **apenas pelo sabor "geral"** de memória no vault Obsidian. O sabor "SDD persistente" (notas em `<org>/<projeto>/state/*/`) é território dos commands do `claude-code-sdd-toolkit` — **não toque**.

## 1. Detecção

```bash
test -n "$CLAUDE_VAULT_PATH" && test -d "$CLAUDE_VAULT_PATH"
```

- Variável definida + diretório existe → modo ativo.
- Caso contrário → não opere. Reporte uma vez: *"Vault não detectado. Exporte `CLAUDE_VAULT_PATH` pra ativar."* Não infira o path nem crie vault automaticamente.

## 2. Tipos de memória (sabor geral)

| Tipo | O que captura | Escopo típico | Exemplo |
|---|---|---|---|
| `user` | Perfil, papel, conhecimento, preferências do usuário | **só `global`** | "User trabalha como tech lead na Acme" |
| `feedback` | Regra de colaboração ("faça X / nunca Y") | qualquer | "Em worktree, usar paths do worktree" |
| `project` | Decisão/contexto/deadline não-óbvio sobre o trabalho | `<org>/<projeto>` (ou `<org>` se vale na org) | "Merge freeze após 2026-03-05" |
| `reference` | Ponteiro pra sistema externo (URL, dashboard, tracker) | qualquer | "Linear INGEST tracks pipeline bugs" |

**`user` é always-global**. Não crie em escopo de projeto.

## 3. Escopos

Três níveis, do mais específico ao mais amplo:

- `<org>/<projeto>/` — específico do projeto (ex: `acme/web-app/`)
- `<org>/` — vale em toda a org (ex: `acme/`)
- `global/` — vale em qualquer projeto

**Heurística pra resolver `<org>/<projeto>`** do cwd:

1. `git rev-parse --show-toplevel`, remover `.worktrees/<branch>` se presente.
2. Se path bate `*/codigos/<seg1>/<seg2>/...` → `<org>=<seg1>`, `<projeto>=<seg2>`.
3. Verificar `$CLAUDE_VAULT_PATH/<org>/<projeto>/` existe.

A convenção `~/codigos/<org>/<projeto>/` é só uma sugestão — adapte a heurística se o usuário organiza repositórios em outra estrutura.

**Promoção de escopo**: comece o mais específico. Se a nota acaba valendo em mais lugares, promover é fácil (mover arquivo + atualizar hubs).

## 4. Estrutura

```
$CLAUDE_VAULT_PATH/
├── Comecar-aqui.md              # índice raiz (lista orgs/hubs)
├── global/
│   ├── Global.md                # hub global
│   ├── user/                    # só global
│   ├── feedback/
│   ├── project/                 # raro em global, mas pode
│   └── reference/
├── <org>/
│   ├── <NomeDaOrg>.md           # opcional — só se houver notas no escopo da org
│   ├── feedback/
│   ├── project/
│   └── reference/
└── <org>/<projeto>/
    ├── <NomeDoHub>.md           # hub do projeto (ex: Web-App.md)
    ├── feedback/
    ├── project/
    ├── reference/
    └── state/                   # ⚠️ NÃO MEXER — território do toolkit SDD
        └── <decisoes|blockers|licoes|ideias|preferencias>/
```

**Não toque em `state/`** — sabor SDD. Comandos `/sdd-plan`, `/executor-plan`, `/quick-task`, `/sdd-learning` cuidam disso.

## 5. Formato da nota (sabor geral)

Ver `references/nota-template.md` para corpo por tipo. Frontmatter sempre:

```yaml
---
name: slug-kebab-case-igual-ao-arquivo
description: 1 linha — usada por agentes pra decidir se vale abrir
type: user | feedback | project | reference
scope: global | <org> | <org>/<projeto>
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [palavras-chave, opcional]
---
```

**Regras invariantes**:
- `type` bate com a subpasta.
- `scope` bate com o path exato (`scope: global` em `global/`, `scope: acme/finance-app` em `acme/finance-app/`).
- Wikilinks `[[outra]]` no corpo pra conectar memórias.
- Rodapé **sempre** `↑ [[<NomeDoHub>]]` (do escopo da nota — nunca `Comecar-aqui` direto).
- Para `feedback` e `project`: incluir **Why** + **How to apply**.
- Para `reference`: incluir **O que tem lá** + **Quando usar** (nunca credenciais).
- Nomes de arquivo **únicos no vault inteiro** — graph view do Obsidian usa nome como nó.

## 6. Hubs

Ver `references/hub-template.md`. Cada escopo tem **um único hub** na raiz do escopo.

**Convenção de nome**: capitalize cada segmento kebab. `web-app` → `Web-App.md`, `claude-code-sdd-toolkit` → `Claude-Code-Sdd-Toolkit.md`.

**Apelidos são permitidos** — se já existir hub com nome diferente (ex: pasta `acme/web-storefront/` com hub `legacy-shop.md`, herdado de um repo antigo), **mantenha o existente**. Descobrir com:

```bash
ls "$CLAUDE_VAULT_PATH/<path>/"*.md 2>/dev/null
```

Primeiro `.md` na raiz da pasta = hub. Cada projeto tem um.

**Hub lista as notas do sabor geral por tipo**, com hook curto:

```
### Feedback
- [[slug]] — uma linha do que cobre
```

Hub **não lista** notas do `state/` — esse sabor tem visualização própria.

## 7. Algoritmo de leitura

```
1. Detectar (seção 1). Falhou? Parar.
2. Ler global/Global.md sempre — perfil + regras transversais.
3. Resolver <org>/<projeto> do cwd (seção 3).
4. Se <org>/<NomeDaOrg>.md existe → ler.
5. Se <org>/<projeto>/<NomeDoHub>.md existe → ler.
6. Pelos hubs, identificar notas individuais relevantes (pelo hook/description). Abrir só as relevantes.
7. NUNCA varrer todas as notas. Hubs são o filtro primário.
```

## 8. Algoritmo de escrita (sob pedido explícito)

**Regra dura**: NÃO salvar por iniciativa. Só com pedido claro do usuário: *"lembra disso"*, *"anota aí"*, *"salva na memória"*, *"guarda isso"*, ou equivalente.

Quando autorizado:

1. **Decidir tipo + escopo** com o usuário. Default: mais específico que faz sentido.
2. **Procurar nota similar** primeiro — atualizar > duplicar.
3. **Criar `<escopo>/<tipo>/<slug>.md`** com frontmatter completo + corpo conforme template. `mkdir -p` na subpasta se nova.
4. **Atualizar o hub do escopo** — adicionar linha na seção do tipo:
   ```
   - [[<slug>]] — hook curto de 1 linha
   ```
   Sem essa linha, a nota fica órfã (só descobrível por graph view).
5. **Se for primeira nota da org/projeto**, atualizar `Comecar-aqui.md` adicionando o hub na seção da org.

**NÃO** anunciar "salvei!" verbosamente — a tool call já é visível.

## 9. Quando promover

Se uma `preferencia` do sabor SDD (`<org>/<projeto>/state/preferencias/...`) virar regra cross-project, **promova manualmente** pra `global/feedback/`:

1. Crie nova nota em `global/feedback/<slug>.md` com frontmatter do sabor geral.
2. Atualize hub `Global.md`.
3. Opcional: deixe nota original em `state/preferencias/` apontando pra promovida (`Ver [[slug-promovida]]`).

**Só promova sob pedido explícito do usuário.**

## 10. Fallback gracioso

Operação falhou (path quebrado, permissão, escrita falhou) → reporte uma vez, continue a tarefa principal sem o vault. Não tente "consertar" automaticamente.

## 11. Invocação direta

Quando o usuário invocar este skill explicitamente, reporte:
- Status detecção + path.
- `<org>/<projeto>` resolvido pro cwd.
- Hubs encontrados (global + org + projeto).
- Contagem de notas **só do sabor geral** por tipo (não conte `state/`).
- Inconsistências detectadas (hub faltando, nota sem entrada no hub, etc).

---

**Regra de ouro**: skill cobre só sabor geral. `state/` é território do toolkit SDD. Toda escrita é sob pedido. Toda leitura passa pelos hubs.
