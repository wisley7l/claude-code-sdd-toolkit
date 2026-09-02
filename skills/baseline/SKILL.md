---
name: baseline
description: Deriva a capability viva de um domínio a partir dos testes e do código existentes — a linha de base do que o sistema já promete hoje — e revalida a que já existe, requisito por requisito, com `--auditar`. Trabalha por lotes, sob confirmação. Use quando um domínio ainda não tem capability, ao adotar o toolkit num projeto com código, pra entender um domínio herdado, ou pra conferir se o que está escrito ainda é verdade.
disable-model-invocation: true
argument-hint: <domínio | área que você quer mapear> [--auditar]
allowed-tools: Read Grep Glob Write Edit Agent Bash(ls *) Bash(mkdir *) Bash(git log*) Bash(git rev-parse*) Bash(git worktree list*) Bash(structure-cache *) Bash(structure-cache)
---

# baseline

Mantém a **capability viva** de um domínio — `thoughts/capabilities/<domínio>.md`, o documento que
responde "o que o sistema faz hoje aqui" — contra o que já existe no repositório: escrevendo o que
falta, e conferindo o que já está lá.

Existe porque a capability normalmente só nasce no fechamento de uma mudança, sob PR mergeado.
Num projeto com código anterior ao toolkit, isso significa que ela **nunca cobre o que já estava
lá** — e a `spec` do próximo ciclo marca `ADDED` o que na verdade é `MODIFIED`, envenenando o
delta desde o primeiro ciclo.

**Não documente o codebase inteiro.** Um domínio por vez, e de preferência o domínio que você
está prestes a mexer. Capability incompleta é normal e útil; capability errada é pior que
nenhuma, porque vira fonte de verdade pro ciclo seguinte e propaga o erro.

## Três momentos, uma peça

O alvo muda; o resto — promessa × acidente, evidência, lotes, formato — é o mesmo nos três.

| Situação | O que você faz | A pergunta que responde |
|---|---|---|
| Domínio **sem** capability | **derivar** do zero | "o que o sistema faz aqui?" |
| Capability existe (padrão) | **complementar** o que não está coberto | "o que falta escrever?" |
| Pedido explícito (`--auditar`) | **revalidar** o que já está escrito | "o que ainda é verdade?" |

Complementar e auditar percorrem caminhos opostos e **não se misturam num mesmo lote** — um sai do
código atrás de buraco, o outro sai do documento atrás de evidência. Rodar os dois na mesma sessão
é normal e útil (é o que responde "o que mudou e o que entrou"), mas em passadas separadas, ou o
usuário perde o fio de qual pergunta está respondendo.

## O que é um domínio

Uma área de **comportamento observável** — `checkout`, `auth-sessao`, `notificacoes` — não um
módulo de código nem uma feature. Slug em kebab-case, sem timestamp.

Antes de propor domínio novo, **liste os que já existem** e prefira encaixar num deles. Domínio
novo só com confirmação explícita: uma pasta cheia de capabilities de um requisito cada destrói
o valor do documento.

Se o usuário não souber delimitar, proponha o recorte a partir do que você encontrou e deixe ele
ajustar — mas não comece a escrever sem o recorte fechado.

## A distinção que decide tudo: promessa × acidente

Nem todo comportamento do código é uma promessa. Registrar um bug como requisito é o **pior**
resultado possível desta skill — a próxima pessoa vai preservá-lo achando que é contrato.

| Evidência | O que é | O que fazer |
|---|---|---|
| Tem **teste dedicado** | promessa — alguém decidiu que deve ser assim | registra, confiança alta |
| Está em doc do projeto (README, ARCHITECTURE) | promessa declarada | registra, confiança alta |
| Só no código, observável pelo usuário | comportamento, origem desconhecida | registra **marcado**, confiança baixa |
| Só no código, detalhe interno (ordem de chamada, estrutura de dado, nome) | não é comportamento | **fora** — isso é implementação |
| Teste e código **discordam** | sinal de bug ou de teste desatualizado | **não escolha** — sinalize e pergunte |
| Cheira a bug (inconsistente, `TODO`/`FIXME` ao lado, caso especial sem razão) | provável defeito | **pergunte antes**, nunca registre calado |

Na dúvida entre registrar e deixar de fora, **deixe de fora e diga que deixou**. Ausência o
próximo ciclo corrige; requisito falso, não.

## Como levantar a evidência

Nesta ordem, do mais confiável pro menos:

1. **Os testes do domínio.** São a spec executável do comportamento atual — contam o que alguém
   *decidiu*, não o que o código acidentalmente faz. Cada teste com nome descritivo é candidato
   direto a cenário `Quando → então`.
2. **Docs do projeto** que falem do domínio.
3. **O código**, pra achar o que não tem teste — especialmente validações, guardas, casos
   especiais e caminhos de erro.
4. **`git log`** nos arquivos do domínio, quando um comportamento parecer arbitrário: a mensagem
   de commit costuma dizer se foi decisão ou remendo.
5. **`structure-cache query --importers`** (TS/JS) pra saber quem consome o domínio — consumidor
   externo é sinal forte de que aquilo é contrato, não detalhe.

Delegue a varredura a subagentes `Explore` quando for ampla, **repetindo no prompt deles** a
diretiva de consultar o `structure-cache` antes de grepar — subagente não herda estas instruções.

## Trabalhe por lotes

Nunca despeje trinta requisitos de uma vez: ninguém revisa trinta, e aprovação em bloco é a
mesma anestesia que este workflow existe pra evitar.

Proponha **3 a 5 requisitos por lote**, agrupados por sub-área. Para cada um mostre o requisito,
os cenários e a evidência (`arquivo:linha` do teste ou do código) — e a confiança, quando não for
alta. O usuário aceita, corta ou corrige cada um antes do próximo lote.

Ao fim de cada lote, **escreva o que foi aceito** antes de seguir. Assim a sessão pode ser
interrompida a qualquer momento sem perder trabalho, e retomada depois — releia o arquivo, veja
o último `C<N>` e continue de onde parou.

Diga sempre quanto falta pela sua estimativa ("cobri autenticação e sessão; faltam recuperação
de senha e 2FA"), pra decisão de parar ser informada. **Parar no meio é resultado legítimo.**

## O formato

Preserve o contrato da capability — ele é lido pela `spec` e escrito pelo fechamento:

```markdown
---
dominio: checkout
atualizado: DD-MM-YYYY
verificado-ate: <sha>
paths:
  - src/checkout/
  - test/checkout/
specs: []
---

# Capability: Checkout

> O que o sistema faz hoje neste domínio.

## Comportamento atual

### C1 — Aplicação de cupom
O sistema DEVE aceitar no máximo um cupom por pedido.
- **Quando** o cliente aplica um cupom válido → desconto sobre o subtotal
- **Quando** o cupom está expirado → erro "cupom expirado", pedido inalterado
[Origem: derivado do código em DD-MM-YYYY · test/checkout/coupon.spec.ts:41]
```

**Regras que não podem quebrar:**

- **`C<N>` sequencial por capability, nunca reusado.** Se o arquivo já existe, continue a partir
  do maior `C<N>` presente — inclusive contando os que estão em `## Removido`.
- **Todo `C<N>` carrega `[Origem]`.** O que você deriva leva
  `[Origem: derivado do código em DD-MM-YYYY · <arquivo:linha da evidência>]` — **distinto** de
  `[Origem: spec-X · PR #N]`, que significa "isto foi especificado e entregue". A diferença é a
  informação mais importante do documento: derivado quer dizer *ninguém validou, confie menos*.
- Comportamento observável, **nunca implementação**. Sem nome de função, arquivo ou lib dentro do
  requisito (o `arquivo:linha` vive no `[Origem]`, que é rastro, não comportamento).
- Cenários em **`Quando → então`**.
- **Seções vazias são omitidas.** Uma capability derivada costuma ter só `## Comportamento atual`
  — e, quando houver, `## Dívida conhecida`.
- Um comportamento por `C<N>`. "E também" significa dois requisitos.

### `verificado-ate` e `paths` — o marcador que faz a capability envelhecer em voz alta

`thoughts/` é local: mudança que não passou por este fluxo nunca entra na capability, e ela segue
afirmando o comportamento velho. Os dois campos são o que permite a `spec` do próximo ciclo
perceber isso — sem eles ela não tem como checar nada e vai dizer que não verificou.

- **`paths`** — os caminhos que sustentaram a evidência deste domínio, código e teste. Saem do
  levantamento que você acabou de fazer, **não de palpite sobre a árvore do projeto**. Confirme com
  o usuário junto do último lote: recorte errado aqui produz alarme falso pra sempre, ou silêncio
  pra sempre.
- **`verificado-ate`** — o `HEAD` do **repositório principal** (`git worktree list | head -1`, onde
  `thoughts/` mora), **capturado antes de começar a levantar evidência**, não no fim. A sessão pode durar, e gravar o HEAD final afirmaria ter olhado commit
  que você não olhou. Conservador é o correto: um alarme a mais custa uma linha na tela; um a menos
  custa a próxima spec inteira.

Ao complementar capability existente, atualize o marcador **só sobre o que você de fato
reconciliou**. Cobriu duas sub-áreas de cinco? O marcador não avança — ele vale pelo domínio, e
avançá-lo por cima do que você não olhou apaga o sinal em vez de resolver o drift.

**Confiança baixa** (comportamento sem teste) ganha marca no próprio requisito:
`> ⚠ sem cobertura de teste — derivado só do código, não confirmado como intencional`.

**Buraco que você encontrou mas não resolveu** vai pra `## Dívida conhecida`, não some.

## Complementar: se a capability já existe

É por aqui que entra o domínio que a `spec` sinalizou como envelhecido — commits tocaram os `paths`
depois do `verificado-ate`. Nesse caso o alvo não é cobrir o que falta, e sim **percorrer o que
mudou**: comece pelos commits do range (`git log <verificado-ate>..HEAD -- <paths>`) e vá aos
requisitos que eles tocam.

Você **complementa**, nunca reescreve. Leia o que está lá, identifique o que não está coberto e
proponha só o delta. Requisito já registrado com `[Origem: spec-… · PR #…]` **não se toca** — ele
foi especificado e entregue, e sua derivação de código não tem autoridade pra corrigi-lo.

Se o código contradiz um requisito existente com origem de spec, isso é **achado**, não correção:
mostre ao usuário e deixe ele decidir. Pode ser regressão, pode ser mudança que nunca foi
sincronizada.

Rodar de novo não duplica: o que já está no arquivo é pulado.

## Auditar: revalidar o que já está escrito

Complementar acha o que **entrou**; nada acha o que **deixou de valer**. Requisito envelhece sem
deixar rastro nos `paths` — mudou uma dependência, mudou a config, mudou o domínio vizinho — e
continua no documento com toda a aparência de contrato. Auditar é o percurso inverso: **de cada
`C<N>` pra evidência que o sustenta hoje**.

**Só sob pedido explícito.** São N buscas dirigidas, uma por requisito; capability grande vira
sessão longa. Isto não roda "de passagem" durante um `complementar`.

### A ordem importa

1. **Os requisitos que os commits do range tocaram** (`git log <verificado-ate>..HEAD -- <paths>`),
   se houver marcador — é onde a chance de ter apodrecido é maior.
2. **Os de `[Origem: derivado]`** — ninguém nunca validou.
3. **O resto**, incluindo os de origem de spec.

Assim uma sessão interrompida no meio já entregou o mais provável. Diga sempre quantos faltam.

### Três estados, e nenhum deles é "corrigido em silêncio"

Para cada requisito, procure a evidência **atual** — teste primeiro, código depois, na mesma ordem
de confiança de sempre:

| Estado | O que você achou | O que fazer |
|---|---|---|
| **confirmado** | evidência sustenta o requisito e os cenários | atualize o `arquivo:linha` do `[Origem]` se ele mudou de lugar; nada mais |
| **contradito** | o comportamento hoje é outro | **achado** — mostre os dois textos lado a lado e deixe a decisão com o usuário |
| **órfão** | nada sustenta, nem teste nem código | **pergunta** — foi removido, foi renomeado, ou você não achou? |

Vale o mesmo lote de 3 a 5 de sempre — e aqui ele **paraleliza**: as buscas de evidência do lote
são independentes entre si, então dispare os `Explore` do lote inteiro **numa única mensagem** (em
mensagens separadas eles rodam em fila) e traga o resultado junto pro usuário decidir. Repita no
prompt de cada um a diretiva do `structure-cache`, e mande o requisito **como está escrito** —
subagente que recebe o comportamento resumido procura outra coisa.

**Os cenários apodrecem antes do requisito.** "DEVE recusar upload acima de 10 MB" continua
verdadeiro em espírito quando o limite virou 20 MB, e o `Quando → então` é que fica mentindo — e é
justamente ele que a `spec` do próximo ciclo lê como fato. Audite **cenário por cenário**, com o
número na mão, não o requisito no atacado.

### A origem decide o que você pode fazer com o achado

- **`[Origem: derivado …]`** — nunca foi validado por ninguém. Pode ser corrigido nesta sessão, com
  confirmação, e o `[Origem]` passa a apontar a evidência nova.
- **`[Origem: spec-X · PR #N]`** — comportamento especificado e entregue. **Não se toca.** Sua
  leitura do código não tem autoridade sobre um contrato: vira achado, e o usuário decide se é
  regressão (que é bug, e o destino é uma mudança) ou mudança que nunca foi sincronizada (que é
  `MODIFIED` de uma spec futura, não uma edição sua).

Essa é a mesma assimetria do `complementar` — aqui ela aparece requisito a requisito.

### Órfão confirmado não some, vira registro

Se o usuário confirmar que o comportamento foi mesmo removido, tire de `## Comportamento atual` e
registre em `## Removido` com a procedência que você tem de verdade:

```markdown
### C4 — Cupom acumulável (removido)
[Removido: auditoria de DD-MM-YYYY · sem evidência no código nem nos testes]
```

**Sem PR, porque você não tem um.** A auditoria descobre que sumiu; ela não sabe por qual mudança —
e inventar um PR aqui é falsificar rastro. O `C<N>` continua queimado, como sempre.

### Ao fim

O marcador (`verificado-ate`) **só avança se você auditou o domínio inteiro** — auditoria parcial
deixa metade da capability sem conferir, e avançar afirmaria o contrário. Se o usuário parou no
meio, diga que parou e que o domínio segue sinalizado.

Buraco que você tropeçar no caminho (comportamento sem `C<N>`) **anote, não escreva**: ele é assunto
do `complementar`. Ofereça a segunda passada ao terminar, com a lista do que viu.

## Ao terminar

**Derivando ou complementando** — mostre: quantos `C<N>` entraram, quantos ficaram de fora **e por
quê**, o que ficou como dívida, o que você não cobriu do domínio, e se o marcador
(`verificado-ate`) avançou ou não — se não avançou, diga que o domínio segue sinalizado como
envelhecido pra `spec`.

**Auditando** — o mesmo, pelos três estados, e o que sobrou aparece com o mesmo destaque do que
passou:

```
Auditado: checkout — 12 requisitos, 9 conferidos
  Confirmados: 9 (2 com [Origem] reapontado)
  Contraditos: 2 — C3 (limite 10 MB → 20 MB, derivado, corrigido)
                   C7 (origem spec-014 · PR #488 — NÃO tocado, decisão sua)
  Órfãos:      1 — C4 sem evidência, você confirmou removido → ## Removido
  Não auditados: 3 (você parou em 2FA) · marcador NÃO avançou
  Fora do escopo desta passada: 2 comportamentos sem C<N> — rode o complementar
```

Encerre lembrando a natureza do que foi escrito:

> Esta capability foi **derivada**, não especificada. Ela descreve o que o código faz hoje —
> incluindo o que talvez ninguém tenha decidido. Cada requisito que passar por uma mudança
> futura ganha origem de spec e vira contrato de verdade.

`thoughts/` é local e gitignored — **nunca commite**.
