---
description: Reorganizar auto-memory do projeto — detectar órfãs/duplicatas/links quebrados, propor sub-sumários quando MEMORY.md cresce, aplicar sob confirmação por bloco.
model: claude-sonnet-4-6
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(ls *), Bash(wc *), Bash(head *), Bash(grep *), Bash(find *), Bash(pwd), Bash(date *), Bash(echo *), Bash(test *)
---

# /memory-organize — Manutenção do auto-memory

Comando de manutenção sob-demanda do auto-memory deste projeto (`~/.claude/projects/<projeto>/memory/`). Funciona **em par com a skill `memory-keeper`** — a skill mantém o índice atualizado a cada escrita, e este comando faz a faxina/reorganização periódica.

**Quando rodar**: quando `MEMORY.md` cresce muito (perto de 150 linhas), quando você suspeita de notas órfãs/duplicadas, ou ao trocar de fase do projeto pra arrumar a casa.

## Princípio

- **Nada é apagado/movido sem confirmação por bloco**. Você aprova cada mudança.
- **Atualizar > criar**. Se duas notas se sobrepõem, propor merge antes de duplicar.
- **Sub-sumários só quando justificado**. Tipo com 3 notas não vira sub-sumário.

## Fluxo

### 1. Resolver path do auto-memory

```bash
PROJ_ENC=$(pwd | sed 's|/|-|g')
MEM_DIR="$HOME/.claude/projects/$PROJ_ENC/memory"
test -d "$MEM_DIR" || { echo "Auto-memory não existe em $MEM_DIR. Saindo."; exit 0; }
```

Se não existir, reportar e sair (não criar).

### 2. Levantamento

Coletar (em paralelo):

- Lista de arquivos `.md` no `$MEM_DIR` (excluindo `MEMORY.md` e `_summary_*.md`).
- Tamanho do `MEMORY.md` em linhas (`wc -l`) e bytes (`wc -c`).
- Lista de sub-sumários existentes (`_summary_*.md`).
- Frontmatter de cada nota (extrair `metadata.type`, `description`, `topic` se houver).
- Linhas do `MEMORY.md` que são entradas de tabela (regex `^| [.*`).

### 3. Análise — gerar relatório

Apresentar pro usuário, em **bloco único de leitura** (não sugerir mudança ainda):

```
=== Estado do auto-memory ===
Path: <MEM_DIR>
Total de notas: N
MEMORY.md: X linhas / Y KB (limite: 200 linhas / 25 KB)
Sub-sumários: <lista ou "nenhum">

Distribuição por tipo:
  user:       N
  feedback:   N
  project:    N
  reference:  N
  decision:   N
  blocker:    N
  lesson:     N
  idea:       N
  preference: N
  (outros):   N
```

### 4. Detectar problemas

Em paralelo, identificar:

**(a) Órfãs** — notas no diretório sem linha correspondente no `MEMORY.md`:
- Pra cada arquivo `<tipo>_<slug>.md`, verificar se aparece em alguma linha do `MEMORY.md`.
- Se não, é órfã. Listar.

**(b) Links quebrados** — linhas do `MEMORY.md` apontando pra arquivo inexistente:
- Pra cada link markdown `[...](arquivo.md)` no `MEMORY.md`, verificar se o arquivo existe.
- Se não, é link quebrado.

**(c) Tipos divergentes** — frontmatter `metadata.type` que não bate com a seção do `MEMORY.md`:
- Nota `feedback_X.md` listada em `## Project`, p.ex.

**(d) Duplicatas potenciais** — slugs/descriptions muito similares:
- Heurística: 2 notas do mesmo tipo com `description` que compartilham ≥3 palavras-chave de >4 letras.
- Marcar pra revisão humana (não auto-merge).

**(e) Frontmatter inválido** — notas sem `metadata.type` ou com type fora dos 9 conhecidos:
- Listar pra correção manual.

**(f) Cresceu demais** — `MEMORY.md` > 150 linhas OU > 20KB:
- Identificar seções maiores (≥ 8 notas) candidatas a sub-sumário.

### 5. Propor mudanças — bloco por bloco

Pra cada categoria com achados, apresentar bloco separado e perguntar:

```
=== Bloco 1: Órfãs (3 notas sem linha no MEMORY.md) ===

1. feedback_old_thing.md
   description: "Padrão de erro X..."
   → Ação proposta: adicionar linha em ## Feedback

2. lesson_e2e_db.md
   description: "Testes E2E precisam de DB real"
   → Ação proposta: adicionar linha em ## Lesson

3. test_spike.md
   (sem metadata.type — frontmatter inválido)
   → Ação proposta: pedir tipo correto ou marcar pra deletar

Aplicar [s/n/parcial]?
```

Se "parcial", perguntar item por item.

### 6. Sub-sumários — caso especial

Se houver candidatos a sub-sumário (seção (f) acima), apresentar:

```
=== Bloco: Sub-sumários ===

MEMORY.md está com 178 linhas (limite: 200). Seções grandes:
- ## Feedback (24 notas, ~28 linhas)
- ## Lesson (12 notas, ~15 linhas)

Proposta: extrair ## Feedback pra _summary_feedback.md.

Antes:
  ## Feedback
  | Slug | Hook |
  |---|---|
  | [bash-perm](feedback_bash_permission_syntax.md) | ... |
  ... 23 linhas ...

Depois:
  ## Feedback
  Ver [_summary_feedback](_summary_feedback.md) — 24 notas.

  ## Sub-sumários
  | Tipo | Arquivo | Notas |
  |---|---|---|
  | Feedback | [_summary_feedback](_summary_feedback.md) | 24 |

Aplicar [s/n]?
```

**Critério pra propor sub-sumário**: seção com ≥ 8 notas E `MEMORY.md` total > 120 linhas. Senão, deixar como está.

### 7. Aplicação

Pra cada bloco aprovado:

- **Órfãs**: adicionar linha no `MEMORY.md` na seção correta (criar seção se não existir, respeitando ordem canônica da skill `memory-keeper`).
- **Links quebrados**: remover linha do `MEMORY.md`. Confirmar item a item se forem ≥ 3.
- **Tipos divergentes**: mover linha pra seção correta (do tipo declarado no frontmatter).
- **Duplicatas**: nunca auto-merge. Listar pro usuário decidir manual.
- **Sub-sumários**: criar arquivo `_summary_<tipo>.md` com a tabela completa daquele tipo, substituir seção no `MEMORY.md` pela linha-resumo, atualizar/criar seção `## Sub-sumários`.

### 8. Validação final

Após aplicar:

- Recontar linhas e bytes do `MEMORY.md` — confirmar redução.
- Re-rodar detecção de órfãs/links quebrados — confirmar que ficaram em zero (ou só as que o usuário decidiu manter).
- Reportar resumo curto:

```
=== Aplicado ===
- Órfãs adicionadas: 3
- Links quebrados removidos: 1
- Tipos corrigidos: 2
- Sub-sumários criados: 1 (_summary_feedback.md, 24 notas)
- MEMORY.md: 178 → 142 linhas

Próximo /memory-organize sugerido quando MEMORY.md voltar a >150 linhas.
```

## Casos especiais

- **MEMORY.md ainda não existe** (projeto novo): criar arquivo vazio com header `# Memory Index\n\n(Vazio — nenhuma memória persistida ainda neste projeto.)\n` e sair. Não há o que organizar.
- **Auto-memory completamente vazio** (sem `.md` além de `MEMORY.md`): reportar e sair sem mexer.
- **Sub-sumário órfão** (`_summary_X.md` existe mas não está listado em `## Sub-sumários` do `MEMORY.md`): adicionar linha.
- **Sub-sumário desatualizado** (tabela do sub-sumário não bate com as notas reais daquele tipo): regenerar conteúdo do sub-sumário sob confirmação.

## O que este comando NÃO faz

- **Não cria notas novas** — só reorganiza as existentes. Pra criar, use a skill `memory-keeper` (escrita sob pedido do usuário).
- **Não deleta notas** sem confirmação explícita por item — só remove linhas órfãs do `MEMORY.md`.
- **Não normaliza convenção de nome** retroativamente — se uma nota antiga tem nome fora do padrão `<tipo>_<slug>.md`, deixar (a menos que o usuário peça).
- **Não migra do vault Obsidian** — esse trabalho é one-shot, não cabe aqui.
