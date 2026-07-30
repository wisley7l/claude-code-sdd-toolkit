---
description: Arquiva SPEC+PLAN concluídos (PR mergeado) — move o par pra closed/, mescla o comportamento na capability viva, colhe follow-ups do review e dívida de teste pro backlog, e move o item do roadmap pra concluido/. Só age sob PR MERGED; confirmação individual; nunca commita.
model: claude-sonnet-5
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls *), Bash(mkdir *), Bash(mv *), Bash(git worktree list*), Bash(git status*), Bash(gh *), Bash(realpath *), Bash(pwd), Bash(find *), Bash(basename *), Bash(dirname *), Bash(grep *), Bash(head *), Bash(cat *)
---

# SDD Close — Arquivar SPEC+PLAN concluídos após merge

Você fecha o ciclo de um **trabalho concluído** (PR mergeado). São quatro coisas, na ordem:

1. **Arquiva** o par SPEC+PLAN: `thoughts/{specs,plans}/` → `closed/` em cada pasta
2. **Mescla** o comportamento entregue na **capability viva** (`thoughts/capabilities/<dominio>.md`)
3. **Colhe** o que sobreviveria perdido: follow-ups do review + dívida de teste do PLAN → `backlog/`
4. **Conclui** o item do roadmap → `concluido/` (+ mostra o que isso desbloqueou)

**Filosofia**: `thoughts/specs/` e `thoughts/plans/` guardam os docs **vivos** (em fila,
em progresso). Quando o PR entra na main, o par vira histórico — sai da raiz pra `closed/`,
mantendo a raiz enxuta sem perder o rastro.

Mas **arquivar não pode significar esquecer**. O merge é o único momento em que sabemos que o
comportamento passou a ser verdade — é por isso que a promoção pra capability e a colheita de
pendências acontecem aqui, e não antes. Sem isso, o comportamento especificado morre em `closed/`
e a dívida registrada no PLAN é registrada *e esquecida do mesmo jeito*.

**`closed/` ≠ `old/`**:
- `closed/` = trabalho **usado e concluído** (PR MERGED). É o que este command gerencia.
- `old/` = spec/plano **descartado** (abandonado, superado sem entrega). NÃO é escopo daqui.

Se um par não foi mergeado (PR fechado sem merge ou nunca existiu), este command **não** o
arquiva em `closed/` — ele sinaliza e sugere `old/`, mas deixa a mudança pro usuário.

## Guardrails (não-negociáveis)

- **Só MERGED vai pra `closed/`.** PR aberto → skip. PR fechado sem merge / sem PR → não move; sinaliza.
- **Confirmação individual, nunca batch.** Um par por vez, mostrando SPEC + PLAN + PR antes.
- **Par junto.** Não arquive a SPEC sem o(s) PLAN(s) dela nem vice-versa (salvo caso de borda explícito).
- **Nunca commita nem pusha.** `thoughts/` é gitignored por convenção — `mv` simples basta.
- **ROADMAP: migração sem perda.** Ao concluir, `mv` o item pra `concluido/` preservando o arquivo inteiro (NNN, título, `Depende de:`, `Docs:`); o wikilink não quebra. Depois regenere o hub e recalcule os 🔓 Desbloqueados.
- **Capability: edição cirúrgica, nunca reescrita.** Mescle o `C<N>` alvo com `Edit`. Reescrever o arquivo inteiro perde o histórico dos outros requisitos. `C<N>` inexistente → PARE nesse delta e avise; nunca invente requisito.
- **Capability nova só sob confirmação.** Domínio novo cria arquivo novo — pergunte antes. Proliferação de capability de 1 requisito destrói o valor do documento.
- **Colheita propõe, nunca cria sozinha.** Follow-up e dívida vão pra tela e viram item só com OK individual. Risco aceito como permanente não é trabalho pendente.
- **Nunca poste no PR.** A colheita lê comentários; não responde, não resolve thread, não comenta.
- **Em dúvida, preserve.** Não mover é reversível; mover errado gera confusão. Rode de novo depois.

## Pré-cheques

1. **Root do projeto** (centraliza mesmo rodando em worktree):
   ```bash
   ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
   ROOT=${ROOT:-$(pwd)}
   ```
   Use `$ROOT/thoughts/` como base.

2. **Pastas vivas existem**: `thoughts/specs/` e `thoughts/plans/`. Se nenhuma existir, diga
   "Sem `thoughts/specs/` ou `thoughts/plans/` neste projeto — nada a arquivar." e saia.

3. **`gh`**: `gh auth status`. Se falhar, peça `gh auth login` e saia (o gatilho depende do status do PR).

## Argumentos

| Invocação | O que faz |
|---|---|
| `/sdd-close` (sem args) | Varre todos os pares vivos, filtra os com PR MERGED, propõe arquivar um a um |
| `/sdd-close <slug \| path-do-PLAN \| path-da-SPEC>` | Foca num par só (resolve o par a partir do que você passou) |
| `/sdd-close --pr <N>` | Foca no par cujo PR é `#N` |

## Workflow

### Passo 1 — Coletar pares vivos

Liste os PLANs na **raiz** de `thoughts/plans/` (ignore `closed/` e `old/`):
```bash
find "$ROOT/thoughts/plans" -maxdepth 1 -name 'PLAN-*.md' -type f
```

O **PLAN é a unidade** — ele referencia a SPEC no topo (linha `SPEC: \`thoughts/specs/spec-...\``).
Para cada PLAN:
- Extraia o path da SPEC dessa linha (`grep -i 'SPEC:' <plan> | head -1`). Resolva pra path absoluto sob `$ROOT`.
- Extraia o **NNN** e o **slug** do nome do PLAN (`PLAN-<DD-MM-YYYY>-<NNN>-<slug>.md`).

Trate os casos:
- **PLANs com mesma SPEC** (multi-PR): agrupe — a SPEC só vai pra `closed/` quando **todos** os PLANs dela estiverem mergeados.
- **SPEC viva sem PLAN** (`spec-*.md` na raiz sem PLAN apontando): liste como candidata órfã → caso de borda (Passo 5).

Se argumento foi passado, restrinja a coleta ao par correspondente antes de seguir.

### Passo 2 — Descobrir o PR de cada par

Ordem de resolução (pare no primeiro que resolver):

1. **ROADMAP** (vault `thoughts/roadmap/`, se existir): ache o item com o mesmo **NNN** (ou slug/`plan:`) e leia o `pr:` dele. Se só existir o `thoughts/ROADMAP.md` antigo, avise que precisa migrar (`/roadmap migrar`) e siga pela busca no GitHub.
2. **Busca no GitHub** pelo slug:
   ```bash
   gh pr list --search "<slug em palavras>" --state all --json number,title,state,mergedAt,headRefName --limit 5
   ```
3. **Pergunte** ao usuário o número do PR (opção `(n)`), ou `(k)` skip.

### Passo 3 — Filtrar por status do PR

```bash
gh pr view <N> --json state,mergedAt,title,url
```
- `state: "MERGED"` → **candidato a arquivar** (Passo 4).
- `state: "OPEN"` → skip: "PR #N ainda aberto — par preservado em specs/plans/".
- `state: "CLOSED"` (sem `mergedAt`) → **não arquiva em `closed/`**. Sinalize: "PR #N fechado sem merge — isto é descarte, não conclusão. Considere mover pra `old/` (fora do escopo do /sdd-close)." Não mova.

### Passo 4 — Propor e arquivar (só MERGED)

Para cada par MERGED, mostre e confirme individualmente:
Antes de mostrar, leia o **delta** da SPEC: os RFs marcados com `[MODIFIED → <dominio> C<N>]` /
`[REMOVED → <dominio> C<N>]`; RF sem marcação é `ADDED`. É isso que define a mesclagem.

```
Par concluído:
  SPEC:  thoughts/specs/spec-<TS>-<slug>.md
  PLAN:  thoughts/plans/PLAN-<...>-<slug>.md   (+ outros PLANs do mesmo grupo, se houver)
  PR:    #N "<título>" — MERGED em <data>
  ROADMAP: item NNN <"encontrado em <pasta>" | "não encontrado">
  CAPABILITY: checkout — +2 novos (ADDED), modifica C1, remove C3
              <ou: "dominio novo 'checkout' — criar arquivo?" | "sem delta na SPEC">

Ao confirmar:
  1. move SPEC → thoughts/specs/closed/
  2. move PLAN(s) → thoughts/plans/closed/
  3. mescla o delta → thoughts/capabilities/checkout.md
  4. move o item NNN → thoughts/roadmap/concluido/  [se existir]
  (depois: colheita de follow-ups e dívida — Passo 5)

  (s) Arquivar    (k) Skip    (a) Abortar tudo
```

Se `(s)`:
1. Crie as pastas destino se faltarem:
   ```bash
   mkdir -p "$ROOT/thoughts/specs/closed" "$ROOT/thoughts/plans/closed"
   ```
2. Mova (não é `git mv` — `thoughts/` é gitignored):
   ```bash
   mv "$ROOT/thoughts/specs/spec-<...>.md"  "$ROOT/thoughts/specs/closed/"
   mv "$ROOT/thoughts/plans/PLAN-<...>.md"  "$ROOT/thoughts/plans/closed/"   # cada PLAN do grupo
   ```
   Se um destino já tiver arquivo de mesmo nome, PARE nesse par e avise (não sobrescreva).
3. **CAPABILITY** — mescle o delta em `thoughts/capabilities/<dominio>.md`. Protocolo completo (formato do
   arquivo, numeração `C<N>`, regras de merge por tipo de delta, idempotência) no reference
   `capability-template.md` — procure em `.claude/sdd-references/` do projeto, senão em
   `~/.claude/sdd-references/`. **Fallback** (reference ausente): `ADDED` → novo `C<N>` = `max(N)+1`;
   `MODIFIED` → edite o `C<N>` e **acrescente** a SPEC+PR ao `[Origem: …]` sem apagar o rastro antigo;
   `REMOVED` → tire de `## Comportamento atual` e registre em `## Removido` com PR e data. Atualize
   `atualizado:` e acrescente a SPEC em `specs:`. Use `Edit` no requisito alvo — **nunca reescreva o arquivo**.

   Casos que **param nesse delta** (não no par inteiro): `C<N>` alvo inexistente, ou SPEC sem marcação
   em domínio que já existe (mostre os `C<N>` e pergunte se é novo ou modificação). Delta cujo `[Origem]`
   já cita esta SPEC+PR → **pule, é idempotente** (rodar duas vezes não duplica requisito).

   Sem `thoughts/capabilities/` e sem delta na SPEC → pule esta etapa em silêncio (projeto ainda não
   adotou capabilities). Domínio novo → **confirme antes de criar** o arquivo.

4. **ROADMAP** (se o item existe): `mv` o arquivo do item pra `thoughts/roadmap/concluido/`, **preservando
   o arquivo inteiro** (NNN, título, `Depende de:`, `Docs:`) — o wikilink não quebra. Se o item já estava
   em `concluido/`, apenas confirme. Se **não há** item no roadmap, não invente um — apenas registre no sumário.
   Depois **regenere o hub** `thoughts/roadmap/ROADMAP.md` e **recalcule os 🔓 Desbloqueados agora** — itens de
   `backlog/` cujas dependências ficaram todas em `concluido/` com este merge (reference `roadmap-item.md`, algoritmo).
   O grafo do Obsidian se atualiza sozinho a partir dos links — não há mermaid a regenerar.
5. Sumarize: "✅ Arquivado: `<slug>` (SPEC + N PLAN(s)) → closed/ · CAPABILITY: `<dominio: +A ~M -R | sem delta>` · ROADMAP: `<item → concluido/ | sem item>` · 🔓 Desbloqueou: `<NNN[, MMM] | nada>`".

Se `(k)`: preserve, siga pro próximo. Se `(a)`: pare a varredura, vá pro sumário.

### Passo 5 — Colheita (follow-ups + dívida de teste)

Para **cada par arquivado** no Passo 4, colha o que sobreviveria perdido:

- **Follow-ups do review** — o padrão mais comum é o **body do review de aprovação**: o revisor aprova o PR *e* deixa o follow-up no comentário final, às vezes marcado como opcional ("se quiser já corrige nesse PR"). A assinatura é **`state: APPROVED` com `body` não-vazio** — sinal mais confiável que caçar frases de adiamento. Comece por `gh pr view <N> --json reviews --jq '.reviews[] | select(.body != "")'`; depois os **inline** (`gh api repos/{owner}/{repo}/pulls/<N>/comments`, que o `gh pr view` não traz) e por fim a conversa geral. **Opcional-neste-PR que mergeou sem a correção é dívida** — com severidade menor e a marca de que o revisor não bloqueava; se mergeou *com* a correção, não é dívida (confirme no diff).
- **Dívida de teste** — seção `6.6 Divida e risco aceito` do PLAN (e `6.4 Gaps`). O próprio template do PLAN já sugere "item separado no roadmap" pras lacunas pré-existentes; este é o passo que executa.

Cada candidato vira item em `thoughts/roadmap/backlog/` — **sob confirmação individual**, com dedup contra o backlog existente.

Protocolo completo (queries `gh`, sinais de triagem, o que **não** vira item, formato do item e procedência) no reference `sdd-close-colheita.md` — procure em `.claude/sdd-references/` do projeto, senão em `~/.claude/sdd-references/`. **Fallback** (reference ausente): colete comentários gerais + inline via `gh`, separe bots dos humanos, triagem por sinal de adiamento explícito, dedup contra `thoughts/roadmap/*/`, e crie item por `roadmap-item.md` com `Depende de: [[<item concluído>]]` (a dependência já satisfeita faz o follow-up nascer em 🔓 Desbloqueados) + 1 linha de procedência (PR #N, autor, path:line).

**Risco aceito como permanente não vira item** — a 6.5/6.6 do PLAN registra o motivo dado pelo usuário; respeite-o. Colheita vazia é resultado normal; não force item de comentário ambíguo.

Se `gh` falhar aqui, **pule a colheita e siga** — o arquivamento do Passo 4 não depende dela.

### Passo 6 — Sumário

```
/sdd-close concluído:
  ✅ Arquivados (SPEC+PLAN → closed/):   N
  🧬 Capabilities mescladas:             C  (+A novos · ~M modificados · -R removidos)
  🌾 Colhidos pro backlog:               F  (follow-up: X · dívida de teste: Y)
  📋 ROADMAP (itens → concluido/):       M
  🔓 Desbloqueados agora:                D
  ⏸️ Skip (PR aberto):                   K
  ⚠️ PR fechado sem merge (sugerir old/): J
  ❓ Sem PR resolvido:                    P

Pares vivos remanescentes em thoughts/{specs,plans}/: <count>
```

Se algum delta parou (C<N> inexistente, domínio ambíguo) ou a colheita foi pulada por falha do `gh`,
liste explicitamente — o par foi arquivado, mas a capability ficou incompleta e precisa de nova rodada.

## Casos de borda

- **SPEC órfã (sem PLAN)**: pergunte se deve arquivar sozinha (às vezes a spec virou quick-task sem PLAN). Só mova sob confirmação; use `--pr` ou peça o PR pra validar o merge.
- **Multi-PR na mesma SPEC**: a SPEC só vai pra `closed/` quando **todos** os PLANs dela estiverem mergeados. Se um ainda está aberto, arquive só os PLANs já mergeados e deixe a SPEC na raiz; avise no sumário.
- **Multi-PR e a capability**: o delta vive na **SPEC**, então **o sync acompanha o arquivamento da SPEC, não do PLAN** — só mescle quando *todos* os PLANs dela tiverem mergeado. Mesclar no primeiro slice afirmaria na capability um comportamento que só existe pela metade. A **colheita**, ao contrário, roda por PLAN/PR mergeado (o review e a dívida de teste são daquele PR).
- **SPEC órfã (sem PLAN) com delta**: mescle a capability normalmente; só não há dívida de teste a colher (não existe seção 6.6).
- **Capability editada à mão** entre ciclos: o merge é cirúrgico por `C<N>`, então edição manual em *outro* requisito não conflita. Mas se o `C<N>` alvo foi renumerado à mão, o sync para — corrija a marcação na SPEC (ou o número na capability) e rode de novo.
- **Colisão de nome em `closed/`**: não sobrescreva. Pare nesse par e avise (provavelmente já foi arquivado).
- **PR `reopened` após `merged`**: trate como MERGED (o código entrou na main).
- **Múltiplos PRs MERGED pro mesmo slug**: liste e peça pro usuário escolher qual item do roadmap referenciar.
- **`gh` falha (rede/rate limit)**: não mova nada. Peça pra rodar de novo mais tarde.
- **Sem vault `thoughts/roadmap/`**: arquive os arquivos normalmente; só pule a etapa de ROADMAP e diga isso no sumário. Se houver o `thoughts/ROADMAP.md` antigo, sugira `/roadmap migrar`.

## Relação com outros commands

- `/sdd-spec` / `/sdd-plan` **criam** os docs vivos em `thoughts/specs/` e `thoughts/plans/`.
- `/sdd-spec` **lê** as capabilities e **marca** o delta nos RFs; este command é o único que **escreve** capability — e só sob PR merged. Comportamento não entregue nunca entra na spec viva.
- Três commands leem comentários de PR, com propósitos distintos: `/sdd-learning` extrai **regra de comportamento** (o que não repetir), `/pair-review` valida **fixes contra o comentário de origem**, e este extrai **trabalho pendente** (follow-up → backlog). Mesma fonte, saídas diferentes — não é redundância.
- `/roadmap` (sync) **move o item** pra `concluido/` por PR merged — `/sdd-close` aplica a mesma transição e **adiciona** o arquivamento dos docs SPEC/PLAN. Rodar `/roadmap` depois é idempotente.
- `/sdd-learning` **extrai aprendizado** do PR mergeado (input complementar; não move arquivos).
- `old/` (descartadas) é gerenciado manualmente — `/sdd-close` só **sinaliza** candidatos, nunca move pra lá.
