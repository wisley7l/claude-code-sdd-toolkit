# claude-code-sdd-toolkit

> **[Leia em Português](./README.md)**

A collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) slash commands that turn the agent into a TDD pair programmer, following a disciplined process: **Research → Understand → Code with TDD**.

## Commands

### Main workflow

**`/sdd-plan`** — researches, understands, and breaks the feature into tasks in a single auto-sized doc (Medium/Large/Complex). Detects Quick scope and hands off to `/quick-task`.

**`/sdd-plan-eco`** — economical variant of `/sdd-plan` for Medium scope: main thread on Sonnet, task breakdown + 3 checks delegated to a single focused-context Opus subagent.

**`/pr-draft`** — opens the initial PR as a draft from the plan (branch + empty commit + title/body from the SPEC) and creates the worktree for isolated implementation. **`/pr-draft sync`** (post-implementation) rewrites the body as a preview for the reviewer — problem, why, how it was solved (including plan deviations), review guide and validation — everything traceable to SPEC/IMP/diff. Never takes the PR out of draft.

**`/executor-plan`** — runs the tasks with TDD in autonomous mode, parallel sub-agents for tasks marked `[P]`, staging per task. Commits are human-approved; `--step` restores the paused mode.

**`/verifica`** — behavioral verification post-implementation: boots the application, exercises the flows the change touched, and records **real evidence** in the IMP (green tests ≠ working feature). Never points at production; payments always in test mode; external side effects only with confirmation.

**`/quick-task`** — small change (≤3 files) with no formal SPEC. Escalates to the formal flow if scope grows.

**`/pair-review`** — interactive companion for the human's manual review after `/executor-plan`. Runs in a **fresh session** (`/clear`): re-hydrates from the staged diff + SPEC/IMP (~3-4k tokens, none of the execution noise), answers factual questions directly and delegates judgment questions to Opus subagents scoped to the files in question, applies small fixes with gate + test count protection. With a PR under team review, the `(r)` mode validates each fix **against the human comment that originated it** (detects unaddressed comments, scopes the diff to the post-review fix round, generates reply drafts for the threads for the user to paste). Optional per-task walkthrough and hotspots. Never commits without explicit choice, never posts to the PR.

**`/sdd-learning`** — after the PR closes, extracts non-obvious learnings from IMPs, reviews, and the GitHub PR and proposes recording them in memory, case by case.

**`/memory-organize`** — reorganizes the auto-memory: orphans, broken links, duplicates, and sub-summaries when `MEMORY.md` grows.

**`/roadmap`** — manages `thoughts/ROADMAP.md`: entries, GitHub issue imports, sync with SPEC/IMP.

### Utilities

**`/sdd-review`** — reviews a PR, branch, or diff via isolated subagents; offers to generate fixes via `/quick-task`.

**`/investiga`** — root cause of non-obvious bugs via a hypothesis protocol: structured symptom → hypotheses with a causal mechanism → evidence via parallel subagents → elimination → cause **with source** + handoff (`/quick-task` or `/sdd-plan`). The biggest factory of `blocker`/`lesson` memories.

**`/sdd-init`** — prepares a new project for the toolkit: audits the prerequisites (CLAUDE.md, ARCHITECTURE.md, `thoughts/`, Context7, references) and creates what's missing under per-block confirmation — constitution drafts marked `[NEEDS REVIEW]`.

**`/git-rebase-seguro`** — safely updates a long-lived branch with the base without eating code: test baseline before, conflicts always shown (both sides + proposal), test count protection after, guaranteed rollback SHA. Recommends merge (not rebase) when the PR already has team review. Never pushes.

**`/busca`** — web research via an isolated subagent, with no impact on the main context. Flags `--rapido`, `--profundo`, and `--save`.

**`/pr-report`** — report of the user's PRs in the repo (weekly inline, monthly and yearly saved).

**`/complexidade`** — measures cyclomatic complexity **only on changed files** (vs base or `--staged`), threshold 10 (or the target project's `CLAUDE.md` override). Detects the tool in order: project linter → `lizard` → `fta`. With `--fix`, offers refactoring via `code-simplifier`. The same gate runs embedded in `/sdd-review` (becomes a MINOR/MAJOR issue) and in `/executor-plan` (automatic fix during Final Verification, hard stop after 2 attempts).

**`/worktree-detect`** — detects opportunities to isolate branches/PRs into worktrees.

**`/modo-livre`** — autonomous mode toggle with three layers: broad allow (flows), **`ask` for `git commit`/`git push`** (human in the loop enforced by the harness — prompts in **any** permission mode, including `auto`) and deny for the dangerous ops (force push, `reset --hard`, `rm -rf`, publishes — always blocked). Compatible with the `auto` permission mode. Requires a session reload.

**`/git-worktree`, `/git-remove-worktree`, `/sync-tests`, `/git-prune-branches`** — git and worktree utilities.

**Model per command**: the main thread runs light (Sonnet base, or Haiku for git utilities) and only escalates to Opus **inside subagents**, on the step that genuinely needs reasoning — so the expensive model only processes focused context instead of burning tokens on mechanical steps (git, file reads, doc writing). Switching models on the main thread (`/model`) invalidates the prompt cache, so the commands avoid it. Exception: `/sdd-plan` runs on Opus in the main thread (planning is dense, interactive reasoning that can't be isolated in a subagent) and delegates only the heavy reads to subagents — for Medium scope, `/sdd-plan-eco` brings that cost down. In the frontmatters, models are full model IDs (the documented format for slash commands); in subagent spawns they are **aliases** (`opus`/`sonnet`/`haiku`), guaranteed by the Agent SDK docs — they track the best model of each tier with no maintenance.

**Progressive disclosure**: large commands keep only the protocol in the body; templates and single-use blocks live in `commands/references/` and are loaded via `Read` only at the step that uses them. This cuts the fixed cost per invocation (~30-40% on the heavy commands) and avoids dragging a report template along for dozens of execution turns.

### Recommended flow

```
Normal feature:   /sdd-plan → /pr-draft → (cd <worktree> && claude) → /executor-plan → /sdd-review
                                                                                          ↓
                                                              you review the diff and commit/push
Manual review:    /clear → /pair-review   (interactive companion over the staged diff, no execution noise)
Small change:     /quick-task
Mysterious bug:   /investiga → root cause with source → /quick-task or /sdd-plan
After PR closes:  /sdd-learning
New project:      /sdd-init (once)
When needed:      /busca · /verifica · /complexidade · /git-rebase-seguro · /roadmap · /memory-organize
```

`/pr-draft` is optional but recommended: it isolates the implementation in a worktree and signals the kickoff to the team. Artifacts in `thoughts/` serve as handoff between sessions — clear the session (`/clear`) between large commands to maximize the context window. The re-hydration cost is low (SPEC + `MEMORY.md` ≈ 2-3k tokens), so clearing is almost always a win: the durable state lives in files, not in the conversation.

## How to use

### 1. Install

```bash
# Global commands (all projects)
cp commands/*.md ~/.claude/commands/
mkdir -p ~/.claude/sdd-references && cp commands/references/* ~/.claude/sdd-references/

# Or project-scoped
cp commands/*.md /your-project/.claude/commands/
mkdir -p /your-project/.claude/sdd-references && cp commands/references/* /your-project/.claude/sdd-references/
```

The `references/` folder is required: large commands load templates from it on demand (progressive disclosure). Without it the commands still work via an inline fallback, but with summarized templates.

### 2. Prerequisites

In the project where the commands run:

- **`CLAUDE.md`** — project rules, stack, and conventions
- **`ARCHITECTURE.md`** — structural decisions and patterns
- **MCP [Context7](https://github.com/upstash/context7)** — to query official documentation (Zero Inference principle):

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

## Principles

- **Zero Inference** — never assume API behavior or patterns; verify against official docs (Context7) or existing code
- **Constitution-first** — reads `CLAUDE.md` and `ARCHITECTURE.md` before any action
- **TDD as a contract** — tests before code; if they break, we stop and discuss
- **Test count protection** — every task declares `Test count: N tests pass`; a drop = block (prevents silent deletion)
- **Test co-location** — tests in the SAME task that creates the code; deferring is an anti-pattern
- **Human-approved commits** — commands run `git add`, never `git commit`/`push` on their own
- **Persistent memory** — native auto-memory holds decisions/blockers/lessons across sessions; writes always under confirmation
- **Pair programming** — collaborative style, not a bureaucratic pipeline

## Persistent memory (auto-memory)

Commands recover context across sessions via **Claude Code's native auto-memory** (`~/.claude/projects/<project>/memory/`), managed by the `memory-keeper` skill. The harness loads `MEMORY.md` into the system prompt at the start of each session (limit 200 lines / 25KB); individual notes are opened on demand.

**Flat** convention (no subfolders): `MEMORY.md` as the index + `<type>_<slug>.md` files. There are **9 types** — 4 native to the harness and 5 SDD:

- **Native** — `user` (profile/preferences), `feedback` (collaboration rule), `project` (non-obvious context/deadline), `reference` (pointer to an external system)
- **SDD** — `decision` (architectural/technical decision), `blocker` (blocker + workaround), `lesson` (learning from execution/review), `idea` (explore later), `preference` (project-specific preference)

Writes are **always under confirmation**. Run `/memory-organize` when `MEMORY.md` grows (>150 lines) or you suspect orphans/duplicates. Full protocol in `skills/memory-keeper/SKILL.md`.

Two usages that raise the return per token:

- **Knowledge cache** — API claims verified via Context7/web become `reference` notes (claim + source + date + lib version). `/sdd-plan` consults this cache as **Step 0** of the Knowledge Verification Chain and only re-researches when the cache has expired (>90 days or a different major version). On a stable stack, it cuts repeated external research across features.
- **Self-sufficient hooks** — the line in `MEMORY.md` carries the **applicable rule**, not just the topic (e.g. `schema has no FKs; validate references at the application layer`). Since the index is loaded for free in every session, in most cases the agent acts without opening the individual note.

## Tests

- **Unit tests** in `thoughts/tests/`, written before the code (TDD). Not committed — they're working scaffolding
- **Integration/e2e** go where the project mandates and are committed
- If passing tests start to fail, or the count drops: mandatory stop to discuss

## Status line (optional)

A bottom bar showing model, folder, colored context bar, rate limits (5h/7d), and `/modo-livre` state — useful to know when to `/clear` (bar turns red at ≥85%) and to track consumption. Run `/statusline` pasting this (the prompt is in Portuguese, but Claude understands either language):

```
mostre [nome-do-modelo] entre colchetes, depois nome da pasta atual (basename de .workspace.current_dir), depois uma barra de progresso de 10 blocos usando █ pra preenchido e ░ pra vazio seguida da porcentagem de contexto e da palavra "ctx", depois " • 5h XX% (HhMm)" usando .rate_limits.five_hour.used_percentage e tempo ate .rate_limits.five_hour.resets_at (epoch), depois " • 7d XX% (Dd Hh)" com .rate_limits.seven_day.* na mesma logica; omita as secoes 5h/7d se rate_limits nao existir. e no fim adicione (ML 🟢) quando o arquivo <workspace>/thoughts/modo-livre/active existir ou (ML 🔴) quando nao existir. formato do tempo ate reset (diff = resets_at - now em segundos): se diff <= 0 omita o parentese; se diff < 60 mostre (<1m); se diff < 3600 mostre (Ym); se diff < 86400 mostre (XhYm) sem espaco; se diff >= 86400 mostre (Xd Yh) com espaco entre d e h. cor por threshold (aplicada na barra de contexto e nos numeros dos rate limits, NAO no resto do texto): verde se < 60%, amarelo se 60-84%, vermelho se >= 85%. salve em ~/.claude/statusline.sh com chmod +x e atualize ~/.claude/settings.json
```

Result: `[Claude Sonnet 4.5] meu-projeto ████░░░░░░ 42% ctx • 5h 8% (5h30m) • 7d 18% (5d 12h) (ML 🟢)`. Reload the session after configuring (`Ctrl+C` then `claude`). The layout does not show the git branch (it assumes your PS1 already does).

## Structure

```
commands/                   # Slash commands — CANONICAL SOURCE (copied to ~/.claude/commands/)
  sdd-plan.md · sdd-plan-eco.md · pr-draft.md · executor-plan.md · pair-review.md
  quick-task.md · sdd-review.md · sdd-learning.md · verifica.md · investiga.md
  sdd-init.md · memory-organize.md · roadmap.md · busca.md · pr-report.md
  complexidade.md · worktree-detect.md · modo-livre.md · git-worktree.md
  git-remove-worktree.md · git-rebase-seguro.md · sync-tests.md · git-prune-branches.md
  references/               # Templates loaded on demand (progressive disclosure)
  deprecated/               # Older versions — fallback (.vN.md suffix). Do not delete
skills/
  memory-keeper/            # Auto-memory: 9 types, flat convention, MEMORY.md as index
  conciso/                  # Concise response mode in pt-BR (lite/full/ultra)
  deprecated/               # Older skills — fallback
```

**`commands/` vs `skills/`** (Anthropic convention): commands are invoked manually (`/sdd-plan`); skills auto-trigger by description when the context matches. `memory-keeper` is a skill because it must always be available to read/write memory without the user having to ask.

### Outputs in `thoughts/` (in the target project)

```
thoughts/
  ROADMAP.md                  # Multi-feature view (optional)
  plans/SPEC-DD-MM-YYYY-slug.md      # /sdd-plan
  history/IMP-DD-MM-YYYY-slug.md     # /executor-plan
  reviews/                    # /sdd-review
  research/YYYY-MM-DD-slug.md        # /busca --save
  reports/prs-YYYY-MM.md             # /pr-report (opt-in)
  quick/NNN-slug/             # /quick-task (TASK.md + SUMMARY.md)
  tests/                      # TDD scaffolding (NOT committed)
```

## Inspiration

- **[spec-kit](https://github.com/github/spec-kit)** — GitHub's official toolkit for Spec-Driven Development
- **[tlc-spec-driven (Tech Lead's Club)](https://github.com/tech-leads-club/agent-skills/blob/main/packages/skills-catalog/skills/(development)/tlc-spec-driven/SKILL.md)** — SDD skill with adaptive phases, auto-sizing, and formalized parallelism. Author: Felipe Rodrigues. Several v7 concepts are adapted from it — see [Attributions](#third-party-attributions--licenses)
- **[HumanLayer — Advanced Context Engineering](https://www.humanlayer.dev/blog/advanced-context-engineering)** and **[Claude Commands](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands)**
- **[Como eu uso o Claude Code — Workflow SDD](https://dfolloni.substack.com/p/como-eu-uso-o-claude-code-workflow)**
- **[caveman](https://github.com/JuliusBrussee/caveman)** — conceptually inspired the `conciso` skill. Author: Julius Brussee
- Extreme Programming (XP) — pair programming, TDD, small releases

## Third-Party Attributions & Licenses

This toolkit incorporates concepts adapted from third-party works. Original licenses are preserved and attribution is given as required.

### tlc-spec-driven

- **Author**: Felipe Rodrigues — https://github.com/felipfr
- **Source**: https://github.com/tech-leads-club/agent-skills/tree/main/packages/skills-catalog/skills/(development)/tlc-spec-driven
- **Original license**: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- **Status**: adapted (not copied verbatim). Concepts incorporated at v7: complexity-based auto-sizing, persistent memory across sessions, `[P]`/`Depends on:`/`Gate:` task markers, Granularity Check, Diagram-Definition Cross-Check, Test Co-location Validation, Phase grouping (Foundation/Core/Integration), `Test count: N tests pass`

CC-BY-4.0 is a permissive license compatible with MIT — it allows use, modification, and redistribution provided the original author is credited and modifications are indicated. This section fulfills that requirement.

### caveman

- **Author**: Julius Brussee — https://github.com/JuliusBrussee
- **Source**: https://github.com/JuliusBrussee/caveman
- **Original license**: [MIT](https://github.com/JuliusBrussee/caveman/blob/main/LICENSE)
- **Status**: conceptually inspired (not copied). The `conciso` skill uses the same principle of cutting output tokens via style reformatting, with an implementation written from scratch in pt-BR and adjustable compression levels (`lite`/`full`/`ultra`). Details in the skill's own `SKILL.md`.

## License

[MIT](./LICENSE) — original code of this toolkit. Excerpts adapted from third-party works retain their original licenses (see [Attributions](#third-party-attributions--licenses)).
