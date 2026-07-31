---
name: pr-close
description: Fecha o ciclo de uma mudança DEPOIS que o PR já foi mergeado — não mergeia nem fecha PR nenhum. Arquiva os artefatos, promove o comportamento entregue pra capability viva, conclui o item do roadmap, colhe a dívida que sobrou e destila os aprendizados pra memória. Um de cada vez, sob confirmação.
disable-model-invocation: true
argument-hint: [<NNN-slug> | --pr <N> | vazio = varre o que já mergeou]
allowed-tools: Read Write Edit Grep Glob Agent AskUserQuestion Bash(roadmap:*) Bash(roadmap) Bash(memory-audit:*) Bash(git worktree list*) Bash(git status*) Bash(git log*) Bash(gh *) Bash(ls *) Bash(mkdir *) Bash(mv *) Bash(find *) Bash(cat *)
---

# pr-close

**Você não fecha o PR aqui** — quem mergeia é o time, e isso já aconteceu. O que fecha é o **ciclo
da mudança**: o que sobrevive ao PR e some se ninguém recolher agora.

O merge é o único momento em que o comportamento **passou a ser verdade**. É por isso que tudo o
que vale além da mudança acontece aqui, e não antes:

1. **Arquiva** a pasta da mudança — sai do caminho sem perder o rastro.
2. **Promove** o comportamento entregue pra **capability viva**.
3. **Conclui** o item do roadmap, e mostra o que isso desbloqueou.
4. **Colhe** o que sobreviveria perdido — dívida de teste e follow-up de review.
5. **Destila** os aprendizados pra memória do projeto.

Sem este passo, o comportamento entregue morre num arquivo arquivado e a dívida registrada é
registrada *e esquecida do mesmo jeito*.

Root é o **repositório principal** (`git worktree list | head -1`), como sempre — `thoughts/` é
gitignored e a worktree nasce sem ele.

## O gate: só mergeado

```bash
gh pr view <N> --json state,mergedAt,title,url
```

| Estado | O que fazer |
|---|---|
| `MERGED` | segue (e `reopened` depois de merged conta: o código entrou) |
| `OPEN` | **não fecha nada.** Diga que segue em andamento e passe adiante |
| `CLOSED` sem merge | **não arquiva.** Isso é descarte, não conclusão — sinalize e deixe a decisão com o usuário |

Nada aqui acontece sem confirmação, **um item por vez**. Fechamento em lote é como se arquiva coisa
errada em silêncio.

**Mudança com vários PRs** (o `plan` quebrou em slices): a pasta só é arquivada e a capability só é
mesclada quando **todos** mergearem. Mesclar no primeiro slice afirmaria na capability um
comportamento que só existe pela metade. Já a colheita e os aprendizados rodam **por PR mergeado** —
o review e a dívida são daquele PR.

## 1 · Arquivar

```
thoughts/changes/<NNN>-<slug>/  →  thoughts/changes/archive/<NNN>-<slug>/
```

A pasta inteira, com `spec.md`, `plan.md`, `tasks.md` e `notes.md`. `mv` simples — `thoughts/` é
gitignored, nunca `git mv`, nunca commit.

Se já existir pasta de mesmo nome no destino, **pare nesta mudança e avise**: provavelmente já foi
arquivada. Não sobrescreva.

O `NNN` continua reservado: a numeração conta `changes/` **e** `archive/`, e número não se reusa.

## 2 · Promover pra capability

O `spec.md` marcou o delta de cada requisito. É ele que manda:

| Delta | O que fazer em `thoughts/capabilities/<domínio>.md` |
|---|---|
| `[ADDED]` | novo `C<N>` = `max(N existente, incluindo os removidos) + 1` |
| `[MODIFIED → <domínio> C<N>]` | **edite** o `C<N>` e **acrescente** ao `[Origem]` — sem apagar o rastro antigo |
| `[REMOVED → <domínio> C<N>]` | tire de `## Comportamento atual`, registre em `## Removido` com PR e data |

Depois, `atualizado:` e a spec em `specs:`.

**Edição cirúrgica, nunca reescrita.** Use `Edit` no requisito alvo. Reescrever o arquivo inteiro
perde o histórico dos outros requisitos, que vieram de mudanças que não são esta.

Quatro situações que **param neste delta** — não na mudança inteira:

- **`C<N>` alvo não existe** → pare e avise. Ou a spec referenciou errado, ou outro fechamento já
  aplicou. **Nunca invente requisito.**
- **`[Origem]` já cita esta spec e este PR** → pule, já foi aplicado. É o que torna rodar duas vezes
  inofensivo.
- **Requisito sem marcação num domínio que já tem capability** → não trate como `ADDED` em silêncio.
  Mostre os `C<N>` existentes e pergunte se é comportamento novo ou modificação.
- **Domínio novo** → confirme antes de criar o arquivo. Uma pasta cheia de capabilities de um
  requisito cada destrói o valor do documento.

Sem `thoughts/capabilities/` e sem delta, pule em silêncio: o projeto ainda não adotou capability.

**Capability errada é pior que capability incompleta** — ela vira a fonte de verdade que a `spec` do
próximo ciclo vai ler, e propaga o erro. Em dúvida, não mescle.

### `fix` e `chore` também passam por aqui

A pergunta é uma só: **mudou o que o sistema promete?**

- Bug fix que corrige comportamento observável → `MODIFIED`. O que estava escrito na capability
  não era verdade, e continuar escrito é pior do que não estar lá.
- Refactor, dependência, build, formatação → não toca capability. Nada do que o sistema promete
  mudou.

## 3 · Concluir no roadmap

```bash
roadmap list --json                          # ache o item pelo change: ou pelo pr:
roadmap move <NNN> --to concluido --pr <N>
```

O comando move o arquivo, regenera o hub e recalcula os 🔓 Desbloqueados — **mostre o que
desbloqueou**, porque é a resposta pro "e agora?" que justifica ter fechado.

Sem item correspondente, não invente um: registre no sumário. Sem o comando instalado, diga numa
linha e siga.

## 4 · Colher o que sobrou

Duas fontes, e as duas somem se ninguém colher agora:

**Dívida de teste** — a seção de dívida do `plan.md` e o que o `notes.md` registrou durante a
execução, incluindo verificação manual que ficou pendente.

**Follow-up de review** — o padrão mais comum é o revisor **aprovar** e deixar o follow-up no corpo
da aprovação, às vezes como opcional:

```bash
gh pr view <N> --json reviews --jq '.reviews[] | select(.body != "")'
gh api repos/{owner}/{repo}/pulls/<N>/comments        # inline, que o `pr view` não traz
```

`state: APPROVED` com `body` não-vazio é sinal mais confiável que caçar frases de adiamento.
**Opcional que mergeou sem a correção é dívida** — com severidade menor e a marca de que o revisor
não bloqueava. Se mergeou *com* a correção, não é dívida: confirme no diff.

Cada candidato vira item, **sob confirmação individual**, com dedup contra o backlog:

```bash
roadmap add "<a consequência, em uma frase>" --dep <NNN da mudança que fechou> \
  --contexto "follow-up do PR #N · <arquivo:linha> · <quem apontou>"
```

A dependência já satisfeita faz o follow-up nascer direto em 🔓 Desbloqueados — que é onde ele tem
chance de ser visto.

### O roadmap é privado. Pergunte se o time precisa ver.

`thoughts/` é gitignored: item que fica só no roadmap é **visível só pra você**. Para o que o time
precisa enxergar, existe a **issue perene** — uma por repositório, o mesmo endereço que o `pr-audit`
alimenta:

```
chore: Auditoria contínua de follow-ups de review
```

Ofereça o destino junto com o item, e deixe claro o que cada um significa: **o roadmap é onde a
prioridade se decide; a issue é o espelho público.** Nem todo follow-up precisa dos dois — o que é
só seu não ganha nada indo pro radar do time, e enche um checklist que vale pela densidade.

Publicando, siga o formato do `pr-audit` **exatamente** — é o que faz a próxima auditoria reconhecer
o item como já rastreado em vez de reabri-lo:

```markdown
- [ ] <consequência em uma frase>.
      `RISCO` · ativo|armado · `arquivo:linha` · PR #N · rev. marcou opcional no PR
```

`RISCO` é um de `SEGURANCA` · `DADO` · `CONTRATO` · `DISPONIBILIDADE` · `ROBUSTEZ` · `COBERTURA` ·
`HIGIENE`. **Procure a issue antes de criar** (`gh issue list --search`) — abrir uma segunda divide
o histórico em dois lugares e nenhum passa a valer. Use `--body-file`, nunca heredoc.

Publicar é ação que o time inteiro vê: **mostre o texto antes e espere o OK**.

**Risco aceito como permanente não vira item.** O `plan.md` registra o motivo que o usuário deu;
respeite. Colheita vazia é resultado normal — não force item de comentário ambíguo.

**Nunca poste no PR.** Aqui se lê comentário; não se responde, não se resolve thread.

## 5 · Destilar os aprendizados

O que este ciclo ensinou vai pra memória do projeto — mas **quase nada passa**, e é assim que deve
ser. Memória cheia de fato histórico é memória que ninguém lê.

Delegue a destilação a um subagente (`subagent_type: general-purpose`, `model: opus`), que lê as
fontes e devolve candidatos já filtrados:

> Leia `${CLAUDE_SKILL_DIR}/learning-filters.md` e siga exatamente.
> Fontes: `<notes.md>`, `<plan.md>`, e os comentários do PR #N (já coletados abaixo).
> Memória atual, pra dedup: `<conteúdo do MEMORY.md>`.

Cada candidato que voltar vai pra tela **um a um**, com o tipo proposto e o gancho. Você aprova,
edita ou descarta. A escrita segue o formato da skill `memory` — e se ela não estiver por perto,
o formato mínimo é `<tipo>_<slug>.md` com `Why:` e `How to apply:`.

O que mais rende aqui é o **comentário de review que apontou um erro**: a regra genérica extraída
dele é o tipo de coisa que não está no commit nem no PR, e que evita repetir na próxima.

## Legado do v9

Projeto que ainda tem `thoughts/specs/` e `thoughts/plans/` do formato antigo: **feche no formato em
que a mudança nasceu**. O par SPEC+PLAN vai pra `specs/closed/` e `plans/closed/`, e o resto do
fluxo é idêntico — capability, roadmap, colheita e aprendizados não mudam.

Não migre para o formato novo durante o fechamento. Mudança que está terminando não é hora de mexer
em estrutura, e converter no fim do ciclo só cria risco sem ganho.

## Ao terminar

```
Fechado: <NNN-slug> — PR #512 "<título>", mergeado em <data>

  Arquivado:   thoughts/changes/archive/<NNN-slug>/
  Capability:  checkout — C7 novo · C3 modificado
  Roadmap:     item 004 → concluído  ·  🔓 desbloqueou: 007
  Colhido:     2 itens (1 follow-up do review, 1 dívida de teste)
               → roadmap: 2  ·  → issue perene #77: 1 (o outro é só seu, a seu pedido)
  Memória:     1 nota (bug_webhook_timeout) · 3 candidatos descartados pelos filtros

Não fechado: 003-slug (PR #498 ainda aberto)
Atenção:     delta [MODIFIED → checkout C9] parou — C9 não existe na capability
```

O que parou aparece com o mesmo destaque do que foi feito. Delta interrompido significa capability
incompleta, e ela vai ser lida como verdade no próximo ciclo.
