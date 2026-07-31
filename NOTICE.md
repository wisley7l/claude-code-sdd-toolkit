# NOTICE — atribuições e licenças de terceiros

Este projeto é distribuído sob a **MIT License** (© 2026 Wisley Alves) — ver [`LICENSE`](./LICENSE).

Partes do toolkit são inspiradas ou derivadas de trabalhos de terceiros. Este arquivo é o
**índice central** dessas fontes, e `LICENSES/` guarda o texto integral de cada licença de
origem — é essa combinação que cumpre a cláusula de inclusão do MIT na distribuição.

## ⚠️ Atribuição NÃO vai dentro do `SKILL.md`

O `SKILL.md` renderizado entra no contexto do agente e **permanece lá pela sessão inteira**
(e no auto-compaction cada skill é cortada nos primeiros 5.000 tokens). Bloco de créditos no
corpo da skill é peso morto que compete com instrução real — e, quando reafirma as regras em
prosa descritiva, vira ruído pior que ruído neutro: o modelo pode ler como contexto histórico
em vez de comando ativo.

Atribuição de peça vai em **`skills/<nome>/CREDITS.md`** — arquivo irmão, **deliberadamente não
referenciado** pelo `SKILL.md`, portanto nunca carregado em runtime. Como a skill é o diretório
inteiro, o arquivo acompanha qualquer cópia ou instalação.

Nenhuma licença exige atribuição inline por arquivo: o MIT pede o copyright **e o texto da
permissão** "em cópias ou porções substanciais" — obrigação de **distribuição**, satisfeita por
`NOTICE.md` + `LICENSES/`. Citar "sob licença MIT" sem incluir o texto é verbosidade que ainda
por cima não cumpre a cláusula.

---

## Fontes

### 1. mattpocock/skills

- **Repo:** https://github.com/mattpocock/skills
- **Autoria:** Matt Pocock
- **Licença:** MIT (© 2026 Matt Pocock) — compatível com a nossa
- **O que usamos:** a skill `grilling` (texto derivado); o vocabulário e os princípios de
  `writing-great-skills` (leading word, completion criterion, context/cognitive load,
  granularidade, failure modes); o padrão de declarar invocação explicitamente.
- **Onde:** `skills/grilling/` (detalhes em `skills/grilling/CREDITS.md`) · critérios de
  aceitação do v10 (Parte C do `REFACTOR-v10.md`)
- **Texto da licença:** [`LICENSES/mattpocock-skills-MIT.txt`](./LICENSES/mattpocock-skills-MIT.txt)

### 2. Fission-AI/OpenSpec

- **Repo:** https://github.com/Fission-AI/OpenSpec
- **Autoria:** OpenSpec Contributors
- **Licença:** MIT (© 2024 OpenSpec Contributors) — compatível com a nossa
- **Status:** **referência conceitual, não dependência.** Não instalamos nem redistribuímos o
  pacote `@fission-ai/openspec`; adotamos ideias, avaliadas uma a uma.
- **O que usamos (conceitos):** workflow fluido em vez de phase-locked (ações sobre um grafo,
  dependência como *enabler* e não gate); "explore antes de propor" como hábito de primeira
  classe; o **two-minute pass** de review do plano; a separação CLI-determinístico ↔
  chat-julgamento; uma mudança = uma pasta.
- **Onde:** Parte H do `REFACTOR-v10.md`; peças da Onda 1 conforme forem nascendo.

Conceito e arquitetura não são cobertos por copyright — a atribuição aqui é boa prática e
rastreabilidade, não obrigação legal. Se em algum momento **texto** deles for copiado ou
adaptado de perto, aí o MIT passa a valer e a peça leva o bloco `## Créditos` com a licença.

### 3. tlc-spec-driven (tech-leads-club/agent-skills) — ⚠️ CC-BY-4.0

- **Repo:** https://github.com/tech-leads-club/agent-skills
- **Autoria:** Felipe Rodrigues
- **Licença:** **CC-BY-4.0** — ⚠️ **mais exigente que MIT**: a atribuição é **obrigatória,
  explícita e deve acompanhar qualquer trabalho derivado**, inclusive adaptações.
- **O que usamos:** doc auto-sized (Medium/Large/Complex); Knowledge Verification Chain;
  **test count protection**; gate commands explícitos; sub-agent paralelo para tarefas `[P]`;
  memória persistente entre etapas; quick mode com safety valve.
- **Onde no v9:** `sdd-plan`, `executor-plan`, `quick-task`, `sdd-learning`
  (todos hoje em `commands/deprecated/*.v9.md`, com a atribuição preservada no cabeçalho).

⚠️ **Regra do refactor:** vários desses conceitos estão na lista de invariantes a preservar
(Parte E.5 — test count protection, gates). **Se a peça v10 herdar o conceito, herda a
atribuição CC-BY junto.** Deprecar o arquivo v9 não extingue a obrigação.

### 4. Gist "Formação da especificação" (@parruda)

- **Fonte:** https://gist.github.com/parruda/85bf3d6ee2e8adee5c0dd9429afd76b3
- **Autoria:** @parruda
- **Licença:** não declarada — tratamos como atribuição por cortesia, e **não copiamos texto**.
- **O que usamos:** a ideia de formação da especificação como fase própria, anterior ao plano
  técnico.
- **Onde no v9:** `sdd-spec` (hoje `commands/deprecated/sdd-spec.v9.md`).

Sem licença declarada, o default legal é "todos os direitos reservados". Por isso a regra aqui
é mais estrita: **conceito sim, texto não.** Se uma peça v10 precisar de trecho literal,
pedir autorização antes.

---

## Protocolo de atribuição (vale pra toda peça nova do v10)

1. **Antes de escrever**, identifique de onde veio a ideia. Se veio de fora, anote a fonte.
2. **Nada de crédito dentro do `SKILL.md`.** Crie `skills/<nome>/CREDITS.md` e **não o
   referencie** no corpo da skill — é o que o mantém fora do contexto em runtime.
3. **O texto integral da licença** de origem vai em `LICENSES/<fonte>-<licença>.txt`, uma vez
   por fonte (não por peça).
4. **Registre aqui** no NOTICE, na fonte correspondente, em qual peça foi usada.
5. **Distinga texto de conceito.** Texto derivado aciona a licença; conceito é atribuição por
   boa prática. Na dúvida, atribua — o custo é zero, já que não vai pro contexto.
6. **CC-BY-4.0 acompanha o derivado pra sempre.** Reescrever com outras palavras não extingue
   a obrigação de atribuir.
7. **Sem licença declarada = todos os direitos reservados.** Conceito sim, texto não.
