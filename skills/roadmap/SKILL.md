---
name: roadmap
description: Gerencia o roadmap do projeto — a visão de cima, um item por PR previsto. Adiciona itens, liga dependências entre eles, sincroniza o status pelo estado real dos PRs no GitHub, e mostra o que está desbloqueado agora. O grafo é nativo do Obsidian.
disable-model-invocation: true
argument-hint: '[add "<título>" | add #<issue> | dep NNN <- MMM | sync | board | migrar | vazio = estado atual]'
allowed-tools: Read Write Edit Grep Glob AskUserQuestion Bash(roadmap:*) Bash(roadmap) Bash(git worktree list*) Bash(git log*) Bash(gh *) Bash(ls *) Bash(mkdir *) Bash(cp *)
---

# roadmap

A visão de cima: o que existe pra fazer, em que ordem, e o que dá pra começar agora. Um item por
**PR previsto** — não por feature, não por mudança. Item é enxuto: o detalhe mora na mudança e no PR
que ele linka.

**O motor é o comando `roadmap`, não você.** Ele faz tudo que é determinístico — numeração, escrita
do arquivo, guarda de ciclo, cálculo dos desbloqueados, regeneração do hub — e faz igual toda vez.
Você faz o que é julgamento: o título, se aquilo vale virar item, qual dependência é real, e o que
apresentar ao usuário.

Nunca edite arquivo do vault à mão quando existe subcomando pra isso. O hub `ROADMAP.md` é **gerado**
— editá-lo é trabalho que a próxima regeneração apaga.

```bash
roadmap status --json    # estado completo, é por onde você começa
roadmap --help           # a lista inteira de subcomandos
```

Comando não encontrado → o usuário precisa rodar `scripts/install-roadmap.sh` uma vez. Diga isso e
pare; não reimplemente o motor em Bash improvisado, porque o formato é dado vivo dele.

## O vault

```
thoughts/roadmap/
  ROADMAP.md              # hub gerado — linka todos, lista 🔴 Próximos e 🔓 Desbloqueados
  backlog/      NNN-slug.md    # identificado, sem PR aberto
  em-progresso/ NNN-slug.md    # PR aberto e ativo
  concluido/    NNN-slug.md    # PR mergeado
```

Três coisas que valem entender antes de mexer:

- **O status é a pasta.** Não existe `status:` no frontmatter, e mover o arquivo *é* mudar o status.
- **`NNN` é o id do nó no grafo.** Nunca reusado, nunca renumerado — nem ao mover de pasta, nem ao
  ganhar PR. Item apagado deixa o número vago pra sempre, de propósito.
- **`Depende de:` é ordem entre PRs**, não decomposição: `NNN` depende de `MMM` significa *não
  começar antes de MMM mergear*. Os wikilinks ficam no corpo porque é de lá que o Obsidian desenha
  a aresta.

Isto é `thoughts/`: gitignored, sempre no **repositório principal**. O motor já resolve isso sozinho
(`git worktree list | head -1`), então rode de onde estiver.

## Quem mais escreve aqui

O roadmap não é alimentado só por você. `plan` cria um item por PR previsto, `pr-draft` promove pra
`em-progresso/` com o número do PR, e o fechamento move pra `concluido/`. Todos chamam o **mesmo
comando** — por isso o formato não diverge.

Consequência prática: quando você abre o roadmap, os itens já costumam estar lá. Seu trabalho é mais
curadoria do que criação.

## Sem argumento: o estado

`roadmap status` e apresente. Se houver ciclo ou órfão, isso vem primeiro — é dado quebrado, não
detalhe. E feche pelo que interessa: **o que dá pra começar agora**.

## `add` — o item novo

O motor numera, gera o slug e escreve. Você decide **o título** (o resultado, não a tarefa) e se
aquilo é mesmo um item.

```bash
roadmap add "<título>" [--dep NNN,MMM] [--change NNN-slug] [--contexto "<uma linha>"]
```

De issue do GitHub, leia antes com `gh issue view <N> --json title,body,url` e passe
`--issue <N> --issue-url <url>`. O motor recusa duplicata pelo `#N`.

Antes de criar, duas checagens que são suas:

- **Já existe?** `roadmap list` — item duplicado com NNN diferente é pior que item faltando, porque
  os dois viram nós separados no grafo.
- **Está no escopo?** Projetos costumam ter regra sobre o que entra (só backend, só produto). Está na
  memória do projeto; na dúvida, pergunte em vez de assumir.

## `dep` — a ordem

```bash
roadmap dep NNN --on MMM,PPP     # NNN não começa antes de MMM e PPP mergearem
roadmap dep NNN --clear
```

O motor rejeita ciclo e auto-dependência sem escrever nada, e recusa `--on` cujo alvo não existe —
apagar aresta é `--clear`, explícito.

O que é seu: **dependência é ordem, não parentesco.** "Os dois mexem no mesmo módulo" não é
dependência; "o segundo importa uma função que o primeiro cria" é. Aresta a mais bloqueia trabalho
que podia estar rodando em paralelo, e ninguém percebe — o item só não aparece em 🔓 Desbloqueados.

## `sync` — reconciliar com o GitHub

O eixo é o **estado real do PR**, não a existência de plano. Pegue os itens com `pr:` preenchido
(`roadmap list --json`) e consulte:

```bash
gh pr view <N> --json state,mergedAt,updatedAt,title
```

| Estado do PR | O que fazer |
|---|---|
| **merged** | `roadmap move NNN --to concluido` |
| **open**, mexido nas últimas ~4 semanas | garantir em `em-progresso/` |
| **open**, parado há mais de ~4 semanas | **não mova** — sinalize, sugerindo voltar pro backlog |
| **closed sem merge** | **não mova** — sinalize; o PR morreu, o item talvez não |

Rebaixar item é decisão do usuário: um PR parado pode ser prioridade suspensa, e mover sozinho
apaga a informação de que aquilo já esteve em andamento.

Depois, `gh pr list --author "@me" --state open --json number,title,headRefName` pega os PRs abertos
**sem item**. Ofereça criar — respeitando o escopo. E termine mostrando os desbloqueados: é o
"o que agora?" que justifica ter sincronizado.

**🔴 Próximos nunca é automático.** `next: true` é curadoria humana; nem o sync nem você ligam isso
sozinhos. Vale sugerir, com o usuário decidindo.

## `board` — o espelho pra olhar

```bash
roadmap board                  # regenera e imprime o file:// (regenerar é o default)
roadmap board -a               # o mesmo, e já abre no navegador padrão
roadmap board --live 10        # recarrega sozinho, pra aba deixada aberta
```

Gera **duas views** em `thoughts/board/`, ligadas por abas no topo:

```
thoughts/board/
  roadmap.html    os itens do vault
  changes.html    as mudanças de thoughts/changes/ — spec, plano, tarefas, notas
```

Derivado não mora junto do dado: `thoughts/roadmap/` fica só com os `.md`. O `changes.html` só
nasce se houver pasta em `thoughts/changes/`, e o comando funciona **sem vault de roadmap** — um
projeto pode ter mudanças e nenhum roadmap ainda. O nome não é `index.html` porque é ele que o usuário
fixa como aba: quando outras views existirem (`changes.html`), entram ao lado na barra de abas,
sem mudar esse caminho. Board de layout antigo é apagado na primeira geração — é tudo regenerável.

A página abre **compacta**: tiles com as contagens, busca (`/` foca), e seções que **nascem
fechadas** — 🔴 Próximos, 🔓 Dá pra começar agora, Em progresso, Backlog, Concluído, e a
consistência do vault (essa abre sozinha se houver ciclo, órfão ou NNN duplicado). Buscar abre só
as seções com resultado.

**Não há grafo na abertura.** Um roadmap real tem a maioria dos itens sem dependência nenhuma, e
desenhar tudo junto dá um paredão inútil (medido: 16.678 px num vault de 268 itens). O grafo
aparece quando se pergunta por um item: clicar abre uma **gaveta que cobre quase a tela** — sobra
uma faixa do fundo à esquerda, pra lembrar que a lista continua ali atrás. Dentro dela: a
vizinhança desenhada na hora (de quem ele espera, quantas ainda estão em aberto, o que ele
destrava) e, abaixo, duas colunas — o corpo renderizado à esquerda com largura de leitura, e à
direita `Depende de` / `Destrava` mais os botões de editar no Obsidian, ver PR e copiar o comando
de prioridade.

Dentro da gaveta, clicar em qualquer card **troca de item**, e o **← Voltar** desfaz o caminho
percorrido: dá pra descer pela cadeia de dependências sem perder de onde veio (`Backspace` faz o
mesmo, `Esc` fecha). O `#item-NNN` na URL abre a gaveta direto.

Só o grafo é desenhado em JS; o resto vem pronto do Python. Sem CDN e sem lib: abre offline.

Depois de existir uma vez, **toda mutação do vault o regenera** — inclusive as que vêm de `plan`,
`pr-draft` e do fechamento. Não é preciso rodar de novo: basta o F5 na aba (ou `--live`).

É **espelho, nunca fonte**: derivado, descartável, e editar o HTML não muda nada em `thoughts/`.
Ele só enxerga o vault — PR parado e PR aberto sem item continuam saindo do `sync`, que fala com o
GitHub.

### A view de changes

Não é markdown renderizado — é **view tipada**, que é de onde vem o ganho de leitura. A spec vira
requisito com `[ADDED]`/`[MODIFIED]` em destaque e os cenários DADO/QUANDO/ENTÃO em duas colunas;
o plano vira abordagem e decisões `D1…Dn` enumeradas; as tarefas viram **progresso por PR
previsto**, com o `#PR` e o branch lidos da nota do bloco; as notas de execução ficam em blocos
que abrem e fecham. A ficha tem abas Spec · Plano · Tarefas · Notas.

O parser aguenta o que o dado real tem, e isso não é opcional: o agrupador de `tasks.md` pode ser
`## PR 1` **ou** `## Etapa 1`; o id da tarefa pode ser `T1` **ou** `S1`; e existe um terceiro
estado, **`[~]` = tarefa movida pra outra mudança**, que não conta como feita nem como pendente.
A mudança se liga ao item do roadmap pelo campo `change:` do item.

Rodar por conta própria não custa nada, mas não substitua o fechamento em texto por "abri o board":
o usuário está no terminal, e o board é pra quando ele quiser **ver** o grafo.

## `migrar` — o formato antigo

Existe `thoughts/ROADMAP.md` (arquivo único, com bloco mermaid) e nenhum vault? O `roadmap status`
avisa. A conversão precisa de você porque o arquivo antigo é texto livre:

1. **Leia e parseie** cada entrada `- [ ] NNN — <título> ... · dep: MMM`, anotando **em que seção**
   estava. Seção vira pasta: 🔴 Próximos e Backlog → `backlog/`; Em progresso → `em-progresso/`;
   Concluído → `concluido/`.
2. **Mostre o de-para e peça confirmação antes de escrever qualquer coisa** — quantos itens por
   pasta, quantas dependências, quantos `next`.
3. Com o OK: `roadmap init`, depois um `roadmap add` por entrada **na ordem crescente de NNN**, para
   a numeração cair igual à original. Só então os `roadmap dep`, que precisam dos alvos já existindo.
4. **`roadmap check`** — órfão e ciclo do arquivo antigo aparecem aqui.
5. **Backup, nunca deleção:** `cp thoughts/ROADMAP.md thoughts/roadmap/_migrado-de-ROADMAP.md.bak`.
   O bloco mermaid não é portado: o grafo agora é nativo.

Se o NNN original tiver buracos, os números **não** vão bater — o motor sempre usa `max+1`. Isso é
mudança de identidade de nó: mostre o de-para completo e confirme antes, item por item.

Vault já existente com itens → **já migrado**. Não re-migre.

## Ao terminar

O que mudou, e o que isso libera:

```
Roadmap · 12 itens
  🔴 Próximos: 2      🔓 Desbloqueados agora: 1
  Backlog: 7 · Em progresso: 3 · Concluído: 2

Nesta rodada: 004 → concluído (#512 mergeado)
Desbloqueou:  007 — Painel de conciliação

Sinais: 1 PR parado há 6 semanas (#498, item 002) · 1 PR aberto sem item (#521)
```

Sinal não é enfeite: PR parado e PR sem item são as duas formas de o roadmap deixar de refletir a
realidade. Mostre sempre, mesmo quando não houver ação a tomar.
