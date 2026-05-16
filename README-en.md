# claude-code-sdd-toolkit

> **[Leia em Português](./README.md)**

A collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) slash commands that implement a **Specification-Driven Development (SDD)** workflow.

These commands turn Claude Code into a structured development partner that follows a disciplined process: **Research → Spec → Plan → Execute → Review**.

## What's Inside

### Main Workflow v7 (auto-sizing, single-doc spec)

| Phase | Command | Description |
|-------|---------|-------------|
| Plan | `/sdd-plan` | Research + understanding + tasks in **1 auto-sized document** (Medium/Large/Complex). Maps existing design docs, reconciles conflicts, classifies scope, breaks down tasks with Phases + `[P]`/`Depends on:`/`Gate:`. 3 pre-approval checks (Granularity, Diagram-Definition Cross-Check, Test Co-location). Detects Quick scope and hands off to `/quick-task` |
| Execute | `/executor-plan` | Pair programming with TDD. Parallel sub-agents for `[P]` tasks. Test count protection (blocks silent deletion). Pauses between tasks. Updates STATE.md |
| Quick | `/quick-task` | Quick mode for small changes (≤3 files, 1 sentence). Skips formal SPEC. Safety valve escalates to formal flow if scope grows |
| Learn | `/sdd-learning` | Reads IMPs and reviews, extracts non-obvious learnings, proposes registration in the vault (SDD flavor in `state/` or general in `feedback`/`project`/`reference`). Confirms per item. Updates > creates. |
| Roadmap | `/roadmap` | Manages `thoughts/ROADMAP.md`. Adds entries, imports from GH issues, syncs status with existing SPEC/IMP |

### Git Utilities

| Command | Description |
|---------|-------------|
| `/sdd-review` | Analyzes a PR, branch, or diff and generates a private review report with confidence scoring |
| `/git-worktree` | Creates an isolated worktree from the default branch for parallel work |
| `/git-remove-worktree` | Safely removes a worktree, syncing TDD tests before deletion |
| `/sync-tests` | Syncs TDD tests between worktree and root, showing diffs before acting |
| `/git-prune-branches` | Removes local branches whose remotes have been deleted |
| `/worktree-detect` | Analyzes branches/PRs and detects opportunities to split into focused worktrees |

### Previous Versions

- **Split v7 (gerador-prd + gerador-spec)** — earlier v7 workflow had 2 separate phases (PRD in `thoughts/research/` + SPEC in `thoughts/plans/`). Merged into `/sdd-plan` (single auto-sized doc) because they duplicated ~40-50% of content between outputs. Files preserved at `commands/deprecated/gerador-prd.v7.md` and `commands/deprecated/gerador-spec.v7.md`
- **v6** — previous stable version, kept in `commands/v6/` as fallback. If v7 doesn't work for a project, copy `v6/` files over `commands/`
- **v1-v5** — historical versions in `deprecated/commands/` and `commands/deprecated/`

## Core Principles

These commands enforce a few non-negotiable rules:

- **Zero Inference** — Never assume API behavior or patterns. Always verify against official documentation (via [Context7](https://context7.com/) MCP) or existing project code. If no verifiable source is found, mark as `[NEEDS VERIFICATION]`
- **Constitution-first** — Commands always read `CLAUDE.md` and `ARCHITECTURE.md` before any action, making them stack-agnostic
- **Persistent memory** — `thoughts/STATE.md` holds decisions/blockers/lessons across sessions. Writes always require user confirmation
- **Auto-sizing** — Complexity determines depth: Quick (`/quick-task`), Medium/Large/Complex (1 SPEC via `/sdd-plan`)
- **Test count protection** — Every task declares `Test count: N tests pass`. If it drops = block (prevents silent deletion)
- **Safe parallelism** — `[P]` tasks run in concurrent sub-agents, with file conflict checks
- **Atomic execution** — The executor never advances to the next task without explicit user approval
- **Source transparency** — Every external reference used by subagents must appear in the final document with a verifiable link

## How to Use

### 1. Install

Copy the command files to your Claude Code commands directory:

```bash
# Global commands (available in all projects)
cp commands/*.md ~/.claude/commands/

# Or project-scoped commands
cp commands/*.md /your-project/.claude/commands/
```

### 2. Prerequisites

**Project files** — These commands expect your project to have:

- **`CLAUDE.md`** — Project rules, stack, conventions (the "constitution")
- **`ARCHITECTURE.md`** — Structural decisions and patterns

The commands read these files first and adapt to whatever stack you use. No hardcoded framework or runtime assumptions.

**MCP Server** — The commands use [Context7](https://github.com/upstash/context7) to query official documentation of libraries and frameworks. This is how they avoid inference — they look up real docs instead of guessing.

To set it up, add to your Claude Code MCP config (`~/.claude.json` or project `.mcp.json`):

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

> The commands will still work without Context7, but documentation lookups will fall back to web search, which is less reliable.

### 3. Run

In Claude Code, invoke any command with `/`:

```
/sdd-plan
/executor-plan
/quick-task
/roadmap
/sdd-review
```

### Recommended Flow

```
Quick — small change (≤3 files, 1 sentence):
  /quick-task     -> runs directly with TDD where applicable
                     (safety valve: escalates to formal flow if scope grows)

Medium/Large/Complex — normal feature:
  /sdd-plan       -> research + understanding + tasks in 1 auto-sized doc
                     (Maps design docs, classifies scope, breaks tasks with [P],
                      3 pre-approval checks: Granularity, Diagram, Test Co-location)
    ↓ clear session
  /executor-plan  -> codes with TDD. Parallel sub-agents for [P].
                     Test count protection.

Multi-feature view:
  /roadmap                       -> syncs status with SPECs/IMPs
  /roadmap add "<description>"   -> adds to Backlog
  /roadmap add #123              -> imports from GH issue
```

> **Important**: Clear the session between large commands (PRD → SPEC → Executor) to maximize the context window. Artifacts in `thoughts/` serve as handoff between sessions.

### 4. Persistent memory (STATE.md or vault)

Commands recover context across sessions through persistent memory. **Two modes**:

**Legacy mode (default)** — monolithic `thoughts/STATE.md`:
- **Architectural decisions** — decisions that persist beyond a single feature
- **Known blockers** — things that have blocked work before, with symptoms to recognize them
- **Lessons learned** — approaches that didn't work, patterns that proved valuable
- **Deferred ideas** — things that came up but didn't fit current scope
- **User preferences** — work style, preferred tools, communication patterns

**Vault mode (optional)** — atomic notes in a central vault (Obsidian second brain):

```bash
export CLAUDE_VAULT_PATH=~/path/to/your/vault
```

If `$CLAUDE_VAULT_PATH` points to an existing directory, commands switch to reading/writing in:

```
$CLAUDE_VAULT_PATH/<org>/<project>/state/
├── decisoes/    # one note per decision, with frontmatter
├── blockers/
├── licoes/
├── ideias/
└── preferencias/
```

Vault mode benefits:
- **Independent versioning** from the project (state doesn't pollute the repo)
- **Unified graph** across projects (Obsidian connects cross-project decisions)
- **Atomic notes** (one file per decision) — better search and filtering
- **Promotion** of decisions to organization or global scope

Path convention: `<org>` and `<project>` are derived from `cwd` (heuristic `~/codigos/<org>/<project>/`). If the heuristic fails, the command asks. See the `vault-memory` skill for the full protocol.

**Integration is fully opt-in** — without `CLAUDE_VAULT_PATH`, the toolkit behaves exactly as before (monolithic STATE.md). You can adopt it gradually.

In either mode: **writes always under user confirmation** — the command proposes entries, you approve case by case.

### 5. Tests

- **Unit tests**: Always in `thoughts/tests/`, written before code (TDD). Not committed — they're our scaffolding
- **Test count protection**: Every task declares `Test count: N tests pass`. If it drops during execution = mandatory stop (prevents silent deletion)
- **Integration/e2e tests**: When the project uses them, go where the project mandates and are committed
- **Test co-location**: Tests go in the SAME task that creates the code. Defer = anti-pattern, blocked by sdd-plan
- If passing tests start failing: mandatory stop to discuss

## Structure

### Toolkit

```
commands/
  sdd-plan.md               # v7+ — Research + Understanding + Tasks (1 auto-sized doc)
  executor-plan.md          # v7 — Code with TDD + parallelism
  quick-task.md             # v7 — Quick mode
  roadmap.md                # v7 — Manage ROADMAP.md
  sdd-review.md             # Review
  sdd-learning.md           # Harvest learnings from IMPs+reviews -> vault
  git-worktree.md           # Create worktree
  git-remove-worktree.md    # Remove worktree
  sync-tests.md             # Sync TDD tests
  git-prune-branches.md     # Prune branches
  worktree-detect.md        # Analyze worktrees
  v6/                       # Previous version (fallback)
    gerador-prd.md
    gerador-spec.md
    executor-plan.md
  deprecated/               # v3, v4, v5, v7 (split PRD+SPEC, vault-memory→skill)
    gerador-prd.v7.md       # Replaced by sdd-plan
    gerador-spec.v7.md      # Replaced by sdd-plan
    vault-memory.v7.md      # Promoted to skill (lives outside commands/)
deprecated/
  commands/                 # v1, v2
```

### Outputs in `thoughts/` (in the project where commands run)

```
thoughts/
  ROADMAP.md                  # Multi-feature view (optional)
  STATE.md                    # Persistent memory (optional, created under confirmation)
  plans/
    SPEC-DD-MM-YYYY-slug.md   # Output of /sdd-plan (1 auto-sized doc)
  history/
    IMP-DD-MM-YYYY-slug.md    # Output of /executor-plan
  reviews/
    (output of /sdd-review)
  quick/
    NNN-slug/
      TASK.md                 # Input of /quick-task
      SUMMARY.md              # Output of /quick-task
  tests/                      # TDD scaffolding (NOT committed)
```

> Before v7, artifacts were in `thoughts/shared/`. v7 simplifies by removing `shared/` — TDD tests remain isolated in `thoughts/tests/`. The `thoughts/research/` folder (used by `gerador-prd`) is no longer needed — `/sdd-plan` writes directly to `thoughts/plans/`.

## Inspiration

This toolkit was heavily inspired by the following resources:

- **[spec-kit](https://github.com/github/spec-kit)** — GitHub's official toolkit for Spec-Driven Development. The foundation of the SDD methodology used here
- **[tlc-spec-driven (Tech Lead's Club)](https://github.com/tech-leads-club/agent-skills/blob/main/packages/skills-catalog/skills/(development)/tlc-spec-driven/SKILL.md)** — Spec-Driven Development skill with 4 adaptive phases (Specify, Design, Tasks, Execute), complexity-based auto-sizing, persistent `STATE.md`, Test Co-location Validation, and formalized parallelism (`[P]`, `Depends on:`, `Gate:`). Author: Felipe Rodrigues. Starting at v7 of this toolkit, several concepts are adapted from this skill — see [Attributions](#third-party-attributions--licenses)
- **[HumanLayer — Advanced Context Engineering](https://www.humanlayer.dev/blog/advanced-context-engineering)** — Deep dive into context engineering patterns for AI agents
- **[HumanLayer Claude Commands](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands)** — Practical examples of PRD generation and structured development commands
- **[Como eu uso o Claude Code — Workflow SDD](https://dfolloni.substack.com/p/como-eu-uso-o-claude-code-workflow)** — Detailed walkthrough of a real-world SDD workflow with Claude Code
- Various YouTube videos on Spec-Driven Development and AI-assisted coding workflows

## Third-Party Attributions & Licenses

This toolkit incorporates concepts adapted from third-party works. Original licenses are preserved and attribution is given as required.

### tlc-spec-driven

- **Author**: Felipe Rodrigues — https://github.com/felipfr
- **Source**: https://github.com/tech-leads-club/agent-skills/tree/main/packages/skills-catalog/skills/(development)/tlc-spec-driven
- **Original license**: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- **Status**: adapted (not copied verbatim). Concepts incorporated starting at v7 of this toolkit: complexity-based auto-sizing (Quick/Medium/Large/Complex), persistent `STATE.md`, `[P]` / `Depends on:` / `Gate:` task markers, Granularity Check, Diagram-Definition Cross-Check, Test Co-location Validation, Phase grouping (Foundation/Core/Integration), `Test count: N tests pass (no silent deletions)`

CC-BY-4.0 is a permissive license compatible with MIT — it allows use, modification, and redistribution provided the original author is credited and modifications are indicated. This section fulfills that requirement.

## License

[MIT](./LICENSE) — original code of this toolkit. Excerpts adapted from third-party works retain their original licenses (see [Attributions](#third-party-attributions--licenses)).
