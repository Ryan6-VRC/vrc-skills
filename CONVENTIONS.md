# vrc-skills conventions

Skills for the Atelier workspace; primary reader: an agent with the full workspace open. Workspace doctrine — the routing ladder, echo rules, tool design — lives in the meta-repo's `docs/tool-design.md`; this file is only the shape a skill in this repo takes.

## A skill's anatomy

In order; the exemplars are `compose-mergeable` (the fullest instance) and `own-gimmick` (the same shape at a quarter the size — the anatomy scales down, not off):

1. **Description** (frontmatter). Starts `Use when`, carries a few quoted operator ask-phrases, and ends with negative routing that names the sibling owning each adjacent intent ("not composing a ready-made gimmick module (compose-mergeable)"). Descriptions are resident in every session: the ask-phrases and negative routes *are* the routing surface — never compress them away to save length.
2. **Intro** (after the imperative H1). One paragraph declaring the ownership split: the domain knowledge lives in named docs — the required reading — and the skill owns the process, its gates, and the judgment calls. `author-gimmick`'s "The taxonomy lives elsewhere and is the required reading… This skill owns the process and its gates only" is the model.
3. **No-operator block.** Every operator-gated skill routes to the no-operator protocol (`workflow.md`) with the canonical `**No operator to ask?**` line — in the intro, or at the gate it governs where that reads better (`import-vendor-asset` and `shoot-thumbnail` place it at the gate, each with the skill's derivable default). A skill with no operator gate to route — one that runs unattended by design, or an authoring skill the agent runs inline — declares itself in the constants' `autonomous_skills` instead of carrying the block.
4. **Scope** (only when the boundary needs stating). What this owns, and the boundary — out-of-scope intents arrow-routed to the sibling that owns them.
5. **The sequence.** Ordered steps (`## The flow` with `### N.`, or `## Phase N — <name>`). **Gates are first-class**: every operator sign-off is bold at the step it gates and says what is being signed off on; every question that needs hardware or another client is a **named handoff** (`verify.md`'s discipline). Verify is the terminal step and is never omitted.
6. **Tools**, when the skill drives tools that need routing to a contract doc: bold-backticked name + role gloss + the owning contract doc — roles, not contracts. Present, it is the terminal section; a tool-light skill cites its tools inline at the point of use and needs no such section (`import-vendor-asset`, `shoot-thumbnail`).

**Cite, don't restate.** A skill that depends on a doc's contract cites it; restating it manufactures the drift the workspace echo rules exist to prevent (`docs/tool-design.md` §Duplication owns the policy).

**Meta-skills** (`fitting-session`) are exempt from the anatomy beyond frontmatter; the exemption is earned by membership in the constants' `exempt_skills` list — its sole authority. The intro should still say a skill is meta-work for its readers, but the gate keys on the list, never on that prose (a substring match would silently un-check any skill that merely names the word).

## The gate

`tools/validate_skills.py` is the repo-local gate: it lints skill anatomy against this contract and runs in a bare clone. The meta-workspace's `tools/check_prose.py` is the cross-repo pass — it invokes this gate, then resolves each skill's doc pointers and Tools-section names against the assembled workspace.

**The anatomy governs a consuming repo's project skills too**, not this repo's alone: `check_prose.py` names both `vrc-skills/skills/*` and the meta-repo's `.claude/skills/*` in one invocation, and a skill written into either enumeration owes the same shape. A project skill's relative links are bounded by *its* repo, which the gate derives per skill rather than from its own location — a project skill linking its own repo's docs is not an escape.

Mechanical, load-bearing facts are errors: a skill that would not load, a name mismatching its directory, more than one H1, a dead link. Anatomy is warnings — the description prefix and length band, and the no-operator block every gated skill owes. Routing quality (does a description name its adjacent siblings?) and tool-citation adequacy are judgment the workspace prose-audit adjudicates, not this gate; whether an anatomy warning hardens into an error is workspace policy (`docs/tool-design.md` there).

Both linters read their constants from this block; the scripts embed no copies:

```yaml
# skill-anatomy constants — read by tools/validate_skills.py and the workspace prose checks
description_prefix: "Use when"
description_length: {warn_min: 200, warn_max: 700, error_max: 1024}
exempt_skills: [fitting-session]          # anatomy-exempt: frontmatter identity checks only
autonomous_skills: [showcase-record, kickoff, write-for-agents]   # no operator gate by design: no no-operator block owed
required_no_operator_pointer: "workflow.md"
terminal_section: "Tools"                  # the Tools section's name (check_prose resolves its entries against TOOLS.md)
```
