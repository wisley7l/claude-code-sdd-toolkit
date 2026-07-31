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

## O que saiu

- **Marker `thoughts/modo-livre/active`** — servia pra outras peças detectarem o modo (o
  `executor-plan` mudava comportamento com base nele, e o validador Haiku só rodava com ML ativo).
  Nada no v10 lê estado de modo: as permissões são do harness, não do agente.
- **Cópia de `thoughts/tests/` pra worktree** e o `/sync-tests` na remoção — o andaime de testes
  unitários não-commitados do v9 morreu. No v10 o teste vive onde o projeto manda.
- **Backup/restore do settings** com pasta dedicada — virou uma linha (`permissions.bak.json`).

## Preservado do v9, sem mudança

O protocolo do symlink de auto-memory, incluindo os quatro casos (não existe, symlink pro root,
symlink pra outro destino, diretório real) e a regra que mais importa: na remoção é **`unlink`,
nunca `rm -r`** — seguir o symlink apagaria o `memory/` do root inteiro. E não remover o diretório
`~/.claude/projects/<worktree>/`, onde o harness guarda histórico de sessões.
