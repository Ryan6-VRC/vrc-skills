---
name: author-gimmick
description: Use when building a NEW gimmick from intent — "make it react when someone touches the tail", "a prop I can drop in the world", "a pettable head", "sync this state to everyone" — anything wiring contacts, physbone grabs, constraints, or synced params into interactive behavior, including a new gimmick cloned from a pattern or another avatar's idea. Not starting from an existing module you'll keep — cutting/trimming one is own-gimmick; not composing a ready-made gimmick module (compose-mergeable); not menu controls alone (author-menu).
---

# Author a gimmick

Design and build a new gimmick as one self-contained module: transport design → mode machine →
affordances → menu front, authored as recompilable text, verified up the ladder. The *taxonomy*
lives elsewhere and is the required reading — `docs/gimmicks.md` (the pattern vocabulary and
design rules this skill sequences), `docs/runtime.md` (the physics), `vrc-patterns` (grown
module/pattern entries), the mechanisms survey for worked examples. This skill owns the process
and its gates only.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## The sequence

**Clone or intent?** Settle this first — it changes how every step below runs. **Either way, scan
the `vrc-patterns` catalog before building.** A full match makes it a clone; short of that,
adjacent entries still carry precedent to lift — how a similar mechanism organizes its states,
names its params, shapes its contacts — the narrow convention that never rose into `gimmicks.md`.
A from-intent build starts from what the scan surfaces, not from scratch. Full-clone precedent,
when it exists, comes in this order of authority: a `vrc-patterns` module → a routed ancestry
asset (`references/README.md`) → a measured example off a working avatar or the mechanisms survey.
**Cloning a known mechanism** (the common case): confirm it against that source *before* step 1 —
the ported state table, bit cost, and affordance constants are what you carry, so the steps below
ratify the port and the operator's first gate signs off the ported design, not a from-scratch one.
**From intent:** run the steps as written. Affordance geometry is cloned from the same source
order either way, never invented (step 3).

Order is load-bearing — the corpus's failure mode is never mechanism, always sync hygiene
discovered too late.

### 1. Transport & bit design

Against `gimmicks.md` §Choosing a transport + §First principles: what state exists, who must
agree on it, which transport carries each edge, what it costs in synced bits. Only intent costs
bits; sensing params are never synced, saved, or menu-exposed. Flag the empirical constants
(dwell, pulse phase, threshold, λ) at design time so verify knows where to look — but the flag is
a starting guess, not a sweep contract: which constants the emulator can actually settle, and
which are feel-owned and can't be discriminated in it at all, often only resolves once the
mechanism is understood; a feel-owned constant ships at its cloned value (the 90% rule) for the
wear-test, never swept. This design is the operator's first gate: the state table and bit cost,
before anything is built.

### 2. Mode machine

`gimmicks.md` §State machine patterns and §Packaging own the shapes (banded-int fusion when
states are exclusive, off-is-reset, deterministic resume from param values alone). Author as
`CompileController` YAML from the start (`animator-schema.md`) — the controller half's source of
truth is the document, compiled in, never hand-built graphs decompiled out. A clip whose binding
the compiler refuses (`animator-schema.md` §clips) is hand-authored as a human-owned `.anim`, not
forced inline or into a hand-built graph — the first-class fork, framed in `animator.md`.

### 3. Physical affordances

Affordances (grab, touch, gesture-near-contact) are the primary interface — but **never invent
affordance geometry from scratch**: clone a proven shape with its constants (the source order
above). Cross-base cloning verifies placement in world space (`gimmicks.md` §Contact patterns).
Two operator gates live here:

- **Affordance selection** — present 2–3 candidates *with their precedent*; what's intuitive in
  VR is operator knowledge, not derivable.
- **Feel vs firing** — firing correctness (does it trigger, latch, release) is emulator work,
  yours; *feel* (size generosity, dwell comfort, reachability on a real body) is a named
  **headset wear-test handoff** over the constants that prove feel-owned, whenever that resolves —
  `verify.md`'s "name what needs two clients" discipline, extended to what needs a headset.

The **scene half** (receivers, constraint rigs, PB chains, freeze roots) is assembled by
`execute_code` or a checked-in editor script and captured as the committed prefab — the prefab
is the artifact, like `built/`; nothing hand-placed and unrecorded.

### 4. Menu front

Last, per `gimmicks.md` §Packaging: enable/options/failsafe, menu-parallel-path for every
affordance intent, frontless as a valid outcome. The front ships **inside** the module; placing
or redirecting it on an avatar is `author-menu`.

### 5. Package & verify

One self-contained module (`gimmicks.md` §Packaging: mixed MA-anchor/VRCF-behavior seam,
config-default params for variant knobs). Verify to `gimmicks.md` §Verification via `verify.md`:
compile + `Check*` are cheap and continuous; play-mode entry costs minutes on a heavy avatar, so
**batch emulator work into few sessions** on the firing questions the emulator can settle. A
question can change identity as you measure — a "settle time" that turns out to be low-FPS sample
delivery — so reframe it rather than forcing the original sweep. Name the in-game residue
(network timing, IK, culling, feel) explicitly as handoff.

## Tools

- **`CompileController` / `DecompileController`** — the controller medium (`animator.md`,
  `animator-schema.md`).
- **Unity MCP `execute_code`** — scene-half assembly, scripted and re-runnable.
- **`ReportGimmick` / `ReportController` / `CheckAnimator` / `Check*`** — structure reads + lint.
- **av3emulator** — the drive/observe venue (`verify.md` §Observation channels).
- **`RenderAvatar`** — operator-facing stills of driven states.
