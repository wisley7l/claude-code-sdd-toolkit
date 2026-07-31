# Reference: 🗂️ Item do ROADMAP (modelo Obsidian)

Contrato do **arquivo de item** do roadmap e algoritmos determinísticos (agrupamento por status, cálculo de desbloqueados, migração do formato antigo).
Consumido por `/roadmap` (dono), `/sdd-plan` e `/sdd-plan-eco` (criam itens), `/pr-draft` (promove) e `/sdd-close` (conclui).

O roadmap é um **vault Obsidian**: cada item é um `.md`, cada dependência é um wikilink `[[...]]`, e o **grafo é nativo** (não se gera mermaid — o Obsidian desenha as arestas a partir dos links). Não existe mais bloco `mermaid` no roadmap.

## Estrutura de pastas

```
thoughts/roadmap/
  ROADMAP.md              # hub/índice — linka todos os itens (conectividade no grafo),
                          #   lista 🔴 Próximos e 🔓 Desbloqueados agora
  backlog/      NNN-slug.md
  em-progresso/ NNN-slug.md
  concluido/    NNN-slug.md
```

- **O status é a pasta onde o item vive** — é a fonte única da verdade. Não se duplica `status:` no frontmatter.
- O item **migra entre pastas** no ciclo de vida: `backlog/` → `em-progresso/` (PR aberto) → `concluido/` (PR merged).
- Mover entre pastas **não quebra wikilink**: o Obsidian resolve `[[NNN-slug]]` por nome de arquivo em todo o vault, independente da subpasta.

## Nome do arquivo (id estável)

`NNN-slug.md`, onde:
- **NNN**: sequencial de 3 dígitos, `max(NNN existentes em todas as pastas) + 1`. Nunca reusa número. É o id estável do nó no grafo — não muda ao mover de pasta nem ao ganhar PR.
- **slug**: 3-6 palavras do título em kebab-case (ex.: `042-checkout-stripe.md`).

O wikilink de dependência é sempre `[[NNN-slug]]` (o nome sem `.md`).

## Frontmatter do item

```yaml
---
id: NNN
titulo: <título completo>
pr:                    # vazio no backlog; #N quando o /pr-draft abre o draft
criado: DD-MM-YYYY
plan: <basename do PLAN>   # ex.: PLAN-16-07-2026-003-estoque.md — rastreabilidade p/ pr-draft/sdd-close
next: false            # true = está na fila curada 🔴 Próximos (ortogonal ao status)
---
```

- **`pr:`** nasce vazio; `/pr-draft` preenche com `#N` ao abrir o draft.
- **`plan:`** é o basename do PLAN — o pareamento ROADMAP ↔ PLAN ↔ PR que `/pr-draft` (promover) e `/sdd-close` (concluir) usam. Item criado fora do fluxo `/sdd-plan` pode não ter.
- **`next:`** é curadoria **humana** — nenhum command liga `next: true` sozinho. É a fila 🔴 Próximos, ortogonal ao status (um item de backlog pode ser `next`).

## Corpo do item

```markdown
# NNN — <título>

**Depende de:** [[MMM-slug-a]], [[PPP-slug-b]]
**Docs:** [[spec-<TS>-slug]] · [[PLAN-<...>-slug]]

<1 linha de contexto opcional>
```

- Os wikilinks ficam **no corpo** (não só no frontmatter) — isso garante que a aresta apareça no grafo em qualquer versão do Obsidian.
- **`Depende de:`** = as arestas de ordem (dependência entre PRs). Ausente/vazio = sem pré-requisito.
- **`Docs:`** = links pra SPEC e PLAN, que continuam em `thoughts/specs/` e `thoughts/plans/`. O item **não copia** conteúdo deles — só linka. Como o link resolve por nome, o `/sdd-close` pode mover SPEC/PLAN pra `closed/` sem quebrar o link.
- Se não há dependência, **omita** a linha `Depende de:` (não escreva "nenhuma").

## Semântica da dependência

`Depende de: [[MMM-slug]]` significa: **este item NÃO deve começar antes que MMM esteja concluído (merged)**. É a aresta de ordem entre PRs (o pai MMM vem antes do filho NNN).

- Todo `[[NNN-slug]]` referenciado deve existir como item. Link apontando pra item inexistente é **link órfão** — sinalize ao usuário (o Obsidian mostra como nó fantasma).
- **Sem ciclos**: se seguindo os `Depende de:` a partir de um item voltar nele mesmo, é erro de dado — não registre a aresta que fecha o ciclo e sinalize.

## Agrupamento por status (o hub `ROADMAP.md`)

O status de cada item = a pasta onde está. Pra montar/atualizar o hub, varra as pastas:

- `backlog/*.md` → seção **Backlog**
- `em-progresso/*.md` → seção **Em progresso**
- `concluido/*.md` → seção **Concluído**
- itens com `next: true` (em qualquer pasta, tipicamente backlog) → topo, seção **🔴 Próximos**

O hub **linka todos os itens** (`[[NNN-slug]]`) — assim nenhum item fica órfão no grafo, mesmo sem dependência. Ordene por NNN dentro de cada seção (determinístico).

## Algoritmo: 🔓 Desbloqueados agora

Responde "o que posso começar agora que tal item mergeou". Um item conta como **desbloqueado** quando:

1. está em `backlog/` (ainda não começou), **E**
2. tem ao menos um `Depende de:`, **E**
3. **todos** os `[[...]]` do seu `Depende de:` estão em `concluido/`.

Liste esses itens na seção **🔓 Desbloqueados agora** do hub. Item de backlog **sem** `Depende de:` não é "desbloqueado" (nunca esteve bloqueado) — vive só no Backlog normal. Recalcule sempre que um item entra em `concluido/`.

## Hub `ROADMAP.md` (template)

```markdown
# Roadmap

> Vault Obsidian: cada item é um `.md`, dependência é `[[link]]`, o grafo é nativo.
> Status = pasta (`backlog/` · `em-progresso/` · `concluido/`). Abra o Graph View pra ver a ordem.
> `/roadmap add "<descrição>"` cria item · `/roadmap dep NNN <- MMM` liga dependência · `/roadmap` sincroniza.

## 🔴 Próximos (fila priorizada)

<!-- itens com next: true, curados à mão -->

## 🔓 Desbloqueados agora

<!-- backlog cujas deps estão todas em concluido/ — derivado, não editar à mão -->

## Backlog

- [[NNN-slug]] — <título>

## Em progresso

- [[NNN-slug]] — <título> · #PR

## Concluído

- [[NNN-slug]] — <título> · #PR
```

## Determinismo & idempotência

- Itens e listas **ordenados por NNN crescente**. Mesma entrada de dados → hub idêntico.
- Regenerar o hub a mais nunca prejudica (idempotente).
- Nunca reusa NNN, mesmo após concluir/descartar.

## Migração do formato antigo (arquivo único → vault)

Converte o antigo `thoughts/ROADMAP.md` (arquivo único com seções e bloco mermaid) pro vault `thoughts/roadmap/`:

1. **Parseie** cada entrada `- [ ] NNN — <título> ... · dep: MMM[, PPP]` do arquivo antigo, anotando a **seção** onde estava.
2. **Pasta destino** pela seção: `🔴 Próximos`/`Backlog (resto)` → `backlog/`; `Em progresso` → `em-progresso/`; `Concluído` → `concluido/`.
3. **Crie** `backlog/NNN-slug.md` (etc.) com o frontmatter (id, titulo, pr do `#N` se houver, criado da data `[criado: ...]`, plan do `PLAN: ...` se houver, `next: true` se estava em 🔴 Próximos).
4. **`· dep: MMM`** → linha `**Depende de:** [[MMM-slug]]` no corpo (resolva o slug de MMM pelo título do item MMM).
5. **`PLAN: nome`** → `**Docs:** [[nome-sem-.md]]` (+ pareie a SPEC se o PLAN referenciar uma no topo).
6. **Descarte** o bloco `## 🗺️ Mapa (dependências)` mermaid — não é mais necessário (o grafo é nativo).
7. **Gere** o hub `ROADMAP.md` novo (template acima) linkando todos.
8. **Backup**: mova o antigo pra `thoughts/roadmap/_migrado-de-ROADMAP.md.bak` (não deleta).
9. **Idempotência**: se `thoughts/roadmap/` já existe com itens, **não** re-migre — avise que já está no formato novo.

A migração mostra o **de-para** (quantos itens, por pasta) e pede confirmação antes de escrever.
