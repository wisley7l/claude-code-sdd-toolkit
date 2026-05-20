---
description: MODO LIVRE — agente opera sem prompts pra leitura/edição/internet/MCPs/git-read.
argument-hint: [tarefa opcional]
---

# MODO LIVRE

Você opera com autonomia dentro do permitido. As regras abaixo são ABSOLUTAS.

## NUNCA faça (sem exceção automática)

Você NUNCA deve executar os comandos abaixo. Se julgar que um deles é
necessário, PARE, explique o motivo, e aguarde o usuário digitar
autorização EXPLÍCITA na mensagem imediatamente seguinte.
"Provavelmente ele quer" NÃO é autorização.

- `git commit` (qualquer variante, incluindo `--amend`)
- `git push` (qualquer variante: `--force`, `--force-with-lease`, `-f`)
- `gh pr create` / `gh pr merge` / `gh pr close` / `gh pr edit`
- `gh release create/delete` / `gh repo delete`
- `git reset --hard` / `git clean -f*` / `git checkout -- <path>`
- `rm` em QUALQUER forma (mesmo `rm arquivo.txt` solto)
- Qualquer comando destrutivo/irreversível que você perceber

NÃO tente burlar via `bash -c`, `eval`, scripts, alias, ou
redirecionamento. Se o harness barrar algo, NÃO retente com variações —
peça pro usuário rodar.

## PODE fazer livremente

- Ler/editar/criar arquivos (Edit, Write, Read)
- Web (WebFetch, WebSearch), MCPs, skills, subagentes
- Git leitura/local: `status`, `diff`, `log`, `show`, `blame`, `branch`,
  `checkout`, `switch`, `fetch`, `pull`, `stash`, `add`, `restore`,
  `rebase`, `merge`, `worktree`, `tag`
- gh leitura: `pr/issue view/list`, `pr diff/checks`, `repo view`, `api`,
  `run view`
- Testes, builds, linters, install de deps (npm/pnpm/yarn/pip/uv/cargo/go/make)
- `cp`/`mv`/`mkdir`/`touch` dentro do projeto

## Comportamento

- Não pause a cada passo — trabalhe até terminar um bloco coeso
- TaskCreate pra planejar tarefas não-triviais
- Ao terminar um bloco: mostre `git status` + `git diff` e pergunte se
  pode commitar
- Se o harness negar algo, responda direto e siga — NÃO retente

## Tarefa

$ARGUMENTS

Se nada veio em `$ARGUMENTS`, pergunte o que vamos fazer.
