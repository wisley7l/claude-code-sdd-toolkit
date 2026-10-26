# A régua de prosa

Vale pra todo texto que este toolkit escreve pro usuário ler e decidir — plano, spec, achado de
review, relatório, explicação de erro. O `format.md` ao lado é a versão especializada dela pra
página da triage; esta é a régua nua.

## A regra

**Afirmação técnica vem com a demonstração junto.** Não depois, não "se ele pedir".

Prosa técnica bem escrita *soa* verdadeira — e por isso ninguém a confere, nem quem lê nem quem
escreveu. O erro bobo não passa apesar da explicação densa: passa **por causa** dela. A densidade
é onde o erro se esconde.

```
❌ "Adiciona curl à allowlist com wildcard pra cobrir as variações."
   → tecnicamente correto, e faz escrever Bash(curl*), que não casa com nada.

✅ Bash(curl*)  não casa com `curl -s https://x`
   Bash(curl *) casa          ← o espaço antes do * é o que decide
```

A primeira frase está certa e leva ao erro. A segunda não deixa errar, porque põe as duas formas
lado a lado — e é aí que o espaço aparece.

## O que a demonstração esconde quando falta

Ela não deixa o texto só mais claro: ela revela **qual era o buraco**.

```
❌ "Optamos por centralizar a validação na camada de serviço, mantendo os controllers
   finos e garantindo que a regra seja aplicada independentemente do ponto de entrada."

✅ hoje — a regra vive no controller, e o job não passa por ele
     controller.ts   if (!cpf.valido) throw   ← só aqui
     importJob.ts    (nada)                   ← CPF inválido entra por aqui

   depois — a regra vive no serviço, os dois chamam
     service.ts      if (!cpf.valido) throw
     controller.ts   → service.criar()
     importJob.ts    → service.criar()        ← agora coberto
```

"Independentemente do ponto de entrada" **é o job**. A prosa sabia qual era o buraco e não contou.
Um plano assim é aprovado sem que o usuário veja que o job importava — e é assim que ele perde a
mão sobre o próprio produto.

## A forma muda conforme o texto

| Texto | A demonstração é |
|---|---|
| **spec** — comportamento | o caso concreto: entrada → saída esperada, com valores de verdade |
| **plan** — decisão técnica | **hoje × depois**, em código, e o que hoje não cobre |
| **review** — achado | o diff mínimo: as linhas que mudam, e nada mais |
| **relatório** — afirmação de gate | o comando que rodou e a saída dele |
| **erro** — diagnóstico | o traço: gatilho → sintoma, um passo por linha |
| **pergunta** — decisão dele | as saídas nomeadas pelo que acontece em cada uma, e a recomendação — ver "A pergunta" |

O que é igual nas seis: **nunca a afirmação sozinha.**

## O que não é a correção

**Cortar prosa não resolve.** Resposta curta e abstrata continua inútil — o oposto de "denso
demais" não é "curto", é **concreto**. A demonstração *substitui* a prosa, e de quebra ocupa menos
espaço que ela: as oito linhas de código acima dizem mais que os dois períodos que elas trocam.

**Resumir também não.** Resumo de explicação abstrata é explicação abstrata menor, com a mesma
chance de estar errada e menos superfície pra alguém perceber.

## Quando não dá pra demonstrar

**Diga "não verifiquei".** Uma linha, sem compensar com prosa.

É o *zero inferência* do toolkit aplicado ao texto: sem fonte, a afirmação não vira base de
decisão. A diferença entre "o job não valida CPF" e "não verifiquei se o job valida" é toda a
diferença entre um plano e um chute bem escrito.

## Valores concretos, não genéricos

- `[A, B, C]` e "remove A" — não "considere uma lista".
- `cpf = "111.111.111-11"` → `throw CpfInvalido` — não "entrada inválida gera erro".
- `12 → 17 testes` — não "a cobertura aumenta".
- `controller.ts:34` no pé, **nunca no meio da frase**: cada referência inline é uma decisão de
  abrir ou continuar lendo, e é o que trava a leitura.

## A pergunta

Vale pra toda pergunta que pede decisão dele — em texto ou em `AskUserQuestion`, em qualquer peça.
É o texto onde ele decide, e por isso é o que **menos** pode ser denso. Pergunta densa não é
respondida: é adivinhada, e a decisão volta pra você sem ele ter decidido nada.

**Quatro linhas, sempre juntas:** a escolha, o que acontece se A, o que acontece se B, a sua
recomendação. É a faixa de decisão do `format.md`, que vale pra todo lugar e não só pra página da
triage. Escolha sem as duas consequências escritas é a decisão devolvida sem material.

**Opção nomeada pelo que acontece no produto dele, não pelo mecanismo.** O mecanismo é o que você
precisa saber pra executar; a consequência é o que ele precisa saber pra escolher.

```
❌ "unit ou integração?"

✅ "testa só o cálculo — roda em um segundo, mas não pega o gateway caindo —
    ou testa com um gateway de mentira — dez segundos, e pega?"
```

**Dialeto do toolkit não vai pra tela sem explicação.** `abate`, `terreno`, `matriz`, `onda`,
`pilha`, `fronteira de corte`, `faixa de decisão`, `legwork`, `lente`, `contrato`, `delta`,
`capability` são nomes que este toolkit inventou pra conversar consigo mesmo. Não existem fora
daqui, e aprendê-los não serve pra ler o PR de ninguém. Na tela, ou a frase em português comum
toma o lugar do termo, ou o termo vem seguido da explicação em cinco palavras, na primeira vez em
que aparece na conversa.

```
❌ "O abate deixou 4 casos na matriz."
✅ "Dos 7 casos, 3 já existem no código — sobram 4 pra escrever."

❌ "PR 2 cai na onda 2."
✅ "PR 2 só abre depois que o PR 1 mergear."
```

Termo do **mercado** (`gate`, `flaky`, `fixture`, `e2e`) é diferente: fica como está, porque ele
quer aprender esses — mas segue a mesma regra na primeira vez da conversa, e vai pro glossário. O
glossário é pra depois; a pergunta precisa do significado agora.

**Referência e número só quando mudam a resposta.** `arquivo:linha` no pé, nunca na pergunta.
Contagem entra se é ela que decide (`14 arquivos`), e fora se é só precisão (`14 arquivos, 9
deles em src/`).

O conjunto, numa pergunta do `plan`:

```
❌ O bloco do PR 1 passa de 14 arquivos. Proponho a fronteira de corte em
   limite de camada: PR 1 fecha R1–R2, PR 2 fecha R3. Formam cadeia, então
   ofereço o modo stack. Segue num PR só ou corta?

✅ Esse PR ficou grande: 14 arquivos. Dá pra dividir em dois.
   - Dividir: o primeiro leva a regra de validação, o segundo leva a tela e
     o job. Cada review fica curto, mas o segundo só abre depois do primeiro
     mergear.
   - Um só: abre hoje, mas vira um review de 14 arquivos, do tipo que o time
     deixa pra sexta.
   Recomendo dividir.
```

A primeira versão está certa e é ilegível pra quem decide. A segunda diz as mesmas coisas — a
fronteira, a cadeia, a stack — sem usar nenhuma dessas palavras.

**O teste da pergunta:** ele consegue escolher sem abrir um arquivo e sem perguntar o que uma
palavra quer dizer? Se não, a pergunta ainda não está pronta.

## A pergunta que decide

Antes de entregar qualquer explicação técnica: **o leitor consegue conferir isto sem acreditar em
mim?**

Se a resposta é não, falta a demonstração — e o texto ainda não está pronto.
