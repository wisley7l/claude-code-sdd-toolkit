# REFACTOR v10 — reconstrução do toolkit, um comando por vez

> **Status:** v9 inteiro deprecado. Este arquivo é o único artefato ativo do repo até a
> reconstrução começar. Ele é o mapa: o que existia, o que vale recriar, o que vale matar,
> e o que NÃO pode ser recriado sem preservar contrato de dados.
>
> **Temporário.** Morre quando a fila da Parte D estiver vazia e o novo README existir.

---

## 0. Por que

Diagnóstico que motivou o refactor (30-07-2026):

1. **Delegação demais, entendimento de menos.** O pipeline v9 produz artefatos prontos e pede
   aprovação. Custo de dizer "ok" = zero; custo de discordar de 300 linhas coerentes = alto.
   Isso gera a *sensação* de entender, não o entendimento.
2. **Metade do toolkit é maquinário de recuperação.** `/pair-review` (re-hidrata contexto),
   `/sdd-close` (colhe o que ficou pendente), `/pr-followup-audit` (resgate retroativo de dívida),
   `/sdd-learning` (extrai aprendizado do que passou). ~1.100 linhas cuja razão de existir é que
   o pipeline principal vaza. A resposta foi construir mais recuperação em vez de não perder.
3. **Diferença de gênero, não de verbosidade.** As skills da referência têm 10–40 linhas.
   `executor-plan.md` tem 736. Um artefato de 736 linhas é um *processo* que roda sozinho e
   devolve resultado — não sobra decisão pra tomar, já está tudo decidido no markdown.
   10 linhas é uma *postura* que se aplica com a mão no volante.
4. **`sdd-` não é leading word.** Prefixo inventado, não ancora nada no modelo. Ver Parte C.

**Referências consultadas** — são **referência, não adoção**. Avaliamos ideia por ideia e usamos
só o que fizer sentido pro nosso caso:

1. [mattpocock/skills](https://github.com/mattpocock/skills) — MIT © Matt Pocock. Peças pequenas,
   componíveis, feitas pra serem hackeadas; usuário decide, agente busca fato. Ver Parte B.
2. [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) — MIT © OpenSpec Contributors.
   Mesmo problema que o nosso, resolvido de forma mais madura: delta specs, archive que mescla,
   CLI determinístico, workflow fluido em vez de phase-locked. Ver **Parte H**.
   **Não é dependência** — não instalamos nem redistribuímos o pacote.

**Regras do refactor:**

1. **Um comando por vez**, revisado antes de nascer. Nada de port automático.
2. Cada peça nova **justifica sua existência contra a Parte C**.
3. **Toda ideia de fora é atribuída.** Antes de escrever qualquer peça, ler o protocolo de
   atribuição em [`NOTICE.md`](./NOTICE.md) e fechar com o bloco `## Créditos`.
   ⚠️ Vários conceitos do v9 vêm de fonte **CC-BY-4.0** (atribuição obrigatória e permanente,
   inclusive em adaptações) — deprecar o arquivo v9 **não** extingue a obrigação.

---

## PARTE A — Inventário v9 (o que foi deprecado)

24 commands + 4 skills + 17 references = **9.283 linhas** de markdown.

Legenda do veredito (recomendação inicial, **não decidido** — a coluna Decisão é sua):

- `RECRIAR` — a função é boa, a forma não. Nasce de novo, menor, com o usuário no volante.
- `AVALIAR` — pode não precisar existir no modelo novo. Discutir antes.
- `MANTER` — não é parte do problema; porta quase como está.
- `MATAR` — a função desaparece no modelo novo.
- ⚠️ — **tem contrato de dados vivo.** Não recriar sem ler a Parte E.

### A.1 — Núcleo do pipeline (onde o problema mora)

| Command | L | O que faz | Equivalente na ref. | Veredito | Decisão |
|---|---|---|---|---|---|
| `sdd-spec` | 279 | SPEC de comportamento (o QUÊ): histórias, critérios, RFs, testes de aceitação. Capability-first, marca delta (`ADDED`/`MODIFIED`/`REMOVED`). `--explore` pesa direções sem escrever. | `to-spec` | RECRIAR — a fase de descoberta vira `grilling`; a SPEC vira transcrição da decisão, não proposta da IA | |
| `sdd-plan` | 639 | Plano técnico (o COMO): pesquisa + tarefas TDD auto-sized. Pair de testes interativo (passo 7.5) + 5 checks + registra no roadmap. | `wayfinder` + `to-tickets` | RECRIAR quebrado em 2–3 peças. **O pair de testes é o melhor pedaço do v9** — é o único ponto onde a IA propõe e você corta. É o modelo a generalizar, não a descartar | |
| `sdd-plan-eco` | 44 | Variante econômica do acima (main Sonnet, quebra em subagente Opus). | — | MATAR — se a peça nova é pequena, não precisa de variante econômica | |
| `executor-plan` | 736 | TDD autônomo **sem pausa entre tarefas**, staging por tarefa, red verificável, review interno, validador Haiku. `--step` ativa pausas. | `implement` + `tdd` | RECRIAR quebrado em 2. **Maior fonte do problema.** Perguntas abertas: por que `--step` não é o default? o review interno sobrevive? | |
| `quick-task` | 364 | Mudança pequena (≤3 arquivos) sem SPEC/PLAN. Modos invocados por `/sdd-review` que só fazem `git add`. | — | AVALIAR — 364 linhas pra "não usar cerimônia" é auto-contraditório. Pode virar o default sem command | |
| `sdd-review` | 373 | Review autônomo de PR/branch/diff via subagents, relatório em `thoughts/reviews/`. | `code-review` | RECRIAR menor | |
| `pair-review` | 157 | **Re-hidrata** do staged + PLAN/IMP em sessão nova; subagentes Opus focados; valida fixes contra comentário humano. | — | AVALIAR/MATAR — existe porque você não estava lá. Se o `implement` novo te mantém no loop + `handoff` existir, a função evapora | |
| `pr-ready` | 251 | Entrega ponta a ponta: avalia → **loop de correção até convergir** → gate de verde → commit/push humano → sync do body. | — | AVALIAR — "loop até convergir" é o vício em forma pura. O **gate de verde** (CI/suíte completa) é bom e deve sobreviver em algum lugar | |
| `pr-draft` | 310 | PR em draft a partir do plano: branch, empty commit, title/body da SPEC, worktree. `sync` reescreve o body depois. | — | ⚠️ RECRIAR menor — promove item no roadmap (Parte E.1) | |

### A.2 — Fechamento de ciclo (⚠️ todos tocam dados vivos)

| Command | L | O que faz | Veredito | Decisão |
|---|---|---|---|---|
| `sdd-close` | 222 | 4 atos sob PR **mergeado**: arquiva SPEC+PLAN → mescla delta na capability viva (`thoughts/capabilities/`) → colhe follow-ups de review + dívida de teste pro backlog → conclui item do roadmap e recalcula 🔓. | ⚠️ RECRIAR — toca capability viva (E.2) **e** roadmap (E.1). Sem equivalente na ref.; é diferencial nosso | |
| `pr-followup-audit` | 341 | Varre N PRs mergeados, extrai o que revisores levantaram, verifica `arquivo:linha` se ainda vive, alimenta **issue perene** no GitHub. Triagem + ordem de urgência por natureza do risco. | ⚠️ RECRIAR — issue perene já existe em repos reais (E.3). Sem equivalente na ref. | |
| `sdd-learning` | 500 | Extrai reforço comportamental de IMPs/reviews/comentários de PR; generaliza instância em princípio+gatilho; propõe registro no auto-memory. | ⚠️ RECRIAR muito menor — escreve memória (E.4). 500 linhas pra "anota o que aprendeu" é sediment | |
| `roadmap` | 218 | Gerencia o vault Obsidian: adiciona itens, liga dependências, sincroniza por PR, migra formato antigo. | ⚠️ RECRIAR — **vault vivo em projetos reais** (E.1). Parente na ref.: `to-tickets` | |
| `memory-organize` | 488 | Reorganiza auto-memory: órfãs, duplicatas, links quebrados, sub-sumários quando MEMORY.md cresce. Modo `revisar` reescreve conteúdo de instância→princípio. | ⚠️ AVALIAR — 488 linhas de manutenção de índice. Sinal de que o formato de memória é caro demais (E.4) | |

### A.3 — Pesquisa e diagnóstico

| Command | L | O que faz | Equivalente | Veredito | Decisão |
|---|---|---|---|---|---|
| `investiga` | 110 | Root cause de bug não-óbvio: hipóteses com mecanismo causal → evidência em subagents paralelos → causa com fonte → handoff. | `diagnosing-bugs` | RECRIAR — já é pequeno e bom. Comparar com o protocolo da ref. (reproduce → isolate → hypothesize → test → verify) | |
| `busca` | 234 | Busca via subagent isolado (Haiku/Sonnet/Opus), inline + opt-in salvar em `thoughts/research/`. | `research` | RECRIAR menor | |
| `verifica` | 90 | Verificação **comportamental**: roda o app, exercita os fluxos tocados, anexa evidência ao IMP. Nunca produção. | — | MANTER conceito — sem equivalente na ref. e resolve o buraco real entre "testes verdes" e "funciona" | |
| `complexidade` | 101 | Complexidade ciclomática só nos arquivos alterados (via `lizard`), threshold configurável, `--fix` oferece refactor. | `codebase-design` / `improve-codebase-architecture` | AVALIAR — pode virar parte de code-review | |

### A.4 — Git e infraestrutura (não são o problema)

| Command | L | O que faz | Veredito |
|---|---|---|---|
| `git-worktree` | 144 | Cria worktree da branch default, ativa MODO LIVRE nela por default; `--ml-off` desliga. Cria symlink de memória. | MANTER |
| `git-remove-worktree` | 121 | Remove worktree checando mudanças não commitadas; faz `unlink` do symlink de memória (nunca `rm -rf`). | MANTER |
| `git-rebase-seguro` | 89 | Baseline de testes → rebase → conflitos sob confirmação → test count protection → rollback garantido. Nunca force-pusha. | MANTER — parente: `resolving-merge-conflicts` |
| `git-prune-branches` | 55 | Remove branches locais cujas remotas sumiram. | MANTER |
| `worktree-detect` | 247 | Analisa branches/PRs abertos e sugere isolamento em worktrees. | AVALIAR — 247L pra uma heurística |
| `sync-tests` | 159 | Sincroniza `thoughts/tests/` entre worktree e root com diff antes. | AVALIAR |
| `modo-livre` | 294 | Toggle do modo autônomo: instala settings (allow + ask pra commit/push + deny dos perigosos), `off` restaura backup. | MANTER — parente na ref.: `git-guardrails-claude-code` (hooks que bloqueiam git perigoso). Vale comparar as duas abordagens |
| `status-deps` | 119 | Status de Cloudflare/GitHub/PlanetScale/AWS via status pages. Read-only. | MANTER — isolado, sem acoplamento |
| `pr-report` | 389 | Relatório de PRs do usuário: semanal (inline) / mensal / anual (salva). | MANTER — isolado |
| `sdd-init` | 106 | Audita e prepara projeto-alvo (CLAUDE.md, ARCHITECTURE.md, thoughts/, Context7, references). | RECRIAR — parente: `setup-matt-pocock-skills`. Só faz sentido no fim, quando o novo conjunto existir |

### A.5 — Skills

| Skill | L | O que faz | Veredito |
|---|---|---|---|
| `memory-keeper` | 285 | Contrato do auto-memory: 9 tipos, convenção flat, `MEMORY.md` como índice-tabela, princípio+gatilho. | ⚠️ RECRIAR preservando formato (E.4) |
| `structure-cache` | 59 | Grafo de dependências (quem importa X, blast radius) via cache invalidado por hash. TS/JS. Tem `scripts/` + hooks. | MANTER — ferramenta real, não prompt |
| `conciso` | 160 | Modo de resposta conciso pt-BR, 3 níveis, persiste na sessão. | MANTER |
| `deprecated/` | — | `memory-keeper.v1`, `vault-memory` | intocado |

### A.6 — References (progressive disclosure)

17 arquivos em `commands/references/` (~2.000L). Existem porque os commands ficaram grandes demais.
**No modelo novo, references só se justificam se a skill continuar grande** — se a reconstrução der
certo, a maioria some junto com o command que a carregava.

Os que carregam **contrato**, não só template (esses sobrevivem em alguma forma):
- `roadmap-item.md` (142L) — ⚠️ formato do vault, ver E.1
- `capability-template.md` (126L) — ⚠️ formato da capability viva, ver E.2
- `sdd-plan-testes.md` (311L) — protocolo do pair de testes (o melhor pedaço do v9)

Os demais são template de output: `sdd-plan-plan-template`, `sdd-spec-template`, `sdd-spec-explore`,
`sdd-close-colheita`, `sdd-review-relatorio`, `sdd-review-action-plan`, `executor-plan-review`,
`executor-plan-validador`, `executor-plan-imp`, `sdd-plan-panel-review`, `pr-report-{semanal,mensal,anual}`,
`memoria-symlink`.

### A.7 — Não deprecado (código executável, não prompt)

`scripts/` ficou **intocado** de propósito: `structure-cache/` (build.py + hooks + installer) e
`ouvir` estão **instalados no PATH e referenciados por `.claude/settings.local.json`**. Mover
quebraria o ambiente fora do repo. Decisão de mexer neles é separada e posterior.

---

## PARTE B — Mapa da referência (mattpocock/skills)

O que existe lá, o que faz, e utilidade pra nós. **Nada é porte automático** — é catálogo pra
decidir peça por peça.

### B.1 — productivity (5)

| Skill | Invocação | O que faz | Utilidade pra nós |
|---|---|---|---|
| **`grilling`** | modelo/usuário | Entrevista relentless sobre plano/decisão/ideia. Percorre cada branch da árvore de decisão, resolvendo dependências uma a uma. **Uma pergunta por vez**, cada uma com recomendação. **Fato que dá pra descobrir no ambiente, o agente busca; decisão é sua.** Não age até você confirmar entendimento compartilhado. | ⭐ **Peça central do v10.** É a inversão que resolve o diagnóstico da Parte 0. Cabe em ~8 linhas |
| **`grill-me`** | usuário (`disable-model-invocation: true`) | 3 linhas: dispara `/grilling`. | Atalho — mostra o padrão "user-invoked fino sobre model-invoked gordo" |
| **`handoff`** | usuário | Compacta a conversa num doc pra outro agente continuar. Salva no **tmp do SO, não no workspace**. Inclui seção "suggested skills". **Não duplica o que já está em spec/plan/ADR/issue/commit/diff — referencia por path.** Redige segredos. Aceita argumento = foco da próxima sessão. | ⭐ Resolve o buraco que `/pair-review` (157L) tenta tapar por trás. Passar contexto adiante > reconstruir depois |
| **`teach`** | usuário | Ensina um conceito ao longo de várias sessões usando o diretório como workspace stateful: `MISSION.md` (por que quer aprender), `reference/*.html` (cheat sheets), `RESOURCES.md`, `learning-records/*.md`, `lessons/*.html`, `NOTES.md`. Princípios: nunca confiar em conhecimento paramétrico, desirable difficulty, retrieval practice, storage strength > fluência. | Endereça o "entendendo de menos" pela raiz. Mais ambicioso — avaliar depois do núcleo |
| **`writing-great-skills`** | usuário | Referência de como escrever skill: vocabulário + princípios. | ⭐ **É o guia de estilo do v10.** Resumo na Parte C |

### B.2 — engineering (17)

**User-invoked:**

| Skill | O que faz | Utilidade |
|---|---|---|
| `ask-matt` | Roteia pra skill/workflow certo dada a situação. | Alto — com N skills pequenas, "qual eu uso agora?" vira problema real (cognitive load) |
| `grill-with-docs` | Sessão colaborativa que desenvolve modelo de domínio e atualiza a documentação. | Alto — parente do nosso `capabilities/` (spec viva) |
| `triage` | Gerencia issues através de uma **state machine** definida. | Médio — comparar com `/roadmap` (nosso status = pasta) |
| `improve-codebase-architecture` | Identifica oportunidades arquiteturais e apresenta os achados visualmente. | Médio — parente de `/complexidade` + `structure-cache` |
| `to-spec` | Transforma a discussão em curso em documento de especificação. | ⭐ Substituto direto do `/sdd-spec`. Nota a direção: **da discussão pro doc**, não do doc pra aprovação |
| `to-tickets` | Converte planos em itens de trabalho rastreados **com dependências**. | ⭐ Parente direto do `/roadmap` (⚠️ E.1) |
| `implement` | Executa trabalho a partir de especificações usando TDD. | ⭐ Substituto do `/executor-plan` |
| `wayfinder` | Planeja iniciativas grandes como **mapa de decisões resolvido incrementalmente**. | ⭐ Substituto do `/sdd-plan`. "Mapa de decisões" ≠ "documento de tarefas" — é a diferença inteira |

**Model-invoked:**

| Skill | O que faz | Utilidade |
|---|---|---|
| `tdd` | Ciclo red-green-refactor. | ⭐ Extrair do `executor-plan`. **Preservar nosso red verificável** (E.5) |
| `imp-review` | Avaliação de dupla perspectiva: padrões + aderência à spec. | ⭐ Substituto do `/sdd-review` |
| `diagnosing-bugs` | reproduce → isolate → hypothesize → test → verify. | Alto — comparar com `/investiga` |
| `research` | Investiga tópicos com fontes confiáveis e documenta. | Alto — substituto do `/busca` |
| `prototype` | Implementação **descartável** pra validar decisão de design. | Alto — não temos. Cobre o buraco entre `--explore` e implementar de verdade |
| `domain-modeling` | Constrói e refina modelos conceituais com documentação. | Médio |
| `codebase-design` | Princípios de design modular com interfaces claras. | Médio |
| `resolving-merge-conflicts` | Resolve conflitos intencionalmente, sem abandonar. | Baixo — temos `/git-rebase-seguro` |

### B.3 — misc (4)

`git-guardrails-claude-code` (hooks que bloqueiam git perigoso — **comparar com `/modo-livre`**),
`setup-pre-commit` (Husky + lint-staged), `migrate-to-shoehorn` (específico TS), `scaffold-exercises`.

### B.4 — Filosofia declarada

- **Alignment first** — alinhar antes de codar; "No-one knows exactly what they want".
- **Shared language** — vocabulário de domínio em `CONTEXT.md` (parente do nosso `capabilities/`).
- **Feedback loops** — "The rate of feedback is your speed limit".
- **Deliberate design** — arquitetura intencional contra a entropia.
- **Composability & control** — skills pequenas, model-agnostic, **feitas pra serem hackeadas, não um processo rígido**.

Rejeita explicitamente abordagens "vibes-based" **e** totalmente automatizadas.

---

## PARTE C — Regras do v10 (do `writing-great-skills`)

Critério de aceitação de toda peça nova. Se não passa, não nasce.

### Vocabulário

- **Leading word** — conceito compacto e **pré-treinado** que ancora comportamento e invocação.
  `tdd`, `triage`, `research`, `implement`, `handoff`, `grill` ancoram. **`sdd-*` não ancora nada** —
  é agrupamento mental nosso. Renomear é parte do refactor.
- **Completion criterion** — a condição checável que diz que terminou.
- **Context load** — custo da description em todo turno (model-invoked paga sempre).
- **Cognitive load** — custo de lembrar que a skill existe (user-invoked paga isso).
- **Branch** — caminhos diferentes dentro da skill conforme o gatilho.
- **Legwork** — o que o agente cava sozinho dentro do trabalho.

### Princípios

1. **"Uma skill existe pra arrancar determinismo de um sistema estocástico."** Determinismo de
   **processo**, não de output.
2. **Invocação é decisão explícita.** Model-invoked = alcance autônomo, paga context load.
   User-invoked (`disable-model-invocation: true`) = zero context load, paga cognitive load.
   **No v9 nunca decidimos isso conscientemente.**
3. **Hierarquia da informação** — *steps* (ações ordenadas) e *reference* (definições, regras,
   fatos) organizados por imediatismo. Progressive disclosure move detalhe pra arquivo linkado.
4. **Granularidade** — só divide skill quando ganha um dos dois custos:
   **(a) por invocação** (leading word distinta que merece gatilho próprio) ou
   **(b) por sequência** (esconder passos pós-conclusão pra evitar conclusão prematura).

### Failure modes a caçar no v9

| Modo | Onde dói aqui |
|---|---|
| **Sediment** (camadas velhas acumuladas) | `sdd-learning` 500L, `memory-organize` 488L, `executor-plan` 736L |
| **Sprawl** | 24 commands + 17 references |
| **Premature completion** | o que `/sdd-close` e `/pr-followup-audit` existem pra consertar |
| **Duplication** | `sdd-plan` vs `sdd-plan-eco`; `sdd-review` vs `pair-review` vs `pr-ready` |
| **Negation** | CLAUDE.md e commands escritos em "NUNCA commita", "nunca posta", "nunca inventa" |
| **No-ops** | passos que não mudam nada — auditar em cada recriação |

---

## PARTE D — Fila de reconstrução

**Ordem recomendada.** Cada peça: revisar → decidir invocação (model vs user) → escrever →
usar de verdade → só então a próxima.

### Onda 0 — as ferramentas que constroem o resto

Sem legado. A partir daqui, **cada peça seguinte nasce sendo grelhada** — é assim que você
recupera a mão já na segunda peça, não no fim.

- [x] **`grilling`** ✅ `skills/grilling/SKILL.md` (30-07-2026) — model **e** user invocable.
      Sem `disable-model-invocation`: o valor está justamente em o agente puxar a skill quando
      percebe que ia decidir algo que é do usuário. Vale o context load da description.
- [x] ~~**`grill-me`**~~ — **não criado, de propósito.** No Claude Code toda skill já é
      `/`-invocável por default, então o par da referência seria duplicação pura (falha o teste
      de granularidade da Parte C: não ganha nem custo de invocação nem de sequência).
      Os gatilhos "me grelha" / "grill me" entraram no `when_to_use` do `grilling`.
- [ ] **`handoff`** — passar contexto adiante. Decidir: tmp do SO (como a ref.) ou `thoughts/`?
- [ ] **`writing-great-skills`** adaptado — guia de estilo do repo, em pt-BR.

### Onda 1 — o ciclo central

- [x] **`spec`** ✅ `skills/spec/` (30-07-2026) — substitui `sdd-spec` (279L). Com `adversary.md`.
- [x] **`baseline`** ✅ `skills/baseline/` (30-07-2026) — peça nova, capability derivada do código.
- [x] **`plan`** ✅ `skills/plan/` (31-07-2026) — substitui `sdd-plan` (639L + 348L de references).
      Com `review-lenses.md` (3 lentes, uma rodada, sem veredito).
- [x] **`test-plan`** ✅ `skills/test-plan/` (31-07-2026) — o pair de testes v9 (Passo 7.5 + 311L)
      extraído pra peça própria, com `lenses.md`. Escreve dentro do `plan.md`.
- [x] **`implement`** ✅ `skills/implement/` (31-07-2026) — substitui `executor-plan` (736L + 261L
      de references) e absorve o `tdd`, que não vira peça própria: dividir não ganharia nem custo
      de invocação nem de sequência (Parte C.4). Com `worker.md` (subagente de uma tarefa) e
      `review-lenses.md`. **Um modo só** — `--step` morreu como flag.
- [x] **`imp-review`** ✅ `skills/imp-review/` (31-07-2026; renomeado em I.35) — consolida `sdd-review` (373L+221L),
      `pair-review` (157L) e a validação de alinhamento do `pr-ready`. Com `lenses.md` (6 lentes).
- [x] **`pr-ready`** ✅ `skills/pr-ready/` (31-07-2026) — o que sobrou do `pr-ready.v9` (251L):
      gate de verde e handoff.
- [x] ~~**`pair-review`**~~ — **não recriado.** Existia porque o `sdd-review` era batch; com achados
      na tela (I.14) a conversa acontece sozinha. O que tinha de único foi pro `imp-review`.

### Onda 2 — ⚠️ os que carregam dados vivos (ler Parte E antes)

- [x] **`roadmap`** ✅ `skills/roadmap/` + `scripts/roadmap/roadmap.py` (31-07-2026) — substitui
      `roadmap.v9` (218L) + reference `roadmap-item.md` (143L). **Primeira peça com motor em
      script** (ver I.28). Contrato E.1 preservado verbatim e verificado por execução; migração
      não foi necessária (o `plan:` legado é lido e nunca apagado).
- [x] **`pr-close`** ✅ `skills/pr-close/` (31-07-2026) — substitui `sdd-close` (222L) + absorve
      `sdd-learning` (500L), com `learning-filters.md`. Contratos E.1 **e** E.2 preservados.
      Resolve I.7 e I.10.
- [x] **`memory`** ✅ `skills/memory/` + `scripts/memory/audit.py` (31-07-2026) — substitui
      `memory-keeper.v9` (285L) + `memory-organize.v9` (488L). Tipos 9 → 8 medindo uso real;
      nada apagado. Ver I.29.
- [x] **`pr-audit`** ✅ `skills/pr-audit/` (31-07-2026) — substitui `pr-followup-audit` (341L), com
      `audit-worker.md`. Contrato E.3 preservado (a issue perene já existe em repos reais).

### Onda 1.5 — pré-requisito de uso (promovido da Onda 3 em 31-07-2026)

Sem estas peças o ciclo não roda de verdade: o usuário parte da branch principal, cria a worktree,
abre o PR draft e migra a sessão pra dentro dela. Estavam classificadas como "portar sem drama" na
Onda 3 — classificação errada.

- [x] **`worktree`** ✅ `skills/worktree/` (31-07-2026) — unifica `git-worktree` (144L) +
      `git-remove-worktree` (122L) + `modo-livre` (294L). Com `permissions.json` (cópia fiel do
      reference v9).
- [x] **`pr-draft`** ✅ `skills/pr-draft/` (31-07-2026) — do `pr-draft.v9` (310L), **com o modo
      `sync` junto**, como no v9. Cheguei a separar em `pr-sync` e voltei atrás — ver I.22.
      **Ganhou `stack` e `restack` em 19-08-2026** — a cadeia de PRs do `tasks.md` nasce empilhada
      via `gh stack`, e o rebase em cascata funciona com worktree. Ver I.40.

### Onda 3 — periferia

- [x] **`pr-review`** ✅ `skills/pr-review/` (31-07-2026) — **peça nova, sem antecessor no v9**:
      revisar o PR de **outra pessoa**. Todo o v9 (`sdd-review`, `pair-review`, `pr-ready`) assumia
      PR próprio. Briefing antes de qualquer achado, promessa × entrega (com "não prometido" como
      estado de primeira classe), sabatina antes do veredito, preview editável e **um** submit
      review com comentários inline. Consome `lenses.md` do `imp-review` por referência, sem cópia.
- [x] **`test-qa`** ✅ `skills/test-qa/` (07-08-2026) — absorve o `verifica` (90L) e vai além:
      exploração adversarial sobre a aplicação rodando, com `lenses.md` (7 lentes — 4 de API, 3 de
      tela). Fecha a dívida de verificação manual que o `test-plan` cria (E.5). Ver I.36.
- [x] **`glossary`** ✅ `skills/glossary/` (25-08-2026) — **peça nova, sem antecessor no v9.**
      Dicionário pessoal global (`~/.claude/thoughts/glossario.md`) que o usuário consulta e que
      cresce sozinho quando o agente usa termo novo. Nasceu de queixa de densidade de jargão nas 16
      skills (`lente` 84×, `red/green` 53×, `gate` 48×). **O usuário recusou a tradução do jargão** —
      traduzir esconde o termo e ele continuaria sem entender PR e doc de fora. Ver I.42.
- [ ] `research` ← `busca` · `diagnosing-bugs` ← `investiga` ·
      `prototype` (novo) · `ask-*` roteador (novo)
- [ ] Decidir o destino de: `quick-task`, `complexidade`, `worktree-detect`, `sync-tests`,
      `sdd-plan-eco`
- [ ] Portar sem drama: git-*, `modo-livre`, `status-deps`, `pr-report`, `conciso`, `structure-cache`
- [ ] `setup` ← `sdd-init`, **por último** (só faz sentido quando o conjunto existir)
- [ ] README.md + README-en.md novos · CLAUDE.md definitivo · **apagar este arquivo**

### Decisões estruturais pendentes (resolver na Onda 0)

1. ~~**Command ou skill?**~~ ✅ **RESOLVIDO POR FATO** — ver Parte G. Tudo vira skill.
2. **Idioma dos nomes.** Docs em pt-BR é convenção nossa. Mas *leading word* é conceito
   pré-treinado — `grilling`, `tdd`, `handoff` ancoram melhor em inglês. Nome em inglês +
   corpo em pt-BR?
3. **Nomenclatura.** Matar o prefixo `sdd-`? Se sim, o repo continua "sdd-toolkit"?
4. **O que fazer com `thoughts/`.** SPEC/PLAN/IMP/reviews/capabilities/roadmap/research/cache —
   a estrutura sobrevive inteira ao v10?

---

## PARTE G — Plataforma: o que mudou desde o v9

Levantado da doc oficial em 30-07-2026 (`code.claude.com/docs/en/skills`). **Isto não é opinião —
é capacidade da plataforma**, e derruba decisões que no v9 foram tomadas por falta de alternativa.

### G.1 — Commands e skills foram fundidos

`.claude/commands/deploy.md` e `.claude/skills/deploy/SKILL.md` produzem o mesmo `/deploy` e
funcionam igual. Arquivos em `.claude/commands/` **continuam funcionando** (a instalação v9 do
usuário não quebra). Mas **skill é superset estrito**: ganha diretório de arquivos de suporte,
controle de invocação e carregamento automático pelo modelo.

→ **Decisão #1 resolvida: o v10 é todo skill.** `skills/<nome>/SKILL.md`.

Precedência quando há conflito de nome: enterprise > personal > project; skill vence command
de mesmo nome; skill de projeto sobrescreve skill bundled (ex.: um `code-review` nosso substitui
o `/code-review` nativo — **atenção ao recriar essa peça**).

### G.2 — Frontmatter disponível (o v9 usava 4 campos de ~17)

| Campo | Por que importa pro v10 |
|---|---|
| `disable-model-invocation: true` | Só o usuário invoca. **Description sai do contexto** → zero context load. Doc recomenda pra "workflows com side effects ou onde você quer controlar o timing" |
| `user-invocable: false` | Só o modelo invoca. Pra conhecimento de fundo que não é ação |
| `context: fork` + `agent` + `background` | **Roda a skill num subagente nativamente.** Substitui a orquestração manual de `Agent` no `busca`, `sdd-review`, `executor-plan` |
| `${CLAUDE_SKILL_DIR}` | Path do diretório da skill, substituído **também nas regras `Bash()` do `allowed-tools`** → script bundled roda sem prompt de permissão |
| `paths` | Globs que limitam quando a skill auto-ativa |
| `hooks` | Hooks escopados ao ciclo de vida da skill |
| `effort` | `low`…`max` por skill, sobrepondo a sessão |
| `disallowed-tools` | Remove ferramenta do pool enquanto a skill está ativa (ex.: tirar `AskUserQuestion` de um loop autônomo) |
| `when_to_use` | Gatilhos extras. `description` + `when_to_use` truncam em **1.536 chars** no listing |
| `model`, `arguments`, `argument-hint`, `shell` | equivalentes ao que o v9 já usava |

### G.3 — `${CLAUDE_SKILL_DIR}` mata a gambiarra das references

O v9 resolvia arquivo de apoio com a cascata "busca em `.claude/sdd-references/` →
`~/.claude/sdd-references/` → fallback inline resumido", porque todo `.md` dentro de `commands/`
virava command namespaced e poluía a lista.

**Não é mais necessário.** Arquivo de apoio vive no diretório da skill e é referenciado por
`${CLAUDE_SKILL_DIR}/…`. Ao recriar qualquer peça que tinha reference, **remover a cascata inteira**.

### G.4 — Ciclo de vida do conteúdo (muda como se escreve)

- O `SKILL.md` renderizado entra na conversa como **uma mensagem e permanece pelo resto da sessão**.
  O Claude Code **não re-lê** o arquivo nos turnos seguintes.
- → **Escreva como *standing instructions*, não como receita sequencial de uma passada.**
  Boa parte do v9 está escrita como "Passo 1… Passo 7.5… Passo 9.5" — formato errado pro modelo de execução.
- Re-invocar com conteúdo idêntico não duplica (só uma nota de "já carregada").
- Auto-compaction re-anexa a invocação mais recente de cada skill: **primeiros 5.000 tokens de cada,
  orçamento combinado de 25.000**, preenchido da mais recente pra trás. **Skill gorda é a primeira a
  ser truncada.** Argumento adicional pra peça pequena.
- `allowed-tools` vale só **no turno** que invocou (a instrução persiste, a permissão não).

### G.5 — Consequências pro refactor

1. Estrutura do repo passa a ser `skills/<nome>/SKILL.md` (+ arquivos de apoio ao lado).
2. Toda peça declara invocação **explicitamente** — é decisão de design, não default.
3. References viram arquivos irmãos do `SKILL.md`; a cascata de fallback morre.
4. Orquestração de subagente vira `context: fork` onde couber, em vez de prosa mandando spawnar.
5. Reescrever em modo *standing instructions*, não em passos numerados.
6. ✅ **Resolvido em I.35** — `code-review` colidia por nome curto; virou `imp-review`.

---

## PARTE E — ⚠️ Contratos de dados (NÃO recriar sem ler)

Estes formatos existem em **projetos reais fora deste repo**. Recriar o comando sem preservar
o formato — ou sem escrever migração — quebra dado vivo. Fonte canônica preservada nos arquivos
deprecados citados.

### E.1 — Roadmap (vault Obsidian)

**Fonte:** `commands/deprecated/references.v9/roadmap-item.md` · **Escrito por:** `/roadmap` (dono),
`/sdd-plan` (cria), `/pr-draft` (promove), `/sdd-close` (conclui).

```
thoughts/roadmap/
  ROADMAP.md              # hub: linka todos, lista 🔴 Próximos e 🔓 Desbloqueados agora
  backlog/      NNN-slug.md
  em-progresso/ NNN-slug.md
  concluido/    NNN-slug.md
```

Invariantes que **não podem quebrar** numa recriação:

- **Status = a pasta.** Fonte única da verdade; não existe `status:` no frontmatter.
- **`NNN`** = sequencial de 3 dígitos, `max(existentes) + 1`, **nunca reusado**. É o id estável
  do nó no grafo — não muda ao mover de pasta nem ao ganhar PR.
- **Frontmatter:** `id`, `titulo`, `pr` (vazio→`#N`), `criado` (DD-MM-YYYY), `plan` (basename do
  PLAN), `next` (curadoria **humana** — nenhum command liga sozinho).
- **Corpo:** `**Depende de:** [[MMM-slug]]` e `**Docs:** [[spec-…]] · [[PLAN-…]]`.
  Wikilinks **no corpo** (garante a aresta no grafo). Sem dependência → **omitir** a linha.
- **Dependência** = "não começar antes de MMM estar em `concluido/`". Sem ciclos. Link pra item
  inexistente = órfão, sinalizar.
- **🔓 Desbloqueados** = em `backlog/` **E** tem `Depende de:` **E** todas as deps em `concluido/`.
  Item sem deps nunca é "desbloqueado" (nunca esteve bloqueado).
- **Idempotente e determinístico:** ordenado por NNN; regenerar o hub a mais nunca prejudica.

**Migração:** o v9 já tinha migração de "arquivo único → vault". Se o v10 mudar o formato,
precisa da mesma cortesia: de-para em tela + confirmação + backup (`_migrado-de-*.bak`), nunca
deletar. E **detectar formato antigo sem re-migrar** (idempotência).

### E.2 — Capability viva (spec viva)

**Fonte:** `commands/deprecated/references.v9/capability-template.md` · **Escrito só por** `/sdd-close`,
**só sob PR mergeado**.

- Vive em `thoughts/capabilities/<dominio>.md` — descreve o que o sistema **faz hoje**.
- Requisitos identificados por **`C<N>`**; todo requisito carrega **`[Origem: <spec> · PR #N]`**.
- Merge do delta: `ADDED` cria `C<N>` · `MODIFIED` edita e **acrescenta** ao `[Origem]` sem apagar
  rastro · `REMOVED` vai pra `## Removido`.
- Edição **cirúrgica e idempotente**. `C<N>` inexistente = **parar e avisar**, nunca inventar requisito.
- Lida (e marcada com delta) por `/sdd-spec`, que **nunca escreve** nela.
- **`## Removido` por auditoria** (desde 12-08-2026, I.38): além de `[Removido: … PR #N]`, existe
  `[Removido: auditoria de DD-MM-YYYY · sem evidência no código nem nos testes]` — a auditoria
  descobre que o comportamento sumiu, mas não sabe por qual mudança. **Sem PR inventado.**
- **Frontmatter** (desde 11-08-2026, I.37): além de `dominio` · `atualizado` · `specs`, o par
  **`verificado-ate: <sha>`** + **`paths: []`** — o marcador de staleness. Escrito pelo `baseline`
  (que é quem olha o código), avançado pelo `pr-close` **só quando o range não contém commit de
  fora do PR**, lido pela `spec` como aviso. **Aditivo e opcional:** capability sem os campos
  continua válida — perde a detecção, e as peças dizem que não verificaram em vez de assumir que
  está em dia.

Se o v10 mudar o formato: `C<N>` é referenciado por SPECs antigas já arquivadas. Renumerar quebra
rastreabilidade histórica.

### E.3 — Issue perene de auditoria (GitHub)

**Fonte:** `commands/deprecated/pr-followup-audit.v9.md` (Fase 5).

- **Uma issue por repositório**, reaproveitada a cada rodada.
  Título canônico: `chore: Auditoria contínua de follow-ups de review`.
  **Já existe em repos reais** — o v10 precisa reconhecê-la, não criar uma segunda.
- **Body = só o que está aberto** (é de onde sai o contador do checklist). Bloco que fecha inteiro
  **sai do body** e sobrevive no comentário. Body que só cresce trava o contador e para de significar.
- **Comentário = a rodada, append-only.** Nunca reeditado; é o histórico.
- **Formato do item** (preservar — é parseável e ordenável):
  ```markdown
  - [ ] <consequência em uma frase>.
        `RISCO` · ativo|armado · `arquivo:linha` · PR #N · <marca de origem>
  ```
- **Taxonomia de risco** (ordem de ataque): `SEGURANCA` > `DADO` > `CONTRATO` >
  `DISPONIBILIDADE` > `ROBUSTEZ` > `COBERTURA` > `HIGIENE`. Desempate: `ativo` antes de `armado`;
  irreversível antes de reversível.
- Regra que vale manter: item aberto rodada após rodada não é problema de prioridade — é má
  descrição, mau dimensionamento ou falta de dono. **Fechar como risco aceito é resultado legítimo.**

### E.4 — Memória (auto-memory nativo)

**Fonte:** `skills/deprecated/memory-keeper.v9/SKILL.md` · **Escrito por** todo command SDD.

- **Local:** `~/.claude/projects/<root-do-repo-com-/-virando-->/memory/` — sempre resolvido pelo
  **root** (não pela worktree), pra centralizar. Worktree usa **symlink** criado pelo
  `/git-worktree` e removido com `unlink` pelo `/git-remove-worktree`
  (**nunca `rm -rf`** — seguir o symlink apagaria o memory do root).
- **Flat, sem subpastas.** Arquivo: `<tipo>_<slug>.md`; `name:` interno em kebab-case.
- **9 tipos:** 4 nativos (`user`, `feedback`, `project`, `reference`) + 5 SDD
  (`decision`, `blocker`, `lesson`, `idea`, `preference`).
  ⚠️ **Os 5 SDD são invenção nossa.** Se o v10 reduzir o conjunto, as notas existentes já usam
  esses `metadata.type` — precisa de mapa de conversão, não de silêncio.
- **`MEMORY.md` é APENAS índice** (tabelas agrupadas por tipo + `## GUARDRAILs`). O harness carrega
  só as primeiras ~200 linhas / 25KB no system prompt; topic files vêm sob demanda.
- **Conteúdo = princípio + gatilho, não instância.** `**Why:**` (a razão) + `**How to apply:**`
  (o gatilho — a situação futura onde a regra reaparece). Sem gatilho, a nota não é acionável.
- Campos `metadata.node_type` e `metadata.originSessionId` são do harness — **não remover**.

**Nota de projeto:** `/memory-organize` tem 488 linhas só pra manter esse índice saudável.
No v10, tratar isso como sinal: se o formato precisa de um comando de 488L pra não apodrecer,
provavelmente o formato é caro demais. Mas **qualquer simplificação precisa migrar as notas existentes.**

### E.5 — Invariantes de qualidade a não perder no porte

Não são dados, são garantias do v9 que a referência **não tem** e que valem mais que o formato:

- **Red verificável** — roda o teste, confirma que falha **pelo motivo certo** antes de implementar.
  **Falso-verde = parada dura.** Evidência do red vai pro log/IMP e é auditada.
- **Test count protection** — número de testes não pode cair silenciosamente (rebase, refactor, fix).
- **Tipo de teste por necessidade** — unit/integração/e2e escolhido pela necessidade, com `Test env:`
  declarado. Não default unit.
- **⭐ Nada sobe sem verificação** (endurecido em 31-07-2026, mais forte que o v9) — todo requisito
  sai do planejamento com uma forma de verificação. Piso: **verificação manual executada pelo
  usuário, com evidência registrada** — e isso é dívida, não pronto. Ausência total de verificação
  só existe depois de **pergunta explícita** ao usuário e OK dele; justificativa que o agente
  escreve sozinho (o `Tests: none` do v9) não vale mais.
- **Commit sob aprovação humana** — `git add` livre; `commit`/`push` sempre com OK explícito.
- **Gate de verde antes da entrega** — CI passou, ou suíte local **completa** (não só os testes do PR).
- **Zero inferência** — comportamento de API se verifica (Context7 ou código existente), não se assume.
- **Spec viva só sob merge** — comportamento não entregue nunca entra na capability.

---

## PARTE F — O que foi deprecado (30-07-2026)

Movido com `git mv` (histórico preservado). **Nada foi deletado.**

| De | Para |
|---|---|
| `commands/*.md` (24) | `commands/deprecated/<nome>.v9.md` |
| `commands/references/` (17) | `commands/deprecated/references.v9/` |
| `skills/{conciso,memory-keeper,structure-cache}/` | `skills/deprecated/<nome>.v9/` |
| `README.md` · `README-en.md` | `deprecated/README.v9.md` · `deprecated/README-en.v9.md` |
| `CLAUDE.md` (v9) | `deprecated/CLAUDE.v9.md` |

**Intocado:** `scripts/`, `LICENSE`, `.gitignore`, `.claude/settings.local.json`,
`commands/deprecated/` e `skills/deprecated/` pré-existentes (v1–v7).

**Não commitado** — o refactor inteiro está no working tree até você aprovar.

⚠️ **Instalações existentes em `~/.claude/commands/` e `~/.claude/skills/` continuam funcionando.**
Deprecar aqui não desinstala nada de lugar nenhum. Você segue trabalhando com o v9 instalado
enquanto o v10 nasce.

---

## PARTE H — OpenSpec (Fission-AI): a convergência e as 5 lições

[github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) — ferramenta npm
(`@fission-ai/openspec`) + slash commands `/opsx:*`. Levantado em 30-07-2026.

**Por que importa mais que a outra referência:** não é analogia, é **o mesmo problema resolvido
de forma mais madura**. Eles chegaram, independentemente, na mesma arquitetura do nosso v9 — e
depois a refizeram. O que eles trocaram é o mapa dos nossos defeitos.

### H.1 — O que já é idêntico (valida o v9, não mexer)

| Nosso v9 | OpenSpec | Veredito |
|---|---|---|
| Delta `ADDED` / `MODIFIED` / `REMOVED` na SPEC | **Delta specs**, exatamente essas 3 seções | ✅ convergência independente — o formato está certo |
| `thoughts/capabilities/<dominio>.md` (spec viva) | `specs/` organizado por domínio (`auth/`, `payments/`) | ✅ mesma ideia, mesmo recorte |
| `/sdd-close` mescla o delta na capability sob merge | **archive** aplica cada seção do delta nas specs principais e move a pasta pra `changes/archive/` com prefixo de data | ✅ mesmo algoritmo |
| RF + AT (critérios de aceitação) | requirements (`SHALL`) + scenarios testáveis | ✅ mesmo formato |
| `/sdd-spec --explore` | `/opsx:explore` | ⚠️ mesma ideia, **status oposto** — ver H.3 |
| `closed/` | `changes/archive/` com prefixo de data | ✅ |

Isso é a melhor notícia do refactor: **o modelo de dados do v9 está certo.** O que está errado
é a forma de operá-lo.

### H.2 — ⭐ Lição 1: fluido, não phase-locked (a maior)

O **legacy** deles era: `planning → implementation → archiving`. Fases rígidas. Descrição do
próprio doc:

> "real work doesn't work that way. You implement something, realize your design was wrong,
> need to update specs, continue implementing."

**Isso é literalmente o v9:** `sdd-spec → sdd-plan → pr-draft → executor-plan → sdd-review →
pr-ready → sdd-close`. Sete estágios, ordem fixa, sem volta barata.

O OPSX substituiu fases por **ações que você toma a qualquer momento** — create, implement,
update, archive — sobre um **grafo de dependências (DAG)** onde as dependências são **enablers**
("isto agora é possível"), não gates ("você não pode ainda"). Dá pra atualizar o design no meio
da implementação e continuar aplicando tasks sem atrito de phase-gate.

**Consequência direta pro nosso diagnóstico:** num pipeline sem volta barata, descobrir no meio
que o design estava errado não gera correção — gera *dívida*. Você segue e conserta depois.
**É por isso que metade do toolkit é maquinário de recuperação** (`sdd-close`, `pr-followup-audit`,
`pair-review`, `sdd-learning`). A recuperação não é um recurso: é a cicatriz do phase-lock.

→ A Onda 1 **não deve** ser um pipeline de peças em ordem. Deve ser um conjunto de ações sobre
estado detectável.

### H.3 — ⭐ Lição 2: explore é hábito, não flag

No v9, explorar é `--explore`, uma flag escondida dentro do `/sdd-spec`. No OpenSpec, `/opsx:explore`
é comando de primeira classe, tem página própria na doc, e é chamado de **"o hábito mais valioso
a formar"**. Aparece no fluxo de 30 segundos.

Características (todas iguais às nossas, exceto o status): lê e busca no codebase pra responder
perguntas reais, compara opções e **nomeia os trade-offs**, **não cria artefato nenhum, não toca
código, não custa nada**.

> "the fuzzier the task, the more explore pays off. The clearer the task, the more you can skip
> straight to proposing."

→ No v10, explorar vira peça própria. Combina naturalmente com `grilling` (explore levanta os
fatos e as opções; grilling resolve as decisões).

### H.4 — ⭐ Lição 3: o "two-minute pass" (o antídoto direto do nosso problema)

Checkpoint humano **barato e definido** antes de gerar código. Três perguntas, uma por artefato:

1. **Proposal — é o problema certo?** "Isto bate com o que eu pedi, e tem alguma coisa entrando
   de contrabando?" Caça scope creep e vagueza.
2. **Specs — "pronto" está definido certo?** *O coração do review.* Cada requisito é testável e
   tem cenário que de fato o exercita. **E, principalmente, pegar o que está faltando** — os casos
   que você se importa e ninguém mencionou.
3. **Tasks — o plano de trabalho é sensato?** Ordenadas, rastreáveis a requisito, nada misterioso
   ou fora de escopo.

**Critério de saída:** *"eu ficaria confortável se a IA construísse exatamente isto e nada mais."*

A economia declarada:

> "catching a wrong turn in a one-paragraph plan is nearly free. Catching the same wrong turn
> in 300 lines of code is not."

→ **Isto ataca a raiz do diagnóstico da Parte 0.** O v9 não tem checkpoint barato definido —
tem "leia 300 linhas e aprove", onde discordar custa caro e concordar custa zero. Um passe de
dois minutos com três perguntas e critério de saída explícito inverte essa economia.
**Candidato a peça própria na Onda 1.**

### H.5 — ⭐ Lição 4: o determinístico vira CLI, não prosa

OpenSpec tem **duas metades**, e a doc diz que confundir as duas é o erro mais comum:

- **CLI no terminal** (`openspec init`, `openspec validate`, `openspec archive`, `openspec feedback`)
  — o trabalho **determinístico**.
- **Slash commands no chat** (`/opsx:*`) — o trabalho de **julgamento**.

Existe até um **Agent Contract**: "the machine-readable CLI surfaces agents drive". A CLI é a
interface que o agente dirige.

**O v9 faz tudo em prosa markdown**, inclusive o que é puramente determinístico: calcular
🔓 Desbloqueados, renumerar `NNN`, mover pasta de status, montar o hub do ROADMAP, aplicar o delta
na capability, dedup de colheita. São ~800 linhas de instrução em português pedindo pro modelo
executar algoritmo — caro, lento e não-determinístico.

→ Já temos precedente disso funcionando: `scripts/structure-cache/build.py`. **O que é algoritmo
deveria ser script; o markdown fica só com julgamento.** Encolhe as peças e mata uma classe
inteira de bug.

### H.6 — ⭐ Lição 5: uma mudança = uma pasta

No OpenSpec, uma change é **uma pasta** com tudo dentro: `proposal.md` (intenção e escopo),
`specs/` (o delta), `design.md` (abordagem técnica), `tasks.md` (checklist). Archive move a pasta
inteira, com contexto completo preservado.

No v9, uma mudança está espalhada por **cinco lugares**: `thoughts/specs/`, `thoughts/plans/`,
`thoughts/imps/`, `thoughts/reviews/`, `thoughts/roadmap/<status>/`.

→ **É por isso que `/pair-review` precisa "re-hidratar".** O contexto de uma única mudança não
mora em lugar nenhum — mora em cinco. Resolve a decisão #4 (o que fazer com `thoughts/`).

### H.7 — Outros pontos aproveitáveis

- **Schema externo em YAML** define os artefatos e suas dependências (DAG, topological sort),
  em vez de template hardcoded. "Editar um template Markdown afeta o comportamento imediatamente,
  sem release cycle." Nosso "schema" está enterrado em 639 linhas de prosa dentro do `sdd-plan`.
- **Brownfield**: "you don't document all of it" — adoção incremental em codebase grande, sem
  ferver o oceano. O `/sdd-init` v9 não tem essa postura.
- **Multi-language**: geram artefatos em outros idiomas — precedente pro nosso pt-BR.
- **Perfil expandido**: `/opsx:new`, `:continue`, `:ff`, `:verify`, `:bulk-archive`, `:onboard`.
  Nota o `:continue` — retomar trabalho é comando de primeira classe, não acidente.
- **30+ ferramentas suportadas**, skills em `.claude/skills/` (mesma pasta que decidimos usar).

### H.8 — Posição decidida: referência, não adoção ✅

**Decisão (30-07-2026):** o OpenSpec entra como **referência conceitual**. Não vira dependência,
não instalamos, não redistribuímos. Avaliamos ideia por ideia e usamos o que fizer sentido —
cada uma atribuída conforme o protocolo do [`NOTICE.md`](./NOTICE.md).

Isso descarta "adotar como base", e por um motivo coerente com a Parte 0: o refactor nasceu de
**delegar demais**. Terceirizar propose/apply/archive pra uma caixa de terceiro seria o mesmo
vício num nível acima — e a doc deles não menciona nenhum dos invariantes da Parte E.5
(red verificável, test count protection, gate de verde), que são justamente o que mais importa aqui.

Fica **em aberto, sem bloquear nada**: rodar um ciclo real do OpenSpec (`explore → propose →
apply → archive`) num projeto de teste, pra avaliar o modelo com evidência em vez de doc.
Vale mais depois que a Onda 1 existir, como comparação.

**Licença:** MIT, compatível com a nossa. Conceito e arquitetura não são cobertos por copyright —
a atribuição no NOTICE é rastreabilidade e boa prática. Se em algum momento **texto** deles for
adaptado de perto, o MIT passa a valer e a peça leva `## Créditos`.

---

## PARTE I — Decisões do núcleo (spec/plan/implement/review)

Tomadas em sessão, 30-07-2026. Esta parte substitui a fila linear da Onda 1 na Parte D.

### I.1 — Uma mudança = uma pasta ✅

```
thoughts/changes/NNN-slug/
  spec.md      # o QUÊ + delta da capability
  plan.md      # o COMO
  tasks.md     # checklist TDD
  notes.md     # IMP / evidência / review
```

Archive move a pasta inteira pra `thoughts/changes/archive/YYYY-MM-NNN-slug/`.

**Fato que remove o obstáculo:** o Obsidian resolve `[[nome]]` por nome de arquivo em todo o
vault, independente de subpasta (é por isso que o `/sdd-close` v9 já podia mover SPEC/PLAN pra
`closed/`). **Reorganizar onde spec e plan moram não quebra wikilink existente** — não precisa
de migração de link.

Motivo: hoje uma mudança mora em 5 lugares (`specs/`, `plans/`, `imps/`, `reviews/`,
`roadmap/<status>/`). É por isso que `/pair-review` precisa "re-hidratar".

### I.2 — Não são fases, são ações sobre estado ✅

Correção de leitura: o OpenSpec **tem** 12 comandos e uma ordem típica. O que ele não tem é
**phase gate**. A diferença está na natureza do pré-requisito:

- **Phase gate** — "você ainda está no planejamento, não pode implementar". Bloqueia por
  *posição no processo*.
- **Enabler** — "`apply` precisa do artefato de tasks, que não existe". Bloqueia por *estado do
  filesystem*, e a saída é óbvia.

Pré-requisitos deles, todos de estado: `explore`/`propose`/`new`/`onboard` = nenhum ·
`continue`/`ff`/`archive` = change folder existe · `apply` = tasks existe · `update` = artefatos
existem · `verify` = tasks + implementação · `sync` = delta specs existem.

**⭐ O v9 não tem `update`.** Não existe comando pra "a spec estava errada, corrige e mantém o
plan coerente". Descobrir isso no meio do `/executor-plan` deixa duas saídas: refazer à mão, ou
seguir e consertar depois. **Essa ausência é a causa mecânica da dívida** que `/sdd-close` e
`/pr-followup-audit` existem pra resgatar — não é falta de disciplina, é caminho de volta
que nunca foi construído.

→ O v10 precisa de uma ação de **volta barata** (`update`/revise) como peça de primeira classe.

Nota de escala: 12 comandos deles contra 4 do nosso núcleo. **Fluido não significa menos
comandos** — significa comandos que operam sobre estado detectável, mais as ações de volta.

### I.3 — `explore` precede a spec, e é peça própria ✅

> "Explore clarifies **the what**, not the how."

Critério é **incerteza**, não fase: fuzzy → explore primeiro; claro → direto pro spec.
No v9 é `--explore`, flag escondida dentro do comando que escreve. No v10 é peça separada que
**não escreve nada**.

Divisão de trabalho com o `grilling`: **explore levanta fatos e opções; grilling resolve
decisões.** Ambos antecedem a spec, e são complementares.

### I.4 — `grilling`: chamada explícita, régua por custo de reverter ✅

**Não confiar na auto-invocação.** Dois fatos da doc: "Skill not triggering" é problema conhecido;
e **descriptions são truncadas quando o listing estoura o budget (1% da janela), começando pelas
skills menos invocadas** — uma skill pouco usada perde a description e some da auto-invocação
sem avisar. A peça que precisa do grilling **chama** o grilling.

**Não é "sempre" nem "por fase"** — se fosse ritual, na quinta vez a resposta vira "tanto faz".
O gatilho é a **irreversibilidade da decisão** (régua compatível com workflow fluido, já que não
há fases):

| Decisão | Reverter custa | Grilling |
|---|---|---|
| O que construir — escopo, comportamento | **tudo**: construiu a coisa errada | sempre |
| Contrato, formato de dado, API pública | migração + consumidor externo | sempre |
| O que **não** vamos testar | dívida silenciosa | sempre |
| Estrutura de módulo interno | refactor local | se não-óbvio |
| Nome, ordem, organização | nada | nunca |

Essa régua explica retroativamente por que o **pair de testes** foi a única parte interativa do
v9: "o que não vamos testar" é decisão cara e silenciosa.

**Forma:** o conteúdo mora só na skill `grilling`; cada peça carrega **uma linha** dizendo quais
decisões *dela* caem na faixa "sempre". Bloco copiado em toda peça seria duplicação (muda em N
lugares) e vira no-op que o modelo aprende a pular.

### I.5 — Pesquisa da spec: capability-first, por pergunta ✅

O método do v9 (Passo 3) está **certo** e deve ser preservado: capability primeiro, código
depois; `structure-cache` antes de grep pra pergunta estrutural; subagente `Explore` pra
varredura ampla — **com a diretiva do cache repetida no prompt do subagente** (ele não herda o
corpo da skill; sem isso vai direto ao Grep). Errada é a forma: 25 linhas de prosa com cascata
de fallback de reference embutida.

Ordem por pergunta, do barato pro caro:

| Pergunta | Fonte |
|---|---|
| O que o sistema promete hoje aqui? | **capability viva** |
| Isso ainda é verdade? | **os testes do domínio** |
| Onde vive / como se comporta nas bordas? | grep/read **num subagente** |
| Por que ficou assim? | `git log` / `blame` |
| O que quebra se eu mexer? | `structure-cache --importers` |

**`structure-cache` não responde a pergunta da spec.** A própria skill diz: "responde
estrutura/dependência, não comportamento interno de uma função". Mais o limite duro: **TS/JS
apenas**. Ele serve pra *dimensionar o delta* (blast radius → escopo e fora-de-escopo), não pra
descobrir o que o sistema faz.

**Os testes existentes são a spec executável do comportamento atual** — fonte mais confiável que
a implementação (implementação conta o que o código faz, incluindo bugs; teste conta o que
alguém *decidiu* que ele deve fazer). O v9 só fazia esse inventário no `/sdd-plan` (Etapa 1 do
pair de testes) — tarde demais: quando se descobre que já existe teste, a spec já declarou o
comportamento como novo.

**Critério de parada:** o método do parruda manda "ler todos os arquivos relevantes", que não tem
limite — pesquisa sem limite vira documento sem limite. A capability é o critério de parada:
lê-se o que o sistema já promete, e vai-se ao código só onde ela não cobre ou está suspeita.

### I.6 — Capability: comando de bootstrap + sync no fechamento ✅

**Problema:** a capability só nasce pelo `/sdd-close`, e só sob PR mergeado. Num projeto
brownfield ela cobre exclusivamente o que passou pelo toolkit — o comportamento pré-existente
**nunca entra**. Hoje, na prática, os projetos não têm capability nenhuma.

Isso envenena o delta: sem `C<N>` pro comportamento alterado, a spec marca `ADDED` o que é
`MODIFIED`, e o merge no fechamento fica errado.

**Decidido:**

1. **Comando novo de bootstrap** ✅ **`baseline`** — `skills/baseline/` (30-07-2026). Deriva a
   capability de um domínio a partir de testes + código, em **lotes de 3–5 requisitos** escritos
   ao fim de cada lote (interrompível e retomável). Núcleo da peça é a tabela **promessa ×
   acidente**: teste dedicado = promessa; só-no-código observável = confiança baixa, marcado;
   detalhe interno = fora; teste × código discordando = sinaliza, não escolhe; cheiro de bug =
   pergunta antes. **Na dúvida, deixa de fora e diz que deixou** — ausência o próximo ciclo
   corrige, requisito falso não. Complementa capability existente, nunca reescreve; requisito com
   origem de spec não é tocado por derivação de código (contradição vira *achado*, não correção).
2. **O fechamento sincroniza** — o último comando do workflow (close) atualiza a capability.
   ⚠️ Só sob PR **merged**, nunca "fechado": comportamento não entregue não entra na spec viva.

**Procedência obrigatória:** requisito derivado de código leva `[Origem: derivado do código em
<data>]`, distinto de `[Origem: spec-X · PR #42]`. O primeiro significa "ninguém validou isto, é
descrição do que o código faz — confie menos". Sem essa distinção se constrói confiança falsa,
que é exatamente o risco que o OpenSpec evita ao não ter comando de povoamento.

**Divergência consciente com a referência:** o OpenSpec recusa povoamento por princípio
("You do not document your whole codebase to start"). Adotamos mesmo assim porque o modelo
delta-first puro só funciona se o delta souber contra o que está sendo calculado — e porque
partimos de zero capability.

### I.7 — ~~⏳ Em aberto~~ ✅ **RESOLVIDO em 31-07-2026** (ver no fim): `fix`/`chore` e a capability

**O furo:** no v9 o `/sdd-close` só age sobre par SPEC+PLAN mergeado. `/quick-task` nunca gera
SPEC, logo nunca chega no fechamento. **Todo bug fix que altera comportamento observável escapa
da capability** — e depois de alguns meses ela descreve um sistema que não existe mais, ainda
parecendo autoritativa.

Opções levantadas, **não decidido**:

| Opção | Como |
|---|---|
| Todo PR merged que muda comportamento | feat/fix/refactor sincronizam; exige julgar "mudou comportamento?" em PR sem spec, e o quick-task ganha passo de fechamento |
| Só PR com spec (v9) | determinístico, sem julgamento — aceita que a capability diverge com o tempo |
| Todo PR + auditoria periódica | sync no merge quando há delta; varredura periódica reconcilia capability × código, pegando até hotfix que nunca passou pelo toolkit |

Também não decidido: o sync acontece no **close** ou no **review**.

> A terceira linha da tabela (**auditoria periódica**) foi fechada pela **I.37** em 11-08-2026 —
> não como varredura avulsa, mas como detector de staleness disparado pela `spec`. Ela cobre o que
> a resolução deste item não alcança: mudança que nunca passa por você.

### I.8 — Formato do `spec.md` ✅ (aprovado 30-07-2026)

**Resolvido:** adotado o modelo de qualidade-por-unidade. Implementado em `skills/spec/`.
Formato final: uma frase de intenção · `**Fora de escopo:**` · requisitos `R<N>` com delta e
cenários colados · gate por requisito (6 critérios) · adversário (I.11) · pergunta humana de
fechamento. Registro da divergência abaixo, preservado porque a pergunta volta.

Divergência entre as fontes:

- **parruda / v9** — 8 seções obrigatórias, orientado a **completude de formulário**. O gate
  (Passo 8, "Verificação Final bloqueante") checa se as *seções existem* — um doc pode passar
  inteiro sendo intestável.
- **OpenSpec** — sem seções fixas; orientado a **qualidade por unidade**: um `SHALL` por
  requisito ("and also" = são dois), observável e testável, cenário que *exercita* em vez de
  reafirmar, nome descritivo, **uma intenção por change**.

⚠️ Contradição herdada: a gist proíbe descrever o COMO, mas a **seção 6 do nosso template é
"Contexto Técnico & Pontos de Integração"** — a spec v9 pede vazamento de implementação numa
seção obrigatória.

Destino provável de cada seção v9: RF + AT viram **requisito + cenário colados** (o coração) ·
Restrições/Fora de Escopo **sobrevive** (é o "e nada mais" do two-minute pass) · RNF vira
requisito normal com número · Critérios de Sucesso e Mapa RF→AT ficam redundantes ·
Contexto Técnico **sai** (é COMO) · Histórias viram 1–2 linhas.

### I.9 — O repo é um plugin, namespace `toolkit` ✅

**Decidido (30-07-2026).** `.claude-plugin/plugin.json` com `name: toolkit` na raiz. Toda peça
carrega namespaced: `skills/spec/SKILL.md` → **`/toolkit:spec`**.

**Problema que resolve:** nome curto e genérico colide. Pior: o toolkit é instalado em
`~/.claude/skills/` (escopo **personal**), e **personal sobrescreve project** — um `spec` nosso
apagaria silenciosamente um `spec` de qualquer projeto que tivesse um. Skills bundled também
estão em risco (`code-review` já era um conflito conhecido, ver G.5).

**Por que não custa a leading word:** *"The bare `/fancy` also invokes the skill unless another
command already uses that name."* → `/spec` continua funcionando como atalho quando está livre;
`/toolkit:spec` sempre funciona. Nome curto preservado, colisão eliminada.

**Fatos da doc (`plugins-reference`):**

- Qualquer pasta sob um skills directory com `.claude-plugin/plugin.json` carrega como plugin
  `<name>@skills-dir` **sem marketplace e sem install step** — descoberta em lugar, não copiada.
- `name` é o **único campo obrigatório** do manifesto, e é ele que faz o namespacing.
- Plugin skills **"cannot conflict with other levels"**.
- Plugin empacota também **hooks, agents e MCP servers** → resolve a instalação dos hooks do
  `structure-cache`, hoje feita por script à parte.
- `claude plugin disable toolkit@skills-dir` desliga tudo de uma vez.
- Mudança em `SKILL.md` vale na hora; mudança em `hooks/`, `agents/`, `.mcp.json` exige
  `/reload-plugins`.
- ⚠️ Plugin `@skills-dir` de escopo **project** carrega só do `.claude/skills/` do diretório
  onde o Claude Code foi iniciado — **não sobe até a raiz do repo** como skill comum faz.

**Consequência estrutural aplicada:** `skills/` passou a ser o diretório varrido pelo scanner,
então **nada morto pode viver lá**. `skills/deprecated/` e `commands/deprecated/` foram
consolidados em `deprecated/{skills-v9,commands-v9}/` na raiz. É a mesma armadilha que o v9 já
tinha com `commands/references/`.

**Resolve também a decisão #3** (Parte D): morre o prefixo `sdd-`, o repo mantém a identidade
"toolkit".

**⏳ A validar:** se `~/.claude/skills/toolkit` pode ser um **symlink** pro repo (editar no repo,
ativo na hora). A doc confirma symlink para skill comum, mas ressalva que "plugin skills handle
symlinks differently". Teste barato: criar o symlink e rodar `claude plugin list`.

### I.10 — ~~⏳ Em aberto~~ ✅ **RESOLVIDO em 31-07-2026** (ver no fim): o legado v9 em `thoughts/`

`thoughts/specs/` e `thoughts/plans/` → `thoughts/changes/NNN-slug/`. O que já se sabe:

- Specs/plans v9 **não precisam se mover**: wikilink resolve por nome de arquivo em todo o vault,
  e o roadmap guarda `plan:` como basename. Nada quebra sozinho.
- O que fica órfão: mudança v9 **ainda aberta** (spec escrita, PR não mergeado) não fecha, a menos
  que o `pr-close` novo saiba ler os dois layouts.

Opções: **coexistir** (v9 termina no v9, `pr-close` detecta o layout) · **migrar tudo** (exige parear
spec↔plan↔IMP↔review, que nem sempre casam) · **migrar só o que está aberto**.

### I.11 — Validação da spec: adversário, não juiz ✅

**Fato levantado:** **nenhuma das três fontes valida a spec com agente separado.** parruda faz
auto-verificação ("releia o arquivo, confira se as seções estão presentes"); o v9 faz igual
(Passo 8) e usa subagentes só na *pesquisa*; o OpenSpec põe a verificação no **humano**
(two-minute pass). O painel de subagentes do v9 vivia no `/sdd-plan`, não na spec.

**Problema:** auto-verificação pega erro de forma, não pega **ausência**. Se o autor soubesse que
faltava um requisito, teria escrito. E "este cenário exercita ou só repete o requisito?" é
exatamente o critério que quem escreveu não consegue aplicar em si mesmo.

**Decidido: adversário, rodando sempre.** Subagente com contexto limpo, read-only, que devolve
**lista de ataque** — nunca veredito.

Ordem de gravidade que ele persegue: **ausência** (comportamento que o código faz e a spec ignora,
borda não coberta, requisito sem cenário, consumidor que quebra) → **delta errado** (`ADDED` que
é `MODIFIED`, `C<N>` inexistente) → **não-testável** (linguagem vaga, número ausente) →
**forma** (multi-cláusula, cenário que repete, COMO vazando).

**Por que adversário e não juiz:** validador que aprova vira anestesia — "o agente validou, deve
estar bom" — e adiciona mais uma camada entre o usuário e o artefato, que é o problema da Parte 0.
Trocaríamos ler 300 linhas por ler um ✅. Por isso ele é **proibido de emitir veredito**, proibido
de reescrever a spec, obrigado a ancorar todo achado em `arquivo:linha`, e obrigado a fechar
dizendo **onde olhou** — pro usuário saber o que *não* foi coberto.

O gate real continua humano: *"você ficaria confortável se isto fosse construído exatamente
assim, e nada além?"*

**Forma:** o prompt vive em `skills/spec/adversary.md`, lido **pelo subagente** via
`${CLAUDE_SKILL_DIR}` — nunca entra no contexto principal. É o padrão a repetir nas outras peças:
instrução volumosa que só o subagente precisa fica em arquivo irmão, referenciado no prompt dele,
não no `SKILL.md`.

### I.12 — Uma mudança = três arquivos ✅ (31-07-2026)

Correção do I.1, a pedido do usuário: *"estamos gerando muito arquivo .md aqui"*.

```
thoughts/changes/NNN-slug/
  spec.md    o quê + delta da capability
  plan.md    o como — abordagem, decisões técnicas, e a seção ## Testes
  tasks.md   checklist + fronteira de PR
```

`notes.md` sai do planejamento — é da peça de execução e só nasce se houver evidência a registrar.

**Peça própria ≠ arquivo próprio.** O `test-plan` é skill separada (ganho por sequência) e escreve
**dentro** do `plan.md`. Separar a skill preserva o guardrail; separar o arquivo só multiplicaria
andaime.

**Por que `plan.md` e `tasks.md` não fundem:** só o `tasks.md` muda de estado durante a execução
(checkbox, evidência de gate). Fundidos, a execução reescreveria o plano inteiro a cada tarefa
marcada, e conflitaria com o usuário editando. Mesmo motivo pelo qual o OpenSpec separa `tasks.md`
de `design.md`.

**O que acontece no fim:** a pasta inteira vai pra `thoughts/changes/archive/YYYY-MM-NNN-slug/`.
O que tinha valor permanente já subiu pra `thoughts/capabilities/<domínio>.md` — a capability é o
único documento que sobrevive à mudança. Os três acima são andaime: `thoughts/` é local e
gitignored, ninguém do time os lê. **Artefato que nem o usuário lê nem outra peça consome não
deveria existir.**

### I.13 — Fronteira de PR mora no `tasks.md` ✅ (31-07-2026)

No v9 era o **Check 5**: calculado no fim, anotado como uma linha (`PRs: 3`) no topo do PLAN, e
espelhado à mão em N itens de roadmap pelo Passo 12.5. Ficava longe das tarefas, que são
justamente a unidade que se agrupa em PR.

No v10 o `tasks.md` **agrupa as tarefas por bloco de PR**. Consequências de graça: a contagem vira
a união verificável dos paths do bloco (não estimativa de fim de plano), o corte respeita
dependência por construção, e a Onda 2 lê 1 item de roadmap por bloco com o `Depende de:` já
escrito — o Passo 12.5 inteiro deixa de existir.

**Faixa apertada** (o v9 tratava 11–15 como "aceitável"):

| Arquivos distintos no diff | Ação |
|---|---|
| ≤8 | segue |
| 9–13 | segue, contagem anotada no bloco |
| ≥14 | **propõe fronteira de corte** e pergunta antes de seguir num PR só |

Vem do usuário: *"prs com mais de 13 a 15 arquivos alterados se torna muito difícil o review
humano [...] eu em particular prefiro prs pequenos"* — mantida mesmo reconhecendo que o time revisa
código cada vez menos. Regra do v9 que continua: **nunca dividir sozinho**, nunca reescrever a
spec pra caber. Propor a fronteira, deixar a decisão com ele.

### I.14 — As lentes ficam; o veredito e o loop saem ✅ (31-07-2026)

**Correção de rumo do usuário**, contra proposta minha de eliminar o painel de review do v9:
*"as avaliações não precisam ser excluídas, eu entrar mais nesse processo é mais para agregar"*.

O defeito do v9 nunca foi a avaliação existir. Foi ela ser **consumida pelo agente antes de chegar
nele**: painel → agente verifica cada `must-fix` → aplica → nova rodada com subagentes frescos →
repete até `APPROVED` → o usuário recebe `"Aprovada em 2 rodadas — 0 must-fix aberto"`. Todo o
conteúdo virou placar.

| v9 | v10 |
|---|---|
| Loop até `APPROVED` | Uma rodada |
| Agente reconcilia sozinho | Achados na tela como vieram, discordância anotada junto |
| Usuário vê "0 must-fix aberto" | Usuário vê os N achados |
| 4 lentes (Pro, Fast, Security, Tests) | 3 (Arquitetura, Executabilidade, Segurança) |

**Tests saiu** porque virou a skill `test-plan` inteira, com três lentes próprias — revisar de novo
o que o usuário acabou de decidir seria reabrir decisão dele.

**Régua geral pro resto do refactor:** ao portar mecanismo de avaliação do v9, cortar o **veredito**
e o **loop de auto-reconciliação**, preservando a perspectiva. Cortar a avaliação inteira não
devolve entendimento — devolve menos informação.

### I.15 — ⏳ Em aberto: a volta barata (`update`)

O I.2 identificou que a ausência de um `update` é a causa mecânica da dívida do v9. O `plan` ganhou
uma seção "Se o plano já existe" que cobre o caso mínimo (revisar plano existente, mostrar o que
isso invalida nas tarefas). **Não decidido:** se a volta barata é branch de cada peça ou peça
própria que reconcilia spec + plan + tasks de uma vez. Resolver quando `implement` existir — é lá
que a divergência aparece.

### I.16 — O `implement` orquestra; o paralelismo é por ambiente ✅ (31-07-2026)

**Decisão do usuário:** o main deixa de ser implementador e vira **orquestrador e validador** —
identifica tarefas independentes, delega a subagentes que rodam em paralelo (todas as chamadas
`Agent` no mesmo turno, ou serializam), e confere cada retorno contra gate e contagem. Executa
direto só o sequencial.

**A unidade de escalonamento é o `Test env:`** que o `plan` declara por tarefa:

| Tarefas | Como rodam |
|---|---|
| Ambiente `none` | paralelo |
| Mesmo ambiente compartilhado | grupo sequencial, ambiente sobe **uma vez** pro grupo |
| Com dependência declarada | sequencial |

Isso resolve o conflito que o usuário levantou: **o red de um e2e precisa do ambiente, e o ambiente
é um só.** As alternativas que ele mesmo listou tinham custo — "rodar integração/e2e só no final"
mataria o red dessas tarefas, porque o teste nasceria depois do código (falso-verde garantido).
Agrupar por ambiente preserva os dois: cada tarefa tem sua vez com o ambiente de pé.

**Ambiente compartilhado tem o usuário como árbitro, não um lock cego.** Marcador em
`<root>/thoughts/.env-em-uso` (no repo principal — único lugar visível entre worktrees) com branch,
tarefa e hora. Ocupado → **pergunta**, dizendo quem usa e desde quando, e aguarda o OK, adiantando
enquanto isso as tarefas sem ambiente.

⏳ **Pendência sem bloqueio:** isolar ambiente por worktree (porta e banco por env var). Quando
existir, some a pergunta e sobra o caminho livre — o desenho atual não muda.

### I.17 — Um modo só no `implement` ✅ (31-07-2026)

O v9 tinha autônomo (default) e `--step`, com **cada passo escrito duas vezes** (~150 linhas de
duplicação) pra uma diferença de duas coisas: pausa entre tarefas e momento do commit.

Morreu a flag. O que mantém o usuário no circuito são as **paradas duras**, que nunca dependeram do
modo — e pausa entre tarefas é incompatível com subagentes paralelos de qualquer forma. O commit
atômico continua como opção no fechamento.

### I.18 — Limite do red no subagente: auditado, não re-executado ✅ (31-07-2026)

O orquestrador **não re-executa** o red do subagente — refazer exigiria desfazer a implementação e
custaria a execução inteira. O que é determinístico é a **contagem de testes**; a evidência do red
é a **saída literal do runner** (`red.saida`), verificada na forma: falha por comportamento ausente
versus falha por import ou setup.

Isso está declarado no `SKILL.md` de propósito. Invariante que se apresenta como garantido sem ser
é pior que invariante com limite conhecido — o primeiro produz confiança falsa exatamente onde o
usuário deixaria de olhar.

### I.19 — `worktree` é uma peça só (criar + remover) ✅ (31-07-2026)

Pergunta do usuário: *"vc vai unificar os comando de worktree? pq quando fechamos um pr a worktree
morre tbm."* Sim.

Mesmo recurso, mesmo conhecimento: quem cria decide onde monta, o que liga no symlink de memória e o
que escreve no `.gitignore`; quem remove **desfaz exatamente isso**. Separado, esse conhecimento
vive em dois lugares e desanda junto — o `unlink` que jamais pode ser `rm -r` (seguiria o symlink e
apagaria o `memory/` do root) só faz sentido conhecendo a criação.

Pela Parte C.4, separar exigiria ganho por invocação ou sequência. Não há.

### I.20 — ⭐ `modo-livre` vira arquivo, não peça ✅ (31-07-2026)

Veio da descrição do próprio usuário: *"na criação do worktree eu usava o modo-livre para a worktree
o harness já nascer com os bloqueios de git commit e push principalmente."*

O nome dizia autonomia; o valor citado é a **cerca** — `ask` em commit/push, `deny` nos destrutivos.
Isso não é comportamento a instruir, é **configuração a copiar**: lição H.5 (o determinístico vira
artefato, não prosa). O JSON de 174 linhas sempre foi a fonte da verdade; as 294 linhas de prosa em
volta eram instrução pra copiar arquivo e escrever marker.

Virou `skills/worktree/permissions.json`, copiado **integralmente e sem edição** na criação. O
`SKILL.md` proíbe reconstruir as regras de memória ou "adaptar pro projeto": permissão inventada é
pior que permissão ausente — se o arquivo não estiver acessível, a worktree nasce sem cerca e isso é
**dito**, não silenciado.

⏳ **Suposição declarada, reversível:** o toggle no repositório principal não sobrevive como peça,
porque o uso descrito é sempre na criação da worktree. Perguntado duas vezes sem resposta. Se o
usuário liga/desliga o modo no root, o toggle volta e o JSON segue sendo a fonte.

### I.21 — Todo artefato de `thoughts/` mora no repositório principal ✅ (31-07-2026)

Buraco encontrado ao escrever a `worktree`: as peças da Onda 1 apontavam para `thoughts/changes/…`
sem resolver o root. Como **`thoughts/` é gitignored, a worktree nasce sem ele** — o `implement`,
que roda dentro da worktree, escreveria numa pasta diferente da que o `plan` escreveu, e o
`pr-sync` não acharia o `notes.md`.

Regra: **`root = git worktree list | head -1`**, e vale pra toda leitura e escrita em `thoughts/`.
Corrigido em `spec`, `plan`, `test-plan` e `implement`.

O v9 tinha isso certo (a seção "Resolução do diretório root" aparecia em quase todo command) — se
perdeu na reescrita porque a worktree só entrou em cena depois. **Achado a favor de construir as
peças que o usuário realmente encadeia, e não só as do núcleo conceitual.**

### I.22 — Kickoff e sync na mesma peça ✅ (31-07-2026, correção)

Separei o `sync` numa skill `pr-sync` e **voltei atrás a pedido do usuário**: *"não dava pro pr-draft
ter um sync para ficar tudo em um só ou é ruim?"*

Ele estava certo. Meu argumento era custo de contexto — mas as duas peças são
`disable-model-invocation: true`, então **só entram no contexto quando invocadas**, e a diferença
real eram ~80 linhas numa invocação. Irrelevante.

O custo que user-invoked paga de verdade é **cognitive load** (Parte C): lembrar que a peça existe.
`pr-draft sync` já está na memória muscular dele; uma peça a mais é mais uma pra esquecer.

E era **inconsistente com a I.19**, tomada minutos antes: unifiquei `worktree` (criar + remover)
argumentando "mesmo recurso, conhecimento compartilhado" — e o corpo do PR é exatamente isso, com a
regra "não vaze artefato interno" valendo idêntica nos dois modos.

**Régua daqui pra frente:** em peça user-invoked, o custo de contexto quase nunca justifica dividir
— ela só carrega quando chamada. Divida por **gatilho distinto** ou por **sequência** (Parte C.4),
nunca por tamanho do arquivo.

### I.23 — Uma peça de review só; entrega é outra coisa ✅ (31-07-2026)

O usuário descreveu o fluxo real e ele separou as águas sozinho:

> *"o code-review aqui é revisar toda a implementação feita caso não tenha feito review, ter as
> lentes para revisar tudo e corrigir o que tiver errado ou delegar novamente para implement.
> [...] quando eu pedia para pr-ready o que queria é que ele validasse que estava tudo coerente,
> que o código fosse bom, para então tirar o pr de draft e marcar o revisor. em seguida quando o
> revisor deixasse seus comentários, quando eu pedia sdd-review era depois das correções feitas
> avaliar que o que foi pedido no review pelo time foi atendido pra depois solicitar nova revisão."*

```
implement → code-review          → pr-ready
            (lentes, corrige)      (verde → draft off → revisor)
                                          ↓  time comenta
            code-review          → pr-ready
            (o pedido foi atendido?)  (re-solicita revisão)
```

Cada peça tem **dois momentos**, detectados pelo estado do PR — estrutura que o `pr-ready` v9 já
tinha e que estava certa. O errado era **três peças** (`sdd-review`, `pair-review`, `pr-ready`)
fazendo pedaços sobrepostos disso, exatamente a `duplication` que a Parte C listou.

**O `implement` perdeu as lentes próprias** e passa a invocar o `code-review` — que tem seis contra
as três que eu havia posto lá. Mesmo padrão de `plan` → `test-plan`: quem faz não revisa a si mesmo.

### I.24 — ⭐ Correção de review que muda comportamento volta pro `implement` ✅ (31-07-2026)

Pedido do usuário: *"corrigir o que tiver errado ou delegar novamente para implement para poder
fazer as devidas correções."*

No v9 as correções saíam pelo Action Plan (Etapa 6 do `/sdd-review`) via `/quick-task`, que **não
tem TDD, red verificável nem test count protection**. Uma correção de review que altera
comportamento entrava por um caminho paralelo que escapava de todos os invariantes da Parte E.5 — e
é justamente o tipo de mudança feita com pressa, no fim do ciclo, quando ninguém quer reabrir nada.

Fronteira agora explícita:

| A correção | Caminho |
|---|---|
| Não muda comportamento (nome, typo, extração local, guarda em caminho já testado) | corrige na hora, com gate + proteção de contagem |
| **Muda comportamento** | vira tarefa em `tasks.md`, bloco `## Correções do review` → `implement` |
| Cresce (decisão arquitetural, lib nova, redesenho) | para: é mudança de plano, não conserto |

### I.25 — Sem relatório de review em arquivo separado ✅ (31-07-2026)

O v9 salvava `thoughts/reviews/REV-DD-MM-YYYY-slug.md` com template de 163 linhas. Dois motivos pra
não recriar: era mais um dos cinco lugares onde uma mudança morava (I.12 fez virar um), e **relatório
salvo é convite a não ler** — o arquivo existe, logo o review "aconteceu".

Achados vão pra tela; o que sobrevive (correções feitas, dívida aceita com motivo, o que ficou fora
do alcance das lentes) é registrado no `notes.md` da própria mudança.

### I.26 — ⭐ A simplificação é o *refactor* do TDD, e volta ao `implement` ✅ (31-07-2026)

Pedido do usuário: *"antes de delegar para o code-review acho que ele pode pedir o code-simplifier...
porque meio que atende o fluxo do TDD né, que vai refatorar pra simplificar daí os testes têm que
passar de novo."* Ele estava certo sobre o encaixe — red, green, **refactor**; a passada só é segura
porque a suíte já está verde, e a suíte roda de novo depois. Sem essa, o ciclo do toolkit parava no
green.

**Três decisões dentro:**

1. **Um ponto de invocação, não três.** O v9 chamava no fim de cada tarefa, no fim do grupo paralelo
   e na verificação final. Por tarefa colide com os subagentes paralelos do I.16 — e o próprio v7 já
   admitia isso ("em modo autônomo: pule, simplifier no fim, reduz ruído entre tarefas"). Ficou entre
   o gate de verde e o `code-review`.
2. **Fronteira trivial × estrutural vai no prompt de invocação.** O agent oficial declara que
   *"operates autonomously and proactively"*, então pedir educadamente no fim não adianta: a restrição
   entra no prompt. Local aplica (comentário redundante, `let`→`const`, early return, guard duplicado);
   estrutural **descreve e não aplica** (split, arquivo novo, assinatura pública, código movido,
   abstração extraída). Base factual: memória de feedback do usuário no gopay
   (`simplify-ask-before-structural-changes`), com os PRs #270 e #272 — o **mesmo** split sugerido e
   rejeitado duas vezes, porque o design unificado com flag era intencional. É a I.14 outra vez: o
   agente levanta, o usuário decide.
3. **Dependência opcional, e o gate não afrouxa.** Plugin ausente → avisa e segue; simplificar é
   ganho, não gate. Mas teste que passava e quebrou depois da passada é **parada dura**, sem reverter
   sozinho e sem ajustar o teste — o simplifier pode ter esbarrado num acoplamento real. Herdado
   verbatim do v9: *"simplificação que quebra contrato é mudança de comportamento, não limpeza."*

Efeito colateral: a skill `simplify` que o CREDITS do `implement` prometia **não existe mais** na
fila. Não havia gatilho próprio nem passo escondido — só o custo de invocação de uma peça a mais
(Parte C.4).

### I.27 — ⚠️ Nenhuma peça invoca outra ✅ (31-07-2026, correção de bug)

**Fato da plataforma, verificado na doc oficial**, não escolha de estilo:

> *"Use `disable-model-invocation: true` to block **programmatic invocation**"* — e a tabela de
> invocação: `disable-model-invocation: true` → **"Claude can invoke: No"**.

Todas as peças do v10 têm essa flag (menos `grilling`). Quatro lugares mandavam invocar outra skill
e **nenhum funcionava**: `plan`→`test-plan`, `implement`→`code-review`, `pr-ready`→`pr-draft sync`,
`pr-draft`→`worktree`. Bug silencioso: a peça teria dito "invocando…" e nada aconteceria.

Três saídas foram oferecidas; **o usuário escolheu a mais conservadora** — não tirar a flag de
nenhuma. Toda transição vira instrução explícita, com o comando já preenchido, como última linha da
peça. Custo: quatro pontos de fricção no ciclo. Ganho: nada com efeito colateral acontece sem um
`/` digitado por ele. É o "usuário no volante" cobrando o preço dele, e ele pagou de olho aberto.

`grilling` continua sendo a única exceção — sem a flag desde a Onda 0, justamente pra que o agente a
puxe sozinho quando perceber que ia decidir algo que é do usuário.

### I.28 — ⭐ O determinístico vira script: o motor do `roadmap` ✅ (31-07-2026)

Primeira aplicação real da **lição H.5** (OpenSpec: o determinístico vira artefato, não prosa).
Escolha explícita do usuário entre script completo, script só de cálculo, e tudo em prosa como o v9.

O que virou código (`scripts/roadmap/roadmap.py`, no molde do `structure-cache`: Python 3 puro,
argparse, `--root` via git, `--json` pra consumo): numeração, escrita do item, guarda de ciclo,
detecção de órfão, cálculo dos 🔓 Desbloqueados, regeneração ordenada do hub. O que ficou na skill:
título, escopo, se vale virar item, se a dependência é real, e o parse do formato antigo na migração
— texto livre é julgamento.

**Por que é a decisão certa aqui e não em toda peça:** o contrato E.1 é escrito por *quatro* peças
(`roadmap`, `plan`, `pr-draft`, fechamento). Em prosa, ele seria repetido quatro vezes e divergiria
na primeira edição. Em script, existe uma vez e é executável. A I.27 reforçou: como nenhuma peça
invoca outra, as demais chamam o **comando** por Bash — que já era o desenho.

**Evidência de que valeu:** a verificação por execução encontrou um defeito que a prosa esconderia —
`dep NNN --on <inexistente>` escrevia lista vazia, ou seja, um número digitado errado apagaria em
silêncio todas as arestas do item. Em prosa isso seria uma instrução ambígua, e só apareceria com o
dado já perdido.

### I.29 — ⭐ Memória: o gargalo é o índice, não a organização ✅ (31-07-2026)

O usuário abriu pedindo pastas (*"vamos precisar separar por pastas talvez"*) e, no meio da conversa,
levantou a dúvida que valia mais que o pedido: *"a memoria é sempre carregada? pq acho q o trabalho
de memoria que fizemos pode não ter ajudado tanto quanto eu achei"*.

**Ele estava certo, e o dado mostra o porquê.** Medição no gopay (236 notas reais):

```
volume escrito:       460 KB        linkadas no índice:    42  (17%)  ← agem toda sessão
volume que carrega:    10 KB        só via sub-sumário:   192  (81%)  ← 2 leituras pra chegar
                                    órfãs:                  2
```

Fato da plataforma: **só o `MEMORY.md` carrega** (200 linhas / 25KB). O resto é lido sob demanda, e
sob demanda significa *se algo der o motivo*. Daí as três decisões:

1. **Pasta recusada com dado, não com preferência.** Mover 236 arquivos não muda os 10KB que entram
   na sessão. Pasta melhora navegação humana; o problema era recuperação. O investimento foi pro
   índice — o único nível que age — em três camadas: GUARDRAILs (age sem leitura), mapa de sintomas
   (é o que faz `bug` funcionar), sub-sumários (a cauda).
2. **O gancho virou critério de existência.** Sem uma linha que diga *quando* aquilo importa, não
   vira nota. Foi assim que 81% do acervo virou cauda inerte: notas escritas como registro do
   passado, não como gatilho pro futuro.
3. **Tipos 9 → 8, decididos por uso medido.** `idea` tinha **zero** notas; `preference` tinha uma, e
   era `decision` disfarçada; `blocker` (4) foi absorvido por `bug`, que descreve o que se procura em
   vez do efeito em você. Criado `win` — *"coisa que acertamos e podemos reforçar"* não tinha lugar
   no v9 e é o tipo que ninguém escreve espontaneamente. **Nada foi apagado**: *"não precisa apagar
   agora não"*. Tipo sai da oferta, nota fica.

### I.30 — ⚠️ O achado fora do plano: memória fragmentada entre configs (31-07-2026)

Rodar a auditoria no dado real revelou o que nenhuma discussão de formato teria achado — o mesmo
projeto com memória em **quatro** diretórios de config:

```
.claude        236 notas   (30-07)
.claude-m2      19 notas   (06-04)
.claude-code7    1 nota    (12-02)  ← ATIVA, e sem MEMORY.md
.claude-old      0 notas
```

Com `CLAUDE_CONFIG_DIR=~/.claude-code7`, o gopay carrega **zero** memória. Parte da sensação de que
"a memória não ajudou" não era qualidade da nota: era a sessão lendo o diretório errado.

Por isso a fragmentação é a **primeira** linha do relatório, antes de qualquer métrica de qualidade —
e por isso a skill **não consolida sozinha**: mover dado entre configs do usuário exige de-para na
tela e OK dele. Pendência aberta, deliberadamente.

Lição de método que vale além desta peça: **auditar o dado real antes de redesenhar o formato.** O
redesenho pedido (pastas) não teria resolvido nada; o problema estava numa camada que ninguém
suspeitava.


### I.31 — `pr-close` absorve o `sdd-learning`; `pr-audit` fica separado ✅ (31-07-2026)

Duas peças leem a mesma fonte (comentários de review) e a pergunta de granularidade (Parte C.4) deu
respostas opostas — o que mostra que a régua funciona.

**`sdd-learning` (500L) entrou no `pr-close`.** Gatilho idêntico: "o PR mergeou". Separar cobraria
custo de invocação sem esconder passo nenhum. Pedido do usuário: *"vamos ter um comando para fechar
o pr quando aprovado, dele vamos extrair os aprendizados e adicioná-los na memória do projeto e
também fechar o domínio"*. Os 6 filtros duros de destilação (CC-BY, tlc-spec-driven) foram pro
`learning-filters.md`, lido pelo subagente — fora do contexto principal.

**`pr-audit` ficou separado.** Gatilho distinto e assíncrono: *"quero saber que dívida sobrou dos meus
PRs"*, sobre uma janela de N PRs já fechados. `pr-close` é profilaxia no momento do merge; `pr-audit` é
resgate retroativo do passivo. Mesma fonte, momentos e escopos diferentes.

### I.32 — Nem todo determinístico vira script ✅ (31-07-2026)

Contraponto necessário à I.28, que poderia virar dogma. O `roadmap` e o `memory-audit` viraram
script; o `pr-audit` **não**, e pelo motivo que o próprio v9 já registrava: *"a montagem da lista de PRs
muda de `jq` conforme o filtro; um script fixo seria contornado na primeira variação."*

A régua não é "é determinístico?", é **"o formato é fixo e o cálculo é sempre o mesmo?"**. Roadmap:
sim — numeração, ciclo, desbloqueados. Auditoria: não — a consulta muda a cada pergunta e a triagem
é julgamento puro. O que varia por pergunta não vira comando.

### I.7 resolvido — `fix`/`chore` e a capability ✅ (31-07-2026)

Não é o tipo do commit que decide: é se **mudou o que o sistema promete**. Bug fix que corrige
comportamento observável vira `MODIFIED` (o que estava na capability não era verdade). Refactor,
dependência e build não tocam nada.

### I.10 resolvido — o legado v9 em `thoughts/` ✅ (31-07-2026)

Das três opções, ficou **coexistir**: o `pr-close` fecha cada mudança **no formato em que ela nasceu**.
Par SPEC+PLAN antigo vai pra `specs/closed/` e `plans/closed/`; capability, roadmap, colheita e
aprendizados são idênticos. Converter no fim do ciclo é risco sem ganho — a mudança está terminando
e um erro de conversão só apareceria muito depois.


### I.33 — Prefixo `pr-` para as peças do ciclo do PR ✅ (31-07-2026)

Pedido do usuário: *"acho q poderia seria pr-close e pr-audit so pra manter o padrão"*. `close` e
`audit` nasceram sem prefixo; `pr-draft` e `pr-ready` já tinham. Renomeadas.

Ganho real além da simetria: **`audit` sozinho é vago** — auditar o quê? `pr-audit` diz o escopo no
nome, que é o que a Parte C pede da leading word.

**Ressalva registrada e tratada:** dentro do padrão `pr-*`, todas as outras peças *agem no PR* —
`pr-draft` abre, `pr-ready` tira do draft, `pr-audit` varre PRs. **`pr-close` é a exceção: ele não
fecha nem mergeia nada**, age depois do merge e sobre os artefatos locais. Como o nome sugere o
contrário, a `description` abre com "DEPOIS que o PR já foi mergeado — não mergeia nem fecha PR
nenhum", e o corpo repete na primeira linha. O nome ganhou consistência; a description paga a
desambiguação.

Aproveitado na mesma passada: a tabela dos READMEs foi reordenada pela **ordem do ciclo** (estava
com `pr-ready` antes de `pr-draft`), com as transversais — `roadmap`, `memory`, `baseline`,
`grilling` — no fim.


### I.34 — ⭐ `pr-close` ganha o momento "aprovado, ainda aberto" ✅ (31-07-2026)

Furo apontado pelo usuário com a peça já commitada: *"as vezes o time aprova o pr e deixa follow-up
ou alterações opcionais a se fazer sem mergear, então o pr-close pode atuar tbm quando o pr esta
aprovado"*.

O gate `MERGED` veio do v9 e deixava um buraco de cobertura: **nenhuma peça do toolkit tratava
"aprovado com opcional pendente"**. E o que se perdia ali não era registro, era **janela** — o
`pr-audit` já registrava que corrigir dentro do PR aberto é o momento mais barato que existe, e que
o opcional recusado ali é dívida confirmada.

Dois momentos agora. Aprovado-e-aberto roda só colheita (4) e aprendizados (5), com a pergunta que
some no merge: corrigir agora (vira tarefa no `tasks.md`), aceitar como dívida, ou descartar com
motivo. Corrigir não é default — mais commits num PR aprovado podem exigir nova rodada de review.

**O invariante segurou o resto.** Aprovação não promove capability, não arquiva e não conclui
roadmap: E.5 diz *spec viva só sob merge*, e a capability é lida como verdade pela `spec` do ciclo
seguinte. Foi o invariante que definiu onde o novo momento para — sem ele, a tentação seria fazer o
fechamento inteiro e "corrigir depois se o PR mudar".

Lição de método: **buraco de cobertura aparece no uso, não na revisão da peça.** Três leituras da
`pr-close` não pegaram; a primeira tentativa de usar, sim.

---

### I.35 — ⚠️ `code-review` → `imp-review`: nome curto é reivindicação global ✅ (04-08-2026)

Fecha o **item 6 da G.5** (*"`code-review` colide com skill bundled — decidir se substitui ou usa
outro nome"*). A previsão estava certa; o que ninguém previu foi **por onde a colisão apareceria** —
não ao usar a nossa peça, mas ao usar a bundled a partir de outro projeto, cujo comando de review
orquestrado chama `/code-review` na primeira fase:

```
Fase 1: /code-review --effort medium
● Skill(code-review)
Error: Skill code-review cannot be used with Skill tool due to disable-model-invocation
```

A chamada resolveu pra nossa peça — que é `disable-model-invocation: true` de propósito (E.5,
*usuário no volante*) — e morreu no erro. A bundled nunca rodou.

⚠️ **Isso contradiz a doc oficial de skills**, que diz: *"Plugin skills use a
`plugin-name:skill-name` namespace, so they cannot conflict with other levels"*, e que uma skill de
projeto substitui a bundled homônima. Na prática, o **atalho de nome curto** do plugin ganhou da
bundled. Fato observado em execução, contra a doc — o namespace impede que a peça seja
*substituída*, não que ela *sequestre* o nome curto de outra.

**O dano é assimétrico, e é isso que importa registrar.** A nossa peça nunca ficou inacessível:
`/tk7:code-review` sempre funcionou. Quem ficou inacessível foi a peça *dos outros*. O namespace
protege quem o carrega e não protege quem é atropelado por ele — G.5 e I.9 só olharam para o
primeiro lado. **Um nome genérico num plugin instalado globalmente é reivindicação sobre todos os
projetos da máquina**, e ninguém consultou os outros projetos.

`imp-review` diz o que a peça faz — revisar a **implementação**, o passo entre o verde e o
`pr-ready` — e forma par simétrico com `pr-review`, que revisa o PR de outra pessoa. Renomeado o
diretório e todas as referências cruzadas (`implement`, `pr-ready`, `pr-review`, READMEs, `CLAUDE.md`,
`install.sh`), inclusive o caminho compartilhado `${CLAUDE_SKILL_DIR}/../imp-review/lenses.md`.
Citações literais do usuário nos `CREDITS.md` ficaram intactas: elas registram o que foi dito, não
o estado atual.

**Regra que fica:** nome de peça não disputa nome curto com o ecossistema. Vale para as peças
existentes também — reler a lista com essa lente antes do próximo nome.

---

### I.36 — ⭐ `test-qa`: a peça que fecha a dívida de verificação ✅ (07-08-2026)

Pedido do usuário: *"quero poder pedir para ele para fazer testes por mim [...] se for uma rota ele vai
testar tudo que puder, para tentar encontra possiveis bugs [...] listar os bugs inconsitencias erros de
escita comportortamenteos insperados"*.

A peça ocupa o slot que a Onda 3 reservava pro `verifica` — mas o `verifica` v9 era **checklist
derivada do IMP**, e o que ele descreveu é **exploração adversarial**: atacar a entrada procurando o
que ninguém previu. São coisas diferentes, e a segunda o v9 nunca teve.

**O encaixe que ninguém tinha notado:** a E.5, endurecida em 31-07, diz que o piso de verificação é
*"verificação manual executada pelo usuário, com evidência registrada — e isso é dívida, não pronto"*.
O `test-plan` **cria** essa dívida e nenhuma peça a **fechava**. É o primeiro item da rodada quando
existe mudança associada — o resto da peça é a exploração em cima.

**Quatro decisões contra o desenho original, todas escolhidas por ele:**

1. **Uma peça, dois momentos** (com mudança na pasta / alvo avulso). `verifica` sai da fila. Mesmo
   recurso, mesmo conhecimento de boot, mesmos guardrails — I.19 e I.22 outra vez.
2. **O main sobe o ambiente; subagente só explora.** O desenho original tinha um agente dedicado que
   subia os servidores e sinalizava. Subagente termina quando devolve o resultado: o processo fica sem
   dono pro teardown e o marcador `<root>/thoughts/.env-em-uso` (I.16) fica órfão. O paralelismo foi
   pra exploração, que é onde vale.
3. **Achados na tela e no `notes.md`.** `thoughts/qa/` seria o sexto lugar onde uma mudança mora — a
   I.12 fez virar um, e a I.25 já tinha matado `thoughts/reviews/` porque relatório salvo é convite a
   não ler. Ele mesmo hesitou no pedido (*"talvez dentro dos changes né, para seguir o padrão"*).
4. **Nome `test-qa`**, contra o `qa-sweep` que propus pelo risco da I.35. Ele fechou par simétrico com
   `test-plan` — argumento melhor que os três da minha lista: um decide o que a mudança garante, o
   outro vai ver se garante mesmo.

**O escalonamento por recurso compartilhado apareceu de novo, com outro recurso.** Na I.16 a unidade
era o `Test env:` da tarefa; aqui é o **navegador** (um só — lentes de tela serializam) e o **dado**
(lentes sobre a mesma entidade se corrompem). Mesma lógica, gatilho diferente. Sinal de que o
princípio é da arquitetura, não daquela peça.

**Risco que o usuário não levantou e a peça trata:** "testar tudo que puder numa rota" é fuzzing, e em
banco compartilhado isso vira lixo no ambiente de todo mundo. Prefixo obrigatório no dado criado,
listagem do que ficou e oferta de limpeza.

**A armadilha do grau `duvida`.** Comportamento não especificado que parece errado vira **pergunta**,
nunca bug. Sem essa separação a peça viraria lista de opinião com aparência de defeito — o mesmo vício
que a `spec` combate, um passo mais tarde no ciclo.

---

### I.37 — ⭐ Capability local × mudança de terceiro: detector de staleness ✅ (11-08-2026)

Achado do usuário: *"e se vier de outra pessoa? nós mantemos spec apenas local"*.

**O furo.** A capability é promovida no `pr-close` sob merge, e vive em `thoughts/`, que é
gitignored. Mudança que **nunca toca o seu fluxo em momento nenhum** — PR de outra pessoa, hotfix
direto na main, você mesmo em outra máquina — não tem por onde entrar. A capability local continua
afirmando o comportamento velho, e continua parecendo autoritativa.

**Isto não é o I.7.** Aquele item cobre PR *seu* sem spec (`quick-task`, `fix`, `chore`), e a
resolução de 31-07 depende de **você** rodar o fechamento. O que sobra é exatamente o que passa
longe de você. A terceira linha da tabela do I.7 (*"todo PR + auditoria periódica"*) tinha ficado
sem decidir; **este item a fecha.**

**A cadeia de dano, e por que ela é pior do que parece:**

1. `spec/SKILL.md` lê a capability como primeira fonte **e como critério de parada** da pesquisa —
   quanto mais confiável ela parece, menos se vai ao código conferir. O erro não só passa: ele
   *desliga* a verificação que o pegaria.
2. O delta sai errado — `[ADDED]` no que já existe, ou `[MODIFIED → <domínio> C<N>]` sobre um
   `C<N>` que não descreve mais nada real.
3. `pr-close` edita esse `C<N>` e **acrescenta** ao `[Origem]`. O rastro fica impecável e o
   conteúdo fica falso — que é o pior formato possível para um documento errado.

Em time o agravante é outro: **cada dev tem a sua capability**, e não existe ponto de reconciliação
entre elas.

**Metade da solução já está construída.** O `baseline`, sobre capability existente, já trata
contradição código × requisito com origem de spec como **achado** para o usuário decidir
(*"pode ser regressão, pode ser mudança que nunca foi sincronizada"*). A máquina de reconciliação
existe. O que falta é o **gatilho**: ninguém roda `baseline` num domínio que já tem capability,
porque nada avisa que ela envelheceu. O furo é silencioso — o atributo que a E.5 mais combate,
já que *capability errada é pior que capability incompleta*.

#### O que foi decidido: detector de staleness (opção A)

A capability passa a guardar **onde ela foi verificada pela última vez**, e a `spec` compara isso
com o repositório antes de confiar nela.

| Peça | Papel |
|---|---|
| frontmatter da capability | ganha `verificado-ate: <sha>` e `paths:` (os caminhos do domínio) |
| `baseline` | escreve os dois — ao derivar e ao complementar |
| `pr-close` | atualiza `verificado-ate` ao promover o delta |
| `spec` | **lê e avisa**, antes de usar a capability como critério de parada |

O sinal é um `git log <verificado-ate>..HEAD -- <paths>` no repositório principal. Havendo commits,
a `spec` mostra a contagem e os assuntos **antes de qualquer outra coisa** e oferece o `baseline`
no recorte suspeito.

**Não filtrar por autoria.** Tentador e errado: hotfix seu, commit seu de outra máquina e merge de
terceiro dão o mesmo estrago. O critério é *não passou por esta capability*, não *não foi você*.

**É aviso, nunca gate** (E.5, *usuário no volante*). Refactor que não muda comportamento vai
aparecer no range e isso é ruído aceito — o custo é uma linha na tela, e o detector é sinal, não
veredito.

**Sem `paths:`, o detector não roda — e diz que não roda.** O fallback é derivar os caminhos dos
`arquivo:linha` dos `[Origem]` derivados; numa capability inteiramente de origem de spec não há
nenhum, e aí a saída correta é declarar que a verificação não foi possível. Inventar cobertura aqui
seria repetir o próprio bug que o item conserta.

**Falso negativo assumido:** comportamento que muda por arquivo fora dos `paths`, ou por
dependência. O detector pega o caso comum e não promete os outros.

#### O que foi recusado, e por quê

- **B · tirar a capability do gitignore.** É a única solução *real* pro caso multi-pessoa — vira
  artefato do repo, o PR do colega atualiza, o merge conflita e alguém resolve. Fica registrada
  como o caminho de quando o time entrar no fluxo, porque hoje exige adoção que não existe e
  quebra a premissa de `thoughts/` local. **O A não vira dispensável nesse dia:** hotfix direto na
  main escapa dos dois.
- **C · auditoria periódica avulsa.** É o A sem gatilho automático e com custo por rodada bem
  maior. Só volta à mesa se o A se mostrar inviável.

#### O que só apareceu ao implementar

**Quem pode avançar o marcador não é quem promove o delta.** O `pr-close` parecia o lugar natural
pra manter o `verificado-ate` em dia — e é onde ele mais estragaria. Promover um delta não é
conferir o domínio; se entre o último marcador e este merge houver commit de outra pessoa nos
`paths`, avançar apaga exatamente o sinal que o item existe pra criar. Daí a condição: o `pr-close`
avança **só** quando o range não contém commit de fora do PR, e para o sha do merge — nunca o `HEAD`
do principal, que arrasta junto o que mergeou depois.

**O marcador nasce no `baseline` e em nenhum outro lugar**, porque ele é uma afirmação sobre ter
olhado o código. Capability antiga sem os campos não ganha um no fechamento: seria declarar
conferido tudo que veio antes. Fica sem detecção e as peças dizem isso.

**No `baseline`, o sha é capturado no início da sessão, não no fim** — a derivação demora, e gravar
o HEAD final afirma ter olhado commit que chegou durante o trabalho. E o marcador só avança sobre o
que foi de fato reconciliado: cobriu duas sub-áreas de cinco, o marcador fica onde está.

Os três casos são o mesmo erro em lugares diferentes — **marcador otimista vale menos que marcador
nenhum**, porque troca "não sei" por "está em dia". É a E.5 (*capability errada é pior que
incompleta*) aplicada ao metadado em vez de ao requisito.

**Implementado em:** `spec` (lê e avisa, antes do critério de parada) · `baseline` (escreve os dois
campos, e ganhou o caminho "domínio sinalizado" — percorrer o range em vez de cobrir o que falta) ·
`pr-close` (mantém sob condição, reporta marcador parado no sumário) · **E.2 atualizada**.

---

### I.38 — ⭐ `baseline --auditar`: o percurso inverso, do documento pro código ✅ (12-08-2026)

Pedido do usuário, na sequência da I.37: *"tem um baseline para forçar uma nova auditoria pra ver
se continua válido e o que novo entrou na capability?"*.

**O que faltava.** A I.37 fez a capability envelhecer *em voz alta*, e o `complementar` sabe achar
o que **entrou**. Nenhum dos dois acha o que **deixou de valer**: o `complementar` lê o documento
só pra saber o que pular, e o detector depende de commit nos `paths`. Requisito que apodreceu sem
tocar os `paths` — mudou dependência, config, ou o domínio vizinho — sobrevive intacto e com cara
de contrato. *"O que entrou de novo"* estava coberto; *"o que ainda vale"*, não.

**Auditar percorre ao contrário:** de cada `C<N>` pra evidência que o sustenta hoje. Três estados
— **confirmado** (só reaponta o `[Origem]`), **contradito** (achado, com os dois textos lado a
lado), **órfão** (pergunta: removido, renomeado, ou você não achou?).

**Terceiro momento da mesma peça, não peça nova** — I.19 e I.36 pela terceira vez. O conhecimento
de boot é idêntico (promessa × acidente, formato, `C<N>`, lotes, guardrails); só o alvo do percurso
muda. Separar em `capability-audit` duplicaria a tabela promessa × acidente, que é o coração da
peça — e, pela I.35, ainda reivindicaria mais um nome curto.

**As quatro decisões que valem o registro:**

1. **Os cenários apodrecem antes do requisito.** "DEVE recusar upload acima de 10 MB" continua
   verdadeiro em espírito quando o limite virou 20 MB — quem mente é o `Quando → então`, e é
   exatamente ele que a `spec` lê como fato. A auditoria é **cenário a cenário**, com o número na
   mão; requisito no atacado passaria por cima do único lugar onde o erro mora.
2. **A origem decide o que se pode fazer com o achado.** `[Origem: derivado]` corrige sob
   confirmação; `[Origem: spec · PR]` **não se toca** — leitura de código não tem autoridade sobre
   contrato entregue. Vira achado, e o usuário decide entre regressão (é bug, vira mudança) e
   dessincronização (é `MODIFIED` de uma spec futura). É a assimetria de "Se a capability já
   existe", agora requisito a requisito.
3. **Órfão confirmado vai pra `## Removido` sem PR** — `[Removido: auditoria de DD-MM-YYYY · sem
   evidência …]`. A auditoria descobre que sumiu e **não sabe por qual mudança**; preencher um PR
   ali seria falsificar rastro no único campo que existe pra rastrear. **E.2 estendida.**
4. **Os dois percursos não se misturam num lote.** Rodar auditar e complementar na mesma sessão é o
   que responde o pedido inteiro do usuário ("o que continua válido **e** o que entrou"), mas em
   passadas separadas — senão o usuário perde o fio de qual pergunta está respondendo, e o buraco
   novo compete com a revalidação pela mesma atenção.

**Ordem de ataque, porque a sessão pode acabar antes:** requisitos tocados pelo range do marcador →
`[Origem: derivado]` → o resto. Interrupção no meio já entregou o mais provável. E o marcador só
avança se o domínio inteiro foi auditado — parcial não avança, mesma regra da I.37.

**O custo que a peça assume, e mitiga:** auditar é N buscas dirigidas, uma por requisito. Por isso
é `--auditar` explícito, nunca de passagem — e o lote de 3 a 5 dispara os `Explore` **numa mensagem
só**, que é o que torna a passada viável em capability grande.

---

### I.39 — ⚠️⭐ O incidente do merge: `allow` amplo anula `deny` específico ✅ (12-08-2026)

**O que aconteceu.** Um agente mergeou um PR que ninguém mandou mergear:

```
gh api repos/OWNER/REPO/pulls/427/merge-async -X PUT -f merge_method=merge
```

O usuário resume a origem sem meias palavras: *"a minha resposta foi ambígua e ele fez o merge
errado"*. Consequência: PR de 2 commits e **zero reviews** entrou em `staging`, o deploy rodou e o
CI commitou `ci: Update Alchemy state and DB migration` por cima. O merge não parou no git — levou
junto migração de banco e estado de infra, que é o que torna `git revert` inútil aqui (o código
voltaria e o banco não). Decisão do usuário: **não reverter**, revisar pelo PR seguinte e trazer as
correções nele.

**A cerca existia e não pegou.** `skills/worktree/permissions.json` já negava `Bash(gh pr merge)` e
`Bash(gh pr merge *)`. Só que a mesma lista **permite `Bash(gh *)`**, e `gh api` faz tudo que a API
REST faz: mergear, fechar, apagar release, apagar repositório, trocar proteção de branch. O deny
cobria o **caminho conhecido**; a API é uma porta lateral que nenhuma regra previa.

**A lição, que vale além deste caso:** `allow` amplo de um binário com subcomando genérico
(`gh api`, `docker exec`, `devbox run`, `npx`) **anula toda a seção de `deny` daquele binário** —
qualquer ação negada pelo nome tem uma forma equivalente pelo genérico. Enumerar formas é uma
corrida que a enumeração perde, porque quem enumera precisa acertar todas e quem contorna precisa
achar uma.

#### O conserto: duas camadas, e a de baixo não é a declarativa

| Camada | O quê | Por que não basta sozinha |
|---|---|---|
| `permissions.deny` | 12 padrões novos de `gh api` (métodos de escrita, `*merge*`, `*protection*`) | enumera sintaxe — a próxima forma não prevista passa |
| **`tk7-guard`** (hook `PreToolUse`) | lê `tool_input.command` inteiro e sai com **2** | é a cerca de verdade: independe da forma do comando |

Verificado na doc antes de escrever, porque as duas premissas mudavam o desenho: **wildcard funciona
em qualquer posição** em regra Bash (`Bash(git * main)`), e **hook pode viver em
`settings.local.json`**, que é justamente o arquivo que a `worktree` escreve. Sem a segunda, o
pedido do usuário (*"quando a gnt criar worktree o settings já deveria vir com essa proteção"*) não
teria como ser atendido no lugar certo.

O guard barra merge de PR (`gh pr merge` **e** `gh api …/merge`), deleção pela API, mudança de
proteção de branch, `gh repo delete`, `gh release delete` e push forçado — incluindo
`git push origin +main:main`, que é force push com outra sintaxe. **25 casos em
`scripts/tk7-guard.test.py`**, metade deles falsos-positivos que precisam passar (`gh pr view`,
`gh api …/comments`, `git push -u`, `git merge` local). Guard sem teste apodrece e vira teatro.

**Três decisões que o incidente forçou:**

1. **Bloqueio duro, não `ask`.** Contraria o default do usuário (*`ask` é o gate pra
   exceção-humana*), e é o certo aqui: merge é ação que o time inteiro vê e que ele já faz pela
   interface do GitHub. O que a mensagem do guard diz ao agente é o essencial — *não tente outra
   forma; diga ao usuário o que você ia fazer e siga com o resto*.
2. **O guard falha aberto, e por isso a `worktree` confere.** Hook apontando pra comando ausente
   não bloqueia nada e não avisa ninguém: o Claude Code segue com a chamada. A skill roda
   `command -v tk7-guard` e **declara na entrega** se o guard está no PATH. Worktree que parece
   cercada e não está é pior que worktree sem cerca — a mesma regra do marcador otimista da I.37.
3. **A camada declarativa fica mesmo sendo redundante**, porque funciona sem nada instalado. Quem
   clonar o toolkit e não rodar o `install.sh` ainda leva os 12 denies.

**O que este item NÃO resolve, e é bom estar escrito:** `staging` não tem branch protection (404 na
API). O hook trava o agente nesta máquina; não trava mais ninguém, nem outra sessão sem o toolkit.
Proteção de branch no GitHub foi oferecida e não foi escolhida agora — quando for, é o complemento
natural deste item.

---

### I.40 — ⭐ Stacked PRs: `pr-draft stack` + `restack`, e o que a worktree quebra ✅ (19-08-2026)

**O desconforto que abriu o item:** o `plan` divide bem em PRs, e o `pr-draft` abria **um por vez** —
o time via um PR isolado, e o resto do desenho aparecia depois, sem contexto. O pedido do usuário foi
empilhar os PRs previstos no `tasks.md` de uma vez, criar as worktrees e receber os comandos na ordem
correta.

**O fato que mudou o desenho:** não existe `git stack` nativo. Existe a extensão oficial
**`gh stack`** — [stacked PRs do GitHub, public preview desde 30-07-2026](https://github.blog/changelog/2026-07-30-stacked-pull-requests-are-now-in-public-preview/)
— e ela **já estava instalada** na máquina do usuário (`gh 2.97.0` + `gh stack v0.1.0`). O pedido era
viável; o que não era óbvio é onde ele colide com o toolkit.

**Quatro achados, todos medidos num repo sandbox — não inferidos da doc:**

1. **`gh stack init b1 b2 b3` adota branches existentes** e monta a cadeia (`main ← b1 ← b2 ← b3`),
   e funciona **offline, sem remote**. É o que permite criar as branches com commit e mensagem
   controlados *antes* de empilhar, em vez de aceitar o que a extensão gera.
2. **`gh stack submit` sem flag abre uma TUI de tela única** — inoperável por agente. `--auto`
   dispensa o editor **e cria os PRs em draft** (`--open` é que tira do draft). Títulos e corpos
   auto-gerados são placeholder: o corpo curado entra depois, por `gh pr edit --body-file`, um por
   camada. Isso preserva integralmente a regra do corpo público desta peça.
3. **⚠️ Worktree por PR quebra o cascade rebase.** Com as branches presas em worktrees:
   `✗ could not start rebase of feat/two onto feat/one: fatal: 'feat/two' is already used by worktree at …`.
   A extensão rebaseia por checkout, e git não deixa duas árvores na mesma branch. Pior: **de dentro
   da worktree o `gh stack` não vê a stack** — o metadado vive em `$GIT_DIR/gh-stack`, e na worktree
   `$GIT_DIR` é `.git/worktrees/<nome>/`; a resposta é *"current branch is not part of a stack"*, que
   parece stack perdida e não é. O contorno **funciona e foi testado**: cascade manual de baixo pra
   cima, `git -C <worktree> rebase <parent>`, com a stack continuando reconhecida pelo `view`.
4. **⚠️ `gh stack merge` mergeia a cadeia inteira num comando — e passava livre.** O `tk7-guard` só
   casava `gh pr merge` e `gh api …/merge`, e `Bash(gh *)` no allow anula o deny (I.39). Era o
   incidente da I.39 multiplicado por N PRs, esperando acontecer.

**As quatro decisões (do usuário, com o panorama na tela antes):**

1. **Modo `stack` dentro do `pr-draft`**, não peça nova. As regras de corpo público, título, branch e
   roadmap já vivem ali — peça própria ganharia leading word (Parte C.4a) e pagaria em duplicação.
   A peça vai a 4 modos: kickoff · `stack` · `restack` · `sync`.
2. **Nenhuma worktree automática.** O modo abre a cadeia e **entrega os comandos `/tk7:worktree` na
   ordem**, com o aviso que importa: PR empilhado é PR dependente, e abrir os N terminais de uma vez
   deixa as camadas de cima escrevendo sobre base que ainda vai mudar. Mantém a I.27 (nenhuma peça
   invoca outra) sem duplicar a lógica de permissões e memória da `worktree`.
3. **Modo `restack` worktree-aware:** sem worktree, `gh stack sync` no root; com worktree, o cascade
   manual de baixo pra cima. O rebase é local; o `push --force-with-lease` que publica é **do
   usuário** — o guard barra, e barrar aqui é o comportamento certo.
4. **Só o `merge` entrou no guard** (`gh stack merge`, + deny declarativo no `permissions.json`).
   `unstack` e `modify` ficaram de fora: não mergeiam nem apagam código, e `modify` tem `--abort`.
   Suíte do guard: **31 casos, 0 falhas** — incluindo `gh stack init/submit/view/sync/rebase` e
   `git -C <wt> rebase` como falsos-positivos que precisam passar.

**Duas pendências escritas de propósito:**

- **[A VERIFICAR]** se `gh stack submit` (push + API, sem checkout aparente) passa com as branches
  presas em worktrees. Só dá pra medir contra um remote real; o sandbox não tinha.
- **`gh stack sync` faz `push --force-with-lease --atomic` por dentro**, e o guard não vê o interior
  do `gh` — barra `git push --force` e deixa passar o force da extensão. Não é furo do mesmo tamanho
  do `merge` (reescreve branch de PR próprio, não muda o `main` de ninguém), mas é assimetria real.
  Barrar ou não é decisão do usuário; fica registrado, não resolvido em silêncio.

### I.41 — ⭐ `test-plan` invertido: ele lista, as lentes criticam ✅ (25-08-2026)

**A queixa:** *"não sei se o test-plan está me agradando, me parece que ele tá crescendo demais os
testes e talvez poderia aproveitar, e eu tô perdendo a mão nos testes — acho que aqui talvez eu
devesse ter mais autonomia e a IA menos."*

Três defeitos de desenho, todos localizáveis no `SKILL.md` de 31-07:

1. **Três geradores, nenhum podador.** As lentes só somavam. A Adversarial era instruída a *não
   repetir happy path* — logo, tudo que ela devolvia era caso adicional. A única redução prevista
   era "deduplique casos equivalentes": matava repetição, nunca caso de baixo valor.
2. **Cobrir era default; cortar era exceção com pedágio.** A regra da E.5 exige pergunta pra deixar
   requisito sem verificação. Todo o atrito ficava do lado de tirar, nenhum do lado de pôr.
3. **Reuso era rodapé.** O campo `reusa` existia no JSON, mas o inventário só alimentava a contagem
   baseline. Nada mandava abater caso contra teste que já cobria aquilo, nem preferir estender
   arquivo existente a criar um novo.

E o quarto, que é o que ele chamou de perder a mão: **a autonomia dele era de veto, não de autoria.**
Ele chegava numa tela com N casos prontos e ✅/⚠️/❓ e carimbava. O trabalho que faz aprender o
sistema — escolher quais cenários importam — já tinha acontecido antes de ele chegar.

**A inversão (escolha dele, entre três desenhos):** a skill levanta o terreno e **para**. Tela 1 não
contém um único caso de teste — só o que existe hoje, o que já cobre a mudança (abate), o que dá pra
reusar, e os requisitos nus. Ele escreve o rascunho de uma vez, em texto corrido. Só então as lentes
rodam, e rodam **sobre a lista dele**, com três blocos de saída: `descoberto`, `redundante`, `caro`.
Dois desses três reduzem a suíte.

**Escolhas dele que contrariam o meu default:**
- **Rascunho de uma vez**, não requisito por requisito — ele quer ver o conjunto enquanto pensa.
  Escape hatch: `"R3: me sugere"` proponho só aquele.
- **Crítica sem teto de quantidade**, priorizada por impacto — o panorama do risco é dele. Mitigação
  que sobreviveu: **todo achado nasce fora da matriz** e entra só com um sim. Ele não corta de uma
  lista pronta, ele puxa pra dentro.

**O que não mudou, de propósito:** o contrato de saída (`## Testes` com tipo, ambiente, gate e
contagem). `plan` quebra tarefas herdando dela e `implement` roda o gate contra ela — o processo de
chegar na matriz mudou inteiro, o formato dela não podia. A E.5 também ficou: reexaminada, ela não
é a causa da inflação (o piso dela é verificação manual, que comprime). Ganhou um parágrafo dizendo
o que ela **não** pede: nem teste automatizado, nem mais de um caso, nem borda.

**Marca de origem nova na matriz:** `[usuário]` e `[lente]` por caso. PR a PR, dá pra ver quanto da
suíte ele decidiu e quanto a máquina empurrou. E a contagem `+K` virou explicitamente **piso, não
meta**.

### I.42 — ⭐ `glossary`: o jargão se aprende, não se traduz ✅ (25-08-2026)

Na mesma conversa da I.41: *"ainda usa muito termo técnico que eu não estou acostumado, gate, nit
entre vários outros, isso torna leitura muito densa"* — e em seguida: *"e tá sendo em tudo
ultimamente"*.

A contagem nas 16 skills: `lente` 84 · `red/green` 53 · `gate` 48 · `baseline` 20 · `nit` 5, mais
`must-fix`, `flaky`, `fixture`, `dedup`, `trade-off`, `overhead`. Quase tudo veio da referência em
inglês, entrou sem tradução e virou vocabulário da casa.

**Eu propus traduzir tudo. Ele recusou, e o argumento dele é melhor:** traduzir esconde o termo. Ele
continuaria sem entender PR, documentação e conversa de fora, que usam `gate` e `nit` de qualquer
jeito. *"Monta uma tabela pra eu usar como dicionário e a gente ir alimentando isso, daí acho que
consigo ir aprendendo os termos."*

**A peça:** `~/.claude/thoughts/glossario.md`, arquivo único e **global** — não por projeto, senão
`gate` seria explicado três vezes e o vocabulário ficaria picado. Nasceu com 22 verbetes, cada um com
a frase real da skill onde o termo aparece. `🆕` marca o que entrou e ele ainda não leu, o que
transforma arquivo de consulta em coisa que dá pra estudar aos poucos.

**Cresce dos dois lados:** quando ele pergunta, e quando o agente usa termo que ainda não está lá —
grava e avisa numa linha, sem parar o assunto pra dar aula. O segundo gatilho é o que faz volume sem
depender de ele lembrar de perguntar, e vale em qualquer projeto: vive na auto-memory
(`feedback_jargao_registra_no_glossario`), não só nesta skill.

**Skill e memória coexistem de propósito.** A memória carrega o gatilho (uma frase, custo baixo em
todo contexto); a skill carrega o procedimento — consulta, listagem, marcar lido, como escrever um
verbete bom. Procedimento em memória seria peso morto em toda conversa.

**Aberto:** a densidade também é ritmo de escrita, não só vocabulário — frase de três andares com
dois apartes no meio. Foi levantado, não resolvido. A memória registra a diretriz pra prosa dirigida
a ele; os `SKILL.md` continuam como estão.

### I.43 — ⭐ `implement-strict`: papéis separados, e o red que volta a ser executado ✅ (02-09-2026)

*"queria testar outra abordagem para ver no que dá (…) dois agentes separados, um totalmente focado
em criar os testes e outro totalmente focado em código, o que escreve teste não opina em código e o
que escreve código não opina em testes."*

Não é insatisfação com o `implement` — é experimento deliberado, e as duas peças coexistem. A Parte
C.4(a) autoriza: gatilho próprio.

**O ganho real, que não estava na pergunta.** O `implement` declara um limite (I.18): o orquestrador
**não** re-executa o red do subagente, porque quando o retorno chega o código já existe e desfazer
custaria a execução inteira. Cortando o ciclo no meio, **no momento do handoff a produção ainda não
existe** — então o red é rodado pelo orquestrador e o falso-verde deixa de ser relato verificado na
forma e volta a ser fato observado. Esse é o argumento mais forte a favor da variante, e vale mais
que a disciplina de papéis que a motivou.

**A colisão que precisou de desenho: "escrever teste é escolher assinatura".** Um test-writer solto
fixa a API por via indireta e o code-writer herda design que o usuário nunca aprovou. Resolvido em
duas partes — o **contrato travado antes do primeiro teste** (do plano quando ele traz; derivado e
travado numa pergunta quando não), e o **esqueleto** como única incursão do test-writer na produção:
assinatura mais `não implementado`, nada além. O esqueleto também resolve o conflito entre "TDD à
risca" e "falha por import não é red" — sem ele, o primeiro red de um módulo novo é `cannot find
module`, indistinguível de caminho errado; com ele, a falha prova que o teste **alcança** o alvo.

**A fronteira é verificada, não pedida.** `git status --porcelain` depois de cada retorno: diff do
test-writer com lógica de produção, ou do code-writer com qualquer arquivo de teste, é parada dura —
e os workers não fazem `git add`, justamente pra o diff ficar legível. Se quem implementa pode mexer
no teste, o teste deixa de ser cobrança e passa a ser negociação, e a negociação ganha no aperto.

**As quatro decisões do usuário:**

| Decisão | Escolha | Alternativa recusada |
|---|---|---|
| Fronteira do handoff | **por tarefa** | batch total (todos os testes → todo o código) acumularia suposições de API contra código inexistente |
| Dono do ambiente | **orquestrador puro** | script `env.sh` (era a recomendação, pela lição H.5) e agente dedicado |
| Quem fixa o contrato | **o plano, antes de tudo** | test-writer fixando; code-writer renegociando |
| Nome | **`implement-strict`** | `tdd` (era a recomendação: leading word pré-treinada e livre) |

⏳ **Duas pendências sem bloqueio:** (1) o `tasks.md` do `plan` não emite campo `contrato:` — por
isso a peça deriva e pergunta; se o padrão pegar, o `plan` passa a emitir e a pergunta some.
(2) Ambiente em prosa é mais frágil que `env.sh` com exit code — foi escolha consciente de não pagar
o custo agora, e o desenho não muda se o script nascer depois.

**Sobre o nome:** apontei que sufixo descritivo é o vício que matou o `sdd-*` no v9 e que `tdd`
estava livre. Ele manteve `implement-strict`. Fica registrado como decisão dele — e renomear depois
é trivial, porque a peça é user-invoked e ninguém depende do gatilho automático.

### I.44 — ⭐ O plano ganha contrato e passos; o teste não vê os passos ✅ (02-09-2026)

*"queria que me mostrasse meio que um passo a passo do código que vão implementar. não o código em
si, mas dizer vamos criar uma função tal que recebe parâmetros tais vindos de tal para fazer isso."*

Ele cogitou peça nova e perguntou se ficava no `plan` ou no `implement`. **É campo, não peça** — e é
a pendência que a I.43 tinha deixado aberta (`contrato:` no `tasks.md`), agora com escopo maior.

**Fica no `plan`, exibido pelo `implement`.** Três razões: quem tem ferramenta de pesquisa é o
`plan` (`structure-cache`, `Explore`, Context7 no `allowed-tools`), e o `implement` descobrindo a
origem dos parâmetros na hora de executar é o executor decidindo design; as três lentes do `plan`
passam a criticar assinatura concreta em vez de prosa de abordagem, o que afia a de Executabilidade
de graça; e é o insumo que as duas peças de execução já precisavam. Peça própria exigiria ganho por
invocação ou sequência (Parte C.4) e não há — o `plan` já para pra aprovação, que é o momento em que
ele quer ver isso.

**Formato, escolhido por ele:** `Contrato:` e `Passos:` **dentro da tarefa**, no `tasks.md`, junto de
Verificação e Pronto quando — não numa seção separada do `plan.md`, que obrigaria a cruzar dois
arquivos por tarefa e abriria espaço pra divergência silenciosa.

**Contrato** — só onde **cruza fronteira** (exportado, endpoint, tipo/schema, migração, evento):
assinatura, **origem de cada parâmetro com `arquivo:linha`** (é afirmação sobre o codebase, então
vale o zero inferência), efeito colateral e erro propagado na forma que o projeto usa. Helper
interno não tem contrato — contrato pra tudo infla o arquivo e a parte que importa se perde.

**Passos** — a sequência de chamadas e decisões observáveis, **teto de 5**. Ele escolheu incluir a
sequência sabendo do risco que eu apontei: pseudocódigo apodrece, porque o codebase manda mais na
ordem do que o plano. Três mitigações no desenho, em vez de re-litigar a escolha:

1. **Passo é intenção, não roteiro.** Codebase que contradiz ganha e o desvio vira registro no
   `notes.md`. Só é parada dura o desvio de **contrato** ou de **comportamento**.
2. **Teto de 5 é sinal de quebra, não cota.** Sequência mais longa significa tarefa que faz duas
   coisas — o `plan` propõe dividir em vez de escrever doze passos. O risco vira diagnóstico.
3. **⭐ O test-writer não recebe os passos.** Só o code-writer. Teste que conhece a ordem das
   chamadas testa implementação: quebra em refactor que não mudou nada de fora, e teste que quebra
   sem bug ensina o time a desconfiar da suíte. A separação de papéis da I.43 é o que torna essa
   proteção executável — no `implement` normal, o mesmo subagente vê as duas coisas e a mitigação
   depende da instrução, não da estrutura.

**Pesos diferentes, escrito nas duas peças de execução:** contrato é lei (o usuário o revisou;
mudar em silêncio é desfazer decisão dele → parada dura com objeção e precedente na mão), passo é
intenção (segue o vizinho, anota o desvio). Confundir os dois é o jeito mais fácil de estragar a
execução — ou o agente trava a cada divergência trivial, ou reescreve a API sem avisar.

**Fica de fora do formato:** ordem de `if`, laço, `try`/`catch`, nome de variável local, ordem de
guard. Tarefa sem código novo (config, migração pura, deleção) escreve `n/a` — campo preenchido por
obrigação ensina o leitor a pular a seção.

### I.45 — ⭐ `triage`: o review recebido se traduz, e a primeira peça model-invoked ✅ (02-09-2026)

*"to recebendo uns review e eles tão ficando muito denso na leitura, talvez pq eu precise ver esse
erros em pseudo codigo, tem hora que não estou entendendo nada"* — com um caso real na mesa: 2.083
palavras num corpo de review só.

**O diagnóstico não foi qualidade.** Os pontos conferiam no head do PR. Era forma: 91 frases, média
de 23 palavras, 9 frases com 40+ palavras, **40 referências `arquivo:linha` dentro da prosa**, e
nenhum cabeçalho por item. Review é escrito por quem **descobriu** (mecanismo → sintoma) e lido por
quem vai **corrigir** (sintoma → mecanismo).

**As quatro faixas de todo achado:** título na língua de quem usa o sistema · quem sente, gatilho,
alcance · **traço** (a sequência do gatilho ao sintoma, uma chamada por linha) · correção, incluindo
o que **não** resolve. Referências saem da prosa e vão pro pé do card.

**⭐ Por que o traço é obrigatório:** metade dos achados de review é sobre **ordem de execução e
estado**, e isso é ilegível em prosa por construção. O caso que provou tinha três fatos que só
fazem sentido juntos — o campo está desmontado, o erro é escrito antes de montar, a escrita
substitui a lista inteira. Em parágrafo o leitor reconstrói a sequência de cabeça; em cinco linhas
indentadas o defeito salta e a correção aparece sozinha.

**⚠️ Model-invoked, a terceira do toolkit** — junto de `glossary` e `grilling`; as outras dezesseis
são `disable-model-invocation: true`. Aqui o usuário pediu o gatilho: *"pr-review pode ter o gatinho pq eu sempre começo a conversa
falando recebemos um review"*. Pela Parte C.2 é decisão explícita e paga context load em todo turno
— o que justifica é o custo real ser o inverso: cognitive load de lembrar que a peça existe
exatamente no momento em que ela serve. A description é curta e ancorada em "review recebido no PR
dele", pra não disparar quando ele está revisando o PR de outra pessoa.

**Peça própria, não branch do `imp-review`** — ganho pelos dois critérios da C.4. Por invocação, o
gatilho acima (habilitar model-invocation numa description que já cobre três trabalhos dispararia
torto e custaria mais). Por sequência, entender vem **antes** de corrigir: a seção "Quando o time já
comentou" do `imp-review` é `Pediu / No código / Leitura`, que pressupõe correção feita.

**A fronteira ficou em três:** `triage` entende o que chegou e prioriza · `imp-review` checa se a
correção atendeu e rascunha a resposta · `pr-review` é o outro lado, e ganhou a régua de forma no
mesmo dia pro problema não nascer de novo. Nenhuma invoca a outra (I.27); cada uma nomeia a seguinte.

**Verificação contra o head, não contra a working tree** — `gh api contents?ref=<headRefOid>`. A
working tree costuma estar em outra branch, e ler o arquivo errado pra concluir que o revisor errou é
o pior resultado possível da peça.

**A entrega é página publicada**, com três linhas no terminal (contagem, as três prioridades, o
link). Coerente com a diretriz que a auto-memory já registrava pra doc denso: relido no terminal, um
review de 2.000 palavras continua sendo 2.000 palavras.

#### I.45.a — Adendo no mesmo dia: relatório de comando é a segunda entrada do `triage`

*"da para ter tbm quando eu executar um comando do projeto ele devolve as resposta geralmente
assim… de ser menos densa?"* — o caso foi o `/fullreview` do projeto (7 fases, output de ~2 mil
caracteres). Eu comecei a desenhar um template de flags **dentro** do `fullreview.md`, e ele cortou:
*"gostei do que vc apresentou no triage não daria para ser igual?"*

**Ele estava certo.** O `fullreview.md` é arquivo versionado e revisado pelo time, num repo de
trabalho, e a peça que faz esse trabalho já existia. Virou **branch de entrada** — Parte C, caminhos
diferentes conforme o gatilho — em vez de peça nova ou formato copiado.

**O que muda entre as entradas é só onde o fato se confirma:** review de PR contra o head
(`contents?ref=<sha>`), relatório de comando contra o **working tree** e o `git diff`, porque o
comando acabou de mexer ali. O procedimento é o mesmo de propósito.

**⭐ A descoberta: densidade inversa à necessidade de decisão.** No relatório real, o que tinha
template era o bloco de contagens e o status do gate — a parte que **não** pede decisão. As 7 flags,
a única coisa que exigia ação dele, não tinham template nenhum: a spec do comando só dizia "liste
cada um e ofereça a ação ao usuário", e improviso sai em prosa. A regra que ficou: **contagem no
cabeçalho, decisão em card**, com a faixa de quatro campos obrigatórios — a escolha, o custo de cada
lado, e a recomendação. Escolha sem os dois lados escritos é decisão devolvida sem material, que é o
que a memória `decisao-de-produto-e-do-usuario` já pedia, agora aplicado à forma.

**E a fonte:** relatório que sai denso **toda vez** é fonte pra consertar, não pra traduzir sempre.
A peça nomeia o arquivo que gera o resumo e o que faltou nele — template pro que pede decisão,
`AskUserQuestion` no lugar da pergunta aberta — e para aí. A edição é do usuário, porque o arquivo é
do time.

#### I.45.b — A página do `triage` é local, não publicada ✅ (02-09-2026)

*"ele pode até chamar o artifact-desing mas eu não queria qe fizesse a postagem na antraopic
deixasse local mesmo e so desse o link para abrir no navegador"*

Eu havia publicado a primeira página como Artifact, e **a auto-memory já dizia o contrário** —
`doc-humano-view-html-gerada`, de 01-09-2026: *"Página local em `file://`, não Artifact"*. A
correção veio dele, não da memória.

**Onde o arquivo mora:** `<root>/thoughts/board/triage/<alvo>.html`, dentro de `thoughts/board/`,
que o `scripts/roadmap/board.py:32` já define como *"todas as views derivadas moram aqui, longe do
dado"* — gitignored, e com **nome estável por alvo**, porque o caminho é o que se fixa no navegador
(a rodada seguinte sobrescreve, não cria `-v2`).

**O que muda tecnicamente sem o Artifact**, e está escrito no `format.md`: a casca é sua
(`<!doctype>`, `<head>`, viewport, favicon como data-URI de SVG); CSS **sempre** embutido, porque
`file://` não garante folha externa — a mesma razão que o `board.py` já registrava; fonte externa é
bônus com stack de sistema atrás; e tema só por `prefers-color-scheme`, já que `data-theme` é do
viewer do Artifact e ali não existe.

⚠️ **Correção do usuário no mesmo dia — o nome era pelo comando, e comando não é alvo.**
*"/fullreview.html impede de fazer mais de um fullreview por vez"*. Ele está certo, e o efeito é
pior do que colisão: `<root>` é o repositório **principal**, então todas as worktrees escrevem no
mesmo diretório — dois `fullreview` em worktrees diferentes se sobrescreveriam em silêncio. O
esquema passou a ser **`<alvo>-<origem>.html`**, alvo primeiro porque é ele que discrimina:
`pr-465-review.html`, `pr-465-fullreview.html`, `feat-estorno-fullreview.html` (sem PR, slug da
branch). Mesma origem no mesmo alvo continua sobrescrevendo — rodar de novo na mesma branch produz o
estado de agora, não uma segunda opinião — e nunca há `-v2` nem timestamp, porque o caminho é o que
se fixa no navegador.

**A razão que vale além da preferência:** review de código e relatório de execução carregam caminho
de arquivo, trecho de código e defeito **não corrigido** de repositório privado. Publicar isso é
mandar pra fora o mapa do que está aberto. A `artifact-design` continua sendo carregada — composição
e tipografia valem igual fora do Artifact; só o publicar não se aplica.

⚠️ **Erro corrigido no mesmo dia:** eu havia escrito em I.45 que o `triage` era a *primeira* peça
model-invoked. Falso — `glossary` e `grilling` já eram. Foi consertado aqui, no README e no CREDITS.
Afirmação errada em doc de toolkit é exatamente o que o próprio `triage` prioriza como "envenena
trabalho futuro".
