# Créditos — skill `worktree`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

Construção própria. Unifica três peças do v9, **nenhuma delas com atribuição de terceiros** — não
carregam header de inspiração, ao contrário de `sdd-plan` e `executor-plan`:

- `git-worktree.v9.md` (144L) — criação
- `git-remove-worktree.v9.md` (122L) — remoção
- `modo-livre.v9.md` (294L) + `references.v9/modo-livre-settings.json` (174L) — permissões

## Por que unificar criar e remover

Pergunta do usuário (31-07-2026): *"vc vai unificar os comando de worktree? pq quando fechamos um pr
a worktree morre tbm."*

Sim. É o mesmo recurso e o mesmo conhecimento: quem cria decide onde monta, o que liga no symlink de
memória e o que escreve no `.gitignore`; quem remove precisa **desfazer exatamente isso**. Em peças
separadas esse conhecimento vive em dois lugares e desanda em silêncio — o `unlink` que não pode ser
`rm -r` é o exemplo perfeito de detalhe que só faz sentido conhecendo a criação.

Pela Parte C.4 do `REFACTOR-v10.md`, separar exigiria ganho por invocação ou por sequência. Não há:
"remover worktree" não é gatilho suficientemente distinto pra pagar a duplicação.

## ⭐ O `modo-livre` virou arquivo, não peça

Observação que veio da descrição do próprio usuário: *"na criação do worktree eu usava o modo-livre
para a worktree o harness já nascer com os bloqueios de git commit e push principalmente."*

O nome dizia autonomia; o valor citado é a **cerca** — `ask` em commit e push, `deny` nos
destrutivos. Isso não é comportamento a instruir, é **configuração a copiar**: a lição H.5
(o determinístico vira artefato, não prosa). O JSON de 174 linhas era a fonte da verdade o tempo
todo; as 294 linhas em volta eram instrução pra copiar arquivo e escrever um marker.

`permissions.json` é cópia **fiel e integral** do reference v9 — o `SKILL.md` proíbe reconstruir as
regras de memória ou "adaptar pro projeto", porque permissão inventada é pior que permissão ausente.

**Suposição declarada, reversível:** assumi que o toggle no repositório principal (`/modo-livre on`
/ `off` / `update`) não sobrevive como peça, porque o uso descrito é sempre na criação da worktree.
O usuário não confirmou — perguntei duas vezes e o assunto seguiu. Se ele liga e desliga o modo no
root, o toggle volta como peça própria e este arquivo continua sendo a fonte.

## ⭐ A branch local deixou de ser intocável (03-08-2026)

Pedido do usuário: *"no comando worktree quando remover ao finalizar acho q deveria ter um
askquestion se quer deletar a a branch local"*.

O v10 dizia "**a branch local fica** [...] apagar branch não é trabalho desta peça". Isso não era
decisão tomada: era herança literal do `git-remove-worktree.v9`, cuja seção *Importante* trazia
"**Nunca** deletar a branch local (apenas a worktree)". Nasceu como guardrail e sobreviveu por
inércia — este arquivo não tinha uma linha justificando.

O que derruba o guardrail é o contexto de uso, e veio do usuário: *"quando ele é solicitado para
excluir uma worktree o trabalho já tá praticamente feito, falta apenas excluir a branch localmente"*.
Remover worktree não é ato isolado, é o fim do ciclo — a branch órfã é resíduo, e obrigar um segundo
comando pra varrer resíduo previsível é atrito sem contrapartida.

**Por que não investigar antes de perguntar.** A primeira versão do desenho consultava o PR via `gh`
pra saber se era seguro apagar. Foi descartado: o `git branch -d` **já** recusa branch não mergeada,
então a rede de segurança existe de graça e só aparece quando é necessária — investigar antes seria
pagar em toda remoção por um risco que se manifesta em poucas. Evita também acrescentar `Bash(gh *)`
a uma peça que vive de git puro.

**O que a recusa do `-d` exige.** Ela é ambígua de um jeito perigoso: significa *ou* trabalho nunca
entregue *ou* PR mergeado por **squash**, em que os commits foram reescritos e o parentesco se
perdeu. Como os dois casos pedem respostas opostas e o repo do usuário faz squash merge, a recusa
nunca pode virar um "não dá" — ela abre um `git log --oneline <default>..<branch>` na tela, e aí a
distinção que o git não consegue fazer leva um segundo pra quem escreveu os commits. `-D` só depois
dessa segunda confirmação.

**Fica de fora:** a branch remota, mesmo com o usuário mandando apagar a local. Apagar coisa do
servidor a partir de uma peça de worktree é alcance que ninguém pediu.

**Sobreposição conhecida:** o `git-prune-branches` do v9 (55L, ainda não portado) varre branches
locais cuja remota sumiu. Não é duplicação — o gatilho é outro: lá é faxina em lote depois, aqui é o
momento exato em que a branch fica órfã. Quando o `prune` for portado, vale citar um no outro.

## O que saiu

- **Marker `thoughts/modo-livre/active`** — servia pra outras peças detectarem o modo (o
  `executor-plan` mudava comportamento com base nele, e o validador Haiku só rodava com ML ativo).
  Nada no v10 lê estado de modo: as permissões são do harness, não do agente.
- **Cópia de `thoughts/tests/` pra worktree** e o `/sync-tests` na remoção — o andaime de testes
  unitários não-commitados do v9 morreu. No v10 o teste vive onde o projeto manda.
- **Backup/restore do settings** com pasta dedicada — virou uma linha (`permissions.bak.json`).

## O `tk7-guard` (12-08-2026)

Extensão do v10, sem equivalente no v9. Nasceu de um merge indesejado que um agente fez com
`gh api repos/…/pulls/427/merge-async -X PUT` — forma que o `deny` de `Bash(gh pr merge)` não previa
e que o `allow` de `Bash(gh *)` liberava. O pedido do usuário foi por onde a proteção deve chegar:
*"quando a gnt criar worktree o settings já deveria vir com essa proteção"*.

O `permissions.json` passou a carregar um hook `PreToolUse`, e a peça confere se o comando existe
antes de prometer que a worktree está cercada. Registro completo em `REFACTOR-v10.md`, I.39.

## Preservado do v9, sem mudança

O protocolo do symlink de auto-memory, incluindo os quatro casos (não existe, symlink pro root,
symlink pra outro destino, diretório real) e a regra que mais importa: na remoção é **`unlink`,
nunca `rm -r`** — seguir o symlink apagaria o `memory/` do root inteiro. E não remover o diretório
`~/.claude/projects/<worktree>/`, onde o harness guarda histórico de sessões.
