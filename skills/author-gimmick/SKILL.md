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

> **Provisional — extraction pending.** No end-to-end authoring session has run under this
> skill yet; the sequence below is corpus-validated (every deep-read vendor/Remy system fits
> it) but the step internals are study, not transcript. The G5 builds (contact-tracker,
> grabprop, then a raycast world-place prop) are the designated extraction beds: a bed session
> follows this skeleton, **logs every deviation it makes as it works**, and afterward kicks off
> `skill-temper` on this skill with the transcript. Weight the skeleton accordingly until this
> block is gone.

**No operator to ask?** A gate you can't put to an operator (a dispatched worker, a headless run)
is expected, not a blocker: surface it to whoever dispatched you and wait. With no channel at all,
take the derivable defaults, flag every undecided call loudly at the top of your report, and never
silently mint a convention — folder or category placement especially.

## The sequence

Order is load-bearing — the corpus's failure mode is never mechanism, always sync hygiene
discovered too late.

### 1. Transport & bit design

Against `gimmicks.md` §Choosing a transport + §First principles: what state exists, who must
agree on it, which transport carries each edge, what it costs in synced bits. Only intent costs
bits; sensing params are never synced, saved, or menu-exposed. Label every empirical constant
(dwell, pulse phase, threshold, λ) as empirical **at design time** — the verify budget
concentrates on exactly these, and feel-tunable ones additionally mark what the wear-test owns.
This design is the operator's first gate: the state table and bit cost, before anything is built.

### 2. Mode machine

`gimmicks.md` §State machine patterns and §Packaging own the shapes (banded-int fusion when
states are exclusive, off-is-reset, deterministic resume from param values alone). Author as
`CompileController` YAML from the start (`animator-schema.md`) — the controller half's source of
truth is the document, compiled in, never hand-built graphs decompiled out.

### 3. Physical affordances

Affordances (grab, touch, gesture-near-contact) are the primary interface — but **never invent
affordance geometry from scratch**: clone a proven shape with its constants, sources in order of
availability — a `vrc-patterns` module if one exists → a routed ancestry asset
(`references/README.md`) → a measured example from a Remy project or the mechanisms survey.
Cross-base cloning verifies placement in world space (`gimmicks.md` §Contact patterns).
Two operator gates live here:

- **Affordance selection** — present 2–3 candidates *with their precedent*; what's intuitive in
  VR is operator knowledge, not derivable.
- **Feel vs firing** — firing correctness (does it trigger, latch, release) is emulator work,
  yours; *feel* (size generosity, dwell comfort, reachability on a real body) is a named
  **headset wear-test handoff** over the feel-labeled constants — `verify.md`'s "name what needs
  two clients" discipline, extended to what needs a headset.

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
**batch emulator work into few sessions**, concentrated on the labeled empirical constants; name
the in-game residue (network timing, IK, culling, feel) explicitly as handoff.

## Tools

- **`CompileController` / `DecompileController`** — the controller medium (`animator.md`,
  `animator-schema.md`).
- **Unity MCP `execute_code`** — scene-half assembly, scripted and re-runnable.
- **`ReportGimmick` / `ReportController` / `CheckAnimator` / `Check*`** — structure reads + lint.
- **av3emulator** — the drive/observe venue (`verify.md` §Observation channels).
- **`RenderAvatar`** — operator-facing stills of driven states.
