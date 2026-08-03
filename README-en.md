# claude-code-sdd-toolkit

> **[Leia em português](./README.md)**

A TDD pair-programming workflow for [Claude Code](https://code.claude.com/docs), in fifteen skills that
chain together: specify behavior → plan → decide what to test → implement → review → ship.

The principle behind all of it: **the agent gathers facts, you make the calls.** No piece here hands
back an "approved" — they hand back findings, along with an explicit account of what went unexamined.

> ⚠️ **v10 is being rebuilt.** The full cycle and the long-lived pieces (roadmap, close-out, memory,
> auditing) are done and in use. What's missing is the periphery — research, bug diagnosis,
> prototyping, setup. The entire v9 toolkit still lives in [`deprecated/`](./deprecated/) and works
> if you're already using it. See [`REFACTOR-v10.md`](./REFACTOR-v10.md) (in Portuguese).

## Install

The repository **is** the plugin — `.claude-plugin/plugin.json` at the root, the pieces under
`skills/`.

**Try it without installing** (session-scoped, nothing gets copied):

```bash
claude --plugin-dir /path/to/claude-code-sdd-toolkit
```

**Install for real** — clone it into your personal skills directory:

```bash
git clone https://github.com/wisley7l/claude-code-sdd-toolkit ~/.claude/skills/tk7
```

A skill folder containing `.claude-plugin/plugin.json` loads as the `tk7@skills-dir` plugin — no
marketplace, no install step. To update, `git pull`.

**Already have the repo cloned?** Symlink it instead of cloning again — edits in the repo take
effect immediately:

```bash
ln -s /path/to/claude-code-sdd-toolkit ~/.claude/skills/tk7
```

**Optional dependency.** `implement` offers a `code-simplifier` pass once the suite is green. Worth
having installed — without it the skill just says so and moves on:

```
/plugin install code-simplifier@claude-plugins-official
```

**The commands the skills call.** One script installs everything — no sudo, idempotent:

```bash
./scripts/install.sh          # or --check to just see what's missing
```

It puts `roadmap`, `memory-audit`, and `structure-cache` in `~/.local/bin` (wrappers pointing at this
repo's code — edit here and it reflects immediately) and offers to pre-authorize them in your
`settings.json`, which avoids a prompt per call. It respects `CLAUDE_CONFIG_DIR`, backs up before
touching anything, and never overwrites a third-party binary of the same name.

Why a command and not prose: the roadmap contract is written by **four** pieces (`roadmap`, `plan`,
`pr-draft`, `pr-close`). In a script it exists once and is executable; in prose it would be repeated
four times and drift on the first edit.

### Invoking

The pieces live under the plugin namespace: **`/tk7:spec`**, `/tk7:plan`, and so on. The bare
name (`/spec`) works too, **as long as no other skill claims it**.

Three pieces here share a name with something that ships with Claude Code — `plan`, `code-review`,
and `memory` (that last one is a built-in command). Use the full name for those: `/tk7:plan`,
`/tk7:code-review`, and `/tk7:memory`. Plugin skills are namespaced and never shadow the
originals, so `/code-review` and `/memory` still reach the built-in ones.

## The cycle

```
   spec  →  plan  →  test-plan  →  pr-draft  →  worktree
                                        │
                                        ▼
              implement  ⇄  code-review  →  pr-ready  →  merge  →  close
                                 ▲              │                     │
                                 └─ the team comments ─┘      capability · roadmap
                                                                memory · debt
```

| Piece | What it does |
|---|---|
| **`spec`** | Writes the behavior the change delivers — the **what**, never the how. Testable requirements with scenarios that actually exercise them, plus the delta against what the system already promises. An adversary reads it before you do. |
| **`plan`** | The **how**: researches the codebase, settles technical decisions with sources, and breaks the work into tasks grouped by the PRs they'll become. |
| **`test-plan`** | Decides **what the change guarantees** — test type, environment, cases, and what's left without a safety net. A session where you cut and prioritize; the agent does the legwork and proposes. |
| **`pr-draft`** | Opens the PR in draft before the first line of code exists. With `sync`, rewrites the body after implementation as a preview for whoever reviews it. |
| **`worktree`** | Creates and removes isolated worktrees. A new worktree comes up with permissions applied and its memory centralized in the main repository. |
| **`implement`** | Runs the tasks with TDD. Delegates independent ones to parallel subagents and validates every result. Closes with the simplification pass — the *refactor* step, with the suite run again afterward. Stages files, never commits on its own. |
| **`code-review`** | Six independent lenses — conformance, bugs, security, naming, queries, and tests. Once the team comments, it checks whether each point was actually addressed. |
| **`pr-review`** | The other side: reviewing **someone else's** PR. It explains the change before judging it, checks what the PR promised against what it delivered, grills you on what only you can decide, and assembles a single submit review with inline comments — which you see before anything is posted. |
| **`pr-ready`** | Confirms the PR is green, refreshes its body, and hands it off: leaving draft and requesting a reviewer, each one gated on your confirmation. |
| **`pr-close`** | Closes the loop once the PR is merged — archives the change, promotes the delivered behavior into the living capability, completes the roadmap item, harvests debt, and distills learnings. When the PR is merely approved, it harvests the follow-ups while fixing inside the PR is still cheap. |
| **`pr-audit`** | Rescues the debt reviews left behind: sweeps merged PRs, checks each point against today's code, and feeds a perennial issue with whatever is still open. |
| **`roadmap`** | The view from above — one item per planned PR, in an Obsidian vault where a dependency is a wikilink and the graph is native. Syncs status against the real state of the PRs and shows what's unblocked right now. |
| **`memory`** | Writes and curates the project's memory — learnings, bugs already solved, decisions. Audits how much of it actually acts, since only the index is ever loaded, and never deletes a note unless you say so. |
| **`baseline`** | Derives a domain's **capability** from the tests and code already in place — for adopting the toolkit in a codebase that has history. |
| **`grilling`** | An interview for the decisions that are yours: one question at a time, each with an explicit recommendation. Other pieces call it when they hit a decision that's expensive to reverse. |

## What the toolkit guarantees

These aren't style preferences — they're what makes the rest of it mean anything:

- **Verified red.** The test runs and **fails for the right reason** before any implementation exists.
  A test that passes without production code is a hard stop, not evidence you were already done.
- **Nothing ships unverified.** The floor is manual verification by you, with the evidence recorded.
  No verification at all takes an explicit question and your yes — not a justification the agent
  writes to itself.
- **The test count never drops quietly.** If it drops, everything stops — deleting a test to get the
  gate green is the failure that disguises itself as progress better than any other.
- **Test type follows need.** `unit` isn't the default; the type comes from the behavior, and the
  environment it requires is stated up front.
- **Commits and pushes are yours.** Staging is free; everything past it waits for your yes. Pushing
  is always a human action.
- **Green before handoff.** CI passed, or the full local suite — every layer, not just the tests this
  PR happened to touch.
- **API behavior gets verified**, via Context7 or the code already calling it. Without a source, the
  claim is flagged and can't support a task.
- **No piece approves anything.** No score, no tally, no "0 issues". Findings arrive as they came —
  including the ones the agent disagrees with, its objection noted alongside.

## Where things live

A change is **one folder**, in the main repository:

```
thoughts/changes/<NNN>-<slug>/
  spec.md     the behavior + the delta
  plan.md     the approach, the technical decisions, the test matrix
  tasks.md    the tasks, grouped by PR
  notes.md    what happened during execution and review
```

And what outlives the change:

```
thoughts/capabilities/<domain>.md    what the system does today
```

`thoughts/` is local and **stays out of git** — none of it gets committed, and none of it shows up in
the PR body.

## Licenses

The toolkit is original work that borrows concepts from others. Attributions live in
`skills/<piece>/CREDITS.md` — sibling files, deliberately outside what the agent loads at runtime.
The protocol and the index of sources are in [`NOTICE.md`](./NOTICE.md), with full license texts
under [`LICENSES/`](./LICENSES/).

---

**A note on language:** skill names are in English (the leading word anchors invocation), while the
skill bodies and all documentation are written in Brazilian Portuguese. This README is the English
entry point; `REFACTOR-v10.md`, the CREDITS files, and the skill bodies themselves are in Portuguese.
