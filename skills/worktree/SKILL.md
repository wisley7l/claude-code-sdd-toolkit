---
name: worktree
description: Cria e remove git worktrees isoladas a partir da branch default. A worktree nasce com as permissões do projeto aplicadas (commit e push sob confirmação, destrutivos bloqueados) e com a memória centralizada no repositório principal. Use pra trabalhar em várias branches em paralelo.
disable-model-invocation: true
argument-hint: <nome-da-branch> | remove <nome>
allowed-tools: Read Write AskUserQuestion Bash(git worktree*) Bash(git remote*) Bash(git fetch*) Bash(git branch*) Bash(git status*) Bash(git rev-parse*) Bash(git ls-remote*) Bash(ls *) Bash(mkdir *) Bash(cp *) Bash(ln -s *) Bash(unlink *) Bash(readlink *) Bash(cat *) Bash(date*)
---

# worktree

Cuida do ciclo de vida das worktrees: **criar** (default) e **remover** (`remove <nome>`). As duas
metades vivem juntas porque a remoção precisa desfazer exatamente o que a criação montou — separadas,
esse conhecimento desanda em silêncio.

Worktrees ficam em `<root>/.worktrees/<branch>`, onde `root` é o repositório principal:

```bash
git worktree list | head -1 | awk '{print $1}'
```

Isso vale para o layout que esta skill cria (clone normal, worktrees em `.worktrees/`). Num
repositório **bare** — `projeto/.bare` com `projeto/main` e `projeto/feat-x` irmãs — não existe main
worktree: a primeira linha é o diretório git, e a segunda é a árvore que vier primeiro em ordem
alfabética, que pode ser efêmera. Ali a âncora é o **pai do `.bare`**. Se for esse o caso do projeto,
diga ao usuário em vez de escrever em `thoughts/` no escuro.

## Criar

A partir da **branch default do remote** (`git remote show origin`, com fallback pra `main`,
`master` ou `dev` local), sempre atualizada com `git fetch` antes — worktree que nasce de base velha
carrega conflito que não era pra existir.

Se a branch já existe (local ou remota), monte a worktree sobre ela em vez de recriar. Se o caminho
já está ocupado, diga e pergunte se é pra navegar até a existente.

Três coisas nascem junto com ela, nesta ordem:

**1. As permissões.** Copie `${CLAUDE_SKILL_DIR}/permissions.json` **integralmente**, sem editar,
para `<worktree>/.claude/settings.local.json`. É o que faz a sessão nova nascer cercada: commit e
push pedem confirmação, comandos destrutivos são negados, o resto do trabalho flui.

Esse arquivo é a fonte única — nunca reconstrua as regras de memória, nem "adapte" pro projeto. Se
ele não estiver acessível, **crie a worktree assim mesmo e diga que as permissões não foram
aplicadas**: worktree sem cerca o usuário resolve; worktree com cerca inventada, não.

Se já existir um `settings.local.json` na worktree (veio commitado na branch), guarde uma cópia em
`<worktree>/thoughts/permissions.bak.json` antes de sobrescrever.

**2. A memória centralizada.** Sem isso o harness cria um `memory/` vazio para a worktree, e você
perde tudo que foi aprendido no root.

```bash
WT_MEM="$HOME/.claude/projects/$(echo "$WORKTREE_DIR" | sed 's|/|-|g')/memory"
ROOT_MEM="$HOME/.claude/projects/$(echo "$ROOT" | sed 's|/|-|g')/memory"
```

- Não existe → `ln -s "$ROOT_MEM" "$WT_MEM"`.
- Já é symlink pro root → nada a fazer.
- Symlink pra outro destino → mostre pra onde aponta e pergunte antes de trocar.
- **Diretório real** → não substitua. Avise que há memória própria ali e siga; trocar sozinho
  descartaria notas que talvez só existam nessa worktree.

**3. `.worktrees/` no `.gitignore`** do root, se ainda não estiver.

Ao terminar, informe: caminho absoluto, branch e base, se as permissões foram aplicadas, e como
entrar — `cd <caminho> && claude`. A sessão nova já lê o settings ao iniciar; não há reload.

## Remover

**Pare imediatamente se o diretório atual estiver dentro da worktree a remover** — isso invalidaria
a sessão em curso. Diga para sair antes.

Sem argumento, liste as worktrees e pergunte qual. Depois, nesta ordem:

1. **Trabalho não salvo** — `git -C <worktree> status --porcelain`. Se houver, mostre o que é e
   pergunte antes de qualquer coisa: remover perde isso.
2. **Branch sem remote** — se a branch não tem tracking, avise. Pode ser trabalho que só existe ali.
3. **Desfazer o symlink de memória** — `unlink`, nunca `rm -r`. Seguir o symlink apagaria o
   `memory/` do root inteiro. Se o caminho for um diretório real em vez de symlink, liste o conteúdo
   e pergunte se move pro root, descarta ou cancela.
4. **`git worktree remove`** — `--force` só depois de confirmação explícita.

**A branch local fica.** Remover a worktree não apaga a branch, e apagar branch não é trabalho desta
peça. Não remova o diretório `~/.claude/projects/<worktree>/`: o harness guarda histórico de sessões
ali, e a perda seria silenciosa.

Ao terminar, diga o que foi removido, que a branch continua existindo, e liste as worktrees restantes.

## Sempre

- **Nunca force nada sem confirmação** — nem remoção, nem sobrescrita.
- **Nunca mexa na worktree principal.**
- **`thoughts/` é local e gitignored**, então a worktree nasce sem ele. Toda peça que escreve em
  `thoughts/` resolve o root primeiro — os artefatos de uma mudança vivem no repositório principal,
  não espalhados por worktree.
