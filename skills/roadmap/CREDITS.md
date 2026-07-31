# Créditos — skill `roadmap`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

**Construção própria.** O `/roadmap` v9 (218L) + a reference `roadmap-item.md` (143L) não têm
equivalente em nenhuma das fontes mapeadas — nem no tlc-spec-driven, nem no OpenSpec, nem no
mattpocock/skills. O vault Obsidian com grafo nativo saiu de uso real, não de referência.

Sem obrigação de atribuição.

## ⚠️ Contrato de dados preservado (Parte E.1)

Esta é a primeira peça da Onda 2 — mexe em **dado que existe em projetos reais fora deste repo**.
Tudo abaixo foi mantido **verbatim** e verificado por execução:

| Invariante | Como foi preservado |
|---|---|
| Status = a pasta, sem `status:` no frontmatter | `move` reescreve em outra pasta e apaga a origem |
| `NNN` = `max(todas as pastas)+1`, nunca reusado | `next_nnn()` — testado apagando um item no meio: o próximo foi 004, não 002 |
| Frontmatter `id`, `titulo`, `pr`, `criado` (DD-MM-YYYY), `next` | `cmd_add` escreve exatamente estes |
| Wikilinks **no corpo**, não no frontmatter | `set_deps_line()` só toca a linha `**Depende de:**` |
| Sem dependência → **omitir** a linha | `--clear` remove a linha inteira, não escreve "nenhuma" |
| Sem ciclos | `would_cycle()` recusa antes de escrever — verificado |
| 🔓 Desbloqueados = backlog **E** tem dep **E** todas em concluido | `unblocked()` — item sem dep nunca conta |
| Determinístico e idempotente | hub regenerado duas vezes deu byte-idêntico |
| `next:` é curadoria humana | nenhum caminho de código liga `next` sozinho; só `set --next` |

**Migração:** nenhuma necessária. Itens do v9 continuam válidos — o campo `plan:` legado é
**lido e preservado** (`list --json` devolve), e nunca apagado, porque o script jamais reescreve o
corpo inteiro de um item existente.

## Decisões do usuário (31-07-2026)

- **⭐ O motor vira script, a skill fica fina.** Escolha explícita do usuário entre três opções.
  É a lição H.5 (OpenSpec) aplicada: o determinístico vira artefato. Ganho decisivo — o contrato E.1
  passou a viver **em um lugar executável**, em vez de repetido em prosa nas quatro peças que
  escrevem no vault (`plan`, `pr-draft`, fechamento, e a própria `roadmap`).
- **⭐ Nenhuma peça pode invocar outra.** O usuário escolheu manter `disable-model-invocation: true`
  em todas — *"toda cadeia vira instrução pra você invocar a próxima peça"*. Isso **reforçou** a
  escolha do script: as outras peças chamam `roadmap` por Bash, não pela skill. Se a decisão fosse
  outra, o desenho ainda funcionaria — mas seria mais caro.

## O que mudou em relação ao v9

- **`plan:` → `change:`** no frontmatter. O v9 guardava o basename do PLAN
  (`PLAN-16-07-2026-003-estoque.md`); o v10 não tem esse arquivo — tem a pasta
  `thoughts/changes/NNN-slug/` (I.12). O campo antigo **não é apagado**, é lido.
- **`Docs:` com caminho, não wikilink solto.** `[[spec]]` seria ambíguo no v10: *toda* mudança tem um
  `spec.md`, e o Obsidian resolve wikilink por nome de arquivo em todo o vault. Virou
  `[[changes/NNN-slug/spec|spec]]`, que assume o vault na raiz de `thoughts/`.
- **Dois sequenciais NNN convivem, de propósito.** O `NNN` da mudança (`thoughts/changes/NNN-slug/`)
  e o `NNN` do item de roadmap são numerações **independentes** — uma mudança pode virar vários PRs,
  e item de roadmap é 1 por PR (I.13). Unificar exigiria renumerar itens existentes, e `NNN` é o id
  do nó no grafo: renumerar quebra rastreabilidade histórica. O pareamento é o campo `change:`.
- **O sync não move PR parado nem PR morto.** O v9 já sinalizava sem rebaixar; mantido e explicitado
  — rebaixar sozinho apaga a informação de que aquilo esteve em andamento.
- **A migração ficou na skill, o resto no script.** O parse do formato antigo é texto livre — é
  julgamento. O `add`/`dep` que ela chama é determinístico. Divisão pela natureza da tarefa, não
  pelo tamanho.

## Onde o vault fica ancorado

Pergunta do usuário: *"o roadmap vai ser por projeto? e sempre vai olhar para o root do projeto,
pode acontecer de eu estar em um worktree"*. Sim para as duas — **um vault por repositório**, e a
resolução é feita pelo motor, não pelo caller. Verificado por execução de dentro de uma worktree:
leu e escreveu no root, com o `thoughts/` local inexistente (gitignored).

Isso levou a um segundo defeito, achado só porque o caso foi testado:

- **Layout bare + worktrees** (`projeto/.bare` com `projeto/main`, `projeto/feat-x` irmãs) não tem
  main worktree. `git worktree list | head -1` devolve o **`.bare`**, e o vault iria pra dentro do
  diretório git.
- Pular a linha `(bare)` **não resolve**: o git lista em ordem alfabética, então o vault caía em
  `feat/` — uma worktree de feature que morre quando o PR fecha. Silenciosamente pior que o bug
  original.
- Âncora final: o **pai do `.bare`**, que é o diretório do projeto e sobrevive a todas as árvores.
  Com fallback avisado para bare fora do projeto (`/srv/git/x.git`), onde o pai não ancora nada.

**Limite declarado:** as outras peças resolvem o root **em prosa** (`git worktree list | head -1`) e
carregam o mesmo ponto cego. Não foi propagado a todas de propósito — o toolkit nunca cria layout
bare (a skill `worktree` monta em `<root>/.worktrees/`), então é caso de borda de quem já usa bare
por conta própria. A nota ficou na `worktree`, que é a peça dona do conceito.

## Defeito encontrado e corrigido durante a verificação

`dep NNN --on 999` (alvo inexistente) escrevia **lista vazia** — um número digitado errado apagaria
em silêncio todas as arestas existentes do item. Corrigido: `--on` sem nenhum alvo válido aborta sem
escrever. Apagar dependência é `--clear`, que é explícito.

Foi o script que tornou isso visível: em prosa, o mesmo bug seria uma instrução ambígua que só
apareceria com o dado já perdido.
