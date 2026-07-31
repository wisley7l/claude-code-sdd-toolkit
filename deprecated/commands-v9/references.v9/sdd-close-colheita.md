# Reference: 🌾 Colheita do `/sdd-close`

Protocolo de **colheita**: o que sobrevive ao arquivamento do par SPEC+PLAN. Roda **só sob PR MERGED**, depois de arquivar os docs.

Duas fontes convergem no fechamento, e hoje as duas se perdem:

| Fonte | Onde morre hoje | Vira |
|---|---|---|
| Comentários de review com follow-up | ficam no PR, ninguém revisita | item em `backlog/` |
| Dívida de teste do pair (seção 6.6 do PLAN) | vai pra `plans/closed/` com o PLAN | item em `backlog/` |

A seção 6.6 do template do PLAN **já sugere** "item separado no roadmap" para lacunas pré-existentes — este passo é quem finalmente executa isso.

Contrato do item: reference `roadmap-item.md`.

## Princípio

**Proposta, nunca criação automática.** Tudo aqui vai pra tela e vira item só sob confirmação individual. Corte, prioridade e risco aceito são do usuário — o command detecta e recomenda, não decide.

Colheita vazia é resultado normal e frequente. Não force item de comentário ambíguo pra "ter entregado algo".

## Parte A — Follow-ups do review

### A1. Coletar

**A fonte principal é o body do review de aprovação.** O padrão mais comum na prática: o revisor
aprova o PR *e* deixa o follow-up no comentário final do review — às vezes marcado como opcional
("pode corrigir nesse PR se quiser"). Ou seja, a assinatura do follow-up é
**`state: APPROVED` com `body` não-vazio**, e isso é um sinal muito mais confiável que procurar
frases de adiamento em comentários soltos.

```bash
# 1º — reviews com texto (é aqui que o follow-up mora)
gh pr view <N> --json reviews \
  --jq '.reviews[] | select(.body != "") | {author: .author.login, state, body}'
```

Ordem de prioridade das fontes:

1. **Review com body** — sobretudo `APPROVED` (follow-up deliberado). `CHANGES_REQUESTED` com body normalmente foi resolvido *antes* do merge; confira no diff antes de tratar como pendência.
2. **Comentários inline** — o segundo lugar mais comum ("isso aqui dá pra melhorar depois"). Não vêm no `gh pr view`; exigem a API de review comments.
3. **Conversa geral do PR** — a menos densa, mas às vezes carrega o acordo final.

```bash
# 2º — comentários inline
gh api "repos/{owner}/{repo}/pulls/<N>/comments" --paginate \
  --jq '.[] | {user: .user.login, path: .path, line: .line, body: .body}'

# 3º — conversa geral + descrição
gh pr view <N> --json comments,body
```

Um review `APPROVED` com body **não** significa que está tudo resolvido — significa o oposto:
o revisor destravou o merge justamente porque decidiu não bloquear por aquilo. É dívida por
construção.

**Preferível quando disponível** — o GraphQL traz `isResolved`, que corta muito ruído:

```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!, $pr:Int!) {
    repository(owner:$owner, name:$repo) {
      pullRequest(number:$pr) {
        reviewThreads(first:100) {
          nodes {
            isResolved
            path
            comments(first:10) { nodes { author { login } body } }
          }
        }
      }
    }
  }' -F owner=<owner> -F repo=<repo> -F pr=<N>
```

Se o GraphQL falhar (permissão, schema), caia no REST e **diga que não há sinal de `resolved`** — aí toda thread entra na triagem manual.

### A2. Triar

**Sinais de follow-up** (trabalho reconhecido e adiado):
- **review `APPROVED` com body descrevendo trabalho** — o sinal mais forte, e o mais comum
- "opcional", "se quiser já corrige nesse PR", "não bloqueia, mas", "fora do escopo deste PR"
- "em outro PR", "próximo PR", "fica pra depois", "follow-up"
- "vamos tratar separado", "abrir issue pra isso"
- `TODO`/`FIXME` mencionado no comentário como pendência aceita

**Opcional-neste-PR é caso próprio.** Quando o revisor ofereceu corrigir no mesmo PR e o PR
mergeou **sem** a correção, é dívida real — mas nasce com severidade menor, porque o revisor
declarou que não bloqueava. Registre o item **dizendo isso**: sem essa marca, o item parece
que alguém ignorou um pedido do revisor, o que envenena a leitura do histórico. Se o PR mergeou
**com** a correção aplicada, não é dívida — confirme no diff antes de descartar.

**Não é follow-up:**
- comentário **já endereçado** no próprio PR (thread `isResolved` + houve commit depois)
- aprovação, elogio, discussão que terminou em "pode deixar assim"
- `nit:` puramente estilístico que o autor aplicou

**Thread resolvida ≠ tratada.** Resolvida porque o código mudou → feito, ignore. Resolvida com "beleza, vemos depois" → **é follow-up**. Essa distinção é a diferença entre colheita útil e ruído; quando não estiver claro pelo texto, mostre o comentário e pergunte.

**Bots** (dependabot, codecov, coderabbit e afins) vão numa lista **separada e marcada**. Volume alto, sinal irregular — o usuário decide se olha. Nunca misture com comentário humano.

### A3. Deduplicar

Antes de propor, varra `thoughts/roadmap/*/` por item que já cubra aquilo (título, slug, `Docs:`). Achou → **atualize o item existente** acrescentando a origem, não crie outro (*atualizar > criar*).

## Parte B — Dívida de teste do PLAN

Leia a seção **`6.6 Divida e risco aceito`** do(s) PLAN(s) sendo arquivados (e `6.4 Gaps`, se algum RF/AT ficou sem teste):

| Linha da 6.6 | Vira item? |
|---|---|
| **Casos cortados** | **Depende do motivo** — ver abaixo |
| **RF/AT sem teste** | Sim, se a tarefa nasceu `Tests: none` por prazo. Não, se por decisão de design |
| **Lacunas pré-existentes (fora de escopo)** | **Sim** — é literalmente o que a 6.6 sugere como item de roadmap |
| **Risco que sobra após este PR** | Normalmente **não** — é contexto, não trabalho. Só vira item se descrever ação concreta |

**Distinção que importa:** dívida **aceita como permanente** ("não acontece na prática") é uma *decisão*, não trabalho pendente — não vira item. Só vira item o que é *"queremos, mas não agora"*. O PLAN registra o motivo dado pelo usuário na 6.5/6.6 — use-o. Na dúvida, mostre o motivo original e pergunte.

Transformar toda dívida em item enche o backlog de coisa que ninguém vai fazer e destrói a confiança no roadmap.

## Parte C — Apresentar e criar

```
🌾 Colheita do PR #142 (<slug>)

Follow-ups do review:
  1. [inline · src/checkout/cart.ts:88 · @<autor>] "dá pra extrair isso, mas não bloqueia"
     → sugiro item: "Extrair cálculo de subtotal de cart.ts"
  2. [thread resolvida com "vemos depois" · @<autor>] "faltou o caso de cupom expirado no e2e"
     → já coberto pelo item [[014-e2e-cupom-expirado]] — atualizo a origem em vez de criar

Dívida de teste (PLAN seção 6.6):
  3. [lacuna pré-existente] "módulo de frete sem teste de integração"
     → sugiro item: "Teste de integração do módulo de frete"
  4. [caso cortado] "cupom expirado — motivo: não acontece na prática"
     → NÃO sugiro item: risco aceito como permanente pelo usuário

Bots (2 comentários, não triados): coderabbit ×2

  (s) criar os sugeridos    (e) escolher um a um    (k) pular a colheita
```

Ao criar, siga `roadmap-item.md`: `thoughts/roadmap/backlog/NNN-slug.md`, `NNN = max(existentes) + 1`, `pr:` vazio, `next: false`.

No corpo, registre a **procedência** e ligue ao item concluído que o originou:

```markdown
# NNN — Extrair cálculo de subtotal de cart.ts

**Depende de:** [[042-checkout-cupom]]
**Docs:** [[spec-1730123456-cupom-frete]] · [[PLAN-30-07-2026-042-checkout-cupom]]

Follow-up do review do PR #142 (comentário de @<autor> em src/checkout/cart.ts:88).
```

O `Depende de:` apontando pro item **já concluído** é intencional: a dependência está satisfeita, então o algoritmo de **🔓 Desbloqueados agora** lista o follow-up de imediato — ele nasce pronto pra ser pego — e o grafo do Obsidian mostra de onde ele veio.

Depois de criar, **regenere o hub** e recalcule os 🔓 (mesmo algoritmo do `roadmap-item.md`).

## Guardrails

- **Só sob PR MERGED.** Colheita de PR aberto é prematura — o comentário pode ser endereçado ainda no PR.
- **Confirmação individual.** Nunca crie item em lote sem o usuário ver cada um.
- **Nunca invente follow-up.** Comentário ambíguo → mostre e pergunte, ou deixe de fora. Ruído no roadmap custa mais que uma lacuna.
- **Dedup antes de criar.** Item existente é atualizado, não duplicado.
- **Risco aceito não é item.** Respeite a decisão registrada na 6.5/6.6 do PLAN.
- **Bot separado do humano.** Sempre marcado, nunca misturado.
- **`gh` falha (rede/rate limit)** → pule a colheita e diga isso no sumário. O arquivamento dos docs **não** depende dela.
- **Nunca commite** — `thoughts/` é local.
- **Nunca poste no PR.** A colheita lê comentários; não responde, não resolve thread, não comenta.
