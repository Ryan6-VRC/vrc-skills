---
name: reproportion
description: Use when reshaping an avatar's or outfit's proportions — "make the arms longer", "reproportion this avatar", "fit this to my custom body", "match my real-life proportions". Covers authoring a proportion profile and applying it, including re-proportioning an already-built prefab in place; not the base-body owning itself (own-base) or owning/wearing a mergeable (own-mergeable, compose-mergeable).
---

# Reproportion an avatar

Reshape an avatar's (or outfit's) proportions and reconcile the Unity side. The `avatarprep`
proportions engine is the deterministic executor — load / validate / apply an edge or recipe, baked to
rest pose, state re-stamped. This skill owns the pathfinding, the gates, and the sequencing. Never
re-explain the engine API; open each tool to learn its entry point.

Every reproportion, whatever the timing, runs the same engine spine: identify the source state, resolve
the path to the target and validate its edge(s) against the live scene (missing bones/shapekeys surface
as named offenders **before** any mutation), then walk the path — object transform + per-bone scales +
shapekey values, baked, re-stamped. Authoring precedes it; Unity reconciliation follows.

## Author or load a profile

Either load an existing profile or author one. Authoring is the judgment-heavy part: applying is a
solved CLI call, but going from intent ("the arms feel short") to a *correct edge against this rig's
real bone names and orientations* is per-rig judgment.

Keep authoring **thin and model-driven** — no template, checklist, or Q&A script (over-specification
degrades a capable model, and operators want very different things). Imitate the example profiles for the
edge schema. Supply only the durable, non-introspectable judgment:

- Determine the rig's **forward axis from the bones** before choosing translate signs.
- `local` / `individual` for per-bone scales; `normal` / `median` for together-from-the-midline ops.
- **Author against the live armature's real bone names and re-run scene-validation until offenders
  clear.** This is the whole instruction — "author a validated edge JSON for what the user describes."
  How to converse (one surgical tweak vs. a from-scratch rebuild) is your discretion.

**Naming gate:** reject a bare-adjective target (`custom`, `base`, `final`) and name the rule — the
naming *policy* is canonical in `docs/LAYOUT.md`; don't restate it here.

**Where the profile lives:** the authored edge is co-located with the avatar it drives — `docs/LAYOUT.md`
owns the rule. Never drive an apply from the shared `vrc-blender-tools/profiles/`.

**If the operator is unsure what they want,** ask *why* once: some reproportion for visual preference,
others to match their real-life proportions so VRChat IK feels more immersive — the motivation tells you
which dimensions matter. One sentence, only if it helps.

## The operation: reproportion, then reconcile

There are not three modes — **one operation whose reconciliation tail scales with how much Unity state
already exists.** A fresh instance (no components yet) and a finished prefab run the same flow; only the
tail differs.

**Entry gate — freshness (already-built avatars).** The bind is frozen in the `.meta`; the freshness
assert FAILs when it disagrees with current geometry — i.e. when a prior reproportion's re-export skipped
the re-rig. **Run it first** on any built avatar you're about to reproportion or trust: a FAIL means the
rig is already stale → re-rig before anything else. It catches the skipped re-rig precisely because it
runs *before* the re-rig below, not after it (where it would trivially pass). Run it only on **bases**
— a mergeable imports Generic (`own-mergeable`), and the assert FAILs on any non-humanoid as bad
input, not staleness.

1. **Reproportion the Blender asset** (the spine) and re-export the FBX. If the owned viewpoint was
   ever hand-tuned, instantiate the current prefab into the scene **before this re-export** — it
   overwrites the gitignored geometry, and step 3's viewpoint fix needs that pre-reshape reference
   (unrecoverable after). **Author at world origin** —
   transform (0,0,0); never bake a position offset into the owned asset (reproportion pivots about
   origin; the coherence checks compare world positions).
2. **(Re)establish the humanoid rig.** Fresh avatar → the first rig-conform lands on already-scaled
   geometry. Already-built avatar → **re-run the humanoid-rig conformer — a hard invariant:** the bind
   is rebuilt from current geometry, and skipping it reintroduces folded hips. (The rig is
   reproportion-safe *because* the skeleton derives from our own model, not the vendor's.)
3. **Reconcile the rest, weighted by what exists** (these stale-state facts are canonical in `unity.md`):
   - **ViewPosition (eye height)** is a descriptor meters-vector that does **not** track baked geometry
     scale, and unlike component radii it is **not** sub-notice — a few-percent height change visibly
     floats the viewpoint off the eyes. **Recompute it on any height-changing reproportion** (both the
     fresh-handoff and in-place cases); verify in-game. Mechanism: the viewpoint-fix tool
     (`FixViewpoint` — recomputes from the reference's known-good viewpoint + both rigs' eyes/head)
     needs any `referenceRoot` whose viewpoint is true to its geometry. Instantiate
     the **untouched vendor prefab** (always on disk, original alignment) — unless the owned viewpoint was
     deliberately adjusted after owning, in which case the reference is the **pre-reshape instance
     captured at step 1**, before the re-export overwrote the FBX. Destroy the temp instance after; a
     missing/renamed eye bone FAILs named rather than guessing.
   - **Blendshape sanity-check.** After the round-trip, verify cross-mesh blendshape coherence: a driven
     body morph must have its matching morph driven on **every** mesh that has one (incl. name-variant
     outfit morphs). Watch for prefab-persisted SMR weights that **unlinked/reset to 0 because a mesh was
     renamed or re-exported** — re-apply them.
   - **Component gate** (below).
   - Fresh avatar → steps 2–3 are just the normal owning rig + descriptor work on scaled geometry;
     the component tail is empty.

**Component risk model — conclusions, not action by default.** avatarprep bakes scale into the rest
pose, so after baking a bone's runtime `localScale` is back to 1 but its head/tail moved. Components on
bones follow **positionally** (remapped by path), but their **absolute dimensions** — physbone /
collider / contact radii, in meters — do **not** track a rescale; that drift is **linear in the
proportion magnitude** and below notice at typical small reproportions. Helper constraint targets
**self-correct** through hierarchy inheritance (a helper rides the accumulated parent deltas, landing
most of the way on its own). Helpers *in the Blender armature* are moved by the edge-walk + bake on
re-export — only **Unity-only helpers** (added after the round-trip) never see the bake and stay
exposed.

**Two-signal gate:** wave the common case through with an informational note. At **large magnitude**,
surface the meter-scale component drift (physbone / collider / contact radii) for operator review — it
scales with magnitude even without helpers. **Hard-stop** for verification only at the narrow intersection
of large magnitude **and Unity-only constraint helpers**, where accuracy actually matters and
self-correction can't be eyeballed. Magnitude compounds across a recipe — accumulate it over the edges
walked, not off a single edge. (Don't hardcode a threshold; calibrate from verification.)

## Realizing shapekeys — two approaches

**What a profile's morphs are (the contract).** A profile drives *only* universal proportion-compatibility
shape-keys — anti-clip morphs (body/breast size, proportion) whose whole purpose is that **the base and
every composed mergeable hold the morph at one shared value**, a mesh's name-variant included
(`Breasts_big` ≡ `Dress_Breasts_big`). Uniform-across-the-compatible-set is the definition, not a goal to
hit: the *same* morph at *different* values across an asset is malformed, not a case to accommodate — the
sole escape hatch is the negative/reverse substitution below (a mesh carrying neither the morph nor its
variant, but carrying the opposite). So an asset's baked state collapses to **one value per morph**, and coherence is a checkable
invariant rather than a per-mesh judgement.

A profile defines *recommended values*; realizing them is a separate choice made at apply/finalize time,
not stored in the profile. Surface the choice rather than silently picking.

**Approach 1 — iterate (set-as-default).** The value can be realized on **either side of the round-trip**:
a Blender shape-key *value* crosses the FBX as the blendshape's import weight (see `blender.md`), or set
and persist the SkinnedMeshRenderer blendshape weight Unity-side (0–1 in Blender → Unity 0–100). Either
way it must land on **every mesh that carries a corresponding morph, including outfit pieces whose morph
is name-variant** (e.g. `Bra_Breasts_big` ↔ `Breasts_big`) — or the body morphs while the outfit stays
flat and clips through. Unity-side prefab weights **unlink (reset to 0) on mesh rename/re-export**
(`unity.md`) — re-verify after any round-trip. Non-lossy and reversible — good while iterating. **Durable only if no FX / gesture / expression
layer already drives that morph** — check for an existing animation curve on the blendshape first. If one
exists, neither realization is clean until you reconcile that curve (see Approach 2's FX note).

**Approach 2 — finalize (normal-preserving bake, preferred).** The bake tool folds the morph delta into
Basis and **leaves the original morph behind** (reversible/extensible — keep it, don't "simplify");
sibling morph effects are preserved (Basis-drag mechanics — see `blender.md`). It then recomputes normals
**except a protected vertex group (default `neck`)** and **never on the head mesh** (a hard rail;
profiles don't morph the head). Protection is an explicit vertex group, not a heuristic. **Ask the operator for the protected-group choice, default pre-selected** (~always taken). Cost:
**lossy at the mesh level** → the profile/recipe link is the recovery artifact, so record provenance.
**FX note:** because the morph block is *retained*, if an animation curve drives the morph you bake, you
must also **remove / retarget / zero that curve** — the delta now lives in Basis, so a live driver doubles
it in FX-active states.

**Missing shapekey:** substitute the inverse of a paired morph (e.g. a negative `Breasts_big` for an
absent `Breasts_flat`) **with operator approval**, via the skip/override machinery — never a silent fail.

## Reproportion into a twin (copy)

The default reproportion is **in place** — re-export the FBX under the existing prefab and reconcile. To
keep the original and produce a proportioned **variant**, build a twin: reproportion the `.blend`,
re-export, and run `own-base` Phase 3 mechanics against the finished original as the transplant source.
It is that same sequence on reproportioned geometry — don't restate it; the deltas a finished-owned
source adds over a vendor one:

- **Same Editor.** Import the re-exported twin into the same Unity scene as the finished source — the
  transplant tools take live GameObject refs. (The source is a fully-assembled avatar, which looks like
  it breaks `nondestructive.md`'s copy-from-standalone rule; it doesn't — that caution is about
  mergeables' cached MA/VRCFury state, and this copies only VRC dynamics.)
- **Rig-conform is the mandatory re-rig.** Phase-3 step 1 *is* this skill's post-reshape re-rig (see
  "The operation") — one call; the finished source is the humanoid-mapping donor, the twin's own model
  supplies the skeleton. Don't run it twice.
- **Dynamics: force the holders.** A finished avatar parks its dynamics on holder GOs, so those hosts flag
  `[holder]` on the bare twin (colliders/contacts whose holder sits under a surviving bone auto-recreate
  instead — see `unity.md`). Force the `[holder]`-classified hosts (per `unity.md`) to scaffold the grouping
  back, and **skip the relocate step** — the scaffold already rebuilt it. Completeness check, split across
  the two runs (the re-run can't show scaffold — the holders exist by then): on the **real forced run's**
  log, `scaffold` equals the number of forced `[holder]` hosts; then a **re-run `whatIf`** shows zero
  `[holder]` flagged-missing left (the former set now plans present-skip), confirming idempotence.
- **Component-risk gate applies.** The copied physbone/collider/contact radii are meters and don't track
  the reshape — run this skill's component gate (see "The operation") over the transplanted dynamics; the
  transplant reproduces radii verbatim, so it isn't optional here.
- **Global systems (VRCFury/MA/NDMF) aren't transplanted** — same deferred boundary as `own-base`.
- **Tail:** a fresh blueprint ID (a co-uploadable variant needs its own; the descriptor transplant mints
  one), and ViewPosition via the FixViewpoint step above — the `referenceRoot` is the finished source,
  already in-scene as the transplant source (no temp instance needed).

## Outfit-fit

A mergeable has **no edge of its own** — fit it by applying the **target base's** edge/recipe to the
mergeable's armature (the same spine, `pivot="origin"` so body and mergeable co-scale about the shared
origin), gating on **referenced-bone presence + rest-match** (not whole-armature identity, which
false-fails legitimate subset/superset mergeables) and reporting name-level divergence as a yellow flag,
not a block. This is the reshape half of `own-mergeable`, which owns the extraction, prune ordering, and seam
authoring around it, and routes the wear/merge to `compose-mergeable`. A later reshape of an
**already-owned** mergeable re-enters here directly: swap the `.blend`'s appended base reference for the
new target, apply the new edge/recipe, re-export armature-scoped — `own-mergeable`'s extraction/prune/seam
apparatus is first-owning work, not repeated. A **cross-base** reshape saves into the **new target base's
bucket** (`Blender/Outfits/<NewBase>/<Outfit>/`) — it never overwrites the original base's `.blend`; one
outfit fitted to two bases is two buckets (the owned-outfit filing rule).

Reconciling a base edge onto a mergeable needs adjustments the base itself never hits. The source guard
is not one of them: a freshly-imported mergeable is **base-absent**, and the guard exact-matches both
axes now, so absent is a hard **offender**, not an assumed pass. The mergeable must be **`stamp_base`'d
to its target base first** — `own-mergeable` does this right after import, before this reshape:
- **Skip base-only morphs.** The base's edge carries morphs the mergeable lacks (`Bra_Breasts_small`);
  an absent shape-key is a hard offender. Skip each with the shape-key override (`NAME=null`).
- **Propagate name-variant morphs.** The edge drives a body morph by exact name (`Breasts_small`); a
  mergeable mesh's variant (`Dress_Breasts_small`) won't match — drive each variant to the same value.
- **Opposite-morph substitution.** If a mesh lacks the driven morph *and* its name-variant but carries
  the **opposite** (no `Breasts_small`, but a `Breasts_big`), bake a **negative** of the opposite to
  approximate it — Unity has no negative live weights, so this must bake into the mesh. The two morphs
  aren't linearly related, so the ratio isn't derivable: **ask the operator to eyeball the exact value.**
  This is a **fit-time coherence bake** — the mesh now matches the target at its own geometry, so it is
  terminal and needs **no compose-side top-up**; the *negative* baked cumulative is the signal to
  `compose-mergeable` that it's a fit-time proxy (flag-only, not a base `Breasts_big` obligation).

**Cross-base via an explicit equivalency profile.** plum, chiffon, and chocolat are **distinct bases**,
not one shared body — what bridges them is an explicit `profiles/*.json` **equivalency edge**: a
**no-op** (identity, shared-mesh bases like chiffon↔chocolat) or a **pure-scale** (e.g. plum↔chiffon).
A base-changing equivalency profile is a valid, trusted edge kind — authored on human judgment, same
trust as any profile, first-class rather than a hack. When the outfit's native base differs from the
target, chain the equivalency edge *before* the reproportion edge, same as any recipe with no direct
edge. Author it like any edge: `unproportioned` origin state, explicit `source_base`/`target_base`. Only
a genuinely **non-topo** different base — one no scale/bone-op/shapekey transform can bridge — is a
**refit** (MochiFitter — not yet integrated; roadmap in `docs/mochifitter.md`), not this.

## Tools

Reuse; this skill only sequences. Open each to learn its exact entry point, and refer to it by role.

- **`avatarprep` proportions engine + CLIs** — load / validate-profile / apply profile + recipe.
- **Humanoid-rig conformer** (avatar-tools package) — rebuilds the bind from current geometry; re-run it
  after every reproportion.
- **Freshness assert** (avatar-tools package) — stored-bind vs. current-geometry guard, PASS/FAIL + named
  offender, run as an entry guard.
- **Normal-preserving shapekey bake** (`avatarprep` core) — Approach 2's executor.
