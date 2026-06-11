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

Use o **root do worktree** pra centralizar memorias (mesmo path quando rodado da raiz ou de uma worktree):

```bash
ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
PROJ_ENC=$(echo "${ROOT:-$(pwd)}" | sed 's|/|-|g')
PROJ_DIR="$HOME/.claude/projects/$PROJ_ENC"
MEM_DIR="$PROJ_DIR/memory"
```

**Antes de prosseguir**, validar nessa ordem:

1. **Se `$MEM_DIR` não existe**: procurar siblings com nome `*-memory/` em `$PROJ_DIR/` (ex: `meuprojeto-memory/`, `backup-memory/`). Esses dirs podem ser renames antigos ou backups esquecidos.
   - **Encontrou sibling com conteúdo** (>1 arquivo `.md` além de `MEMORY.md`): **NÃO criar stub vazio**. Reportar pro usuário e perguntar:
     ```
     ⚠️ memory/ não existe, mas achei sibling com dados:
       /home/.../projects/<proj>/<sibling>/  (N notas, MEMORY.md X linhas)

     O que fazer?
       (r) renomear sibling → memory/ (convenção padrão)
       (s) sair sem mexer (você organiza manual)
       (c) continuar criando memory/ vazio (sibling fica intacto)
     ```
   - **Não encontrou sibling** (projeto realmente novo): seguir o caso "MEMORY.md ainda não existe" (criar stub vazio).

2. **Se `$MEM_DIR` existe**: seguir normal pra próxima etapa.

```bash
# Pseudocódigo da detecção:
test -d "$MEM_DIR" || {
  siblings=$(find "$PROJ_DIR" -maxdepth 1 -type d -name '*-memory' 2>/dev/null)
  for s in $siblings; do
    count=$(ls "$s"/*.md 2>/dev/null | wc -l)
    [ "$count" -gt 1 ] && echo "Candidate: $s ($count .md files)"
  done
}
```

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

**(g) Conteúdo inline no MEMORY.md** — anti-padrão: o índice deve ter apenas tabelas e headers.
- Detectar blocos de bullets expandidos (≥ 3 bullets seguidos fora de tabela), código inline, ou parágrafos descritivos no `MEMORY.md`.
- Propor extrair pra arquivo individual `<tipo>_<slug>.md` (perguntando tipo se ambíguo) e deixar só linha-resumo no índice.

**(h) GUARDRAIL diluído** — regra inviolável que está em `## Feedback` ou `## Preference` em vez de `## GUARDRAILs`:
- Critério: a regra está formulada como "NUNCA X" / "JAMAIS Y" / "obrigatório Z" E romper a regra causa dano irreversível (commit indevido, push, deleção de dados, vazamento) — não é só preferência ergonômica.
- Propor: promover via `/memory-organize rename <slug> --guardrail` (ou aplicar manual sob confirmação).

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

**Critério pra propor sub-sumário** (qualquer um dispara):
- Seção com **≥ 10 notas** (independente do tamanho do MEMORY.md — antecipa crescimento), OU
- Seção com ≥ 8 notas E `MEMORY.md` total > 120 linhas (corte de pressão atual).

Abaixo desses thresholds, deixar como está. O `## GUARDRAILs` **nunca** vira sub-sumário — fica sempre inline no topo do MEMORY.md, é a parte mais saliente do índice.

### 7. Aplicação

Pra cada bloco aprovado:

- **Órfãs**: adicionar linha no `MEMORY.md` na seção correta (criar seção se não existir, respeitando ordem canônica da skill `memory-keeper`).
- **Links quebrados**: remover linha do `MEMORY.md`. Confirmar item a item se forem ≥ 3.
- **Tipos divergentes**: mover linha pra seção correta (do tipo declarado no frontmatter).
- **Duplicatas**: nunca auto-merge. Listar pro usuário decidir manual.
- **Sub-sumários**: criar arquivo `_summary_<tipo>.md` com a tabela completa daquele tipo, substituir seção no `MEMORY.md` pela linha-resumo, atualizar/criar seção `## Sub-sumários`.

### 8. Validação final (checklist obrigatório)

Após aplicar, rode o checklist abaixo. **Cada item gera saída verificável**:

1. **Tamanho do MEMORY.md**:
   ```bash
   wc -l "$MEM_DIR/MEMORY.md"
   ```
   Esperado: **< 150 linhas** (limite operacional; o harness trunca após 200).

2. **MEMORY.md é só índice** (sem conteúdo inline):
   - Conferir que não há blocos de bullets expandidos (≥3 bullets seguidos fora de tabela), nem código inline, nem parágrafos de descrição.
   - Linha que não seja header, tabela ou linha-resumo de sub-sumário = candidato a violação.

3. **Frontmatter válido em cada arquivo**:
   ```bash
   for f in "$MEM_DIR"/*.md; do
     [[ "$(basename "$f")" == "MEMORY.md" || "$(basename "$f")" =~ ^_summary_ ]] && continue
     head -7 "$f" | grep -q "metadata:" || echo "MISSING frontmatter: $f"
   done
   ```
   Esperado: zero output (todos com frontmatter).

4. **Contadores em sub-sumários batem**:
   - Pra cada `_summary_<tipo>.md` na seção `## Sub-sumários`, conferir que o número declarado bate com `ls "$MEM_DIR" | grep -c "^<tipo>_"`.

5. **Sem órfãs e sem links quebrados**:
   - Re-rodar detecção da etapa 4 (a) e (b) — esperado zero (ou só itens que o usuário decidiu manter).

Reportar resumo curto:

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

---

## Modo relink — centralizar memorias de worktrees

`/memory-organize relink` é um sub-modo focado em **centralizar** o auto-memory de worktrees: garante que cada worktree do projeto atual tem `memory/` como symlink pro `memory/` do root.

**Quando usar**:
- **Retroativo** — depois de adotar a centralizacao, worktrees criados antes (ou que tiveram sessao Claude antes do `/git-worktree` ser atualizado) ainda tem `memory/` separado.
- **Auditoria** — checar inconsistencias: symlink quebrado, worktree apontando pra root errado, etc.

### Fluxo

1. **Identificar root** + listar worktrees:
   ```bash
   ROOT=$(git worktree list | head -1 | awk '{print $1}')
   ROOT_ENC=$(echo "$ROOT" | sed 's|/|-|g')
   ROOT_MEM="$HOME/.claude/projects/$ROOT_ENC/memory"
   mkdir -p "$ROOT_MEM"

   # Lista paths dos worktrees (sem o root)
   git worktree list | tail -n +2 | awk '{print $1}'
   ```

2. **Pra cada worktree** `WT`:
   ```bash
   WT_ENC=$(echo "$WT" | sed 's|/|-|g')
   WT_MEM="$HOME/.claude/projects/$WT_ENC/memory"
   ```
   Casos:
   - **Nao existe**: cria diretorio pai + symlink. Reporta *"Linked $WT → root"*.
   - **E symlink pro root certo** (`readlink "$WT_MEM"` = `$ROOT_MEM`): skip (idempotente). Reporta *"OK (ja linkado)"*.
   - **E symlink pra outro destino**: mostra destino atual, pergunta — substituir, cancelar ou skip esse worktree.
   - **E diretorio real** (caso conservador — **NUNCA descartar sozinho**): faca diff de notas:
     ```bash
     # Listar nomes de notas do worktree e do root
     diff <(ls "$WT_MEM"/*.md 2>/dev/null | xargs -n1 basename | sort) \
          <(ls "$ROOT_MEM"/*.md 2>/dev/null | xargs -n1 basename | sort)
     ```
     - **Sem notas unicas no worktree** (tudo ja existe no root): pergunta *"Posso descartar $WT_MEM e criar symlink?"* (s/n).
     - **Com notas unicas no worktree**: lista os arquivos unicos, oferece:
       - `(m)` Mover unicos pro root (`mv`) e entao criar symlink
       - `(k)` Manter ambos — skip symlink (usuario resolve depois)
       - `(c)` Cancelar relink desse worktree
     - **MEMORY.md ou `_summary_*.md` divergentes**: caso especial — pergunta caso a caso. Geralmente o MEMORY.md do root deve prevalecer (ele e a fonte canonica), mas pode haver entradas locais que faltam la.
   - **E dir vazio**: `rmdir` + cria symlink. Reporta.

3. **Sumario final**:
   ```
   /memory-organize relink concluido:
     Worktrees verificados:        N
     ✅ Ja linkados (skip):         K
     🔗 Novos symlinks criados:     M
     📦 Notas movidas pro root:     J
     ⏸️ Pulados (manual):           P
     ❌ Cancelados:                 C
   ```

### Importante (seguranca)

- **Nunca `rm -rf` em `$WT_MEM`** — se for symlink (mesmo quebrado), `rm -rf` pode seguir e apagar `memory/` do root. Use:
  - `unlink "$WT_MEM"` pra symlinks
  - `rmdir "$WT_MEM"` pra dirs vazios
  - `mv "$WT_MEM"/<arquivo>.md "$ROOT_MEM"/` pra mover conteudo
  - **Perguntas explicitas** antes de qualquer destruicao.
- **Diretorio pai do worktree** (`~/.claude/projects/<worktree-encoded>/`) nao e tocado — fica intacto (pode ter historico de sessoes). So o `memory/` dentro dele e gerenciado.

---

## Modo rename — renomear ou migrar tipo de uma memória

`/memory-organize rename <slug-antigo> [novo-slug-ou-tipo]` é um sub-modo pra mudar o **tipo** ou o **nome** de uma nota existente. Requer confirmação por passo — nunca aplica sem visualizar o efeito.

**Quando usar**:
- Mudar tipo: ex. `feedback` → `project` (a regra na verdade descrevia decisão do projeto, não preferência do user).
- Renomear slug: ex. `bash_perm` → `bash_permission_syntax` (slug pouco descritivo).
- Promover a GUARDRAIL: regra inviolável que estava em `## Feedback` deve subir pra `## GUARDRAILs`.

### Fluxo

1. **Localizar a nota**:
   ```bash
   ls "$MEM_DIR" | grep -i "<slug-antigo>"
   ```
   Se acharmais de um match, pedir desambiguação.

2. **Mostrar estado atual** ao usuário (frontmatter + primeiras 5 linhas do corpo):
   ```
   Arquivo: feedback_bash_perm.md
   Frontmatter: name=feedback-bash-perm, type=feedback
   Linha em MEMORY.md: ## Feedback → [bash-perm](feedback_bash_perm.md)
   ```

3. **Propor a mudança** baseado nos args:
   - **Renomear slug**: `mv <antigo>.md <novo>.md` + atualizar `name:` no frontmatter + atualizar link no MEMORY.md / sub-sumário.
   - **Mudar tipo**: `mv <tipo-antigo>_<slug>.md <tipo-novo>_<slug>.md` + atualizar `metadata.type:` + mover linha pra seção correta no MEMORY.md.
   - **Promover a GUARDRAIL**: renomear pra `guardrail_<slug>.md` + manter `metadata.type` original (`feedback` ou `preference` conforme natureza) + mover linha pra seção `## GUARDRAILs` (formato `| Regra | Detalhe (link) |`).

4. **Apresentar o plano completo** antes de aplicar:
   ```
   Plano:
   - mv feedback_bash_perm.md → feedback_bash_permission_syntax.md
   - Atualizar frontmatter: name=feedback-bash-permission-syntax
   - Atualizar MEMORY.md: linha de [bash-perm] → [bash-permission-syntax]
   - Atualizar _summary_feedback.md (se existir): mesma linha
   - Atualizar contador no sub-sumário (se houver)

   Aplicar [s/n]?
   ```

5. **Aplicar sob confirmação**. Não faz `git add` automaticamente — auto-memory não é versionado por git de qualquer forma.

6. **Rodar a etapa 8 (checklist de validação)** ao final pra garantir consistência.

### Casos especiais

- **Slug aponta pra arquivo que não existe**: reportar e sair. Não criar nota nova nesse modo.
- **Tipo destino não é válido** (fora dos 9 tipos): rejeitar com lista dos tipos válidos.
- **Promovendo a GUARDRAIL nota que não cabe**: se a nota é só uma preferência ergonômica (não causa dano irreversível se romper), avisar e pedir confirmação extra. Ver critério em `memory-keeper` seção 8.

---

## O que este comando NÃO faz

- **Não cria notas novas** — só reorganiza as existentes. Pra criar, use a skill `memory-keeper` (escrita sob pedido do usuário).
- **Não deleta notas** sem confirmação explícita por item — só remove linhas órfãs do `MEMORY.md`.
- **Não normaliza convenção de nome** retroativamente — se uma nota antiga tem nome fora do padrão `<tipo>_<slug>.md`, deixar (a menos que o usuário peça).
- **Não migra do vault Obsidian** — esse trabalho é one-shot, não cabe aqui.
- **Modo relink nao apaga `<worktree-encoded>/`** — so gerencia o `memory/` dentro. Outros artefatos do harness ficam intactos.
