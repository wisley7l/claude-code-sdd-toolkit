# Template do MEMORY.md — memory-keeper

Formato canônico do índice `MEMORY.md`. Tabela agrupada por tipo, ordem fixa.

## Estrutura

```markdown
# Memory Index

## User
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Feedback
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Project
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Reference
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Decision
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Blocker
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Lesson
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Idea
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Preference
| Slug | Hook |
|---|---|
| [<slug>](<arquivo>) | <hook ≤90 chars> |

## Sub-sumários
| Tipo | Arquivo | Notas |
|---|---|---|
| <Tipo> | [_summary_<tipo>](_summary_<tipo>.md) | <N> |
```

## Regras

1. **Ordem das seções é fixa** (user → feedback → project → reference → decision → blocker → lesson → idea → preference → sub-sumários).
2. **Seções vazias são omitidas** — não deixar `## Decision` com tabela vazia.
3. **Cabeçalho da tabela** é sempre `| Slug | Hook |` (exceto sub-sumários — `| Tipo | Arquivo | Notas |`).
4. **Slug** é link markdown `[<nome-curto>](<arquivo>.md)`. Use `<nome-curto>` sem o prefixo do tipo (já implícito na seção).
   - ✅ `[bash-permission-syntax](feedback_bash_permission_syntax.md)`
   - ❌ `[feedback-bash-permission-syntax](feedback_bash_permission_syntax.md)` (redundante)
5. **Hook** ≤90 caracteres, copia da `description:` do frontmatter (ou versão mais curta se passar).
6. **Sem frontmatter** no `MEMORY.md` — só `# Memory Index` no topo.
7. **Limite**: 200 linhas ou 25KB (o que vier primeiro). O harness trunca depois disso.
8. **Quando passar de ~150 linhas** (margem segura), `/memory-organize` propõe converter seções grandes em sub-sumários.

## Exemplo de seção convertida em sub-sumário

Antes (24 notas de feedback inline, ocupa ~28 linhas):

```markdown
## Feedback
| Slug | Hook |
|---|---|
| [bash-permission-syntax](feedback_bash_permission_syntax.md) | patterns precisam de espaço antes do `*` |
| [bash-compound-pitfalls](feedback_bash_compound_pitfalls.md) | newlines/subshells quebram pattern matching |
| ... mais 22 linhas ... |
```

Depois (1 linha + entrada em sub-sumários):

```markdown
## Feedback
Ver [_summary_feedback](_summary_feedback.md) — 24 notas.

...

## Sub-sumários
| Tipo | Arquivo | Notas |
|---|---|---|
| Feedback | [_summary_feedback](_summary_feedback.md) | 24 |
```

E o `_summary_feedback.md` contém a tabela completa das 24 notas, carregada sob demanda quando necessário.

## Quando o MEMORY.md está vazio

Primeira vez no projeto, sem nenhuma nota:

```markdown
# Memory Index

(Vazio — nenhuma memória persistida ainda neste projeto.)
```

Conforme notas vão sendo adicionadas, as seções aparecem na ordem canônica.
