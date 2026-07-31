# claude-code-sdd-toolkit

> **[Read in English](./README-en.md)**

Um workflow de pair programming com TDD para o [Claude Code](https://code.claude.com/docs), em quinze
skills que se encadeiam: especificar comportamento → planejar → decidir o que testar → implementar →
revisar → entregar.

O princípio que organiza tudo: **o agente busca o fato, a decisão é sua.** Nenhuma peça devolve
"aprovado" — elas devolvem achados, com o que ficou de fora declarado junto.

> ⚠️ **v10 em reconstrução.** O ciclo completo e as peças de longo prazo (roadmap, fechamento,
> memória, auditoria) estão prontos e em uso. Falta a periferia — pesquisa, diagnóstico de bug,
> protótipo, setup. O toolkit v9 inteiro segue em [`deprecated/`](./deprecated/) e continua
> funcionando se você já o usa. Ver [`REFACTOR-v10.md`](./REFACTOR-v10.md).

## Instalar

O repositório **é** o plugin — `.claude-plugin/plugin.json` na raiz e as peças em `skills/`.

**Experimentar sem instalar** (vale só para a sessão, nada é copiado):

```bash
claude --plugin-dir /caminho/para/claude-code-sdd-toolkit
```

**Instalar de vez** — clone dentro da sua pasta de skills pessoal:

```bash
git clone https://github.com/wisley7l/claude-code-sdd-toolkit ~/.claude/skills/toolkit
```

Uma pasta de skill com `.claude-plugin/plugin.json` carrega como plugin `toolkit@skills-dir`, sem
marketplace e sem passo de instalação. Para atualizar, `git pull`.

**Dependência opcional.** O `implement` oferece uma passada do `code-simplifier` depois do verde.
Vale ter instalado — sem ele a skill apenas avisa e segue:

```
/plugin install code-simplifier@claude-plugins-official
```

**Os comandos que as skills chamam.** Um script instala tudo — sem sudo, idempotente:

```bash
./scripts/install.sh          # ou --check pra só ver o que falta
```

Ele põe `roadmap`, `memory-audit` e `structure-cache` em `~/.local/bin` (wrappers apontando pro
código deste repo — editou aqui, reflete na hora) e oferece pré-autorizá-los no seu `settings.json`,
o que evita um prompt por chamada. Respeita `CLAUDE_CONFIG_DIR`, faz backup antes de mexer, e não
sobrescreve binário de terceiro que tenha o mesmo nome.

Por que comando e não prosa: o contrato do roadmap é escrito por **quatro** peças (`roadmap`, `plan`,
`pr-draft`, `pr-close`). Num script ele existe uma vez e é executável; em prosa, seria repetido
quatro vezes e divergiria na primeira edição.

### Como invocar

As peças ficam sob o namespace do plugin: **`/toolkit:spec`**, `/toolkit:plan`, e assim por diante.
O nome curto (`/spec`) também funciona **enquanto não houver outra skill com esse nome**.

Três peças daqui têm nome igual ao de algo que já vem com o Claude Code — `plan`, `code-review` e
`memory` (esta última é comando embutido). Nesses casos use o nome completo: `/toolkit:plan`,
`/toolkit:code-review` e `/toolkit:memory`. Plugin skills têm namespace próprio e não substituem as
originais, então `/code-review` e `/memory` continuam chamando as nativas.

## O ciclo

```
   spec  →  plan  →  test-plan  →  pr-draft  →  worktree
                                        │
                                        ▼
              implement  ⇄  code-review  →  pr-ready  →  merge  →  close
                                 ▲              │                     │
                                 └── o time comenta ──┘        capability · roadmap
                                                                memória · dívida
```

| Peça | O que faz |
|---|---|
| **`spec`** | Escreve o comportamento que a mudança entrega — o **quê**, nunca o como. Requisitos testáveis com cenários que os exercitam, e o delta contra o que o sistema já promete. Passa por um adversário antes de chegar em você. |
| **`plan`** | O **como**: pesquisa o codebase, fecha as decisões técnicas com fonte, e quebra em tarefas agrupadas pelos PRs que vão nascer. |
| **`test-plan`** | Decide **o que a mudança garante** — tipo de teste, ambiente, casos, e o que fica sem rede. Sessão em que você corta e prioriza; o agente levanta e propõe. |
| **`pr-draft`** | Abre o PR em draft antes da primeira linha de código. Com `sync`, reescreve o corpo depois da implementação como prévia pra quem revisa. |
| **`worktree`** | Cria e remove worktrees isoladas. A worktree nasce com as permissões aplicadas e a memória centralizada no repositório principal. |
| **`implement`** | Executa as tarefas com TDD. Delega as independentes a subagentes em paralelo e valida cada retorno. Fecha com a passada de simplificação — o *refactor* do ciclo, com a suíte rodando de novo depois. Faz `git add`, nunca commita sozinho. |
| **`code-review`** | Seis lentes independentes — conformidade, bugs, segurança, nomenclatura, queries e testes. Depois que o time comenta, valida se cada ponto foi de fato atendido. |
| **`pr-review`** | O outro lado: revisar o PR **de outra pessoa**. Explica a mudança antes de julgá-la, confere o que o PR prometeu contra o que entregou, sabatina você sobre o que só você decide, e monta um submit review com comentários inline — que passa pelos seus olhos antes de sair. |
| **`pr-ready`** | Confirma que está verde, atualiza o corpo do PR, e faz o handoff: sair do draft e marcar quem revisa — cada um sob sua confirmação. |
| **`pr-close`** | Fecha o ciclo sob PR mergeado — arquiva a mudança, promove o comportamento pra capability viva, conclui o item do roadmap, colhe a dívida que sobrou e destila os aprendizados pra memória. |
| **`pr-audit`** | Resgata a dívida que os reviews deixaram para trás: varre PRs mergeados, confere ponto por ponto no código de hoje e alimenta uma issue perene com o que continua aberto. |
| **`roadmap`** | A visão de cima — um item por PR previsto, num vault Obsidian onde dependência é wikilink e o grafo é nativo. Sincroniza o status pelo estado real dos PRs e mostra o que está desbloqueado agora. |
| **`memory`** | Escreve e cura a memória do projeto — aprendizados, bugs já resolvidos, decisões. Audita quanto da memória de fato age, já que só o índice é carregado, e nunca apaga nota sem você mandar. |
| **`baseline`** | Deriva a **capability** de um domínio a partir dos testes e do código que já existem — para adotar o toolkit num projeto que já tem história. |
| **`grilling`** | Entrevista para decisões que são suas: uma pergunta por vez, cada uma com recomendação explícita. As outras peças a chamam quando encontram decisão cara de reverter. |

## O que o toolkit garante

Não são preferências de estilo — são as regras que fazem o resto valer alguma coisa:

- **Red verificável.** O teste roda e **falha pelo motivo certo** antes de existir implementação.
  Teste que passa sem o código de produção é parada dura, não sinal de que já estava pronto.
- **Nada sobe sem verificação.** O piso é verificação manual sua, com evidência registrada. Ausência
  total de verificação exige uma pergunta explícita e o seu OK — não uma justificativa que o agente
  escreve para si mesmo.
- **A contagem de testes não cai em silêncio.** Se cair, para — apagar teste para fazer o gate passar
  é o defeito que mais se disfarça de progresso.
- **Tipo de teste por necessidade.** `unit` não é padrão; o tipo sai do comportamento, e o ambiente
  que ele exige fica declarado.
- **Commit e push são seus.** `git add` é livre; o resto espera o seu OK. Push é sempre ação humana.
- **Verde antes de entregar.** CI passou, ou a suíte local completa — todas as camadas, não só os
  testes que o PR tocou.
- **Comportamento de API se verifica**, no Context7 ou no código que já o usa. Sem fonte, a afirmação
  fica marcada e não sustenta tarefa.
- **Nenhuma peça aprova nada.** Sem nota, sem placar, sem "0 pendências". Os achados chegam como
  vieram — inclusive aqueles de que o agente discorda, com a discordância anotada do lado.

## Onde as coisas ficam

Uma mudança é **uma pasta**, no repositório principal:

```
thoughts/changes/<NNN>-<slug>/
  spec.md     o comportamento + o delta
  plan.md     a abordagem, as decisões técnicas e a matriz de testes
  tasks.md    as tarefas, agrupadas por PR
  notes.md    o que aconteceu na execução e no review
```

E o que sobrevive à mudança:

```
thoughts/capabilities/<domínio>.md    o que o sistema faz hoje
```

`thoughts/` é local e **fica fora do git** — nada disso é commitado, e nada disso aparece no corpo
do PR.

## Licenças

O toolkit é construção própria, mas incorpora conceitos de terceiros. As atribuições ficam em
`skills/<peça>/CREDITS.md` — arquivos irmãos, deliberadamente fora do que o agente carrega em
runtime. O protocolo e o índice das fontes estão em [`NOTICE.md`](./NOTICE.md), e os textos
integrais das licenças em [`LICENSES/`](./LICENSES/).
