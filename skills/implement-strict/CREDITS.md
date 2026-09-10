# Créditos — skill `implement-strict`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

Deriva do `implement`, e portanto herda a atribuição dele:

**tlc-spec-driven** (tech-leads-club/agent-skills) por Felipe Rodrigues — **CC-BY-4.0**.
⚠️ Atribuição obrigatória e permanente, inclusive em adaptações reescritas.

Conceitos que chegaram por essa linhagem e continuam aqui:

- **Test count protection** — contagem que cai é parada dura, não algo a consertar sozinho.
- **Gate explícito por tarefa** — comando de verificação declarado, não inferido.
- **Subagente paralelo para tarefas independentes** — aqui em pares (teste, código) por tarefa.

**Red verificável e falso-verde como parada dura** são construção nossa, sem equivalente nas fontes
mapeadas (Parte E.5 do `REFACTOR-v10.md`).

## O que é novo nesta peça

Nada disto veio de fonte externa — saiu da conversa de 02-09-2026:

- **Papéis separados por especialidade**, não por tarefa. O `implement` dá a tarefa inteira a um
  subagente; aqui o ciclo é cortado no meio, e a fronteira é verificada no `git diff --name-only`.
- **O red volta a ser executado pelo orquestrador.** No `implement` isso é impossível (o código já
  existe quando o retorno chega, e desfazer custaria a execução — decisão I.18). Aqui, no momento
  do handoff a produção ainda não existe, então o falso-verde deixa de ser relato verificado na
  forma e volta a ser fato observado. É o ganho principal da variante.
- **O esqueleto como fronteira do test-writer** — assinatura do contrato mais `não implementado`, e
  nada além. Resolve a colisão entre "TDD à risca" e "falha por import não é red": sem esqueleto, o
  primeiro red de um módulo novo é `cannot find module`, indistinguível de caminho errado.
- **O ambiente é do orquestrador, declaradamente.** Worker que pode subir server é worker que
  retenta contra porta morta; o status `ambiente-caiu` existe pra o worker devolver na primeira
  falha de conexão em vez de insistir.
- **Contrato travado antes do primeiro teste.** Sem isso o test-writer fixaria a API por via
  indireta — escrever `calcRefund(order, amount)` é escolher nome, aridade e retorno.

## Decisões do usuário (02-09-2026)

Quatro escolhas dele, todas registradas em I.43 do `REFACTOR-v10.md`:

- **Handoff por tarefa**, não em bloco. Ciclo curto, red verificado tarefa a tarefa; a alternativa
  ("todos os testes, depois todo o código") acumularia suposições de API contra código inexistente.
- **Ambiente pelo orquestrador puro**, sem script e sem agente dedicado. Ele preferiu não pagar o
  custo de um `env.sh` por projeto agora; a consequência assumida é que a lógica de subir, vigiar e
  detectar queda vive em prosa no `SKILL.md`.
- **Contrato fixado antes**, vindo do plano. Como o `tasks.md` de hoje não tem o campo, a peça
  deriva e trava com o usuário numa pergunta só.
- **Peça separada chamada `implement-strict`.** Eu recomendei `tdd` — leading word compacta e
  pré-treinada, livre no toolkit, alinhada com a Parte C. Ele escolheu `implement-strict` mesmo
  depois do apontamento de que o sufixo descritivo é o mesmo vício que matou o `sdd-*` no v9. É a
  decisão dele e está registrada como tal; se o nome incomodar no uso, renomear é trivial (a peça é
  user-invoked, ninguém depende do gatilho automático).

## Não é substituta

As duas peças coexistem por escolha explícita, e a Parte C.4(a) autoriza: gatilho próprio, custo
próprio. `implement` é o default de rotina; `implement-strict` custa dois handoffs por tarefa e
paga isso onde a disciplina do teste importa mais que a velocidade — refactor delicado, área que já
falso-verdejou, teste que tende a nascer amaciado.

Isso **não** contradiz a decisão I.17 (que matou os dois modos dentro do `implement`): lá era um
arquivo com ~150 linhas duplicadas pra uma diferença de duas coisas. Aqui são dois arquivos
independentes, com protocolos de subagente diferentes, e a duplicação que existe é a de invariantes
que precisam valer nos dois de qualquer forma.

## O review saiu daqui

Igual ao `implement`: `imp-review` é peça própria, invocada pelo usuário (I.23, I.27). O orquestrador
termina pedindo, não invocando.
