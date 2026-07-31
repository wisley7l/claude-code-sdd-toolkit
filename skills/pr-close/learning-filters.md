# Destilação de aprendizados — filtros e formato

Você lê as fontes de um ciclo que acabou de mergear e devolve **candidatos a memória**, já
filtrados e classificados. Não escreve arquivo nenhum: quem decide é o usuário, depois.

O trabalho não é resumir o que aconteceu. É achar a **regra de comportamento** que faria a próxima
sessão agir diferente. Quase tudo o que você vai ler não é isso.

## Os seis filtros

Aplique **todos**. Falhou em qualquer um, descarte — sem propor, sem mencionar.

**1 · É reforço?** A nota faz alguém agir diferente numa próxima tarefa — evitar um erro ou repetir
um acerto? Fato histórico sem implicação de ação futura ("nesta feature usamos a lib X") não passa.
Este é o filtro mais importante: **não se captura fato, se captura regra.**

**2 · É transferível?** Vale só nesta feature e neste arquivo, ou o princípio se aplica a situações
parecidas? Amarrado a um caso que não se repete, descarte. Generalizável, capture o **princípio**
e o **gatilho**, nunca a instância.

**3 · É não-óbvio?** Sem esta nota, alguém que lê o código e o `git log` perderia algo? Cuidado com o
outro extremo: se a versão generalizada virou platitude ("teste antes de commitar"), também
descarte. Óbvio demais falha aqui.

**4 · Tem o porquê?** Sem motivo, ninguém sabe quando a regra se aplica nem quando abrir exceção —
e regra sem exceção conhecida vira superstição. Sem "por que", é ruído.

**5 · Não é redundante?** Já existe nota parecida na memória? Então proponha **atualizar** a
existente, não criar outra. Reforçar uma nota vale mais que ter duas.

**6 · Não está no commit nem no PR?** Se a mensagem de commit ou a descrição do PR já contam a
história, o `git log` resolve. **Exceção que importa:** o *comentário de review que apontou o erro*
não é "a história do PR" — a regra genérica extraída dele passa neste filtro, e costuma ser o
material mais valioso do ciclo.

## Onde olhar

| Fonte | O que costuma render |
|---|---|
| Comentário de review que pediu mudança | A regra que evita repetir — o melhor material |
| `notes.md`, seção de desvios | Onde o plano não bateu com a realidade, e por quê |
| `notes.md`, achados do review descartados | O que o usuário decidiu não fazer, e o motivo |
| `plan.md`, decisões técnicas | Escolha com trade-off que alguém vai querer refazer |
| Bug que custou tempo durante a execução | Sintoma reconhecível — vira `bug` |
| O que funcionou melhor que o esperado | Quase nunca anotado — vira `win` |

## Classificação

| Tipo | Quando |
|---|---|
| `bug` | Problema que já custou tempo e vai voltar — recuperável **pelo sintoma** |
| `feedback` | O usuário corrigiu ou confirmou um jeito de trabalhar |
| `decision` | Escolha técnica com trade-off, que alguém vai querer reabrir |
| `lesson` | Falha de processo, com o porquê |
| `win` | Deu certo e vale repetir de propósito |
| `project` | Contexto do projeto que o código não conta |
| `reference` | Ponteiro pra sistema externo |

Escolha pelo **gatilho** — quando aquilo vai ser útil de novo — e não pelo assunto. Na dúvida entre
dois, devolva os dois e deixe o usuário escolher; não caia em `feedback` por preguiça.

## O que devolver

JSON, e nada além dele:

```json
{
  "candidatos": [
    {
      "tipo": "bug",
      "slug": "webhook-timeout-sem-retry",
      "gancho": "quando o webhook de pagamento estourar ~30s sem retry",
      "conteudo": "<o princípio, 1-2 frases>",
      "why": "<a razão — quando a regra se aplica e quando abrir exceção>",
      "how_to_apply": "<a situação futura em que isso reaparece>",
      "fonte": "PR #512, comentário de @fulano em src/webhook/handler.ts:88",
      "atualiza": "<nome da nota existente, se for pra atualizar em vez de criar>"
    }
  ],
  "descartados": [
    { "resumo": "<o candidato, em uma linha>", "filtro": 3 }
  ]
}
```

Para `bug`, o `conteudo` traz **Sintoma / Causa raiz / Correção / Reconhecer de novo**. Para `win`,
traz **O que funcionou / Por que funcionou / Quando repetir**.

Devolver **zero candidatos é resultado legítimo e comum**. Um ciclo que correu bem e sem surpresa
não gera aprendizado, e inventar um só piora a memória de quem vai ler depois.

Conte os descartados com o número do filtro que barrou. É o que mostra ao usuário que a peneira
funcionou, em vez de parecer que ninguém procurou.
