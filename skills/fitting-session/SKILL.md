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

Coverage means **breadth**, not a single success. A tool that passed on one outfit breaks on the
next — a different rig, blendshape set, or material layout — or when that outfit is stacked with a
second and a hair. Two misses defeat the exercise equally: proving a capability once and moving on,
and building one avatar deep while the corpus stays untouched. Quantity is a quality of its own.

## Parameters and venue

At launch: a **task budget** (default ~10 *dispatches* — a batch is one dispatch no matter how
many assets it carries, so ~10 dispatches should exercise far more than 10 assets) and the Unity
project the session was started in. The whole envelope is in scope every run — geometry, behavior,
and the handoffs between them; an operator-suggested focus in the prompt weights the sample,
nothing more. Two sessions may run concurrently only in **different projects** — and even then
they share state: re-read `LEDGER.md` before each write and edit only rows your own run touched,
and treat physical singletons (Blender, each Editor) as claimed by operator coordination rather
than grabbed on sight.

Behavior arcs (controller round-trips, gimmick and menu authoring, emulator verification per
`verify.md`) need vendor assets already **imported**, not composed: a shipped vendor FX is itself
a round-trip/rebuild target, and a simple compose done as the task's setup is a test in its own
right. When the project starts empty, run the corpus-building imports as graded setup tasks in
their own right, not a silent pre-step.

The vendor library root comes from `CLAUDE.local.md` (machine-local). It is **read-only** — a
worker writing to it is an automatic grade-fail regardless of task outcome. Search and probe it
freely otherwise, workers on the same terms.

## The assay record

Everything durable lives in the Atelier root's `docs/assay/` (gitignored — create the directory
and seed an empty ledger if missing; being untracked, it needs no worktree to write):

- `LEDGER.md` — cross-run state. It opens with a **run registry** — one line per run,
  `run-N — <project> — <date>`; claim your N by appending your line before any dispatch, so
  concurrent sessions never share a number and a bare `run-N` in any status routes to its report
  and project. A run may instead **adopt an interrupted predecessor** — reuse its N and report
  rather than claim a fresh one, note the adoption, and resample its unexecuted frontier under
  Phase 1's fresh-sample rule. Below that, one row per **capability claim**, keyed
  `arc | claim | asset-class`. The class is the key; what a row *records* depends on the
  claim's **variance** — whether breadth across the corpus can change the answer. Low-variance
  claims (most deep-behavior arcs) still pass or fail as a class and close: `pass@run-N`.
  High-variance claims accumulate a **coverage profile** and never terminally close:
  `covering@run-N — covered N assets / V vendors / topologies:simple|mixed; fragile-on <classes>`.
  Variance, not execution speed, decides this: a heavy single-deep arc like own-base is still
  high-variance and carries a profile. A `fragile-on <class>` entry is regression-verified next run
  exactly as a `fail` is — it enters Phase 1 priority 1 (regression), not just priority 3's
  thin-coverage resample. Rest of
  the vocabulary: `untested`; `blocked` (a precondition the claim needs is absent — pattern library
  unseeded, fixture missing — so it can't be tested yet, distinct from tested-and-failed);
  `fail@run-N → <kickoff-id>`; `fixed-verified@run-N`. Keep keys
  stable across runs; a later fitter must recognize its predecessor's rows.
- `run-N.md` — this run's report: envelope map, queue with predictions, per-task verdicts,
  findings with IDs — including friction with *this skill's own instructions*, which a run tempers
  the same way it tempers the workshop. Append as you go — the report must survive an interrupted
  session.

## Phase 0 — map the envelope

Derive the claimed capability envelope from `TOOLS.md`, the docs, and the skill
descriptions: a checklist of task shapes a competent model should complete. Do not carve the
envelope into a taxonomy and sample per bucket — classifying every tool and skill invites
coverage gaps and double-testing; the checklist is flat, and cross-arc handoffs (a deep
multi-arc build on one avatar) are claims in their own right. Diff it against the
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
delivered mid-run lands as a finding. Priority order:

1. **Regression-verify prior fails** — every `fail` ledger row, and every `fragile-on` class carried
   by a `covering@` row. First check whether
   a fix plausibly landed (its kickoff's status; `git log` of the tool repos since the fail was
   recorded), but test regardless — the ledger distinguishes "fix never attempted" from "fix
   landed but insufficient", and they produce different kickoffs.
2. **Anti-backslide spot-checks** — one or two prior passes, chosen because their tool surface
   *churned* since the pass (`git log` of vrc-unity-tools / vrc-blender-tools / vrc-skills
   against the pass date). Retesting an untouched code path is worthless; backslides live
   downstream of churn.
3. **Frontier** — untested rows, new asset classes, and **coverage rows still thin or skewed** (few
   assets, one vendor, all simple topologies), drawn as a **fresh sample each run** so no two runs
   repeat a queue; stratified across vendor, asset type, and expected weirdness (the library's
   inventory doc helps), plus 2–3 limit-pushers.

**Execution speed is set by the arc.** Mechanical arcs (import, compose, repath) run as **batch**
dispatches — one worker, many assets, one FRICTION REPORT — and each batch must span multiple
vendors and topologies (the inventory doc stratifies it); a two-asset, single-vendor batch is
try-once-and-done in a batch costume. Heavy arcs (controller authoring, gimmicks, reconciles, and
the heavy geometry arcs — own-base, own-mergeable, reproportion) stay **single-deep**: one asset,
fully graded and escalated. Speed is orthogonal to ledger closure (set by variance, above).

**Combination tasks** are a frontier category of their own — the *interaction* between composed
pieces, where bone conflicts, param collisions, menu overflow, and material-slot clashes live,
invisible to any arc tested alone. Keep them real: a combination is **partial mix-and-match** (shoes
and pants from outfit A, shirt and necklace from B, onto a base), not stacked full outfits, and
bounded to **2–3 sources** of one type — the worker prompt names which slots come from which source,
the way an owner would ask. Queue a small set stratified across base, source pair, and slot split,
and rotate it across runs like any other coverage; its ledger home is the `compose` arc with a
`combination` asset-class.

Each entry: asset, arc, the worker prompt, an assigned **tier**, a `mutating | read-only` token, a
**prediction** (pass/fail, one line of why), and — where the arc's skill contains an operator gate —
the **gates you expect the worker to hit and the answer you'll give in the operator's voice** (the
operator-proxy script; Phase 2 Dispatch resolves it). Tier is itself a calibration claim: Sonnet for
mechanical arcs, Opus for complex behavior work, Fable only for frontier limit-pushers. Predictions —
outcome and tier — are what make the envelope map falsifiable: a miss in either direction is a
finding, including a task that needed a higher tier than assigned.

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

A task that produces a written artifact gets a drop-path **outside `docs/assay/`**: a worker who
can read the run reports there can absorb a prior verdict, contaminating the independent-grade
premise.

**Operator-proxy.** The workshop's skills contain first-class *ask-the-operator* gates, but a
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
ask channel is the canonical no-operator line each gated skill carries; this is only the
fitting-session harness half, and the two must agree.

**Grade — never trust the worker's self-report.** The grader is a **disinterested, low-effort
auditor, not a second worker** — its edge is freedom from the worker's sunk cost ("I succeeded"),
not more compute. It **re-runs only the cheap objective checks and reads the transcript; it does
not re-execute the worker's expensive work** (a 100k-token play-mode battery, a long bake). The
failure modes here aren't fabrication — the worker doesn't lie about having entered play mode —
but skipped steps, off-script shortcuts, and rationalized judgment calls. So it (a) re-derives the
cheap signals — the relevant `Check*` doors (`CheckSeam` mechanizes the compose-fit per-bone spread a
grader would otherwise eyeball), the `venue-integrity` change-list, a spot-checked delta (param
counts) — and (b) audits the transcript for off-script behavior: raw `execute_code` where a tool door
exists, diagnostics ignored, steps silently skipped, skill instructions bypassed, an operator gate
skipped (or asked when the docs already answer it). **A pass reached off-script is still a finding** —
the sharp edges that never surface as failures. Read the change-list against the entry's token: on a
**mutating** task an empty list is the hollow-work tell, and a list of only `.meta`/scene-save
touches is churn *only* when the expected artifact is a new asset the `Check*` doors confirm
absent — a task whose deliverable is in-scene state legitimately shows just a scene save. On a
**read-only** task (a report written outside `Assets/`) an empty list confirms, not flags. Same-tier grading catches a
rationalized error only where the truth is cheaply re-derivable, and cannot cross a blind spot both
models share; so it **never renders a judgment call** — a
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

**Grading a batch is cheaper, not blinder.** Run the cheap objective door — the relevant `Check*`, a
`venue-integrity` change-list — on **every** item, never a sampled subset: sampling re-trusts the
worker's "the rest were fine", which the self-report rule forbids. A batch is one worker over many
assets returning once, so a single before/after snapshot — never one per item — yields a flat
change-list that can't attribute a touch per-asset when imports scatter into shared folders. What
batch grading drops is per-item *escalation*, not verification: when the door surfaces a chafing
asset, **promote it to a single-deep escalated re-run** (this run if budget allows, else a kickoff)
— that recovers the per-asset resolution the flat list lost and the differential Phase 3 triage
needs; a chafing item left un-escalated has no route to a triage class.

**Escalate.** On a fail (or drift bad enough to void the run): replay the *identical* prompt one tier
up. The escalated worker is blind — so re-establish the cheap precursor the task needs (re-import the
base, or clear the mess and have it rebuild the precursor first), but **never** re-run the prior
worker's expensive work to fake a pristine start; where even the cheap reset isn't feasible, the run
report notes the dirty-substrate confound. The differential is the diagnostic — a pass one tier up is
a legibility/doc or tier-calibration bug; a fail at the top tier is a tool or envelope hole.

**Hygiene.** The venue is disposable and cumulative — nothing is rolled back. Grade an item by
snapshotting the venue before it and diffing after with `venue-integrity.ps1`: the change-list proves
a file was *touched*, while the `Check*` doors judge whether that touch was the right *substance*.
Update the ledger row and append the task verdict to the run report after every task, not at the end.

## Phase 3 — synthesize

Triage every finding: **tool bug** / **doc-or-skill legibility gap** / **envelope hole** (docs
imply a capability that doesn't exist) / **vendor-corpus surprise** / **worker-model limitation**.
Prediction misses are findings about the envelope map itself.

Two filters gate a finding into a kickoff. **The bar:** a worker who complains but succeeds is no
automatic fix — a fix earns a kickoff only if it lands in tool output (zero ongoing context cost)
or ~one line in a doc the task already reads; otherwise drop it, don't document it. **Softness:**
a fitter closing a long run has spent its research budget, so write each finding as a *hypothesis*
that hands the design space to the implementing agent — which has the room to research what you
couldn't — not a decision to relitigate.

Then produce three artifacts:

- Finish the run report: predictions vs outcomes, updated ledger, and each finding with its evidence
  pointers — task id, RunLog, and a **backing anchor** (a distinctive verbatim phrase from the transcript
  that recorded it) so the row routes a later agent to the moment, not a re-description it would re-derive.
- Distill the findings into kickoff blocks appended to the Atelier root's `kickoffs.md`, authored
  with the **kickoff** + **lapidary** skills — each scoped to one future session, each citing the
  finding IDs it closes, each recorded in the ledger row it should flip.
- Leave the run's surviving avatars standing side by side in **one saved review scene**, so the
  operator's end-of-run check is a single eyeball pass over everything the session built.
  Vision-illegible passes (a controller graph, a shape map) get no stand-in; only avatars that
  should *look* right belong there. Pair the scene with an **operator handoff**: per surviving
  avatar, a line on what was done and what to check or test and how ("enter play mode and drive
  the Hair Color radial").

Do not fix anything yourself mid-run — a fitting session measures; the kickoffs fix. The one
exception is operator-sanctioned: a run-*stopping* tool bug the operator explicitly rules on may
be fixed mid-run (its own worktree, a normal PR), recorded as a run-report addendum — and even
then the ledger row flips only on verified evidence once the fix lands, never on the fix alone.
