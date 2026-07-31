# Créditos — skill `pr-close`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

**tlc-spec-driven** (tech-leads-club/agent-skills) por Felipe Rodrigues — **CC-BY-4.0**.
⚠️ Atribuição obrigatória e permanente, inclusive em adaptações reescritas.

O `/sdd-learning` v9 declarava no cabeçalho: *"Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe
Rodrigues — fecha o loop: implementação + review humano → aprendizado não-óbvio → memória
persistente."* O ciclo *fechar o loop com aprendizado destilado* vem de lá, e sobrevive no passo 5
desta peça e no `learning-filters.md`.

O `/sdd-close` (222L) e o reference `capability-template.md` são construção própria — a capability
viva com `C<N>` rastreável não tem equivalente em nenhuma fonte mapeada, inclusive o OpenSpec.

## ⚠️ Contratos de dados preservados (E.1 e E.2)

Esta peça toca **os dois** contratos ao mesmo tempo. Preservado verbatim:

**E.2 — Capability viva:**

| Invariante | Como sobreviveu |
|---|---|
| Escrita **só sob PR mergeado** | é o gate de entrada, e sem exceção |
| `C<N>` sequencial, nunca reusado — contando os removidos | mantido |
| Todo `C<N>` carrega `[Origem: <spec> · PR #N]` | mantido |
| `MODIFIED` **acrescenta** ao `[Origem]`, não substitui | mantido |
| `REMOVED` vai pra `## Removido`, nunca some | mantido |
| Edição cirúrgica com `Edit`, nunca reescrita do arquivo | mantido |
| `C<N>` inexistente = **parar e avisar**, nunca inventar | mantido |
| Idempotência: `[Origem]` já citando spec+PR → pula | mantido |
| Domínio novo só sob confirmação | mantido |

**E.1 — Roadmap:** a transição pra `concluido/` agora é `roadmap move`, o mesmo comando que a skill
`roadmap` usa. Foi o ganho da I.28: o v9 repetia o protocolo de mover arquivo + regenerar hub +
recalcular desbloqueados dentro do `/sdd-close`, e essa duplicação era candidata natural a divergir.

## O que mudou

- **Uma pasta, não um par.** O v9 arquivava SPEC e PLAN em `closed/` separados, com toda a
  complexidade de agrupar PLANs da mesma SPEC. Com I.12 (uma mudança = uma pasta), virou um `mv` de
  diretório. **A nuance multi-PR sobreviveu**, porque é real: a capability só é mesclada quando
  *todos* os slices mergearem — mesclar no primeiro afirmaria comportamento que existe pela metade.
- **`sdd-learning` (500L) absorvido.** Não virou peça própria: o gatilho é o mesmo ("o PR mergeou"),
  e separar cobraria custo de invocação sem ganhar nada (Parte C.4). Pedido explícito do usuário:
  *"vamos ter um comando para fechar o pr quando aprovado, dele vamos extrair os aprendizados e
  adicioná-los na memória do projeto e também fechar o domínio"*. Os 6 filtros duros foram pro
  `learning-filters.md`, lido pelo subagente — não pesam no contexto principal.
- **A colheita agora usa `roadmap add --dep <a mudança que fechou>`.** A dependência já satisfeita
  faz o follow-up nascer direto em 🔓 Desbloqueados, que é onde ele tem chance de ser visto. O v9
  já fazia isso; aqui é o comando que garante.

## Gap corrigido: o follow-up ficava invisível pro time

Pergunta do usuário depois de pronta: *"o pr-close alimenta a issue perene ou preciso fazer a
auditoria?"* — e a resposta era **não**, o que expunha uma contradição entre as duas peças.

O `pr-close` escrevia o follow-up **só** no `roadmap`, que vive em `thoughts/` — **gitignored**. E o
`pr-audit` denuncia exatamente essa situação como armadilha: *"backlog em diretório ignorado pelo
git significa 'visível só pra uma pessoa'"*. Ou seja: o fechamento produzia, por desenho, o problema
que a auditoria existe pra consertar — e o item só apareceria pro time quando alguém rodasse uma
varredura retroativa, refazendo a coleta já feita com o contexto quente.

Corrigido: a colheita oferece **os dois destinos**, com o significado de cada um explícito — o
roadmap é onde a prioridade se decide, a issue é o espelho público. Nem todo follow-up merece os
dois: o que é só do usuário não ganha nada indo pro radar do time, e um checklist vale pela
densidade.

O item publicado segue o **formato do `pr-audit` exatamente** (taxonomia de risco inclusive), pra a
próxima auditoria reconhecê-lo como rastreado em vez de reabri-lo. Publicar é ação outward-facing:
texto na tela e OK antes.

## I.7 resolvido — `fix` e `chore` na capability

Pendência aberta desde o começo do refactor. A régua é uma pergunta: **mudou o que o sistema
promete?**

- Bug fix que corrige comportamento observável → `MODIFIED`. O que estava na capability não era
  verdade, e continuar escrito é pior do que nunca ter estado lá.
- Refactor, dependência, build, formatação → não toca. Nada do que o sistema promete mudou.

Não é o tipo do commit que decide; é se o comportamento observável mudou.

## I.10 resolvido — o legado v9 em `thoughts/`

Das três opções (coexistir / migrar tudo / migrar só o aberto), ficou **coexistir**: fecha-se cada
mudança **no formato em que ela nasceu**. Par SPEC+PLAN antigo vai pra `specs/closed/` e
`plans/closed/`; o resto do fluxo — capability, roadmap, colheita, aprendizados — é idêntico.

Motivo: converter no fim do ciclo é risco sem ganho. A mudança está terminando, ninguém vai reler
aqueles arquivos, e um erro de conversão só apareceria muito depois. O formato novo vale pro que
nasce daqui pra frente.
