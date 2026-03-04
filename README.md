# claude-code-sdd-toolkit

> **[Leia em Português](./README-pt.md)**

A collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) slash commands that implement a **Specification-Driven Development (SDD)** workflow.

These commands turn Claude Code into a structured development partner that follows a disciplined process: **Research → Spec → Plan → Execute → Review**.

## What's Inside

### SDD Workflow (3-phase pipeline)

| Phase | Command | Description |
|-------|---------|-------------|
| 0 — Research | `/gerador-prd` | Scouts the codebase and external docs, producing a PRD (Preliminary Design Research) without prescribing solutions |
| 1 — Spec + Plan | `/gerador-spec` | Reads the PRD and produces a two-part document: **Part A** (what & why) and **Part B** (how — atomic micro-tasks) |
| 2 — Execute | `/executor-plan` | Executes micro-tasks one at a time, pausing for user approval after each step |
| Review | `/sdd-review` | Analyzes a PR, branch, or diff and generates a private review report with confidence scoring |

### Git Utilities

| Command | Description |
|---------|-------------|
| `/git-worktree` | Creates an isolated worktree from the default branch for parallel work |
| `/git-remove-worktree` | Safely removes a worktree, checking for uncommitted changes first |
| `/git-prune-branches` | Removes local branches whose remotes have been deleted |
| `/worktree-detect` | Analyzes branches/PRs and detects opportunities to split into focused worktrees |

### Deprecated (v1)

Older versions of the SDD commands are kept in `deprecated/commands/` for reference. They work independently but lack some features of the current versions (worktree integration, checkpoint tracking, diagram generation).

## Core Principles

These commands enforce a few non-negotiable rules:

- **Zero Inference** — Never assume API behavior or patterns. Always verify against official documentation (via [Context7](https://context7.com/) MCP) or existing project code. If no verifiable source is found, mark as `[NEEDS VERIFICATION]`
- **Constitution-first** — Commands always read `CLAUDE.md` and `ARCHITECTURE.md` before any action, making them stack-agnostic
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
/gerador-prd
/gerador-spec
/executor-plan
/sdd-review
```

### Recommended SDD Flow

```
/gerador-prd          → produces PRD in thoughts/shared/research/
  ↓ review the PRD, resolve [NEEDS CLARIFICATION], fix any inaccuracies
/gerador-spec          → reads PRD, produces SPEC in thoughts/shared/plans/
  ↓ review the SPEC, resolve [NEEDS CLARIFICATION], approve before Plan
/executor-plan         → reads SPEC, executes micro-tasks with user checkpoints
  ↓ review the implementation, approve each micro-task
/sdd-review            → reviews the resulting PR/branch
```

> **Important**: Always review the output of each phase before moving to the next. Resolve any `[NEEDS CLARIFICATION]` items and correct inaccuracies — the next phase uses the previous one as its source of truth.

## Directory Structure

```
commands/
  gerador-prd.md            # Phase 0 — Research
  gerador-spec.md           # Phase 1 — Spec + Plan
  executor-plan.md          # Phase 2 — Execute
  sdd-review.md             # Review
  git-worktree.md           # Create worktree
  git-remove-worktree.md    # Remove worktree
  git-prune-branches.md     # Prune local branches
  worktree-detect.md        # Analyze worktree opportunities
deprecated/
  commands/
    gerador-prd.v1.md       # Legacy research (v1)
    gerador-spec.v1.md      # Legacy spec (v1)
    executor-plan.v1.md     # Legacy executor (v1)
```

## Inspiration

This toolkit was heavily inspired by the following resources:

- **[spec-kit](https://github.com/github/spec-kit)** — GitHub's official toolkit for Spec-Driven Development. The foundation of the SDD methodology used here
- **[HumanLayer — Advanced Context Engineering](https://www.humanlayer.dev/blog/advanced-context-engineering)** — Deep dive into context engineering patterns for AI agents
- **[HumanLayer Claude Commands](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands)** — Practical examples of PRD generation and structured development commands
- **[Como eu uso o Claude Code — Workflow SDD](https://dfolloni.substack.com/p/como-eu-uso-o-claude-code-workflow)** — Detailed walkthrough of a real-world SDD workflow with Claude Code
- Various YouTube videos on Spec-Driven Development and AI-assisted coding workflows

## License

[MIT](./LICENSE)
