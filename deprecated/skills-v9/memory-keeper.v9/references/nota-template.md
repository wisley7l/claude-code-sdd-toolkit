# Templates de nota — memory-keeper

Frontmatter base único + variações por tipo (o que muda: `metadata.type`, campos extras e corpo recomendado).

---

## Frontmatter base (todos os tipos)

```markdown
---
name: <tipo>-<slug-kebab>
description: <1 linha do tipo — vira hook no MEMORY.md>
metadata:
  type: <tipo>
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
---

<corpo recomendado do tipo>
```

- **Arquivo**: sempre `<tipo>_<slug>.md` (ex: `user_statusline_layout.md`, `feedback_bash_permission_syntax.md`).
- **Campos extras opcionais** (só nos tipos indicados abaixo): `topic`, `pr`, `branch`.
- Adapte campos opcionais conforme necessário (`created`, `updated`, `topic`, `pr`, `branch`).

---

## user

- `metadata.type: user` — sem campos extras.
- `description:` <perfil/preferência do usuário em 1 linha>

Corpo:

```markdown
<descrição da preferência, papel, conhecimento ou contexto pessoal>

**Why:** <razão — geralmente "preferência confirmada após X">
```

---

## feedback

- `metadata.type: feedback` + extra opcional `topic: <agrupamento>`.
- `description:` <regra de colaboração em 1 linha>

Corpo:

```markdown
<descrição da regra: "Faça X" ou "Nunca Y", com detalhes do gatilho>

**Why:** <razão — incidente passado, constraint técnica, preferência forte>

**How to apply:** <quando/onde a regra dispara — gatilhos concretos>
```

---

## project

- `metadata.type: project` — sem campos extras.
- `description:` <decisão/contexto do projeto em 1 linha>

Corpo:

```markdown
<fato, decisão ou contexto não-óbvio sobre o projeto/trabalho>

**Why:** <motivação — constraint, deadline, stakeholder>

**How to apply:** <como essa info deve moldar sugestões/decisões futuras>
```

---

## reference

- `metadata.type: reference` — sem campos extras.
- `description:` <ponteiro pra sistema externo em 1 linha>

Corpo:

```markdown
<URL ou identificador do sistema (Linear, Grafana, Notion, etc)>

**O que tem lá:** <conteúdo/dado disponível no destino>

**Quando usar:** <gatilho — qual tipo de pergunta/task remete a esse recurso>
```

**Nunca incluir credenciais, tokens ou secrets.**

---

## decision (SDD)

- `metadata.type: decision` + extras opcionais `pr: <número-do-pr-se-aplicável>` e `branch: <nome-da-branch-se-aplicável>`.
- `description:` <decisão arquitetural/técnica em 1 linha>

Corpo:

```markdown
<descrição da decisão tomada: o quê + como>

**Why:** <razão técnica, trade-off considerado, alternativas descartadas>

**How to apply:** <como aplicar/manter essa decisão em decisões futuras relacionadas>
```

Exemplo de arquivo: `decision_2026_05_21_vault_deprecation.md`

---

## blocker (SDD)

- `metadata.type: blocker` + extra opcional `pr:`.
- `description:` <bloqueio + workaround em 1 linha>

Corpo:

```markdown
<descrição do bloqueio: o que falha, em que condições>

**Why:** <causa raiz — API limit, bug upstream, design constraint>

**How to apply:** <workaround conhecido + quando aplicar; se permanente, marcar como tal>
```

---

## lesson (SDD)

- `metadata.type: lesson` + extra opcional `pr:`.
- `description:` <aprendizado não-óbvio em 1 linha>

Corpo:

```markdown
<descrição do aprendizado extraído de execução/review/incidente>

**Why:** <contexto que tornou esse aprendizado claro>

**How to apply:** <generalização — onde/quando aplicar pra evitar repetir o erro ou repetir o acerto>
```

---

## idea (SDD)

- `metadata.type: idea` — sem campos extras.
- `description:` <ideia pra explorar em 1 linha>

Corpo:

```markdown
<descrição da ideia, contexto que a motivou, impacto estimado>

**Why:** <gatilho — observação durante outra task>

**Próximos passos:** <o que validar/explorar quando voltar pra ela>
```

---

## preference (SDD)

- `metadata.type: preference` — sem campos extras.
- `description:` <preferência específica do projeto em 1 linha>

Corpo:

```markdown
<preferência: como o usuário gosta de operar NESTE projeto>

**Why:** <razão — contexto do projeto, estilo do time>

**How to apply:** <quando a preferência se aplica>
```

---

## Notas gerais

- **Slugs** preferencialmente descritivos: `bash_permission_syntax` > `bash_perm`. Underscore ou kebab — mantenha consistência com o que já existe no projeto.
- **`name:`** sempre kebab-case correspondente ao arquivo (sem o tipo prefix duplicado se o slug já começa com ele).
- **`description:`** ≤120 caracteres — vai pro `MEMORY.md` como hook.
- **Datas** absolutas (`2026-05-21`), nunca relativas (`ontem`, `semana passada`).
- **Wikilinks** `[[outra-nota]]` no corpo são opcionais — preferir `[texto](outra_nota.md)` pra ser portável.
