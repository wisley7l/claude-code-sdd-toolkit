# Templates de nota — memory-keeper

Modelos por tipo. Frontmatter mínimo + corpo recomendado. Adapte campos opcionais conforme necessário (`created`, `updated`, `topic`, `pr`, `branch`).

---

## user

```markdown
---
name: user-<slug-kebab>
description: <perfil/preferência do usuário em 1 linha>
metadata:
  type: user
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
---

<descrição da preferência, papel, conhecimento ou contexto pessoal>

**Why:** <razão — geralmente "preferência confirmada após X">
```

Arquivo: `user_<slug>.md` (ex: `user_statusline_layout.md`)

---

## feedback

```markdown
---
name: feedback-<slug-kebab>
description: <regra de colaboração em 1 linha>
metadata:
  type: feedback
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  topic: <agrupamento opcional>
---

<descrição da regra: "Faça X" ou "Nunca Y", com detalhes do gatilho>

**Why:** <razão — incidente passado, constraint técnica, preferência forte>

**How to apply:** <quando/onde a regra dispara — gatilhos concretos>
```

Arquivo: `feedback_<slug>.md`

---

## project

```markdown
---
name: project-<slug-kebab>
description: <decisão/contexto do projeto em 1 linha>
metadata:
  type: project
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
---

<fato, decisão ou contexto não-óbvio sobre o projeto/trabalho>

**Why:** <motivação — constraint, deadline, stakeholder>

**How to apply:** <como essa info deve moldar sugestões/decisões futuras>
```

Arquivo: `project_<slug>.md`

---

## reference

```markdown
---
name: reference-<slug-kebab>
description: <ponteiro pra sistema externo em 1 linha>
metadata:
  type: reference
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
---

<URL ou identificador do sistema (Linear, Grafana, Notion, etc)>

**O que tem lá:** <conteúdo/dado disponível no destino>

**Quando usar:** <gatilho — qual tipo de pergunta/task remete a esse recurso>
```

**Nunca incluir credenciais, tokens ou secrets.**

Arquivo: `reference_<slug>.md`

---

## decision (SDD)

```markdown
---
name: decision-<slug-kebab>
description: <decisão arquitetural/técnica em 1 linha>
metadata:
  type: decision
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  pr: <número-do-pr-se-aplicável>
  branch: <nome-da-branch-se-aplicável>
---

<descrição da decisão tomada: o quê + como>

**Why:** <razão técnica, trade-off considerado, alternativas descartadas>

**How to apply:** <como aplicar/manter essa decisão em decisões futuras relacionadas>
```

Arquivo: `decision_<slug>.md` (ex: `decision_2026_05_21_vault_deprecation.md`)

---

## blocker (SDD)

```markdown
---
name: blocker-<slug-kebab>
description: <bloqueio + workaround em 1 linha>
metadata:
  type: blocker
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  pr: <opcional>
---

<descrição do bloqueio: o que falha, em que condições>

**Why:** <causa raiz — API limit, bug upstream, design constraint>

**How to apply:** <workaround conhecido + quando aplicar; se permanente, marcar como tal>
```

Arquivo: `blocker_<slug>.md`

---

## lesson (SDD)

```markdown
---
name: lesson-<slug-kebab>
description: <aprendizado não-óbvio em 1 linha>
metadata:
  type: lesson
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  pr: <opcional>
---

<descrição do aprendizado extraído de execução/review/incidente>

**Why:** <contexto que tornou esse aprendizado claro>

**How to apply:** <generalização — onde/quando aplicar pra evitar repetir o erro ou repetir o acerto>
```

Arquivo: `lesson_<slug>.md`

---

## idea (SDD)

```markdown
---
name: idea-<slug-kebab>
description: <ideia pra explorar em 1 linha>
metadata:
  type: idea
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
---

<descrição da ideia, contexto que a motivou, impacto estimado>

**Why:** <gatilho — observação durante outra task>

**Próximos passos:** <o que validar/explorar quando voltar pra ela>
```

Arquivo: `idea_<slug>.md`

---

## preference (SDD)

```markdown
---
name: preference-<slug-kebab>
description: <preferência específica do projeto em 1 linha>
metadata:
  type: preference
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
---

<preferência: como o usuário gosta de operar NESTE projeto>

**Why:** <razão — contexto do projeto, estilo do time>

**How to apply:** <quando a preferência se aplica>
```

Arquivo: `preference_<slug>.md`

---

## Notas gerais

- **Slugs** preferencialmente descritivos: `bash_permission_syntax` > `bash_perm`. Underscore ou kebab — mantenha consistência com o que já existe no projeto.
- **`name:`** sempre kebab-case correspondente ao arquivo (sem o tipo prefix duplicado se o slug já começa com ele).
- **`description:`** ≤120 caracteres — vai pro `MEMORY.md` como hook.
- **Datas** absolutas (`2026-05-21`), nunca relativas (`ontem`, `semana passada`).
- **Wikilinks** `[[outra-nota]]` no corpo são opcionais — preferir `[texto](outra_nota.md)` pra ser portável.
