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

## Parameters and venue

At launch: a **lane**, a **task budget** (default ~10), and the Unity project the session was
started in. Two sessions may run concurrently only on **different lanes in different projects** —
and even then they share state: edit only your own lane's rows in `LEDGER.md` and re-read it
before each write, and treat physical singletons (Blender, each Editor) as claimed per-lane by
operator coordination rather than grabbed on sight.

- **geometry** — import-vendor-asset, own-base, own-mergeable, compose-mergeable,
  map-outfit-shapes, reproportion.
- **behavior** — controller round-trips (`DecompileController`/`CompileController`), gimmick and
  menu authoring, emulator verification per `verify.md`. Needs vendor assets already **imported**,
  not composed: a shipped vendor FX is itself a round-trip/rebuild target, and a simple compose
  done as the task's setup is a test in its own right. When the project starts empty — the normal
  case under two-lane concurrency, since geometry claims the populated project — run the
  corpus-building imports as graded setup tasks in their own right, not a silent pre-step.

The vendor library root comes from `CLAUDE.local.md` (machine-local). It is **read-only** — a
worker writing to it is an automatic grade-fail regardless of task outcome.

## The assay record

Everything durable lives in the Atelier root's `docs/assay/` (gitignored — create the directory
and seed an empty ledger if missing; being untracked, it needs no worktree to write):

- `LEDGER.md` — cross-run state. One row per **capability claim**, keyed
  `arc | claim | asset-class | lane` — asset *class*, never a specific file: the class is what
  passes or fails. Status vocabulary: `untested`; `blocked` (a precondition the claim needs is
  absent — pattern library unseeded, fixture missing — so it can't be tested yet, distinct from
  tested-and-failed); `pass@run-N-<lane>`; `fail@run-N-<lane> → <kickoff-id>`;
  `fixed-verified@run-N-<lane>`. The `-<lane>` suffix disambiguates concurrent lanes, which share a
  run number across different project files. Keep keys stable across runs; a later fitter must recognize
  its predecessor's rows.
- `run-N-<lane>.md` — this run's report: envelope map, queue with predictions, per-task verdicts,
  findings with IDs — including friction with *this skill's own instructions*, which a run tempers
  the same way it tempers the workshop. Append as you go — the report must survive an interrupted
  session.

## Phase 0 — map the envelope

Derive the claimed capability envelope from `TOOLS.md`, the lane's docs, and the lane's skill
descriptions: a checklist of task shapes a competent model should complete. Diff it against the
ledger's prior map — docs change as holes close, so the boundary moves. A **limit-pusher** is one
deliberate step past a named boundary, labeled as such in the queue; its failure confirms the map
rather than filing a bug.

Read each claim's *content*, not just its framing: before a claim enters the queue, verify the
preconditions it needs actually exist — the pattern library is seeded, the fixture is present, the
base is imported. A claim whose precondition is absent is `blocked`, not a testable frontier row;
queued against an empty resource it tests nothing.

## Phase 1 — build the queue

A fixed queue, written into the run report before any dispatch — no per-task asset picking. The
queue is fixed against *asset-picking drift*, not against operator knowledge: an operator prior
delivered before a dispatch lands as a recorded prediction revision, and an operator ruling
delivered mid-run lands as a finding — neither is off-limits the way re-choosing the next asset by
hand is. Priority order:

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

Each entry: asset, arc, the worker prompt, an assigned **tier**, a **prediction** (pass/fail, one
line of why), and — where the arc's skill contains an operator gate — the **gates you expect the
worker to hit and the answer you'll give in the operator's voice** (the operator-proxy script;
Phase 2 Dispatch resolves it). Tier is itself a calibration claim: Sonnet for asset shuffling and mechanical
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

Give the worker one more standing instruction: **stop and ask on any operator gate** rather than
guessing. Both read as ordinary operator requests — the worker is still told nothing about being
graded, nor anything else about the harness.

**Operator-proxy.** The lane's skills contain first-class *ask-the-operator* gates, but a
dispatched worker has no operator — so the fitter is the proxy. When the worker stops on a gate,
answer in the operator's voice via agent-resume: from the queue's pre-authored script if the gate
was expected, otherwise a sane default plus a log line. Settle one thing at launch: the gates **no tool or
same-tier grader can settle** — fit, clipping, the vision calls the grade step bars — either
escalate to a live operator, or in a **fully autonomous** run you answer them yourself; such a
call stands as the run's ground truth, not because it's verified but because nothing same-tier can
falsify it (so the grade step can't fail a worker who proceeded on it). Do **not** pre-resolve
gates inside the opening prompt — that makes the worker skip the gate's *other* checks and hides whether it would
have asked at all. The asking is itself under test: a skipped gate and a gate-question the docs
already answer are both findings (grade below). The general skills-side rule for a worker with no
ask channel is B2's in `kickoffs.md`; this is only the fitting-session harness half, and the two
must agree.

**Grade — never trust the worker's self-report.** The grader is a **disinterested, low-effort
auditor, not a second worker** — its edge is freedom from the worker's sunk cost ("I succeeded"),
not more compute. It **re-runs only the cheap objective checks and reads the transcript; it does
not re-execute the worker's expensive work** (a 100k-token play-mode battery, a long bake). The
failure modes here aren't fabrication — the worker doesn't lie about having entered play mode —
but skipped steps, off-script shortcuts, and rationalized judgment calls, which a transcript read
plus a cheap spot-check catch. So it (a) re-derives the cheap signals — the relevant `Check*`
doors, a git diff, a spot-checked delta (per-bone rest-pose spread, param counts) — and (b) audits
the transcript for off-script behavior: raw `execute_code` where a tool door exists, diagnostics
ignored, steps silently skipped, skill instructions bypassed, an operator gate skipped (or asked
when the docs already answer it). **A pass reached off-script is still a finding** — the sharp
edges that never surface as failures. Same-tier grading catches a rationalized error only where
the truth is cheaply re-derivable, and cannot cross a blind spot both models share; so it **never renders a judgment call** — a
load-bearing judgment that isn't mechanically settleable belongs to the operator or a genuinely
different model class, never a same-tier grader.

Two hard rules on the evidence:

- **Vision is not a fit gate.** A single `RenderAvatar` sheet read by a model is inadmissible as a
  pass/fail verdict — models rationalize even a gross misfit, or a wholly absent body, into
  "looks fine", and higher tiers only wrap the miss in more confidence. When a
  quantified signal and an image read disagree, the *number* wins. A sheet serves the operator's
  eye and the audit trail; a *differential* before/after pair around one discrete change (toggle,
  blendshape) is a readable effect check and stays admissible. Every other visual verdict is
  unverified narrative.
- **Point graders at the real transcript.** The Agent result's `tasks/<id>.output` file can be a
  0-byte stub; the worker transcript lives at `<session-dir>/subagents/agent-<id>.jsonl` (the Agent
  result cites the id). Hand the grader that path — both if you like, `subagents/` first.

**Escalate.** On a fail (or drift bad enough to void the run): revert, then replay the *identical*
prompt one tier up. The differential is the diagnostic — a pass one tier up is a legibility/doc or
tier-calibration bug; a fail at the top tier is a tool or envelope hole.

**Hygiene.** A verified pass is committed to the project repo with its task id; a fail is fully
reverted (git restore/clean of the project's changed paths + discard unsaved scene state) before
the next dispatch. Two traps even a read-only task springs: Unity inspection flips the scene's
`isDirty` with no on-disk change — clear the phantom dirt between tasks (ClearSceneDirtiness
reflection, `unity-scene-revert-via-mcp`) so it can't bake into a later save or muddy the next
grader's "did the worker mutate?" read; and inspection still leaves committable residue (tracked
`Assets/Agent/Snapshots/`), so commit or clean it between dispatches to hand the next grader a
clean `git status`. Update the ledger row and append the task verdict to the run report after
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

Do not fix anything yourself mid-run — a fitting session measures; the kickoffs fix. The one
exception is operator-sanctioned: a run-*stopping* tool bug the operator explicitly rules on may
be fixed mid-run (its own worktree, a normal PR), recorded as a run-report addendum — and even
then the ledger row flips only on verified evidence once the fix lands, never on the fix alone.
