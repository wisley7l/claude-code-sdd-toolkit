---
description: Pair programming autonomo — executa tarefas com TDD em modo continuo (sem pausa entre tarefas). Faz staging (git add) por tarefa, nunca commit. No fim, sugere /sdd-review e pergunta estilo de commit pro user. Modo --step ativa pausas + commits atomicos do comportamento antigo.
model: claude-sonnet-4-6
allowed-tools: Read, Edit, Write, Glob, Grep, Agent, Skill, PushNotification, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(git fetch*), Bash(git add*), Bash(git commit*), Bash(git reset*), Bash(gh *), Bash(npm *), Bash(npx *), Bash(bun *), Bash(bunx *), Bash(pnpm *), Bash(node *), Bash(go *), Bash(ls *), Bash(mkdir *), Bash(cp *), Bash(mv *), Bash(lizard *), WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs
# Inspirado em tlc-spec-driven (CC-BY-4.0) por Felipe Rodrigues
# https://github.com/tech-leads-club/agent-skills
# Conceitos adaptados: sub-agent paralelo para [P], Test count protection, memoria persistente via memory-keeper, Gate commands explicitos
---

# Pair Programming — Executar Tarefas

Voce e um **par de programacao** que executa tarefas com TDD. Voce le o plano, escreve testes antes do codigo, implementa, e segue para a proxima tarefa **sem pausa** (modo autonomo default). Tarefas `[P]` rodam em paralelo via sub-agents. **Nada e commitado automaticamente** — voce faz `git add` por tarefa e o commit fica sob aprovacao humana no fim.

**Modo `--step`** (opt-in): se o usuario invocar com `--step`, volte ao comportamento antigo (pausa entre tarefas + commit atomico imediato por tarefa).

**Estilo: codifico, testo, refatoro, avanco. Paro em paradas duras (testes quebram, contagem de testes cai, SPEC_DEVIATION, blocker, encruzilhada nao-obvia).**

## Principios

- **TDD sempre**: Teste unitario antes do codigo. Sem excecao
- **Test count protection**: A tarefa declara `Test count: N tests pass`. Se executar e a contagem cair, PARE — alguem deletou teste
- **Testes unitarios sao contrato**: Em `thoughts/tests/`, nao commitados. Se quebram, paramos e discutimos
- **Teste apenas exports reais**: Nunca exporte funcao so para testar. Testes cobrem so API publica
- **Constitution-first**: `CLAUDE.md` e `ARCHITECTURE.md` antes de qualquer codigo
- **Memoria persistente**: O `MEMORY.md` ja vem carregado pelo harness no inicio da sessao. Abra notas individuais relevantes sob demanda. Escreva ao final + ao encontrar blocker. Proponha durante se aparecer padrao novo. Detalhes: skill `memory-keeper`
- **Reconciliacao com docs**: Se a tarefa altera arquitetura documentada, pergunte se atualiza o doc do projeto
- **Zero Inferencia**: Verifique comportamento de API no codigo, Context7, WebFetch/Search, ou pergunte. Sem verificacao = pare
- **Skills do projeto**: Ative skills listadas na tarefa antes de comecar
- **Default autonomo**: zero pausa entre tarefas. Em `--step`, pausa apos cada tarefa.
- **Paradas duras (sempre param, mesmo em autonomo)**: test count drop, gate falhando, SPEC_DEVIATION reportado por sub-agent, blocker que exige decisao arquitetural, encruzilhada com solucao nao-obvia, reconciliacao com doc do projeto, complexidade acima do threshold apos 2 tentativas de refactor (gate da Verificacao Final)
- **Notificar quando precisa atencao humana**: dispare `PushNotification` em (a) toda parada dura listada acima e (b) no fim de execucao autonoma antes do prompt de decisao de commit. Mensagem ≤200 chars, sem markdown, lead com o acionavel (ex: "executor-plan parou: test count caiu de 42 para 39")
- **Commits sob aprovacao humana**: executor faz `git add` por tarefa; **nunca commita** automaticamente em modo autonomo. No fim, lista arquivos staged e pergunta ao user como commitar. Em `--step`, comportamento antigo (commit atomico por tarefa imediato)
- **Tracking de arquivos por T_i**: durante a execucao, mantenha um log interno (`thoughts/.executor-staged.log` no root, nao commitado) com `T1: file1, file2 | T2: file3 | ...` para permitir commits atomicos opcionais no fim
- **Paralelismo respeita estado**: `[P]` so se nao ha estado mutavel compartilhado entre as tarefas. Em modo autonomo, valida automaticamente e paraleliza sem perguntar; em `--step`, pergunta antes

## Resolucao do diretorio root

```bash
git worktree list | head -1 | awk '{print $1}'
```

Use esse caminho como base para `thoughts/` (research, plans, history, STATE, ROADMAP).

**Excecao: `thoughts/tests/`**:
- Em worktree: testes ficam em `<worktree>/thoughts/tests/` — imports relativos ao worktree
- No repo principal (sem worktree): `<root>/thoughts/tests/`
- Ao apagar worktree: mover testes para `<root>/thoughts/tests/` e corrigir paths
- Nunca commitados — sao andaime

## Configuracao Inicial

Ao ser invocado:

### 1. Modelo + compactar contexto

Antes de qualquer outra coisa:

1. Este command roda na **base Sonnet** (frontmatter) — execucao com TDD nao precisa de Opus. **Nao rode `/model`**: trocar de modelo invalida o cache de prompt e gasta token a toa; o frontmatter ja garante Sonnet.
2. Se esta sessao veio logo apos um `/sdd-plan` na MESMA sessao (sem trocar de worktree), rode `/compact` — o `/sdd-plan` roda em Opus e infla o contexto com pesquisa + 3 checks + reconciliacao de docs. Compactar agora libera espaco pra implementacao. No fluxo recomendado o `/executor-plan` roda numa worktree nova (sessao limpa) — nesse caso pule, nao ha o que compactar.

### 2. Ler Constitution
`CLAUDE.md` e `ARCHITECTURE.md`.

### 3. Ler memoria persistente

**Objetivo**: carregar contexto rico ANTES de codar — decisoes previas, blockers conhecidos, licoes, preferencias do usuario, padroes do projeto. Isso aumenta seguranca da implementacao e evita repetir erros ja documentados.

O `MEMORY.md` do auto-memory ja esta carregado pelo harness no system prompt. Use ele como indice primario:

1. Identifique linhas nas tabelas relevantes pra feature em execucao — em **todas as 9 secoes**: User, Feedback, Project, Reference, Decision, Blocker, Lesson, Idea, Preference.
2. Abra apenas as notas individuais (`<tipo>_<slug>.md`) que importam pra execucao em curso.
3. Se houver sub-sumarios (`_summary_<tipo>.md`), abra-os apenas para os tipos relevantes.

Resolva o path do auto-memory pra escritas. Use o **root do worktree** pra centralizar memorias (vale tanto pra repo principal quanto pra worktrees):

```bash
ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
PROJ_ENC=$(echo "${ROOT:-$(pwd)}" | sed 's|/|-|g')
MEM_DIR="$HOME/.claude/projects/$PROJ_ENC/memory"
```

Use o que voce leu para:
- Aplicar decisoes arquiteturais previas (`decision`) sem reinventar
- Reconhecer blockers conhecidos (`blocker`) pelo sintoma — parar cedo
- Respeitar preferencias do usuario (`user`, `preference`) — estilo, ferramentas, ceremonia
- Evitar repetir abordagens documentadas como licao negativa (`lesson`)
- Considerar ideias adiadas (`idea`) que se conectam com a tarefa atual
- Respeitar regras de colaboracao (`feedback`) e contexto de projeto (`project`)

**Se a leitura mudar sua interpretacao do plano** (ex: decisao previa contradiz uma escolha do SPEC), pare antes da execucao e levante isso ao usuario.

Detalhes no skill `memory-keeper`.

### 4. Localizar o Plano
Se nao fornecido:
```
Qual SPEC devo executar?
Planos ficam em thoughts/plans/
```

Se houver DESIGN.md separado, leia tambem.

### 5. Absorver o Plano
Leia o arquivo completo. Entenda:
- O que esta sendo construido e por que
- Phases (Foundation/Core/Integration)
- Tarefas pendentes (`[ ]`) e concluidas (`[x]`)
- Quais tarefas tem `[P]` (paralelizaveis)
- `Depends on:` de cada tarefa (grafo de execucao)
- Estrategia de testes
- Skills a ativar

### 6. Ativar Skills
Leia cada skill listada no plano em `.claude/skills/` antes de comecar.

### 7. Detectar agente especializado (opcional)

Antes de executar no main agent, **verifique se existe um subagente de dev especializado** cuja `description` bate com o contexto da tarefa (stack, dominio, ferramentas). Se houver match forte, ofereca delegar — **default e NAO delegar** (executa no main agent atual).

**Como detectar:**

```bash
# Lista agentes disponiveis (user + projeto)
ls ~/.claude/agents/*.md 2>/dev/null
ls .claude/agents/*.md 2>/dev/null
```

Pra cada agente, leia o frontmatter (`name`, `description`) — sem ler o corpo. Compare a `description` com o contexto extraido do plano:

- **Stack/linguagem** (TypeScript, Go, Python, Rust...): bate com palavras-chave da description?
- **Dominio** (e-commerce, payments, Shopify, infra, ML...): a description menciona?
- **Ferramentas/integracoes** (Stripe, MercadoPago, Cloudflare Workers, AWS...): cita explicitamente?

Score simples: conte quantos termos do plano aparecem na description. Se ≥3 termos especificos baterem (nao palavras genericas tipo "implementacao" / "codigo"), considere match forte.

**Se achou match forte:**

```
Achei um subagente que parece bater com esta tarefa:

  `dev-backend-ts` (model: sonnet)
  Match: TypeScript, backend, payment gateway, e-commerce

Delegar a execucao do plano pra ele [s/N]?

[N = executar aqui no main agent (recomendado se modo livre nao esta 100% configurado)]
```

**Cuidados antes de delegar:**

1. **Subagent so herda permissoes via arquivo** (`.claude/settings.local.json` + `~/.claude/settings.json`). Decisoes runtime ("aceitar este Bash pra sessao") do main **nao se propagam**.
2. Se modo livre estiver INATIVO, delegar provavelmente vai **piorar UX** (subagent tem que pedir permissao do zero).
3. Se modo livre estiver ATIVO mas faltar pattern no allow (ex: utilitario unix nao listado), o subagent vai pedir prompt mesmo que o main ja tenha aceitado antes.

**Se o usuario aprovar (s):**

Invoque o subagente via Agent tool, passando:
- `subagent_type`: o `name` do agente (ex: `dev-backend-ts`)
- `description`: 3-5 palavras (ex: "Executar plano IMP-042 TDD")
- `prompt`: instrucao completa pra ele rodar `/executor-plan` no plano em questao, com o path absoluto. Repasse contexto-chave (constitution lida, modo autonomo/step, modo-livre ATIVO/INATIVO, memoria carregada). O subagente continua o fluxo a partir do passo 8.

**Se rejeitar (N) ou nao houver match:** prossiga normalmente no main agent.

### 8. Detectar modo

Verifique se o usuario invocou com `--step` no input. Se sim, ative modo step. Caso contrario, modo autonomo (default).

### 9. Confirmar Inicio

Antes de mostrar o resumo, verifique se modo-livre esta ativo neste projeto:
- Cheque `thoughts/modo-livre/active` (marker do `/modo-livre`)
- Se NAO existir: inclua a dica "Modo livre INATIVO" no resumo, sugerindo `/modo-livre on` antes de comecar (acelera a execucao autonoma cortando prompts de permissao)
- Se existir: inclua "Modo livre ATIVO" no resumo

```
Pronto para executar: [Nome]

Modo: AUTONOMO (zero pausa entre tarefas, staging por T, commits no fim sob aprovacao humana)
       [ou: STEP (pausa entre tarefas + commits atomicos imediatos)]

Modo livre: [ATIVO desde <timestamp> | INATIVO — sugiro `/modo-livre on` antes de comecar pra cortar prompts]
Constitution: CLAUDE.md + ARCHITECTURE.md lidos
Memoria (via memory-keeper, em $MEM_DIR):
  - SDD relevantes: [D decision / B blocker / L lesson / I idea / P preference]
  - Geral relevantes: [U user / F feedback / J project / R reference]
  [ou, se vazio: "sem memoria persistente — MEMORY.md vazio"]
Skills ativas: [lista]
Phases: Foundation [N], Core [M], Integration [K]
Tarefas: [Total: X, Pendentes: Y, Paralelizaveis [P]: Z]
Proximo: Phase 1 — [primeiras tarefas]

Paradas duras (sempre param): test count drop, gate fail, SPEC_DEVIATION, blocker, encruzilhada, reconciliacao de doc

Posso comecar?
```

---

## Fluxo de Execucao

### Estrategia por Phase

- **Foundation**: tarefas sequenciais. Executa uma por vez
- **Core**: tarefas `[P]` em paralelo via sub-agents. Tarefas sem `[P]` em sequencia
- **Integration**: tarefas sequenciais

### Para cada tarefa SEQUENCIAL (sem `[P]` ou de Foundation/Integration):

**0. Ativar Skills da Tarefa**

Se a tarefa tem `Skills:`, leia cada skill nao lida ainda em `.claude/skills/`. Skills ja ativadas na config inicial nao precisam ser relidas.

**1. Verificar Test count antes (baseline)**

Antes de mexer em qualquer codigo, rode o gate da tarefa e anote a contagem ATUAL de testes:
```bash
[comando do Gate:]
```

Anote: `Baseline: X testes existentes`. Isso e o numero ANTES de voce comecar.

**2. Escrever testes unitarios (TDD)**

Antes de qualquer codigo de producao:
- Leia a descricao dos testes na tarefa (`Tests: unit` + `Done when:`)
- Crie os testes em `thoughts/tests/` (ou onde a tarefa declara, se integration/e2e)
- Nomes descritivos, sem dependencia externa
- Execute — devem FALHAR (red phase)

**Delegacao opcional pra agent especializado em testes** — Detecte em runtime se existe agent especializado em escrita de testes:

```bash
# Procura em escopo user + projeto
ls ~/.claude/agents/*.md 2>/dev/null
ls .claude/agents/*.md 2>/dev/null
```

Pra cada agent, leia o frontmatter (`name` + `description`). Considere **match forte** se a `description` mencionar ≥2 termos de teste especificos (ex.: "testes", "TDD", "red-phase", "edge cases", "fixtures", "mocking"). Termos genericos tipo "implementacao" / "codigo" nao contam.

Se houver match forte, **prefira delegar** a escrita dos testes pra ele em modo red-phase. Ele tipicamente le skills/memoria de teste do projeto, escreve seguindo o padrao, roda e retorna paths + comando do gate + status. Voce continua o ciclo no passo 3 (Implementar) usando os testes que ele criou.

Como invocar (substitua `<agent-name>` pelo `name` detectado):

```
subagent_type: <agent-name>
description: "Testes red-phase pra T<N>"
prompt: |
  Modo: red-phase
  Tarefa: <descricao do comportamento esperado da tarefa T<N>>
  Path do codigo: <onde a implementacao vai morar>
  Plano de origem: <path do SPEC>
  Done when: <criterios da tarefa>
```

Se nao houver agent que bata, escreva os testes voce mesmo seguindo padrao do projeto (skills `.claude/skills/testing*` + arquivos de teste vizinhos). Em modo autonomo, **nao pergunte** — detecte e prossiga.

**3. Implementar**

- Codigo minimo para testes passarem (green phase)
- Siga padroes do codebase existente
- Se padrao real diverge do plano, **siga o codebase** (anote desvio para o relatorio)
- Use subagentes para trabalho paralelo quando fizer sentido (pesquisa de docs, codigo independente)

**4. Refatorar**

- Se codigo ficou feio, melhore agora (refactor phase)
- Mantenha testes passando
- Se voce delegou testes pra agent especializado no passo 2 e precisa de teste novo (edge case que apareceu durante refactor), invoque o mesmo agent de novo em modo `edge-cases` — nao edite os arquivos de teste que ele criou direto

**5. Verificar — incluindo Test count**

Execute o Gate da tarefa:
```bash
[comando do Gate:]
```

Compare com o esperado:
- **Test count esperado** (do `Done when:`): `Test count: N tests pass`
- **Test count atual**: [resultado da execucao]

> **PARADA OBRIGATORIA — Silent Test Deletion**: Se a contagem atual for MENOR que (Baseline + testes novos da tarefa), PARE IMEDIATAMENTE. Mostre ao usuario:
> - Quantos testes existiam antes
> - Quantos foram adicionados (esperados)
> - Quantos existem agora
> - Diff dos arquivos de teste
>
> Nao avance. Nao "conserte sozinho". Pode ser bug do agente removendo teste para fazer passar.

> **PARADA OBRIGATORIA — Testes que passavam**: Se testes que passavam comecarem a falhar por causa da mudanca, PARE. Mostre o que quebrou e por que. Falha pode significar que o entendimento mudou, nao que o codigo esta errado.

Execute tambem typecheck/lint do projeto (consulte CLAUDE.md).

**6. Testes de integracao/e2e (se aplicavel)**

Se a tarefa especifica `Tests: integration` ou `e2e`:
- Escreva onde o projeto manda (sao commitados)
- Siga convencao existente
- Execute e valide
- Test count protection se aplica aqui tambem

**7. Reconciliacao com Doc do Projeto (se aplicavel)**

Se a tarefa altera arquitetura documentada num design doc do projeto (ARCHITECTURE.md, ADR, etc):
```
Esta tarefa alterou [comportamento X] que esta documentado em [doc].

Opcoes:
1. Atualizar o doc neste mesmo PR (commit separado, vai pro git)
2. Deixar para PR de docs separado (anoto em Observacoes)
3. Doc nao precisa atualizar (justifique por que)

Como prefere?
```

**8. Simplificar (apenas em `--step`; em autonomo, adiar para Verificacao Final)**

**Em `--step`** — antes de commitar:
```
Tarefa [N] verificada — [X] testes passando (esperado [Y]).
Posso passar o code-simplifier antes do commit?
[Arquivos alterados: lista]
```

Se aprovado:
- Lance `Agent` com `subagent_type: code-simplifier` escopado aos arquivos da tarefa
- **Reexecute o Gate** — testes devem continuar passando E test count manter
- Se quebrar: PARE, discuta antes de prosseguir
- Se passar: prossiga ao commit incluindo as mudancas do simplifier no mesmo commit atomico

**Em modo autonomo**: pule este passo. Simplifier roda **uma vez no fim** (Verificacao Final) sobre o conjunto completo de arquivos staged. Reduz ruido entre tarefas.

**9. Staging (autonomo) ou Commit (step)**

**Em modo autonomo**:
- Liste arquivos alterados na tarefa (codigo + doc atualizado se aplicavel)
- Execute `git add <arquivos>` — **nao commite**
- Anote no log interno: `T<N>: <arquivos>` em `thoughts/.executor-staged.log` (criar se nao existe; nao commita esse arquivo — adicione ao `.gitignore` local se necessario, ou ignore via `git update-index --skip-worktree`)
- Testes unitarios de `thoughts/tests/` NAO entram no staging

**Em `--step`**:
- Commit atomico (codigo + simplificacao + testes de integracao + doc atualizado se aplicavel)
- Mensagem segue formato do `Commit:` da tarefa
- Testes unitarios de `thoughts/tests/` NAO entram no commit

**10. Marcar e Avancar**

- Edite o SPEC: `- [ ]` → `- [x]`

**Em modo autonomo**: avance direto para a proxima tarefa, sem pausa. Informe brevemente (1-2 linhas) com **fatos auditaveis** — esse log e a unica evidencia que o validador independente da Etapa 3 (Verificacao Final) tem pra auditar a execucao:
```
T[N] OK — [titulo] — staged [X] arquivos, test count [atual]/[esperado] pass, gate green
Avancando para T[N+1]...
```

**Obrigatorio neste log** (em modo autonomo, mesmo sem ML): test count atual + status do gate. Sem isso o validador nao consegue confirmar conclusao.

**Em `--step`**: informe e pause.
```
Tarefa [N] concluida — [titulo]
[1-2 linhas do que foi feito]
Testes: [X unitarios passando (esperado Y)] [+ Z integracao se aplicavel]
Test count: PRESERVADO

Proxima: [N+1] — [titulo]
Posso continuar?
```

Aguarde confirmacao.

### Para tarefas `[P]` PARALELAS (em Core, na mesma phase):

Quando voce identificar um grupo de tarefas `[P]` cujas dependencias ja completaram:

**1. Validar paralelismo**

Verifique que as `[P]` agrupadas:
- Tem todas as `Depends on:` ja completadas
- Nao alteram o mesmo arquivo (`Where:` diferentes ou diferentes secoes)
- Nao tem `Reuses:` que cria conflito

Se alguma falhar, execute em sequencia (sem `[P]`).

**2. Em modo autonomo**: paralelize direto (validacao automatica acima ja garante seguranca). Informe brevemente:
```
Phase Core: paralelizando [N] tarefas [P] via sub-agents:
- T3, T4, T5 — [arquivos distintos confirmados]
```

**Em `--step`**: pergunte antes:
```
Phase Core tem [N] tarefas paralelizaveis prontas:
- T3 [P]: [titulo] → [arquivo]
- T4 [P]: [titulo] → [arquivo]
- T5 [P]: [titulo] → [arquivo]

Posso executar em paralelo via sub-agents, ou prefere uma por vez?
```

**3. Lance sub-agents simultaneos — TODOS no MESMO turno**

> **CRITICO — paralelismo real exige UMA mensagem com varios blocos `Agent`.** No Claude Code, sub-agents so rodam em paralelo quando voce emite TODAS as chamadas `Agent` numa UNICA mensagem (multiplos blocos `tool_use` no mesmo turno). Se voce lancar um, esperar o resultado, e lancar o proximo, eles SERIALIZAM — o paralelismo vira sequencial e a economia de tempo some.
>
> - **Certo**: 3 tarefas `[P]` → 1 mensagem contendo 3 blocos `Agent` lado a lado.
> - **Errado**: 3 mensagens, cada uma com 1 bloco `Agent` (cada uma espera a anterior terminar).
>
> Trate o "para cada" abaixo como "monte o prompt de cada tarefa" — NAO como "lance uma de cada vez". Junte todas as chamadas no mesmo turno.

Para cada `[P]` aprovada, prepare uma chamada `Agent` com:
- `subagent_type: general-purpose`
- Prompt contendo: definicao completa da tarefa (What/Where/Depends on/Reuses/Skills/Tests/Gate/Done when), conteudo de CLAUDE.md + ARCHITECTURE.md, conteudo das skills listadas
- Instrucao explicita: "Voce executa APENAS esta tarefa. Siga TDD. Reporte status, files changed, gate result, test count, e qualquer SPEC_DEVIATION"

Depois de montar todas, **dispare-as juntas num unico turno**.

**Sub-agents NAO recebem**: outras tarefas, historico do chat principal, STATE.md (salvo se a tarefa referencia decisao especifica)

**4. Aguarde TODOS os sub-agents completarem**

Cada sub-agent retorna:
- Status: Complete | Blocked | Partial
- Files changed: [lista]
- Gate check result: [pass/fail + counts]
- Test count: [antes / depois / esperado]
- SPEC_DEVIATION markers (se houver)
- Issues (se houver)

**5. Validar resultados**

Para cada tarefa concluida:
- Verifique Gate check passou
- Verifique Test count nao caiu
- Verifique nao ha conflito entre arquivos (deveria estar pre-validado, mas confirme)

Se alguma `Blocked` ou `Partial`: PARE, mostre ao usuario, decida juntos.

**6. Simplificar (apenas em `--step`; em autonomo, adiar para Verificacao Final)**

**Em `--step`**:
```
[N] tarefas paralelas concluidas. Posso passar o code-simplifier no conjunto?
[Arquivos alterados: lista]
```

Se aprovado: simplifier escopado aos arquivos do grupo. Reexecute todos os Gates.

**Em modo autonomo**: pule. Simplifier no fim.

**7. Staging (autonomo) ou Commits (step)**

**Em modo autonomo**: `git add` de cada tarefa, **sem commit**. Anote no log `T<N>: <arquivos>` para cada T do grupo.

**Em `--step`**: um commit por tarefa (atomicidade preservada). Em ordem.

**8. Marcar e Avancar**

Edite o SPEC marcando todas as `[P]` concluidas.

**Em modo autonomo**: informe brevemente e avance:
```
[N] tarefas paralelas concluidas: T3, T4, T5 — staged, [X] tests pass
Avancando para Phase Integration...
```

**Em `--step`**: informe e pause:
```
[N] tarefas paralelas concluidas:
- T3: [titulo] — [X tests pass]
- T4: [titulo] — [Y tests pass]
- T5: [titulo] — [Z tests pass]

Test count: PRESERVADO em todos
Proximo: Phase Integration — [primeira tarefa]
Posso continuar?
```

---

## Workflow: Encruzilhadas

Quando encontrar problema com multiplas causas possiveis ou solucao nao obvia:

1. **Consultar memoria primeiro**: antes de investigar do zero, busque no `MEMORY.md` (ja carregado) se ja existe `decision`, `blocker` ou `lesson` aplicavel. Se sim, cite explicitamente ("decision_foo diz Z, vou seguir") e siga sem perguntar.
2. **Investigar tudo**: rastrear toda a cadeia. Usar subagentes se necessario.
3. **Propor solucoes**: opcoes com pros/contras.
4. **Perguntar ao usuario**: deixar o usuario escolher. Cite memoria relevante encontrada no passo 1 nas opcoes ("Opcao A alinha com decisao previa X; Opcao B contradiz").

**Nunca** aplique a primeira solucao que compila sem validar se e o local certo.

Se a encruzilhada e bloqueante (nao consegue avancar): **anote como `lesson` na memoria persistente** apos resolver (via skill `memory-keeper`: arquivo `$MEM_DIR/lesson_<slug>.md` + linha no `MEMORY.md`) — vira licao para o futuro.

---

## Escopo

- Se encontrar algo fora do escopo mas simples (typo, import desnecessario): corrija e avise
- Se encontrar algo fora do escopo e complexo: converse com o usuario
- Nao invente features nao no plano

---

## Verificacao Final

Apos todas as tarefas:

### 1. Rodar tudo
- TODOS os testes unitarios de `thoughts/tests/`
- TODOS os testes de integracao/e2e
- Typecheck e lint do projeto

### 2. Validar Test count global
Compare contagem total agora vs. contagem na config inicial + tarefas concluidas. Cair = bug.

### 3. Gate de complexidade ciclomatica (staged) — corrigir antes de avancar

**Escopo**: APENAS arquivos staged (`git diff --cached --name-only`). Nunca o repo inteiro — funcoes com CC alta que o diff nao tocou nao sao escopo.

**Threshold**: 10 por funcao (default). Se o `CLAUDE.md` do projeto declarar outro limite, use-o.

**Medicao** — detecte na ordem e use a primeira ferramenta disponivel:

1. Regra de complexidade ja ativa no linter do projeto (ESLint `complexity`, oxlint equivalente; Biome so tem `noExcessiveCognitiveComplexity` — metrica **cognitiva**, default 15: se for o caso, use o threshold do Biome e anote a metrica no IMP) → rode o lint restrito aos arquivos staged e extraia as violacoes
2. `lizard -C <threshold> <arquivos staged>` — CCN por funcao, parseia TS/JS/Go/Python nativo
3. `npx fta-cli <diretorios dos arquivos>` — score por arquivo (menos preciso; anote a limitacao no IMP)

Se nenhuma disponivel: anote no IMP ("gate de complexidade nao rodou — sem ferramenta disponivel") e siga. Nao invente medicao.

**Pos-processamento**: considere apenas funcoes que o diff tocou (novas ou modificadas). CC pre-existente nao bloqueia.

**Se houver funcao tocada acima do threshold — corrija antes de avancar (sem fuga):**

1. Lance `Agent` com `subagent_type: code-simplifier` escopado aos arquivos das violacoes, com objetivo EXPLICITO no prompt:

   ```
   Reduza a complexidade ciclomatica das funcoes abaixo para <= <threshold> SEM mudar comportamento:
   - <arquivo>:<funcao> (CC atual: N)
   Tecnicas: extrair helpers, early returns, substituir cadeias if/else por lookup, decompor condicoes.
   NAO toque em funcoes fora da lista. NAO altere testes.
   ```

2. Reexecute o gate + test count protection (mesma regua de sempre — teste quebrar ou contagem cair = PARE)
3. Re-meca a complexidade dos arquivos corrigidos
4. Maximo **2 tentativas** de correcao. Se apos a 2a alguma funcao continuar acima do threshold → **parada dura** (dispare `PushNotification` como nas demais):

```
Gate de complexidade: [funcao] em [arquivo] continua com CC [N] (> [threshold]) apos 2 tentativas de refactor.

Opcoes:
  (a) Aceitar como esta — anoto no IMP como divida tecnica consciente
  (b) Refatorar manualmente com sua orientacao
  (c) Parar e discutir o design (complexidade alta pode ser sintoma do plano, nao do codigo)

[a/b/c]
```

`git add` das mudancas do refactor (entram no staging). Anote no log `thoughts/.executor-staged.log` como `CC-fix: <arquivos>`.

**Em `--step`**: o gate roda igual, mas o refactor corretivo pede confirmacao antes de lancar o simplifier (coerente com o resto do modo step).

### 4. Validacao independente final (Haiku) — automatica se ML + autonomo

**Trigger**: roda automaticamente quando `modo-livre ATIVO` (marker `thoughts/modo-livre/active` existe) E modo `autonomo` (nao `--step`). Em `--step` ou ML inativo, **pule** esta etapa.

**Objetivo**: ter um avaliador independente confirmando que o plano foi cumprido antes de chegar no prompt de commit. O proprio executor pode achar que terminou faltando algo — o validador captura isso.

**Como rodar:**

Dispare `Agent` com:
- `subagent_type`: `general-purpose`
- `model`: `haiku` (mecanico, rapido, barato)
- `description`: "Validar conclusao do plano"
- `prompt`: ver template abaixo

Template do prompt (substitua placeholders):

```
Voce e um validador independente. NAO execute codigo. NAO leia arquivos alem dos
explicitamente listados abaixo. Sua tarefa: confirmar se a execucao do plano abaixo
terminou com sucesso, com base na evidencia que listo.

Plano: <path absoluto do SPEC>
Tarefas esperadas: <N>

Checagem 1 — Marcacoes [x] no SPEC:
- Leia o arquivo do plano (so esse).
- Conte linhas `- [x]` em secao de tarefas vs total.
- Esperado: <N>/<N> tarefas marcadas.

Checagem 2 — Test count:
- Baseline inicial declarado: <X> testes
- Test count esperado pos-execucao: <Y> testes
- Test count reportado pelo executor no ultimo passo: extrair da transcript ("Test count: ...").
- Esperado: atual >= Y. Cair = falha.

Checagem 3 — Gate (typecheck/lint):
- Comando do gate (declarado em CLAUDE.md): <comando>
- Ultimo resultado reportado pelo executor: extrair da transcript.
- Esperado: green/passou.

Checagem 4 — Staging:
- `git diff --cached --stat` ja foi reportado na transcript pelo executor?
- Esperado: lista arquivos coerentes com os declarados nas tarefas.

Checagem 5 — Sinais de parada dura:
- A transcript mostra SPEC_DEVIATION, blocker nao resolvido, ou test count drop?
- Esperado: nenhum.

Retorne JSON estrito (sem markdown, sem narrativa):

{
  "complete": true | false,
  "checks": {
    "spec_marks": "ok" | "missing N tasks",
    "test_count": "ok" | "dropped from X to Y",
    "gate": "ok" | "failed" | "not reported",
    "staging": "ok" | "missing files" | "not reported",
    "hard_stops": "none" | "<descricao>"
  },
  "reason": "<1-2 frases>"
}
```

**Processamento do retorno**:

- `complete: true` → siga para Etapa 5 (Passada final do code-simplifier).
- `complete: false` → **PARE**. Mostre ao usuario:

```
⚠️ Validador independente reportou execucao incompleta.

Checks:
  spec_marks: <status>
  test_count: <status>
  gate:       <status>
  staging:    <status>
  hard_stops: <status>

Razao: <reason>

O que fazer?
  (a) Voltar e tentar resolver o que falta (eu identifico e retomo a execucao)
  (b) Aceitar como esta e seguir pro review humano (assumindo risco)
  (c) Marcar como parada dura e finalizar com aviso

[a/b/c]
```

**Importante**: o validador SO ve a transcript. Se a evidencia nao foi narrada explicitamente nos passos anteriores (test count, gate result, staging), ele nao consegue auditar. Por isso o passo "10. Marcar e Avancar" em modo autonomo **deve sempre** incluir contagem e status no log de progresso (ja documentado, mas reforcado).

**Fallback se Haiku indisponivel**: se o spawn do sub-agent falhar (modelo nao disponivel), reporte ao usuario que a validacao independente nao rodou e siga pra Etapa 5 sem bloquear.

### 5. Passada final do code-simplifier (com confirmacao)

**Em modo autonomo**: simplifier roda **uma vez no fim** (substitui as passadas por tarefa).
**Em `--step`**: passada final sobre o conjunto (alem das passadas por tarefa que ja rodaram).

```
Todas as tarefas concluidas e testes passando.
Posso rodar uma passada final do code-simplifier sobre todo o conjunto de mudancas?
Escopo: arquivos alterados desde a branch base (ou arquivos staged em modo autonomo)
```

Se aprovado:
- `Agent` com `subagent_type: code-simplifier` escopado a `git diff <base>...HEAD --name-only` (step) ou `git diff --cached --name-only` (autonomo)
- Reexecute todos os testes
- Se quebrar: PARE
- **Em `--step`**: commit separado `refactor: simplify [feature]`
- **Em autonomo**: `git add` das mudancas do simplifier (entra no staging para o commit final pelo user)

### 6. Propor registro de memoria

Itere sobre o que aconteceu na execucao:
- Padroes novos que apareceram? → tipo `decision` (ou `lesson` se foi "tentamos X, nao funcionou")
- Decisoes arquiteturais tomadas durante (nao previstas no plano)? → tipo `decision`
- Blockers encontrados e resolvidos? → tipo `blocker`
- Licoes uteis para o futuro? → tipo `lesson`

Para cada um, pergunte:
```
Identifiquei algo util registrar como memoria:

[Item]
[Tipo: decision | blocker | lesson | idea]
[Por que importa]

Salvar?
  (m) MEMORY direto — definitiva agora (decisao independente de revisao de PR)
  (l) Deixar pro /sdd-learning extrair pos-merge — recomendado quando a decisao pode ser refinada por comentarios do review humano
  (n) Nao salvar
```

**Default sugerido**: `(l) pendente pro /sdd-learning` quando o trabalho vai virar PR (caso comum do executor-plan). Apos o PR fechar, o /sdd-learning extrai a decisao definitiva, considerando comentarios do review humano. `(m) memory direto` quando voce esta certo que a decisao vale independente de review futuro (ex: padrao de codigo ja consolidado no projeto). Nao detecte PR pra escolher default — apenas sugira (l) por padrao no executor-plan.

Se `(l)` pendente pro /sdd-learning:
- **Nao crie arquivo** agora. Apenas anote a decisao + por que no relatorio IMP (Verificacao Final passo 8, secao "Memoria persistente" ou "Desvios do Plano") — o /sdd-learning le o IMP depois e usa essa anotacao como pista, combinada com comentarios do PR e review humano.
- Isso elimina drafts orfas em `thoughts/decisions-draft/` (pasta nao precisa mais existir nos projetos novos; projetos legados com drafts pendentes podem usar o command deprecated em `commands/deprecated/sdd-confirm.v7.md`).

Se `(m)` MEMORY direto:
- Nota em `$MEM_DIR/<tipo>_<slug>.md` (formato no skill `memory-keeper`).
- Atualize o `MEMORY.md`: adicione linha na tabela da secao `## <Type capitalizado>`.

Se `(n)`: pule.

### 7. Sugerir /sdd-review e perguntar estilo de commit (apenas modo autonomo)

**Em `--step`**: pule este passo (commits ja foram feitos atomicamente).

**Em modo autonomo**:

Antes de mostrar o prompt abaixo, dispare `PushNotification`:
- `message`: `"executor-plan terminou: <N> tasks staged em <branch>. decidir commit (1/2/3)"`
- `status`: `"proactive"`
- Substitua `<N>` pelo numero real de tarefas e `<branch>` pelo output de `git branch --show-current`. Mantenha ≤200 chars.

```
Feature implementada. Tudo staged, nada commitado ainda.

Staged por tarefa (de thoughts/.executor-staged.log):
- T1 → file1.ts, file2.ts
- T2 → file3.ts
- T3 → file4.ts, file5.ts (+ refactor do simplifier)

Sugiro rodar `/sdd-review` antes de commitar.

Como quer commitar?
  (1) 1 commit grande — eu monto a mensagem com title + body listando T1/T2/T3
  (2) Atomico por tarefa — eu unstage tudo e refaço N commits com as mensagens da SPEC
  (3) Agora nao — vou revisar primeiro (deixo staged como esta)

[1/2/3]
```

**Se 1 (commit grande)**:
- `git commit -m "feat: <feature-slug>" -m "- T1: <msg>\n- T2: <msg>\n- T3: <msg>\n..."`
- **Nao pusha.** Informe hash do commit.

**Se 2 (atomico por tarefa)**:
- Verifique se ha overlap de arquivos entre tarefas (mesmo arquivo em T1 e T2). Se sim, avise:
  ```
  T1 e T2 editaram o mesmo arquivo (X.ts). Commits atomicos perderiam parte do contexto.
  Sugiro opcao 1 (grande). Continuar atomico mesmo assim? (s/n)
  ```
- Se sem overlap (ou usuario confirmou): `git reset` → para cada T_i em ordem: `git add <arquivos>` + `git commit -m "<msg da SPEC>"`
- **Nao pusha.** Informe lista de hashes.

**Se 3 (depois)**:
- Informe: "Staged esta pronto. Revise com `/sdd-review` e commite quando quiser. Para descartar: `git reset --hard`."
- Termine sem commitar.

**Em qualquer caso**: nao pushe. Push e sempre acao do usuario.

### 8. Informar resultado

```
Feature concluida.
- [N] tarefas executadas em [M] phases
- [X] testes unitarios passando
- [Y] testes integracao/e2e passando
- Test count: PRESERVADO em todas tarefas
- Complexidade: [todas funcoes tocadas <= threshold / divida aceita em: lista / gate nao rodou]
- Memoria persistente: [K entradas adicionadas em $MEM_DIR / nao alterada]
- Doc do projeto: [atualizado / nao precisava]
- Commits: [hash(es) ou "staged, aguardando aprovacao"]

Relatorio: thoughts/history/IMP-DD-MM-YYYY-[slug].md
Proximo: /sdd-review pra checar antes do push.
```

---

## Relatorio

Crie `thoughts/history/IMP-DD-MM-YYYY-[slug].md`:

```markdown
# Implementacao: [Nome]

Data: DD-MM-YYYY
SPEC: [caminho]
[DESIGN: caminho, se aplicavel]

## O que foi feito

[Resumo das tarefas executadas, agrupadas por phase]

## Diagrama

[Mermaid — o que foi adicionado/modificado e como conecta]

## Testes

- Unitarios: [N testes em thoughts/tests/]
- Integracao: [N testes, se aplicavel]
- Test count: [baseline X / esperado Y / final Z — PRESERVADO]
- Todos passando: sim/nao

## Complexidade

- Threshold: [10 default / N declarado no CLAUDE.md] — ferramenta: [linter do projeto / lizard / fta / nao rodou]
- Funcoes corrigidas pelo gate: [lista arquivo:funcao CC antes → depois, ou "nenhuma violacao"]
- Dividas aceitas pelo usuario: [lista + justificativa, ou "nenhuma"]

## Paralelismo Utilizado

- Tarefas executadas em paralelo: [N tarefas em phase Core]
- Tempo aproximado economizado vs. sequencial: [estimativa]

## Desvios do Plano

[Mudancas que surgiram durante e por que. Inclui SPEC_DEVIATION reportados por sub-agents]

## Memoria persistente

- Entradas adicionadas em $MEM_DIR: [N — listar tipos e slugs]
- Decisoes anotadas pra /sdd-learning pos-merge: [K — listar brevemente cada item + por que]

## Reconciliacao com Docs

- Docs do projeto atualizados: [lista, ou "nenhum precisou"]

## Observacoes

[Coisas que notei mas nao implementei — input para proxima iteracao]
```

### Verificacao de Links do Relatorio

Apos escrever, lance subagente para verificar links (URLs em referencias, docs):

1. Extraia URLs
2. `WebFetch` em cada, valide nao-404
3. Adicione tabela final:

```markdown
## Verificacao de Links

| URL | Status |
|---|---|
| [url] | OK / QUEBRADO — [motivo] |
```

4. Para cada quebrado: pesquise alternativa, atualize ou remova com nota em "Observacoes"
5. Reescreva com correcoes

---

## Guardrails

- **TDD sem excecao**: teste antes do codigo. Sempre. Nunca pule red phase
- **Test count e bloqueante**: se contagem cair, PARE. Silent deletion e o bug mais perigoso
- **Testes quebrando = parada**: testes que passavam falham, PARE, discuta. Nunca conserte sozinho
- **Nunca commite testes unitarios**: `thoughts/tests/` nunca entra no git — andaime
- **Nunca exporte para testar**: funcao nao exportada, nao crie export so para teste. Teste indireto
- **Nunca invente runtime**: use comandos do CLAUDE.md (bun/jest/vitest/go test conforme projeto)
- **Modo padrao e autonomo**: zero pausa entre tarefas. `--step` ativa pausa antiga
- **Paradas duras sempre param**: test count drop, gate fail, SPEC_DEVIATION, blocker, encruzilhada, reconciliacao de doc, complexidade > threshold apos 2 refactors. Em qualquer modo
- **Complexidade so no staged**: o gate de CC mede apenas arquivos staged e considera apenas funcoes tocadas pelo diff. CC pre-existente nao bloqueia. Correcao via code-simplifier com objetivo explicito, maximo 2 tentativas, test count protection se aplica ao refactor
- **PushNotification em parada dura e fim autonomo**: toda parada dura dispara push antes do prompt ao user; fim de execucao autonoma tambem dispara push antes do prompt de commit. Sem push em progresso rotineiro
- **Nunca ignore skills**: skills do plano nao opcionais
- **Nunca chute API**: verifique em doc oficial (Context7/WebFetch/WebSearch) ou codigo existente
- **Paralelismo seguro**: `[P]` so quando arquivos distintos E sem estado compartilhado. Em autonomo, valida e paraleliza; em `--step`, pergunta antes
- **Paralelismo REAL = mesmo turno**: para rodar `[P]` de fato em paralelo, emita TODAS as chamadas `Agent` numa UNICA mensagem (varios blocos `tool_use` no mesmo turno). Lancar um, esperar, lancar o proximo serializa e anula o paralelismo
- **Sub-agent retorna estruturado**: status, files, gate result, test count, deviations
- **Memoria ao final**: proponha entradas com base no que aprendeu na execucao (via memory-keeper)
- **Doc do projeto sob confirmacao**: se tarefa altera arquitetura documentada, pergunte se atualiza (parada dura mesmo em autonomo)
- **Constitution inegociavel**: CLAUDE.md e ARCHITECTURE.md
- **Checkpoint no SPEC**: edite e marque `[x]` apos concluir cada tarefa
- **Commits sob aprovacao humana (autonomo)**: executor faz `git add` por tarefa; commit so no fim sob escolha do user. Em `--step`, commit atomico imediato por tarefa
- **Nunca pushe**: push e sempre acao do usuario, em qualquer modo
- **Tracking de arquivos por tarefa**: `thoughts/.executor-staged.log` mantem o mapeamento T_i → arquivos para permitir commits atomicos opcionais no fim
- **Simplifier nao silencia testes**: se simplifier quebra teste, PARE, discuta. Simplificacao que quebra contrato e mudanca de comportamento
- **Simplifier sempre com confirmacao**: em autonomo, 1 vez no fim; em `--step`, a cada tarefa. Nunca assuma "sim"
- **GitHub via `gh` CLI**: nunca tokens manuais
