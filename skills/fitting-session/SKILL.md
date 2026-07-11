---
name: fitting-session
description: Use when stress-testing the workshop itself against the vendor asset library — "run a fitting session", "wear-test the tooling", a QA sweep dispatching worker agents on real avatar tasks to find where tools, docs, and skills chafe, ending in fixup kickoffs. Not a single avatar task (that task's own skill), nor measuring one skill (skill-assay).
---

# Fitting session — wear-test the workshop on real vendor work

You are the fitter: an orchestrator that maps what the workshop *claims* it can do, dispatches
worker agents to actually do it against real vendor assets, grades them independently, and
distills every sharp edge into directed kickoff prompts. The system under test is the tooling +
docs + skills, **not the workers** — a worker failing where the docs say it should succeed is a
finding about the docs. Stay context-light: dispatch the heavy work (tasks, grading, transcript
reads) to subagents and hold only their verdicts.

**Provisional skill — no run has happened yet.** Run 1 doubles as this skill's shakedown: log
friction with *this skill's own instructions* in the run report, and `skill-temper` it afterwards.

## Parameters and venue

At launch: a **lane**, a **task budget** (default ~10), and the Unity project the session was
started in. Two sessions may run concurrently only on **different lanes in different projects**.

- **geometry** — import-vendor-asset, own-base, own-mergeable, compose-mergeable,
  map-outfit-shapes, reproportion.
- **behavior** — controller round-trips (`DecompileController`/`CompileController`), gimmick and
  menu authoring, emulator verification per `verify.md`. Needs vendor assets already **imported**,
  not composed: a shipped vendor FX is itself a round-trip/rebuild target, and a simple compose
  done as the task's setup is a test in its own right. Only a project with nothing imported stops
  the run — say so rather than importing a corpus first.

The vendor library root comes from `CLAUDE.local.md` (machine-local). It is **read-only** — a
worker writing to it is an automatic grade-fail regardless of task outcome.

## The assay record

Everything durable lives in the Atelier root's `docs/assay/` (gitignored — create the directory
and seed an empty ledger if missing; being untracked, it needs no worktree to write):

- `LEDGER.md` — cross-run state. One row per **capability claim**, keyed
  `arc | claim | asset-class | lane` — asset *class*, never a specific file: the class is what
  passes or fails. Status vocabulary: `untested`, `pass@run-N`, `fail@run-N → <kickoff-id>`,
  `fixed-verified@run-N`. Keep keys stable across runs; a later fitter must recognize its
  predecessor's rows.
- `run-N-<lane>.md` — this run's report: envelope map, queue with predictions, per-task verdicts,
  findings with IDs. Append as you go — the report must survive an interrupted session.

## Phase 0 — map the envelope

Derive the claimed capability envelope from `TOOLS.md`, the lane's docs, and the lane's skill
descriptions: a checklist of task shapes a competent model should complete. Diff it against the
ledger's prior map — docs change as holes close, so the boundary moves. A **limit-pusher** is one
deliberate step past a named boundary, labeled as such in the queue; its failure confirms the map
rather than filing a bug.

## Phase 1 — build the queue

A fixed queue, written into the run report before any dispatch — no per-task asset picking.
Priority order:

1. **Regression-verify prior fails** — every `fail` ledger row in this lane. First check whether
   a fix plausibly landed (its kickoff's status; `git log` of the tool repos since the fail was
   recorded), but test regardless — the ledger distinguishes "fix never attempted" from "fix
   landed but insufficient", and they produce different kickoffs.
2. **Anti-backslide spot-checks** — one or two prior passes, chosen because their tool surface
   *churned* since the pass (`git log` of vrc-unity-tools / vrc-blender-tools / vrc-skills
   against the pass date). Retesting an untouched code path is worthless; backslides live
   downstream of churn.
3. **Frontier** — untested rows and new asset classes, stratified across vendor, asset type, and
   expected weirdness (the library's inventory doc helps), plus 2–3 limit-pushers.

Each entry: asset, arc, the worker prompt, an assigned **tier**, and a **prediction** (pass/fail,
one line of why). Tier is itself a calibration claim: Sonnet for asset shuffling and mechanical
arcs (import, compose, repath), Opus for complex behavior work (controller authoring, gimmicks,
multi-step reconciles), Fable only for frontier limit-pushers. Predictions — outcome and tier —
are what make the envelope map falsifiable: a miss in either direction is a finding, including a
task that needed a higher tier than assigned.

## Phase 2 — the task loop

Strictly serial for anything that touches the Unity Editor — concurrent editing churns NDMF
rebuilds and poisons `RenderAvatar`. Graph-only, Blender-headless, or doc-reading work may
overlap.

**Dispatch.** Worker on the tier the queue entry assigned (below). The prompt is a natural
operator request, phrased as the repo's owner would ask it, ending with one standing instruction:

> When done, end with a FRICTION REPORT: tools that misbehaved or refused unexpectedly, docs or
> skills that said something untrue or unhelpful, workarounds you resorted to, and anything about
> this asset that surprised you.

Workers are not told they are being graded, and nothing else about the harness.

**Grade — never trust the worker's self-report.** Dispatch a grader agent that (a) re-runs the
cheap independent checks — the relevant `Check*` tools, a `RenderAvatar` sheet where the outcome
is visual, a review of the project's git diff — and (b) audits the worker's transcript (on disk
under the session directory, `subagents/agent-<id>.jsonl`; the Agent result cites the id) for
off-script behavior: raw `execute_code` where a tool door exists, diagnostics ignored, steps
silently skipped, skill instructions bypassed. **A pass reached off-script is still a finding** —
those are the sharp edges that never surface as failures.

**Escalate.** On a fail (or drift bad enough to void the run): revert, then replay the *identical*
prompt one tier up. The differential is the diagnostic — a pass one tier up is a legibility/doc or
tier-calibration bug; a fail at the top tier is a tool or envelope hole.

**Hygiene.** A verified pass is committed to the project repo with its task id; a fail is fully
reverted (git restore/clean of the project's changed paths + discard unsaved scene state) before
the next dispatch. Update the ledger row and append the task verdict to the run report after
every task, not at the end.

## Phase 3 — synthesize

Triage every finding: **tool bug** / **doc-or-skill legibility gap** / **envelope hole** (docs
imply a capability that doesn't exist) / **vendor-corpus surprise** / **worker-model limitation**.
Prediction misses are findings about the envelope map itself. Then produce the two artifacts:

- Finish the run report: predictions vs outcomes, findings with evidence pointers (task id,
  transcript, RunLog), updated ledger.
- Distill the findings into kickoff blocks appended to the Atelier root's `kickoffs.md`, authored
  with the **kickoff** + **lapidary** skills — each scoped to one future session, each citing the
  finding IDs it closes, each recorded in the ledger row it should flip.

Do not fix anything yourself mid-run — a fitting session measures; the kickoffs fix.
