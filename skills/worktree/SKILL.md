---
name: worktree
description: Cria e remove git worktrees isoladas a partir da branch default. A worktree nasce cercada (commit e push sob confirmação, destrutivos negados, merge de PR e push forçado barrados por hook) e com a memória centralizada no repositório principal. Ao remover, oferece apagar a branch local que ficou pra trás. Use quando ele pedir pra criar, montar, remover ou apagar uma worktree, ou pra trabalhar em outra branch em paralelo sem largar a atual.
when_to_use: Gatilhos do usuário — "cria uma worktree", "monta uma worktree pra <branch>", "quero mexer nisso em paralelo", "remove/apaga a worktree", "limpa a worktree do <branch>", "já mergeou, pode tirar a worktree". Gatilhos seus — você ia rodar `git worktree add` ou `git worktree remove` na mão, ou a worktree de uma mudança já encerrada ficou pra trás.
argument-hint: <nome-da-branch> | remove <nome>
allowed-tools: Read Write AskUserQuestion Bash(git worktree*) Bash(git remote*) Bash(git fetch*) Bash(git branch*) Bash(git status*) Bash(git log*) Bash(git rev-parse*) Bash(git ls-remote*) Bash(ls *) Bash(mkdir *) Bash(cp *) Bash(ln -s *) Bash(unlink *) Bash(readlink *) Bash(cat *) Bash(date*) Bash(command -v *)
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

**1. As permissões e o guard.** Copie `${CLAUDE_SKILL_DIR}/permissions.json` **integralmente**, sem
editar, para `<worktree>/.claude/settings.local.json`. É o que faz a sessão nova nascer cercada:
commit e push pedem confirmação, comandos destrutivos são negados, o resto do trabalho flui.

Esse arquivo é a fonte única — nunca reconstrua as regras de memória, nem "adapte" pro projeto. Se
ele não estiver acessível, **crie a worktree assim mesmo e diga que as permissões não foram
aplicadas**: worktree sem cerca o usuário resolve; worktree com cerca inventada, não.

Ele traz junto um **hook `PreToolUse`** que chama o `tk7-guard` — a parte da cerca que não depende
de adivinhar a forma do comando. Regra de permissão enumera sintaxe (`gh pr merge`), e sintaxe se
contorna (`gh api …/merge-async -X PUT`, que foi como um merge indesejado passou); o guard lê o
comando inteiro e barra merge de PR, deleção pela API e push forçado em qualquer forma.

**Confira que ele existe** — `command -v tk7-guard`. Hook que aponta pra comando ausente **falha
aberto**: o Claude Code segue com a chamada e a worktree parece protegida sem estar. Ausente, diga
na entrega, com o conserto numa linha:

```bash
<caminho do toolkit>/scripts/install-tk7-guard.sh
```

Se já existir um `settings.local.json` na worktree (veio commitado na branch), guarde uma cópia em
`<worktree>/thoughts/permissions.bak.json` antes de sobrescrever.

**2. A memória centralizada.** Sem isso o harness cria um `memory/` vazio para a worktree, e você
perde tudo que foi aprendido no root.

```bash
WT_MEM="$HOME/.claude/projects/$(echo "$WORKTREE_DIR" | sed 's|[^a-zA-Z0-9]|-|g')/memory"
ROOT_MEM="$HOME/.claude/projects/$(echo "$ROOT" | sed 's|[^a-zA-Z0-9]|-|g')/memory"
```

O slug troca **todo** caractere não-alfanumérico por `-`, não só a barra: o ponto de `.worktrees`
também vira `-`, então o diretório é `…-meu-projeto--worktrees-feat-x`, com dois hifens. Trocando apenas
`/` sai `…-meu-projeto-.worktrees-feat-x`, um diretório que o harness nunca lê — o link fica criado no
lugar errado e a worktree roda sem a memória do root. Se houver qualquer dúvida sobre o slug,
descubra em vez de montar: `ls ~/.claude/projects/ | grep <nome-da-branch>`.

- Não existe → `ln -s "$ROOT_MEM" "$WT_MEM"`.
- Já é symlink pro root → nada a fazer.
- Symlink pra outro destino → mostre pra onde aponta e pergunte antes de trocar.
- **Diretório real** → não substitua. Avise que há memória própria ali e siga; trocar sozinho
  descartaria notas que talvez só existam nessa worktree.

**3. `.worktrees/` no `.gitignore`** do root, se ainda não estiver.

Ao terminar, informe: caminho absoluto, branch e base, se as permissões foram aplicadas, **se o
guard está no PATH**, e como entrar — `cd <caminho> && claude`. A sessão nova já lê o settings ao iniciar; não há reload.

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

5. **A branch local** — pergunte se apaga. Quem remove a worktree quase sempre já entregou o
   trabalho, e a branch fica como resíduo; mas apagar é decisão dele, e manter é resposta legítima.

   Use `git branch -d`, nunca `-D` de saída — a recusa do git é a rede de segurança, não obstáculo a
   contornar. Se ele recusar, mostre o que existe só ali antes de perguntar de novo:

   ```bash
   git log --oneline <default>..<branch>
   ```

   A recusa tem dois significados opostos: trabalho de verdade que nunca foi entregue, ou um PR
   mergeado por **squash**, em que os commits foram reescritos e o git não reconhece mais o
   parentesco. Com a lista na tela o usuário separa os dois em um segundo; sem ela, ou perde
   trabalho ou guarda lixo. `-D` só depois dessa segunda confirmação.

   A branch **remota** não é assunto desta peça, nem quando o usuário manda apagar a local.

**Não remova o diretório `~/.claude/projects/<worktree>/`**: o harness guarda histórico de sessões
ali, e a perda seria silenciosa.

Ao terminar, diga o que foi removido, o que aconteceu com a branch, e liste as worktrees restantes.

## Sempre

- **Nunca force nada sem confirmação** — nem remoção, nem sobrescrita.
- **Nunca mexa na worktree principal.**
- **`thoughts/` é local e gitignored**, então a worktree nasce sem ele. Toda peça que escreve em
  `thoughts/` resolve o root primeiro — os artefatos de uma mudança vivem no repositório principal,
  não espalhados por worktree.
