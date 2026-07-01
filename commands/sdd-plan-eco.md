---
description: Variante economica do /sdd-plan pra escopo Medium — consome a SPEC, main em Sonnet, quebra de tarefas + 4 checks num subagente Opus.
model: claude-sonnet-5
allowed-tools: Read, Write, Edit, Glob, Grep, Skill, Agent, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(git worktree list*), Bash(git branch*), Bash(git fetch*), Bash(gh *), Bash(ls *), Bash(mkdir *), Bash(find *), Bash(pwd), WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# SDD Plan (eco) — planejamento com main em Sonnet

Voce segue o **protocolo completo do `/sdd-plan`** (consome a SPEC de comportamento, gera o PLAN tecnico), mas com a thread principal em Sonnet. O raciocinio mais denso (quebra de tarefas + 4 checks de qualidade) roda num **unico subagente Opus** de contexto focado — o modelo caro processa so o pacote sintetizado, nao a conversa inteira.

**Quando usar**: escopo Medium com orcamento apertado. **Quando NAO usar**: Large/Complex — o raciocinio fica espalhado demais; use o `/sdd-plan` cheio.

## Como carregar o protocolo base

Leia o command base: `.claude/commands/sdd-plan.md` do projeto, senao `~/.claude/commands/sdd-plan.md`. Siga TODOS os passos dele, com as modificacoes abaixo.

## Modificacoes sobre o protocolo base

1. **Ignore a secao "1. Modelo" do base** — aqui a main e Sonnet por design (frontmatter). **Nao rode `/model`** (invalida cache de prompt). A regra de delegar leituras volumosas a subagentes continua valendo.

2. **Escopo alvo: Medium.** No Passo 1, se classificar como Large/Complex, sugira migrar pro `/sdd-plan` cheio:

   ```
   Classifiquei como [Large/Complex] — escopo acima do alvo do modo eco.
   Sugiro rodar /sdd-plan (Opus na main) pra esse caso. Continuar no eco mesmo assim?
   ```

   Se o usuario insistir, prossiga no eco (ciente da limitacao).

3. **Passos 8 e 9 (quebrar tarefas + 4 checks) rodam num subagente Opus.** Monte um pacote de contexto com: a SPEC de comportamento (RFs + ATs), sintese da pesquisa (Passos 2-4), decisoes tecnicas resolvidas (Passo 6), reconciliacao com docs (Passo 7), constraints da constitution e skills do projeto. Dispare `Agent` com:
   - `subagent_type: general-purpose`
   - `model: opus`
   - `description`: "Quebrar tarefas + 4 checks"
   - `prompt`: o pacote + instrucao pra produzir as secoes de tarefas do PLAN (formato What/Covers/Where/Depends on/Reuses/Skills/Riscos/Tests/Test count/Gate/Done when/Commit, phases Foundation/Core/Integration, marcacao `[P]`, Parallel Execution Map) e executar os 5 checks (Granularity, Diagram-Definition Cross-Check, Test Co-location, SPEC Coverage — todo RF/AT coberto por ≥1 tarefa via `Covers:` — e PR Size: estimar arquivos distintos do diff, Ideal ≤10 / aceitavel ≤15 / 16-20 caso raro com aviso+split sugerido / >20 recomendar dividir) com tabelas. Checks 1-4 bloqueantes; se falhar, ele mesmo reestrutura e re-roda (ate 2x). Check 5 e advisory. Retorno: secoes prontas + status dos checks + contagem de arquivos.

   Se apos 2 tentativas algum check seguir falhando, traga o detalhe pro usuario decidir.

4. **Passo 9.5 (revisao por painel) fica OFF por design.** No `/sdd-plan` cheio o painel de reviewers roda sempre; o modo eco e justamente o escape pra Medium com orcamento apertado — varios subagentes Opus por rodada contradiz o proposito. Os 4 checks (rodados pelo subagente Opus unico do item 3) bastam. Se o usuario quiser a revisao por painel, sugira migrar pro `/sdd-plan` cheio.

5. **Checkpoints com o usuario** (Passos 6, 7 e 10) continuam na main, normalmente — o subagente nunca interage com o usuario.

6. Todo o resto (localizar/ler a SPEC no Passo 2, auto-sizing, Knowledge Verification Chain com Step 0 de memoria, template do PLAN via reference, Passos 11-14, guardrails) segue o base sem alteracao.
