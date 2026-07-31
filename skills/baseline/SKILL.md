---
name: baseline
description: Deriva a capability viva de um domínio a partir dos testes e do código existentes — a linha de base do que o sistema já promete hoje. Trabalha por lotes, sob confirmação. Use quando um domínio ainda não tem capability, ao adotar o toolkit num projeto com código, ou pra entender um domínio herdado.
disable-model-invocation: true
argument-hint: <domínio | área que você quer mapear>
allowed-tools: Read Grep Glob Write Edit Agent Bash(ls *) Bash(mkdir *) Bash(git log*) Bash(git worktree list*) Bash(structure-cache *) Bash(structure-cache)
---

# baseline

Escreve a **capability viva** de um domínio — `thoughts/capabilities/<domínio>.md`, o documento
que responde "o que o sistema faz hoje aqui" — derivando do que já existe no repositório.

Existe porque a capability normalmente só nasce no fechamento de uma mudança, sob PR mergeado.
Num projeto com código anterior ao toolkit, isso significa que ela **nunca cobre o que já estava
lá** — e a `spec` do próximo ciclo marca `ADDED` o que na verdade é `MODIFIED`, envenenando o
delta desde o primeiro ciclo.

**Não documente o codebase inteiro.** Um domínio por vez, e de preferência o domínio que você
está prestes a mexer. Capability incompleta é normal e útil; capability errada é pior que
nenhuma, porque vira fonte de verdade pro ciclo seguinte e propaga o erro.

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

**Confiança baixa** (comportamento sem teste) ganha marca no próprio requisito:
`> ⚠ sem cobertura de teste — derivado só do código, não confirmado como intencional`.

**Buraco que você encontrou mas não resolveu** vai pra `## Dívida conhecida`, não some.

## Se a capability já existe

Você **complementa**, nunca reescreve. Leia o que está lá, identifique o que não está coberto e
proponha só o delta. Requisito já registrado com `[Origem: spec-… · PR #…]` **não se toca** — ele
foi especificado e entregue, e sua derivação de código não tem autoridade pra corrigi-lo.

Se o código contradiz um requisito existente com origem de spec, isso é **achado**, não correção:
mostre ao usuário e deixe ele decidir. Pode ser regressão, pode ser mudança que nunca foi
sincronizada.

Rodar de novo não duplica: o que já está no arquivo é pulado.

## Ao terminar

Mostre: quantos `C<N>` entraram, quantos ficaram de fora **e por quê**, o que ficou como dívida,
e o que você não cobriu do domínio. Encerre lembrando a natureza do que foi escrito:

> Esta capability foi **derivada**, não especificada. Ela descreve o que o código faz hoje —
> incluindo o que talvez ninguém tenha decidido. Cada requisito que passar por uma mudança
> futura ganha origem de spec e vira contrato de verdade.

`thoughts/` é local e gitignored — **nunca commite**.
