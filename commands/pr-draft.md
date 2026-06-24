---
description: Abre PR inicial em draft a partir do plano — branch, empty commit, title/body da SPEC de comportamento, worktree via /git-worktree. `sync` reescreve o body pós-implementação como prévia pro reviewer.
model: claude-sonnet-4-6
argument-hint: [nome-da-branch | sync]
allowed-tools: Read, Glob, Grep, Skill, AskUserQuestion, Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(git fetch*), Bash(git checkout*), Bash(git switch*), Bash(git commit*), Bash(git push*), Bash(git remote show origin*), Bash(git rev-parse*), Bash(git log*), Bash(gh *), Bash(ls *), Bash(find *), Bash(mkdir *), Bash(pwd)
---

# PR Draft — Kickoff de feature

Voce abre o **pull request inicial em draft** pra uma feature que ja foi planejada. O PR nasce vazio (empty commit), em draft, com **title e body derivados da SPEC de comportamento** — pra sinalizar ao time que o trabalho comecou, descrevendo o QUE vai ser feito e pra quem, antes mesmo da primeira linha de codigo. Em seguida, voce isola o trabalho numa **worktree** via `/git-worktree` e devolve o repositorio principal pra branch default.

**Voce nao implementa nada aqui.** Esse command e o pontape inicial entre `/sdd-plan` e `/executor-plan`:

```
/sdd-spec  →  /sdd-plan  →  /pr-draft  →  cd <worktree> && claude  →  /executor-plan
                               ↑ voce esta aqui
```

## Argumentos

- `$ARGUMENTS` (opcional) — nome da branch. Se fornecido, usa ele direto (pulando a derivacao do plano). Se vazio, deriva dos artefatos (ver Passo 3).
- `sync` — **modo de atualizacao**: nao cria nada; reescreve o body do PR aberto da branch atual pra refletir o que foi implementado de fato, como previa pro reviewer. Ver secao "Modo sync" no final.

## Principios

- **Spec-first**: o "o que" do body sai da **SPEC de comportamento** (`thoughts/specs/`); a meta (escopo, N tarefas) sai do **PLAN tecnico** (`thoughts/plans/`). Sem nenhum, sintetiza do contexto da conversa
- **Draft sempre**: o PR nasce `--draft`. Sair de draft e acao humana, depois da implementacao
- **Empty commit e andaime**: o unico proposito do commit vazio e dar ao PR um diff inicial. O codigo real vem no worktree
- **Branch default intocada**: ao final, o root **volta pra branch default**. Todo trabalho acontece na worktree
- **Nunca force**: sem `--force`, sem reescrever historico, sem deletar branch
- **Fallback manual quando bloqueado**: se `git push` ou `gh pr create` for negado por permissao (ou `gh` nao autenticado), nao desista nem invente — passe a sequencia exata de comandos pro usuario rodar e **espere ele concluir** antes de seguir pro worktree

## Fluxo de Execucao

### Passo 1 — Resolver root, branch default e estado

```bash
ROOT=$(git worktree list | head -1 | awk '{print $1}')
DEFAULT=$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}')
```

Se `git remote show origin` falhar (sem remote), verifique `main`/`master`/`dev` localmente e avise que sem remote o push/PR vao exigir o fallback manual.

Cheque o estado do working tree:

```bash
git status --short
```

- **Working tree sujo**: PARE. O empty commit deve nascer de um estado limpo, e mudancas nao commitadas viajariam junto no `checkout`. Avise e pergunte se o usuario quer commitar/stashar antes. Nao prossiga sem resolver.
- **Nao esta na branch default**: avise qual branch esta ativa. O kickoff parte da default — faca `git switch "$DEFAULT"` (so se limpo) ou pergunte.

Atualize a default:

```bash
git fetch origin "$DEFAULT"
```

### Passo 2 — Detectar os artefatos (SPEC de comportamento + PLAN tecnico)

Localize o **PLAN tecnico** mais recente e a **SPEC de comportamento** que o originou:

```bash
ls -t "$ROOT"/thoughts/plans/PLAN-*.md 2>/dev/null | head -1   # PLAN tecnico
ls -t "$ROOT"/thoughts/specs/spec-*.md 2>/dev/null | head -1   # SPEC de comportamento (fallback)
```

- **PLAN encontrado**: leia o frontmatter (`scope`, `issue`, `skills`, `spec`) e a lista de tarefas (pra contar `N tarefas em M phases`). O campo `spec:` aponta a SPEC de comportamento que originou o plano — **abra essa SPEC** (se o campo existir; senao, use a SPEC mais recente).
- **SPEC de comportamento**: leia o titulo (`# SPEC: ...`), o **Resumo**, as **Historias de Usuario** e os **Criterios de Sucesso**. Essa e a fonte do "o que"/"pra quem" do body.
- **Nem PLAN nem SPEC**: sintetize title/body a partir do **contexto desta conversa**. Marque no body que o PR nao tem planejamento formal.

### Passo 3 — Derivar a branch

Se `$ARGUMENTS` foi fornecido, use-o como nome da branch e pule pra validacao no fim deste passo.

Caso contrario, derive `<prefixo>/<slug>`:

- **slug**: do nome do arquivo do PLAN (`PLAN-DD-MM-YYYY-NNN-<slug>.md` → `<slug>`) ou, sem PLAN, da SPEC (`spec-<ts>-<slug>.md` → `<slug>`). Sem nenhum, gere um slug kebab-case curto (≤4 palavras) do titulo sintetizado.
- **prefixo por escopo/natureza**:
  - bug fix (root cause, correcao) → `fix/`
  - refatoracao sem mudanca de comportamento → `refactor/`
  - qualquer feature nova (Medium/Large/Complex) → `feat/`
  - tarefa de infra/config/doc → `chore/`

  Use o `scope` do PLAN + o teor da SPEC pra decidir. Na duvida entre dois, mostre o nome derivado e confirme com AskUserQuestion antes de criar.

**Validacao**: confirme que a branch ainda nao existe (`git branch --list "<branch>"` e `git ls-remote --exit-code origin "<branch>"`). Se existir, avise e pergunte: reusar (pula a criacao, vai direto pro PR/worktree) ou escolher outro nome.

### Passo 4 — Title e body do PR

- **title** (conventional commit): `<prefixo>: <descricao curta>` — ex.: `feat: autenticacao via OAuth`. Derive do titulo da SPEC.
- **body**: escreva num arquivo temporario e use `--body-file` (evita problemas de escaping):

```bash
BODY_FILE=$(mktemp)
```

Template do body:

```markdown
## Contexto

<O que vamos implementar e pra quem — 2-3 linhas do Resumo + Historias de Usuario da SPEC de comportamento, ou do contexto da conversa>

## Plano

<!-- Body publico: NUNCA o caminho dos artefatos (`thoughts/specs/...`, `thoughts/plans/...` sao locais, o reviewer nao abre). So o sinal de que ha planejamento + meta derivada. -->
- Planejado via SPEC + PLAN formais  <!-- ou: "Sem planejamento formal — derivado da conversa" -->
- Escopo: <Medium | Large | Complex | n/a>
- Tarefas: <N> em <M> phases  <!-- omitir se nao houver PLAN -->
- Issue: <link, se houver>

## Status

🚧 **Draft** — implementacao ainda nao iniciada. PR aberto via `/pr-draft` pra sinalizar kickoff. O trabalho acontece na worktree `<prefixo>/<slug>`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

> **Body e publico** — vale pro kickoff e pro sync: nunca exponha caminho de `thoughts/` (SPEC/PLAN/IMP), numero de ROADMAP nem link de sessao do Claude (`claude.ai/code/session_...`). Só sobrevive o que o reviewer abre: link da Issue/PR.

O empty commit usa o **mesmo title** do PR como mensagem.

### Passo 5 — Criar branch + empty commit + push + PR draft

Execute na ordem. **Se qualquer comando de mutacao remota (`git push`, `gh pr create`) for negado por permissao, ou `gh auth status` indicar nao-autenticado, mude pro Modo Manual (abaixo) a partir daquele ponto.**

```bash
git checkout -b "<branch>" "origin/$DEFAULT"
git commit --allow-empty -m "<title>"
git push -u origin "<branch>"
gh pr create --draft --base "$DEFAULT" --head "<branch>" --title "<title>" --body-file "$BODY_FILE"
```

Capture a URL do PR retornada pelo `gh pr create`.

### Passo 6 — Devolver o root pra branch default

```bash
git switch "$DEFAULT"
```

O empty commit e o trabalho futuro ficam na branch `<branch>`, acessada pela worktree no proximo passo.

### Passo 7 — Criar a worktree

Invoque a skill **git-worktree** com o nome da branch:

```
/git-worktree <branch>
```

A branch ja existe (acabamos de cria-la e pushar), entao o `/git-worktree` adiciona a worktree sobre ela sem recriar. Ele cuida de: copiar `thoughts/tests/`, centralizar o auto-memory via symlink, garantir `.worktrees/` no `.gitignore`, e reportar o caminho.

### Passo 8 — Handoff final

Apos a worktree criada, reporte:

```
PR draft aberto: <url-do-pr>
Branch: <branch>  (base: <DEFAULT>)
Worktree: <caminho-absoluto-da-worktree>
Root devolvido pra: <DEFAULT>

Pra continuar a implementacao isolada:

  cd <caminho-absoluto-da-worktree>
  claude

E la dentro, rode /executor-plan pra executar o plano.
```

---

## Modo sync — body como prévia pro reviewer (pós-implementação)

Invocado como `/pr-draft sync`, tipicamente após `/executor-plan` + `/verifica` + review interno, antes de marcar o PR como ready. O body de kickoff ("draft, implementação não iniciada") fica obsoleto — o sync o reescreve como um **mini-spec pro reviewer** em 4 seções: **O quê** (a mudança), **Por quê** (o problema/motivação), **Como** (a solução, com decisões e desvios) e **Test plan** (como foi validado e como o reviewer testa).

**Funciona de sessão limpa** (e é o uso recomendado, pós-`/clear`): todo o necessário é re-hidratado dos artefatos + código — nada depende do histórico da conversa.

### Passos

1. **Detectar o PR**: `gh pr list --head $(git branch --show-current) --state open --limit 1`. Sem PR aberto → avise e encerre (sync atualiza, não cria).
2. **Coletar o estado real** (leia de fato, não presuma):
   - **SPEC de comportamento** (`thoughts/specs/`): o problema, as histórias de usuário e os critérios de sucesso — fonte do **Por quê** e do **O quê**
   - **PLAN técnico** (`thoughts/plans/`): Decisões Técnicas (o como, com justificativa) — fonte do **Como**
   - **IMP** (`thoughts/history/`): o que foi feito de fato, desvios do plano, test count
   - **Verificação comportamental** (seção do IMP ou `VER-*.md`), se existir
   - **Diff completo**: `gh pr diff <N>` (não só nomes de arquivos) — é dele que saem o "O quê" real e os apontadores do "Comece o review por"
   - **O próprio código**: abra os arquivos centrais da mudança quando o diff sozinho não explicar (contexto em volta, contrato da função alterada). O body descreve o código real, não a intenção do plano. Diff volumoso (>10 arquivos): delegue a leitura a um subagente (`Agent`, `subagent_type: Explore`) que devolve a síntese por arquivo
3. **Montar o body novo** (template abaixo) e mostrar ao usuário o resumo da troca (seções novas vs body atual).
4. **Aplicar com confirmação**: `gh pr edit <N> --body-file "$BODY_FILE"`. Title só muda se o usuário pedir explicitamente.
5. **Nunca saia de draft**: se tudo estiver pronto, encerre com "PR pronto pra ready — o clique é seu (`gh pr ready <N>`)".

### Template do body (sync)

```markdown
## O quê

<O que este PR faz — a mudança em si, 1-3 linhas diretas. Fonte: Resumo da SPEC + diff real>

## Por quê

<O problema/motivação — o que estava errado ou faltando e por que importa, 2-4 linhas. Fonte: SPEC de comportamento (problema + critérios de sucesso) + issue>

## Como

<A estratégia em 2-3 linhas, depois as decisões-chave com justificativa:>

- <decisão 1 — por quê (Decisões Técnicas do PLAN)>
- <decisão 2 — por quê>
- <desvio do plano, se houve — o que mudou e por quê (IMP). NUNCA omitir>
- Comece o review por: `<arquivo central>` — <papel dele em 1 linha> <pontos de atenção: trade-off, edge case, área sensível>

## Test plan

- Testes: <N unitários + M integração — test count preservado>
- Gates: <typecheck/lint green>
- Verificação comportamental: <checagens ✅ do /verifica, ou "não rodou">
- Pra testar manualmente: <passos curtos — como o reviewer reproduz/exercita a mudança, se aplicável>

---
<!-- Rodapé: SÓ referências que o reviewer externo consegue abrir. Issue: <link> quando houver — senão, omita a linha inteira. -->
Issue: <link, se houver>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**Regras do template**: cada afirmação rastreável a SPEC/PLAN/IMP/diff — não invente narrativa; desvio do plano NUNCA é omitido (é o que o reviewer mais precisa saber); "Comece o review por" aponta arquivos reais do diff, não genéricos. Sem SPEC/PLAN/IMP (PR fora do fluxo SDD): derive do diff + commits e marque "Body derivado do diff — sem planejamento formal".

**Guardrail — body é público, não vaze artefato interno**: o body do PR é lido por gente que NÃO tem acesso ao seu ambiente. NUNCA inclua no body:
- **Link de sessão do Claude** (`https://claude.ai/code/session_...`, IDs de sessão/conversa) — privado, sem valor pro reviewer. O rodapé `🤖 Generated with [Claude Code](https://claude.com/claude-code)` é o único marcador permitido.
- **Caminhos internos** de `thoughts/` (SPEC `thoughts/specs/...`, PLAN `thoughts/plans/...`, IMP `thoughts/history/...`) — são locais/não-versionados, o reviewer não os abre. A rastreabilidade SPEC/PLAN/IMP é insumo SEU pra escrever o body, não conteúdo dele.
- **Número/posição no ROADMAP** (`ROADMAP: 106`) e qualquer numeração de planejamento interno.

Só sobrevive no body o que o reviewer consegue abrir: link da Issue/PR. Na dúvida sobre um item, omita.

---

## Modo Manual (quando bloqueado)

Acionado quando `git push`, `gh pr create` sao negados por permissao, ou `gh` nao esta autenticado. **Nao tente contornar.** Em vez disso:

1. Avise claramente que voce nao tem permissao pra concluir a etapa remota e que vai guiar o usuario.
2. Liste os comandos **exatos, ja com os valores preenchidos** (sem placeholders), a partir do ponto onde parou. O usuario pode rodar cada um direto na sessao com o prefixo `!` (ex.: `!git push -u origin feat/slug`) ou no terminal dele.
3. Entregue **um comando por vez** quando houver dependencia (ex.: push antes do PR), e **espere o usuario confirmar** que rodou (cole a saida, se relevante) antes de mandar o proximo.

Sequencia tipica do Modo Manual (preencha com os valores reais):

```bash
# 1. (se ainda nao criou a branch/commit localmente — normalmente voce ja conseguiu)
git checkout -b feat/slug origin/main
git commit --allow-empty -m "feat: <descricao>"

# 2. publicar a branch
git push -u origin feat/slug

# 3. abrir o PR em draft
gh pr create --draft --base main --head feat/slug \
  --title "feat: <descricao>" \
  --body "<cole o body aqui, ou use --body-file>"

# (se 'gh' nao estiver autenticado, antes de tudo:)
gh auth login
```

4. Quando o usuario confirmar que o PR foi criado (peca a URL), prossiga normalmente pro **Passo 6** (devolver root pra default) e **Passo 7** (worktree). Esses passos sao locais — voce mesmo executa.

---

## Tratamento de Erros

- **Sem remote configurado** → push/PR exigem Modo Manual; avise no inicio.
- **Branch ja existe (local ou remota)** → perguntar: reusar (pula criacao) ou novo nome. Nunca sobrescrever.
- **PR ja existe pra essa branch** (`gh pr view <branch>` retorna) → informe a URL existente e pule a criacao; siga pro worktree.
- **Working tree sujo** → parada dura no Passo 1. Nao crie branch/commit sobre estado sujo.
- **`/git-worktree` falha** (ex.: worktree ja existe naquele caminho) → reporte o erro do command de worktree e o caminho; o PR ja esta aberto, entao oriente o usuario a resolver a worktree manualmente se preciso.

## Guardrails

- **PR sempre em `--draft`** — sair de draft e decisao humana (vale tambem no modo sync: `gh pr ready` e do usuario)
- **Sync nao inventa narrativa** — toda afirmacao do body rastreavel a SPEC/PLAN/IMP/diff; desvios do plano nunca omitidos; `gh pr edit` so com confirmacao
- **Body e publico, sem artefato interno** — NUNCA inclua link de sessao do Claude (`claude.ai/code/session_...`), caminhos de `thoughts/` (SPEC/PLAN/IMP) nem numero de ROADMAP no body. Sobrevive so o que o reviewer abre: link da Issue/PR
- **Empty commit, nunca codigo** — o commit do kickoff e vazio (`--allow-empty`); implementacao so na worktree
- **Root volta pra branch default** — o repositorio principal nunca fica preso na branch da feature
- **Nunca force-push, nunca delete branch, nunca reescreva historico**
- **Bloqueio → instrucao, nao contorno** — push/PR negado vira guia comando-por-comando, esperando o usuario
- **GitHub via `gh` CLI** — nunca tokens manuais
- **Working tree limpo antes de comecar** — kickoff parte de estado limpo na default
- **Title em conventional commit** — `<tipo>: <descricao>`, consistente com o prefixo da branch
