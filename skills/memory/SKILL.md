---
name: memory
description: Escreve e cura a memória do projeto — o que aprendemos, os bugs que já resolvemos, as preferências e as decisões. Audita o índice pra mostrar quanto da memória de fato age, e reorganiza pro que foi escrito ser encontrado na hora certa. Nunca apaga nota sem você mandar.
disable-model-invocation: true
argument-hint: [auditar | <o que registrar> | curar]
allowed-tools: Read Write Edit Grep Glob AskUserQuestion Bash(memory-audit:*) Bash(memory-audit) Bash(git worktree list*) Bash(ls *) Bash(cat *) Bash(wc *)
---

# memory

A memória do projeto vive em `~/.claude/projects/<projeto>/memory/`, escrita por você e por mim ao
longo das sessões. Esta peça cuida de duas coisas: **escrever nota que vai ser encontrada** e
**manter o índice capaz de encontrá-la**.

## O fato que organiza tudo

**Só o `MEMORY.md` carrega** — as primeiras 200 linhas ou 25KB, em toda sessão. As notas
individuais **não carregam**: são lidas sob demanda, e só se algo no índice der motivo.

Isso tem uma consequência que muda como se escreve: uma nota perfeita que ninguém abre não existe.
O trabalho não termina no arquivo, termina na **linha do índice** que faz alguém abri-lo. Escrever é
barato; ser encontrado é o que custa.

Daí a régua desta peça: **se você não consegue escrever um gancho que diga *quando* aquilo importa,
não vira nota.** Nota sem gatilho é registro do passado, e o passado não age.

## Comece auditando

```bash
memory-audit          # ou --json, pra consumir
```

Ele responde o que não dá pra ver de olho: se o índice cabe no que carrega, quantas notas de fato
são alcançáveis, e — primeiro de tudo — **se a memória está fragmentada entre configs**.

Esse último é o achado que mais aparece: `CLAUDE_CONFIG_DIR` diferente, ou várias pastas `~/.claude*`,
e o mesmo projeto acumula memória em lugares distintos sem que nenhuma sessão veja as outras. Se
aparecer, **reporte com os números e pare**. Consolidar é mover dado do usuário entre diretórios;
proponha o de-para e espere o OK. Nunca mova sozinho.

Comando ausente → `scripts/install-memory-audit.sh`, uma vez.

## Os tipos

Oito, e o gatilho de cada um importa mais que o nome:

| Tipo | Quando | O que garante |
|---|---|---|
| `bug` | Um problema que já nos custou tempo e vai voltar | Reconhecer pelo **sintoma**, não pela causa |
| `feedback` | Você me corrigiu, ou confirmou um jeito de trabalhar | Não repetir o erro na próxima sessão |
| `decision` | Escolha técnica com trade-off, que alguém vai querer refazer | Não reabrir decisão fechada sem dado novo |
| `lesson` | Falhamos em algo de processo e sabemos por quê | Mudar o processo, não só o código |
| `win` | Deu certo e vale repetir de propósito | Reforçar o que funciona, que ninguém anota |
| `project` | Contexto do projeto que o código não conta | Não redescobrir o não-óbvio |
| `user` | Quem você é, como trabalha, o que prefere | Ajustar o modo de trabalhar |
| `reference` | Ponteiro pra sistema externo | Achar de novo sem perguntar |

**Escolha pelo gatilho, não pelo assunto.** "Bug no webhook" pode ser `bug` (vai voltar), `decision`
(escolhemos conviver) ou `lesson` (o processo deixou passar) — e o tipo certo é o que descreve
**quando aquilo vai ser útil de novo**.

Na dúvida entre dois, pergunte. `feedback` é o default mais usado, e é justamente por isso que ele
vira depósito: não caia nele por preguiça.

**Aposentados:** `idea` e `preference` não são mais oferecidos, e `blocker` foi absorvido por `bug`.
Notas antigas com esses tipos **continuam válidas e não se apaga nada** — a auditoria mostra quantas
existem e sugere destino, mas migrar é decisão do usuário, uma a uma.

## O arquivo

`<tipo>_<slug>.md`, flat, sem subpasta — o diretório é plano e o symlink de memória entre worktrees
depende disso.

```markdown
---
name: <tipo>-<slug-em-kebab>
description: <uma linha: o gatilho, não o resumo — é o que decide relevância na recall>
metadata:
  type: <tipo>
---

<o princípio, em uma ou duas frases>

**Why:** <a razão — sem isso a regra vira superstição e ninguém sabe quando abrir exceção>
**How to apply:** <a situação futura em que isso reaparece>
```

`bug` tem forma própria, porque é o único que se recupera **por sintoma**:

```markdown
**Sintoma:** <o que se vê quando acontece — a mensagem, o comportamento, o número>
**Causa raiz:** <o que realmente estava errado>
**Correção:** <o que resolveu, com o comando ou o diff mínimo>
**Reconhecer de novo:** <o sinal mais barato de checar antes de investigar do zero>
```

`win` é o inverso do `lesson` e quase nunca é escrito:

```markdown
**O que funcionou:** <a abordagem>
**Por que funcionou:** <a condição que fez dar certo — sem isso vira culto à carga>
**Quando repetir:** <em que situação vale, e em qual não vale>
```

Antes de criar, **procure nota parecida** (`ls`, `grep` por palavra-chave do sintoma). Atualizar
uma nota existente é quase sempre melhor que criar a nona variação do mesmo tema — foi assim que a
cauda longa cresceu.

## O índice, em três camadas

`MEMORY.md` é **só índice**. Conteúdo mora nos arquivos; aqui vive o que faz abri-los.

**1. GUARDRAILs** — o que precisa agir sem ninguém pedir. Uma linha, o link, e o teor da regra.
Teto de ~25 linhas, e entrar aqui é disputa: se tudo é guardrail, nada é. É a parte que mais rende,
porque é a única que age sem leitura extra.

**2. Mapa de sintomas** — a camada que faz `bug` funcionar. Não lista títulos, lista o que se vê:

```markdown
| Quando você vir isso | Vá direto pra |
|---|---|
| timeout no webhook de pagamento depois de ~30s | [bug_webhook_payment_timeout](./bug_webhook_payment_timeout.md) |
| `lint-staged` engoliu arquivo unstaged no commit | [bug_lint_staged_swallows_unstaged](./bug_lint_staged_swallows_unstaged.md) |
```

**3. Sub-sumários por tipo** — para a cauda. Passou de ~10 notas de um tipo, o índice ganha uma linha
apontando pro `_summary_<tipo>.md`, e é lá que as notas são listadas. O sub-sumário também é **mapa
de gatilhos**, não lista de títulos: "quando X, veja Y". Sub-sumário que só enumera nomes empurra o
problema um nível abaixo em vez de resolver.

Índice estourando o limite não se resolve apagando nota: promova detalhe pro sub-sumário, funda
entradas do mesmo tema, e corte linha que não diz quando importa. O harness avisa quando você está
perto e **dá erro** quando passou — o que exceder é descartado na sessão seguinte, em silêncio.

## Curar

Com a auditoria na mão, ataque nesta ordem — é a ordem do retorno:

1. **Fragmentação**, se houver. Nada mais importa se a sessão lê o diretório errado.
2. **Índice estourado**, se houver. O que passa do limite não existe.
3. **Linhas sem gancho** — citam um arquivo mas não dizem quando abri-lo. Reescreva o gancho ou
   tire a linha; ocupar o recurso escasso sem recuperar nada é o pior dos dois mundos.
4. **Órfãs** — nota fora do índice e de qualquer sub-sumário. Ou ganha entrada, ou o usuário decide
   que não valia. Traga a lista, não decida sozinho.
5. **Tipos aposentados e prefixos fora da convenção** — proposta de migração, uma a uma.

**Você propõe, ele decide.** Apagar ou mover nota é sempre dele — memória é registro do que o
usuário viveu, não rascunho seu. Mostre o que faria e espere.

## Ao terminar

O que mudou, e o efeito no que de fato carrega:

```
Memória · <projeto>
  Índice:  67 → 71 linhas (limite 200)
  Escrito: 2 notas (1 bug, 1 win) · 1 atualizada
  Índice:  +1 GUARDRAIL · +2 no mapa de sintomas
  Alcance: 42 → 45 notas linkadas direto (de 236)

Proposto, aguardando você: 4 notas `blocker` → `bug` · 2 órfãs sem entrada
```
