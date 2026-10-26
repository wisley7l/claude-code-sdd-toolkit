---
name: spec
description: Escreve a especificação de comportamento de uma mudança — o QUÊ que o sistema passa a fazer, com requisitos testáveis e cenários que os exercitam. Marca o delta contra a capability viva. Nunca escreve código, plano técnico ou tarefas.
disable-model-invocation: true
argument-hint: <o que você quer mudar>
allowed-tools: Read Grep Glob Write Agent Bash(ls *) Bash(mkdir *) Bash(git log*) Bash(git worktree list*) Bash(structure-cache *) Bash(structure-cache)
---

# spec

Escreve o **comportamento observável** que a mudança entrega. O QUÊ, nunca o COMO — arquivo,
função, biblioteca, desenho técnico e ordem de implementação são do `plan`, não daqui.

**Uma intenção por mudança.** Se você não consegue dizer o que ela faz numa frase, são duas
mudanças. Divida antes de escrever.

## Antes de escrever, o legwork

Responda cada pergunta na fonte mais barata que a responde, nesta ordem. Pare quando souber o
suficiente pra escrever — não existe obrigação de percorrer tudo.

| Pergunta | Fonte |
|---|---|
| O que o sistema promete hoje aqui? | `thoughts/capabilities/<domínio>.md` |
| Isso ainda é verdade? | os testes do domínio |
| Onde vive, como se comporta nas bordas? | Grep/Read — em subagente `Explore` se for varredura ampla |
| Por que ficou assim? | `git log` / `git blame` |
| O que quebra se eu mexer? | `structure-cache query --importers <file>` |

**A capability é o critério de parada.** Leia o que o sistema já promete e vá ao código só onde
ela não cobre ou está suspeita. "Ler tudo que for relevante" não tem limite, e pesquisa sem
limite produz documento sem limite.

### Antes de confiar nela: até onde ela foi verificada

`thoughts/` é local. Mudança que não passou por este fluxo — PR de outra pessoa, hotfix direto na
main, você mesmo em outra máquina — **nunca entrou na capability**, e ela continua afirmando o
comportamento velho com toda a aparência de autoridade. O dano não é só um requisito errado: é que
uma capability confiável **desliga** a pesquisa que pegaria o erro.

O frontmatter diz até onde ela foi conferida. Compare com o repositório **antes** de usá-la como
critério de parada:

```bash
# root = repositório principal, como sempre (ver "Onde escrever")
git -C <root> log <verificado-ate>..HEAD --format='%h %an %s' -- <paths do frontmatter>
```

Havendo commits, mostre a contagem e os assuntos **antes de qualquer outra coisa**, e ofereça o
`baseline` no domínio pra reconciliar — `--auditar` quando o que pesa é conferir se o que já está
escrito ainda vale. É o `baseline` que trata contradição entre código e requisito já registrado —
aqui você só levanta a suspeita.

- **Não filtre por autoria.** Hotfix seu, commit seu de outra máquina e merge de terceiro dão o
  mesmo estrago. O critério é *não passou por esta capability*, nunca *não foi você*.
- **É aviso, não gate.** Refactor que não mudou comportamento vai aparecer no range, e tudo bem —
  isto é sinal, não veredito. Quem decide se para pra reconciliar é o usuário.
- **Sem `verificado-ate` ou sem `paths`, diga que não deu pra verificar** e siga. Capability antiga
  ou promovida sem marcador não tem como ser checada — tratar isso como "está em dia" é inventar
  cobertura, que é exatamente o defeito que a checagem existe pra pegar. Vale igual quando o `git
  log` reclama do sha: histórico reescrito é marcador perdido, não domínio em dia.

**Os testes valem mais que a implementação** pra saber o que o sistema promete: implementação
conta o que o código faz hoje, bugs inclusive; teste conta o que alguém *decidiu* que ele deve
fazer. O inventário de testes que você levantar aqui serve de novo no `plan` — anote.

`structure-cache` responde **estrutura**, não comportamento, e só cobre TS/JS. Use pra dimensionar
o impacto (quem depende disso), nunca pra descobrir o que o sistema faz. Ao delegar pesquisa a um
subagente, **repita no prompt dele** a diretiva de consultar o cache antes de grepar — subagente
não herda estas instruções.

Sem capability no domínio, siga pelo código e **ofereça o `baseline`** ao usuário: a capability
nasce no primeiro toque, não num big-bang de documentação. Capability é aceleração, nunca
dependência — ausente ou incompleta, o trabalho continua.

## Decisões que não são suas

Invoque `grilling` quando o legwork revelar qualquer uma destas, **nomeando quais são antes da
primeira pergunta**:

- **Escopo** — o que fica de fora. Reverter escopo errado custa a mudança inteira.
- **Todo delta `MODIFIED` ou `REMOVED`** — mexer em comportamento que já existe quebra quem
  depende dele, e quem depende nem sempre está neste repo.
- **Conflito entre o que a demanda pede e o que a capability promete.**

Fora dessas, decida e **mostre o que assumiu** numa linha por suposição. Contestar suposição
escrita é barato; descobrir suposição implícita depois do código, não.

Toda pergunta daqui — a do escopo, a do delta, a do conflito — segue a seção "A pergunta" de
`${CLAUDE_SKILL_DIR}/../triage/prosa.md`: a escolha, o que acontece em cada saída, a recomendação.
"Delta", "capability" e "requisito MODIFIED" são palavras suas; na tela, "o que muda no que o
sistema já faz hoje", "o que o sistema promete", "comportamento que já existe e vai mudar".

## Onde escrever

```
<root>/thoughts/changes/<NNN>-<slug>/spec.md
```

**`root` é sempre o repositório principal** — `git worktree list | head -1`. `thoughts/` é
gitignored, então uma worktree nasce sem ele; escrever no diretório local espalharia os artefatos de
uma mesma mudança por worktrees diferentes. Vale para toda leitura e escrita em `thoughts/`.

`NNN` = `max(existentes em thoughts/changes/ e no archive) + 1`, três dígitos, nunca reusado.
`slug` = 3–6 palavras em kebab-case. A pasta é a mudança inteira — `plan.md`, `tasks.md` e
`notes.md` vão nascer ao lado.

## O formato

```markdown
# <título — o comportamento, não a implementação>

<uma frase: o que passa a ser possível, e pra quem>

**Fora de escopo:** <o que deliberadamente não entra — e nada mais entra>

## R1 · [ADDED] <nome do comportamento>

O sistema DEVE <comportamento observável, com o número/limite explícito>.

- **<nome do cenário>** — DADO <estado>, QUANDO <ação>, ENTÃO <resultado verificável>
- **<caso de borda ou erro>** — DADO <estado>, QUANDO <ação>, ENTÃO <resultado verificável>

## R2 · [MODIFIED → checkout C3] <nome do comportamento>

...
```

**Delta** — todo requisito carrega o seu: `[ADDED]` (comportamento novo), `[MODIFIED → <domínio>
C<N>]` (altera requisito existente da capability), `[REMOVED → <domínio> C<N>]` (retira). Sem
marcação, é `ADDED`. O `C<N>` precisa existir na capability — se não existe, ou o domínio não tem
capability (ofereça `baseline`) ou você está marcando errado.

**Requisitos não-funcionais são requisitos** — `DEVE responder em até 200ms no p95` é um `R<N>`
como qualquer outro, com cenário que o verifica. Não existe seção separada pra eles.

Use **DEVE** (inegociável) por padrão. **DEVERIA** só quando a exceção é justificável, e **PODE**
só quando é genuinamente opcional.

## A barra

O gate não é "as seções existem". É isto, requisito por requisito — e é o que você mostra ao
usuário no fechamento:

1. **Um comportamento por requisito.** Se tem "e também", são dois requisitos. Divida.
2. **Observável por quem não leu o código.** "DEVE exibir erro quando o upload passa de 10 MB"
   passa; "DEVE tratar uploads grandes adequadamente" não passa — ninguém sabe testar.
3. **Cenário que exercita, não que repete.** Reafirmar o requisito com outras palavras não testa
   nada. E os bugs moram nas bordas: entrada vazia, token expirado, limite exato, o caminho que
   dá errado. Um requisito só com caminho feliz está incompleto.
4. **Nome que diz o que acontece** — "Recusa cartão expirado", não "Cenário 2".
5. **Nada de COMO.** Nome de arquivo, função, biblioteca ou estrutura de dados na spec é
   vazamento — mova pro `plan`.
6. **Fora de escopo preenchido.** Se nada ficou de fora, a mudança provavelmente está grande
   demais e você ainda não percebeu.

Requisito que falha em qualquer uma volta pra reescrita antes de a spec ser entregue.

## O adversário — sempre, e antes de mostrar ao usuário

A barra acima você aplica em si mesmo, e é boa pra erro de forma. Ela não pega **ausência**: se
você soubesse que faltava um requisito, teria escrito. Por isso a spec passa por um adversário
com contexto limpo, **toda vez**.

Lance um subagente (`Agent`, `subagent_type: general-purpose`, `model: opus`) com este prompt:

> Leia `${CLAUDE_SKILL_DIR}/adversary.md` e siga exatamente. A spec está em
> `<caminho do spec.md>`. A capability do domínio está em `<caminho>` (ou: não existe).
> Você é read-only e não tem poder de aprovar.

**Ele não é juiz.** Não aprova, não reprova, não dá nota — devolve uma lista de ataque, e quem
decide o que fazer com cada item é o usuário. Se você tratar o retorno dele como carimbo, a spec
ganhou mais uma camada entre o usuário e o texto, que é exatamente o que este workflow existe
pra evitar.

Traga os achados **como vieram**, sem filtrar os que você discorda. Se você discordar de um,
diga por quê **junto** do achado, e deixe os dois na tela.

## Ao terminar

Mostre ao usuário, em tela: os requisitos, separados em **o que é novo**, **o que muda no que já
existe** e **o que deixa de existir**; as suposições que você assumiu; o que ficou fora de escopo;
e os achados do adversário, cada um com o que acontece se ficar como está. A pergunta que fecha é
a única que importa:

> **Você ficaria confortável se isto fosse construído exatamente assim, e nada além?**

Se a resposta for não, é mais barato consertar agora do que em qualquer momento posterior.
Nada de código, plano ou tarefa nasce aqui — o próximo passo é o `plan`.
