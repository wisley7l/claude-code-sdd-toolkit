# Créditos — skill `pr-review`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

**Peça nova, sem antecessor no v9.** Todo o v9 — `sdd-review`, `pair-review`, `pr-ready` — assumia
que o PR era do usuário. Revisar código de terceiro nunca teve peça.

Sem atribuição de terceiros. O motor de análise é o `lenses.md` do `imp-review`, compartilhado por
referência em vez de copiado; a procedência daquele arquivo está em `skills/imp-review/CREDITS.md`.

## O pedido do usuário (31-07-2026)

> *"geralmente eu estou sendo requisitado pelo time para fazer review em PR feito por eles, então
> queria um comando/agente que me ajudasse com o review, mas que me desse um contexto do que o
> review se trata, pq as vezes eu posso ler o pr e acabar por não entender totalmente, dai precisa
> validar se o que eles prometeram cumprir esta de fato feito e se não há furos, bugs, falhas de
> seguranca e etc."*

Duas coisas nesse pedido não existiam em nenhuma peça do toolkit, nem no `/review` built-in: o
**briefing antes do julgamento**, e a **conferência de promessa contra entrega**.

## ⭐ Por que não virou modo do `imp-review`

Os dois testes de granularidade da Parte C passam, mas o que decide é que as peças se contradizem:

| | `imp-review` | `pr-review` |
|---|---|---|
| Papel | autor procurando o próprio furo | revisor de código alheio |
| Âncora | SPEC / `tasks.md` / `notes.md` locais | body do PR + issue vinculada |
| Review humano | contexto pré-existente, "não duplique" | você **é** o humano |
| Saída | "nunca comente no PR" | o comentário é o produto |

A regra mais dura do `imp-review` — jamais escrever no PR — passaria a valer em metade do arquivo.
Isso é o failure mode **Negation** somado a condicional em quase toda seção.

## ⭐ Briefing antes de qualquer achado

O ponto que o usuário levantou e que todo reviewer automático erra, incluindo o `/review` built-in:
abrir direto no achado. Um revisor que não entendeu a mudança não consegue julgar se o achado é
achado.

A fase 1 é explicitamente proibida de reportar problema. Ela produz o que o diff não dá: o que o PR
promete, o que ele de fato toca, **por onde ler**, o que muda para quem chama, e — o mais
importante — **o que o agente não conseguiu determinar**, declarado em vez de virar achado com
confiança inventada. Foi a preocupação literal dele: *"talvez o agente entenda errado por não ter o
contexto 100%"*.

## ⭐ "Não prometido" como estado de primeira classe

A tabela da fase 2 tem quatro estados, e o quarto é o que justifica a fase. Entregue / parcial /
não encontrei são conferência normal. **Não prometido** — comportamento que entrou de carona sem
ninguém anunciar — é o que ninguém procura, porque revisor confere a lista que recebeu.

## ⭐ Sabatina antes do veredito, não depois

Veio dele: *"pode até usar o grill-me pq a gnt decidir o que faz sentido se vamos aprovar pr com
algum furo"*.

Ficou como **seção própria**, não como invocação da skill `grilling` — decisão tomada na conversa.
A `grilling` é genérica para "plano, decisão ou ideia"; chamada crua aqui renderia pergunta
genérica. A seção herda a disciplina inteira (uma pergunta por vez, sempre com recomendação, fato
se busca / decisão é do usuário, discordar uma vez e registrar) aplicada às quatro decisões que um
review de verdade tem: bloqueia ou vira follow-up, o padrão é aceito no time, quanto de porquê o
autor precisa, e o que ficou aberto na fase 1.

A ordem importa: achados na mão **antes** da sabatina, senão não há sobre o que decidir.

## ⭐ Inline obrigatório, submit review único

Regra do usuário, textual: *"reviews geralmente solicitações de alteração precisam ser inline pra
ajudar quem esta fzndo a tarefa, e quando enviar o review sempre em submit review."*

Consequências técnicas que moldaram três seções do `SKILL.md`:

- **`gh pr review` não serve** — só posta corpo geral, sem inline. É a REST API
  (`POST /repos/{owner}/{repo}/pulls/{N}/reviews`) com array `comments[]`, um único POST.
- **O schema do `lenses.md` devolve `arquivo:linha` como string única** — precisa quebrar em `path`
  e `line` ao consolidar.
- **Achado sem âncora no diff faz o POST inteiro falhar (422)** — daí a separação em dois baldes já
  na fase 3, e o fallback de mover para o corpo quando o 422 vem.
- **`commit_id` fixado no `headRefOid`** capturado no início: se o autor pushou no meio da revisão,
  o POST falha em vez de ancorar comentário em código que mudou de lugar.

## Preview editável antes do POST

Também dele: *"depois do veredito ai me mostra uma msg que sera postada podendo eu pedir para
alterar ou não"*.

É a única escrita externa do toolkit inteiro, e escrita no repositório de outra pessoa. Vale a
parada obrigatória: tudo na tela — veredito, corpo, cada inline com seu `arquivo:linha` — e quantas
rodadas de ajuste o usuário quiser antes do POST. Serve ao invariante "usuário no volante" da
Parte E.5 no ponto onde ele é mais caro de violar: comentário público no PR de um colega não tem
desfazer social.

## Invocação

`disable-model-invocation: true`. Peça que escreve no GitHub, no repositório de terceiro, não deve
ser alcançável autonomamente — o custo de um disparo indevido é externo e irreversível. Paga
cognitive load, que é o custo certo aqui.

## Reaproveitado sem alteração

`lenses.md` do `imp-review`, cru. Ele já abre com *"Você não implementou este código: avalie do
zero, sem supor que as decisões foram tomadas por boa razão"* — escrito na voz do revisor externo
antes de existir um. Nenhuma menção a SPEC ou artefato SDD local.

Compartilhado por caminho relativo (`${CLAUDE_SKILL_DIR}/../imp-review/lenses.md`) em vez de
copiado. Duas cópias das mesmas seis lentes divergiriam na primeira correção. Se surgir uma
terceira peça consumidora, vale promover o arquivo a lugar neutro.
