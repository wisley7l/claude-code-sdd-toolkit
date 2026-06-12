---
description: Abre PR inicial em draft a partir do plano — cria branch, empty commit, title/body do SPEC. Ao final, isola o trabalho em worktree via /git-worktree.
model: claude-sonnet-4-6
argument-hint: [nome-da-branch opcional]
allowed-tools: Read, Glob, Grep, Skill, AskUserQuestion, Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(git fetch*), Bash(git checkout*), Bash(git switch*), Bash(git commit*), Bash(git push*), Bash(git remote show origin*), Bash(git rev-parse*), Bash(git log*), Bash(gh *), Bash(ls *), Bash(find *), Bash(mkdir *), Bash(pwd)
---

# PR Draft — Kickoff de feature

Voce abre o **pull request inicial em draft** pra uma feature que ja foi planejada. O PR nasce vazio (empty commit), em draft, com **title e body derivados do plano** — pra sinalizar ao time que o trabalho comecou antes mesmo da primeira linha de codigo. Em seguida, voce isola o trabalho numa **worktree** via `/git-worktree` e devolve o repositorio principal pra branch default.

**Voce nao implementa nada aqui.** Esse command e o pontape inicial entre `/sdd-plan` e `/executor-plan`:

```
/sdd-plan  →  /pr-draft  →  cd <worktree> && claude  →  /executor-plan
                 ↑ voce esta aqui
```

## Argumentos

- `$ARGUMENTS` (opcional) — nome da branch. Se fornecido, usa ele direto (pulando a derivacao do SPEC). Se vazio, deriva do plano (ver Passo 3).

## Principios

- **Plano-first**: title e body saem do SPEC mais recente. Sem SPEC, sintetiza do contexto da conversa
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

### Passo 2 — Detectar o plano

Procure o SPEC mais recente:

```bash
ls -t "$ROOT"/thoughts/plans/SPEC-*.md 2>/dev/null | head -1
```

- **SPEC encontrado**: leia o frontmatter (`scope`, `issue`, `skills`), o titulo (`# SPEC: ...`) e o **Resumo Executivo**. Essa e a fonte de title/body.
- **Nenhum SPEC**: sintetize title/body a partir do **contexto desta conversa** (o que foi discutido/decidido). Marque no body que o PR nao tem SPEC formal.

### Passo 3 — Derivar a branch

Se `$ARGUMENTS` foi fornecido, use-o como nome da branch e pule pra validacao no fim deste passo.

Caso contrario, derive `<prefixo>/<slug>`:

- **slug**: do nome do arquivo SPEC (`SPEC-DD-MM-YYYY-NNN-<slug>.md` → `<slug>`). Sem SPEC, gere um slug kebab-case curto (≤4 palavras) do titulo sintetizado.
- **prefixo por escopo/natureza**:
  - bug fix (root cause, correcao) → `fix/`
  - refatoracao sem mudanca de comportamento → `refactor/`
  - qualquer feature nova (Medium/Large/Complex) → `feat/`
  - tarefa de infra/config/doc → `chore/`

  Use o `scope` do SPEC + o teor do Resumo pra decidir. Na duvida entre dois, mostre o nome derivado e confirme com AskUserQuestion antes de criar.

**Validacao**: confirme que a branch ainda nao existe (`git branch --list "<branch>"` e `git ls-remote --exit-code origin "<branch>"`). Se existir, avise e pergunte: reusar (pula a criacao, vai direto pro PR/worktree) ou escolher outro nome.

### Passo 4 — Title e body do PR

- **title** (conventional commit): `<prefixo>: <descricao curta>` — ex.: `feat: autenticacao via OAuth`. Derive do titulo do SPEC.
- **body**: escreva num arquivo temporario e use `--body-file` (evita problemas de escaping):

```bash
BODY_FILE=$(mktemp)
```

Template do body:

```markdown
## Contexto

<O que vamos implementar — 2-3 linhas do Resumo Executivo do SPEC, ou do contexto da conversa>

## Plano

- SPEC: `thoughts/plans/SPEC-DD-MM-YYYY-NNN-<slug>.md`  <!-- ou: "Sem SPEC formal — derivado da conversa" -->
- Escopo: <Medium | Large | Complex | n/a>
- Tarefas: <N> em <M> phases  <!-- omitir se nao houver SPEC -->
- Issue: <link, se houver>

## Status

🚧 **Draft** — implementacao ainda nao iniciada. PR aberto via `/pr-draft` pra sinalizar kickoff. O trabalho acontece na worktree `<prefixo>/<slug>`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

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

- **PR sempre em `--draft`** — sair de draft e decisao humana
- **Empty commit, nunca codigo** — o commit do kickoff e vazio (`--allow-empty`); implementacao so na worktree
- **Root volta pra branch default** — o repositorio principal nunca fica preso na branch da feature
- **Nunca force-push, nunca delete branch, nunca reescreva historico**
- **Bloqueio → instrucao, nao contorno** — push/PR negado vira guia comando-por-comando, esperando o usuario
- **GitHub via `gh` CLI** — nunca tokens manuais
- **Working tree limpo antes de comecar** — kickoff parte de estado limpo na default
- **Title em conventional commit** — `<tipo>: <descricao>`, consistente com o prefixo da branch
