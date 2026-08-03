---
name: pr-draft
description: Abre o pull request inicial em draft de uma mudança planejada — branch, commit vazio, título e corpo derivados da spec — e isola o trabalho numa worktree. Com `sync`, reescreve o corpo depois da implementação pra refletir o que foi feito de fato. Nunca tira o PR do draft.
disable-model-invocation: true
argument-hint: [nome-da-branch] | sync
allowed-tools: Read Write Grep Glob Agent Skill AskUserQuestion Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git worktree list*) Bash(git branch*) Bash(git fetch*) Bash(git switch*) Bash(git checkout*) Bash(git commit --allow-empty*) Bash(git push*) Bash(git remote show origin*) Bash(git rev-parse*) Bash(git ls-remote*) Bash(gh *) Bash(ls *) Bash(mktemp) Bash(roadmap:*) Bash(roadmap)
---

# pr-draft

Cuida do corpo do PR nos dois momentos em que ele importa:

- **sem argumento** — o **kickoff**: abre o PR em draft antes da primeira linha de código, e isola o
  trabalho numa worktree.
- **`sync`** — depois da implementação: reescreve o corpo pra refletir o que foi feito de fato,
  como prévia pra quem vai revisar.

**O PR nasce e permanece em draft.** `gh pr ready` é o seu clique, nos dois modos.

## O corpo é público — vale nos dois modos

Quem lê o PR não tem acesso ao seu ambiente. **Nunca** entram no corpo:

- caminhos de `thoughts/` — `spec.md`, `plan.md`, `tasks.md`, `notes.md` são locais e não
  versionados; pro leitor são ruído que parece referência;
- link ou id de sessão do Claude;
- número de item de roadmap ou qualquer numeração de planejamento interno.

Esses arquivos são **insumo pra escrever o corpo, nunca conteúdo dele**. Sobrevive só o que o leitor
consegue abrir: o link da issue. Na dúvida sobre um item, deixe de fora.

A tentação é maior no `sync`, porque você acabou de ler os artefatos todos.

## Onde estão os artefatos

Em `<root>/thoughts/changes/<NNN>-<slug>/`, onde **`root` é o repositório principal**
(`git worktree list | head -1`). `thoughts/` é gitignored, então dentro de uma worktree o diretório
local está vazio — e no `sync` você quase sempre está dentro de uma.

---

# Kickoff (sem argumento)

Abre o PR antes do código existir, pra sinalizar ao time que o trabalho começou e o que ele vai
entregar. Você não implementa nada aqui: o commit é vazio, e seu único propósito é dar ao PR um
ponto de partida.

## Antes de tocar em qualquer coisa

Resolva o root e a branch default (`git remote show origin`, com fallback pra `main`, `master` ou
`dev` local), e **cheque o estado**:

- **Working tree sujo é parada.** Mudanças não commitadas viajariam junto no checkout. Diga o que
  está pendente e pergunte se é pra commitar ou guardar antes.
- **Fora da branch default** — o kickoff parte dela. Volte (só se limpo) ou pergunte.

Depois `git fetch` da default: o PR nasce da versão atual, não da de ontem.

## Título, branch e corpo

- **`spec.md`** — o comportamento e para quem. Fonte do "o quê" e do "por quê".
- **`plan.md`** — a abordagem e quantos PRs foram previstos.
- **`tasks.md`** — se o plano previu mais de um PR, **qual bloco este PR fecha**. Com vários blocos
  e nenhuma indicação, pergunte antes de abrir: PR errado é caro de desfazer depois de publicado.

Sem artefato nenhum, sintetize da conversa e registre no corpo que não houve planejamento formal.

**Branch:** `<tipo>/<slug>` — `feat/` para comportamento novo, `fix/` para correção, `refactor/`
para mudança sem efeito observável, `chore/` para infra e configuração. O slug vem da pasta da
mudança. Confirme que a branch não existe local nem remotamente; se existir, pergunte antes de
reusar.

**Título:** `<tipo>: <descrição curta>`. O commit vazio usa o mesmo texto.

```markdown
## Contexto

<o que vai ser implementado e pra quem — 2 a 3 linhas, da spec>

## Plano

- Planejado via spec + plano técnico
- Tarefas: <N>, em <M> PR(s)
- Issue: <link, quando houver>

## Status

🚧 **Draft** — implementação ainda não iniciada.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Escreva num arquivo temporário e use `--body-file`; corpo inline quebra com aspas e quebras de linha.

## Abrir

```bash
git checkout -b "<branch>" "origin/$DEFAULT"
git commit --allow-empty -m "<título>"
git push -u origin "<branch>"
gh pr create --draft --base "$DEFAULT" --head "<branch>" --title "<título>" --body-file "$BODY"
```

Guarde a URL e o número.

**Promova o item do roadmap**, se houver um pra este slice — o número do PR é o que faz o item sair
do backlog:

```bash
roadmap list --json          # ache o item pelo change: desta mudança
roadmap move <NNN> --to em-progresso --pr <N>
```

Sem item correspondente, ou sem o comando instalado: siga em frente, dizendo numa linha. O roadmap
reflete o trabalho, não autoriza o trabalho.

**Se `push` ou `gh` forem negados**, ou o `gh` não estiver autenticado: não contorne e não desista.
Entregue os comandos exatos, já com os valores reais preenchidos, **um por vez** quando houver
dependência, e espere a confirmação de cada um antes do próximo. O resto do fluxo é local.

## Isolar e devolver

`git switch` de volta pra default — o repositório principal nunca fica preso na branch da feature.

A worktree é o passo seguinte e é **do usuário**: nenhuma peça deste toolkit invoca outra. Feche
pedindo, com o nome da branch já preenchido:

> PR draft aberto. Agora rode **`/tk7:worktree <branch>`** — ela monta a worktree sobre a branch
> recém-publicada, aplica as permissões e centraliza a memória.

```
PR draft: <url>
Branch:   <branch>  (base: <default>)
Worktree: <caminho absoluto>
Root:     de volta em <default>

  cd <caminho> && claude

E lá dentro, `implement` executa as tarefas.
```

---

# Sync (`sync`)

O corpo do kickoff ("draft, implementação não iniciada") fica obsoleto no minuto em que o código
existe. Este modo o troca por uma prévia pra quem vai revisar: o que mudou, por quê, como foi
resolvido e como foi verificado.

**Funciona de sessão limpa**, e esse é o uso recomendado — tudo é re-hidratado dos artefatos e do
diff, nada depende do histórico. Sessão longa carrega a narrativa da implementação, e narrativa
mente por omissão: o que foi difícil parece importante, o que foi trivial some.

## Reunir o estado real

Detecte o PR pela branch atual (`gh pr list --head $(git branch --show-current)`). Sem PR aberto,
pare e diga — o sync atualiza, não cria.

| Fonte | O que tirar dela |
|---|---|
| `spec.md` | o problema e o comportamento prometido → **por quê** e **o quê** |
| `plan.md` | decisões técnicas com justificativa → **como**; a seção `## Testes` → **verificação** |
| `notes.md` | o que foi feito de fato, **desvios do plano**, contagem de testes, dívida |
| `gh pr diff <N>` | o diff **completo**, não só os nomes — é dele que sai o "o quê" real |
| o código | quando o diff não se explica: o contrato que mudou, o contexto em volta |

Diff grande (mais de 10 arquivos): delegue a leitura a um subagente `Explore` que devolve a síntese
por arquivo. O corpo descreve **o código que existe**, não a intenção que o plano tinha.

## O corpo novo

```markdown
## O quê

<a mudança em si, 1 a 3 linhas diretas>

## Por quê

<o que estava errado ou faltando, e por que importa — 2 a 4 linhas>

## Como

<a estratégia em 2 a 3 linhas, seguida das decisões que valem explicação:>

- <decisão — e por quê>
- <desvio do plano — o que mudou e por quê>
- Comece o review por: `<arquivo central>` — <papel dele, e o ponto de atenção>

## Verificação

- Testes: <N novos, contagem de X para Y>
- Gates: <typecheck e lint>
- <verificação manual, quando houver: o que foi exercitado, e o que ficou de fora>
- Pra testar: <passos curtos, se aplicável>

---
Issue: <link, quando houver>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**Desvio do plano nunca é omitido.** É o que quem revisa mais precisa saber, e o que mais some por
parecer feio: o plano dizia X, o código faz Y, e a razão importa. Corpo que descreve o plano em vez
do código transforma o review numa caça ao erro.

**"Comece o review por"** aponta arquivo real do diff, com o motivo — trade-off, borda delicada,
área sensível. Genérico ("comece pelos testes") é ruído.

**Dívida aceita aparece.** O `plan.md` registra o que foi cortado e o que ficou como verificação
manual, com quem decidiu. Isso vai pro corpo em linguagem que quem revisa entende — sem apontar o
arquivo interno. Comportamento sem rede de proteção que não aparece no PR é o defeito que mais
escapa do review.

Toda afirmação rastreia a um artefato ou ao diff. Sem artefato nenhum (PR fora do fluxo), derive do
diff e dos commits, e diga no corpo que foi derivado assim.

## Aplicar

Mostre o corpo novo e o que ele substitui **antes** de aplicar, e espere o OK.

```bash
gh pr edit <N> --body-file "$BODY"
```

O título só muda se você pedir. Se estiver tudo pronto, feche dizendo isso — sair do draft é seu.

---

## Sempre

- **Draft sempre**, nos dois modos.
- **Commit vazio, nunca código.**
- **Sem force-push, sem reescrever histórico, sem deletar branch.**
- **GitHub pelo `gh`**, nunca token na mão.
