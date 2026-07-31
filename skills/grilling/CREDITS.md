# Créditos — skill `grilling`

> **Este arquivo não é carregado no contexto do agente.** Vive ao lado do `SKILL.md` e é
> deliberadamente **não referenciado** por ele, para que atribuição e notas de design não
> consumam contexto em runtime. É documentação pra humano e cumprimento de licença na
> distribuição — a skill é o diretório inteiro, então este arquivo acompanha qualquer cópia.

## Origem

Derivada de [`grilling`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)
por Matt Pocock — MIT © 2026 Matt Pocock.

Texto integral da licença: [`LICENSES/mattpocock-skills-MIT.txt`](../../LICENSES/mattpocock-skills-MIT.txt)

## O que veio do original

O núcleo e a formulação: entrevistar até entendimento compartilhado; percorrer cada branch da
árvore de decisão resolvendo dependências uma a uma; uma pergunta por vez, cada uma com
recomendação; fato o agente busca no ambiente, decisão é do usuário; não agir até haver
confirmação.

## O que é adaptação nossa

- Corpo em pt-BR.
- **"Discorde quando tiver motivo"** — sem atrito, a entrevista degenera em formulário.
- **"Cave onde for vago"** — "tanto faz" / "depois a gente vê" é branch aberto, não resposta.
- **Fechamento** com decisões tomadas + o que ficou deliberadamente em aberto.
- Escrita como *standing instructions* em vez de passos sequenciais, porque no Claude Code o
  conteúdo do `SKILL.md` entra no contexto uma vez e permanece pela sessão — receita numerada
  se perde depois do primeiro turno.

As três primeiras adições atacam a delegação excessiva que motivou o refactor v10
(ver `REFACTOR-v10.md`, Parte 0).

## Decisões de design

- **Sem `disable-model-invocation`.** A skill é invocável pelo modelo de propósito: o valor
  maior não é o usuário lembrar de pedir, é o agente puxar a skill quando percebe que ia decidir
  algo que é do usuário. Paga-se o context load da `description` por isso.
- **`grill-me` não foi criado.** No Claude Code toda skill já é `/`-invocável por default, então
  o par user-invoked do original seria duplicação. Os gatilhos ("me grelha", "grill me") entraram
  no `when_to_use`.
