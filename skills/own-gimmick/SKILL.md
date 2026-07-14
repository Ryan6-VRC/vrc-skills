---
name: own-gimmick
description: Use when taking ownership of an existing gimmick module's behavior — keep part of a module ("just the tail part", "the glow system without the prop"), trim/clean a vendor gimmick kept whole, or cut a with/without variant; also whenever any task must edit a gimmick's animator or params (own first, then change), and when building "one like avatar Y's" starting FROM avatar Y's module. Not a new gimmick from intent, even one cloning a pattern (author-gimmick); not geometry (own-mergeable); not composing a module whole or wholly removing one while composing (compose-mergeable); not menu placement (author-menu).
---

# Own a gimmick

Make our own owned, editable copy of (part of) an existing gimmick module — animator, params,
menu, and the scene rig they drive — so the result composes like any module and contains
**nothing but what you chose to keep, still wired to everything it needs**. A gimmick module is
one system: its layers cross-reference, its params have multiple declaration sites, and its
menu is only the visible face — so a partial take is surgery with a defect checklist, never an
in-scene strip. Any edit to a vendor gimmick's controller/params enters here first (the
`own-material` pattern: materialize the owned copy, then change it).

**No operator to ask?** A gate you can't put to an operator (a dispatched worker, a headless run)
is expected, not a blocker: surface it to whoever dispatched you and wait. With no channel at all,
take the derivable defaults, flag every undecided call loudly at the top of your report, and never
silently mint a convention — folder or category placement especially.

## Scope — what this owns, and the boundary

In scope: extract a subsystem from a gimmick module, trim/de-cruft a module kept whole, fork a
variant, repair/change an installed gimmick's behavior. The meshes/rig it animates come along as
part of the system; a *geometry-led* extraction (clothing, hair — where the animator is incidental)
is `own-mergeable`, including its Phase 2C (repointing motion assets for a controller **kept
whole**) — any cut, trim, or param surgery on that controller is this skill.

- Composing the finished module, or removing a whole module during composition → `compose-mergeable`.
- Placing/redirecting the module's menu front on an avatar → `author-menu`.
- A genuinely new subsystem grafted in during surgery → that part is `author-gimmick`.

## Phase 0 — Graph, baseline, decide

- Graph the module before touching it: `ReportGimmick` (subtree topology), `ReportController`
  (layer/param digest — its live-reachable vs orphan split is the liveness read), `ReportPackage`
  (prefab + seam layout). **Liveness = inbound reference from the installed prefab/descriptor** —
  never name, folder tidiness, or clip-sharing; vendor packages carry convincing-looking dead
  controller copies and orphan sub-asset graveyards.
- **Capture the pre-cut baseline now**: one bake read (`verify.md` — play entry is the bake) of
  param count, true synced-bit total, and layer provenance. Phase 2's proof is a diff against
  this; without it the "only the intended cut moved" claim costs a git-stash round-trip and an
  extra minutes-long play entry.
- Operator gates: **which subsystem** (by observed behavior, mapped to the layers/params/rig that
  produce it); **trim-whole vs extract-part**; **seam target** (mixed MA-anchor/VRCF-behavior
  ruling: `gimmicks.md` §Packaging).

## Phase 1 — Surgery

Decompile to `CompileController` text and cut there — deterministic, reviewable, recompilable —
not in scene-YAML or the animator window. The happy path never writes a vendor asset: Decompile
reads without mutating, Compile emits fresh owned assets. **Expect refusals on vendor
controllers** (they are the population Decompile refuses: Trigger params, duplicate sibling
names, out-of-vocabulary constructs — `animator-schema.md` lists the classes). A refusal fix is
the one pre-owned controller write, and it **never lands on the vendor asset** (`LAYOUT.md`
read-only rule): duplicate the controller into the owned module folder, fix the duplicate
(rename the duplicate-named sibling, convert the Trigger), decompile the duplicate. A genuinely
out-of-vocabulary controller falls back to layer-level surgery via `CleanController` /
`OwnControllerClips` (both write only owned assets), with this same checklist run manually.

The cut checklist — every item is a defect class observed ≥2× across independent vendors; check
each, name findings:

1. **Dead-copy contamination** — carry only what the liveness graph reaches
   (`ReportController`'s live/orphan split); a copied "spare" resurrects later.
2. **Dual param-source drift** — post-cut, same-name params must agree across the loose
   `VRCExpressionParameters` asset, MA Parameters components, and the controller (diff
   `AgentInspector` reads of both against the param list). Vendor sync/saved defects found here
   — synced or saved *sensing* params — get **fixed, not preserved**.
3. **Stamped foreign params** — drivers and exclusion meshes cross-link layers: the kept layers
   may drive params belonging to layers you cut (`ReportController` decodes drivers typed);
   strip or re-derive them, or the module ships driving ghosts.
4. **Undeclared cross-module deps** — every param the kept layers *read* but nothing kept
   *writes* (grep the decompiled text): re-home the writer, stub with a config-default param
   (`gimmicks.md` §Packaging), or declare it a dependency of the module.
5. **Raw-string repath escapes** — enumerate SDK behaviours carrying string path/param fields
   (`VRCAnimatorPlayAudio` at minimum; `ReportController` surfaces behaviours) after any rename
   or re-root; they dodge repath tooling under an MA seam (VRCFury handles them).
6. **Menu strip ≠ param strip** — removing a control removes intent, not the machine: merged
   layers' default-active params re-enable whatever they animate at runtime, invisible to every
   edit-time gate. Anything you disabled must have its animating layer cut or gated, not just
   its menu entry.

## Phase 2 — Repackage & verify

- One self-contained module, menu front inside; seams and front shape per `gimmicks.md`
  §Packaging. Variants by **prefab composition + config-default params, never a controller
  fork** — a fork silently drifts from its mainline.
- **Own the clips with the controller** — `OwnControllerClips(recompiledController,
  <module folder>, scope=VendorOnly)`. The round-trip doesn't do this for you: a standalone
  `.anim` decompiles as a path `ref:` back to the same vendor asset, so recompile alone leaves
  the controller vendor-coupled — and `RepathClips` is owned-clips-only, so the seam repath a
  module usually needs is blocked until the fork. Leave vendor-coupled only clips you'd never
  change or repath (face-expression / gesture-set animations).
- Verify to `gimmicks.md` §Verification's bar, plus the two surgery-specific proofs:
  - **Baseline diff** — the Phase 0 bake vs a fresh bake: only the intended cut moved (params,
    bits, layers).
  - **Resurrect check** — in the emulator, drive every remaining control through its states and
    let the module sit through play entry (the default-active class fires bare at load): nothing
    removed comes back. Read through `verify.md` §Observation channels — removed params are
    checked against **post-build names** (VRCFury prefixes module params), and driver vs AAP
    values live in different channels (crossing them reads all-zero).
- Cross-base moves re-verify contact/PB placement in world space (`gimmicks.md`
  §Contact patterns) — bone rolls differ per base.

## Tools

- **`DecompileController` / `CompileController`** — the surgery medium (`animator.md`; authoring
  language `animator-schema.md`).
- **`ReportGimmick` / `ReportController` / `ReportPackage`** — the Phase 0 graph; liveness,
  typed drivers/behaviours, seam layout.
- **`AgentInspector`** — MA Parameters + loose expression-params reads for the drift diff.
- **`CleanController` / `OwnControllerClips` / `RepathClips`** — the no-decompile fallback layer
  and clip ownership (`animator.md`).
- **`CheckAnimator` (basis=auto) / `Check*`** — post-surgery lint; **av3emulator** — the
  resurrect check (`verify.md`).
