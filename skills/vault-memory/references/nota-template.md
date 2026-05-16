# Template de Nota — Sabor Geral

Para os tipos `user`, `feedback`, `project`, `reference`. **NÃO** use este template para notas do sabor SDD (`decisao`/`blocker`/`licao`/`ideia`/`preferencia` em `state/`) — esse sabor tem template próprio nos commands do toolkit.

## Frontmatter

```yaml
---
name: slug-kebab-case-igual-ao-arquivo
description: Uma linha — usada por agentes pra decidir se vale abrir
type: user | feedback | project | reference
scope: global | <org> | <org>/<projeto>
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [palavra-chave, opcional]
---
```

**Regras**:
- `name` = nome do arquivo sem `.md`.
- `type` bate com a subpasta.
- `scope` bate com o path:
  - `global/feedback/<slug>.md` → `scope: global`
  - `acme/feedback/<slug>.md` → `scope: acme`
  - `acme/web-app/feedback/<slug>.md` → `scope: acme/web-app`
- `created` é fixo. `updated` muda a cada edição.

## Corpo por tipo

### `user` (sempre em `global/user/`)

Captura papel, conhecimento, preferências do usuário.

```markdown
# Título legível

[Fato sobre o usuário em 1-3 parágrafos. Concreto, não genérico.]

## Como aplicar

[Quando essa informação muda como o agente trabalha?]

↑ [[Global]]
```

### `feedback`

Regra de colaboração. **Sempre** inclua Why + How to apply.

```markdown
# Título legível

[A regra em si — 1-3 parágrafos com exemplo do caso fundador.]

## Why

[Qual incident/dor/discussão originou? Sem isso, futuro-você não consegue julgar se a regra ainda é válida.]

## How to apply

[Quando a regra dispara? Que sinal o agente observa pra invocar?]

## Relacionadas

- [[outra-nota]] — hook curto

↑ [[<NomeDoHub>]]
```

### `project`

Decisão/contexto/deadline não-óbvio. Inclua Why + How to apply.

```markdown
# Título

[A decisão/contexto/fato em 1-3 parágrafos.]

## Why

[Motivação: restrição, deadline, stakeholder ask, regulatório, etc.]

## How to apply

[Como isto deve moldar futuras sugestões/escolhas do agente.]

## Relacionadas

- [[outra-nota]] — hook curto

↑ [[<NomeDoHub>]]
```

### `reference`

Ponteiro pra sistema externo.

```markdown
# Título

[URL/path/identificador + o que tem lá.]

## Quando usar

[Em que contexto a referência vira útil — palavras-chave que devem disparar consulta.]

## Acesso

[Método de auth — NUNCA credenciais. Ex: "SSO via Google Workspace".]

↑ [[<NomeDoHub>]]
```

## Convenção de wikilinks

- Rodapé **sempre** aponta pro hub do escopo da nota:
  - `↑ [[Global]]` se `scope: global`
  - `↑ [[<NomeDaOrg>]]` se `scope: <org>`
  - `↑ [[<NomeDoHub>]]` se `scope: <org>/<projeto>` (ex: `↑ [[Web-App]]`)
- **Nunca** aponte direto pra `Comecar-aqui` — só o hub faz isso.
- Em **Relacionadas**, slug sem `.md`: `[[worktree-vs-root-paths]]`.

## Slug do arquivo

- Kebab-case puro: minúsculas, hífens, sem acentos.
- Curto mas descritivo: `worktree-vs-root-paths` ✅, `wt-paths` ❌.
- **Único no vault inteiro** — graph view do Obsidian usa nome como nó.
