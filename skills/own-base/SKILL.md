---
name: own-base
description: Use when making our own owned, editable copy of a vendor VRChat avatar's base body — "own this avatar", "build our own copy of the base body", "turn this vendor avatar into one of ours". Covers the base body + underwear into a clean, uploadable starting prefab; not outfits/hair/accessories or MA/VRCF copy.
---

# Own a vendor avatar base

Build the operator's own normalized avatar from a vendor package: a clean, uploadable base body (+ underwear)
with our naming, our renderer/descriptor conventions, and a fresh blueprint ID. Vendor packages are messy and
each is different — the scripted tools handle the deterministic mechanics and emit PASS/FAIL diagnostics; this
skill holds the judgment, the gates, and the sequencing. Open each tool to learn its exact entry point; the
prose below only tells you which to reach for and when.

The flow is three phases: graph-and-decide, Blender normalize, Unity rebuild. Don't skip ahead — each phase's
gates feed the next.

**No operator to ask?** A gate you can't put to an operator (a dispatched worker, a headless run)
is expected, not a blocker: surface it to whoever dispatched you and wait. With no channel at all,
take the derivable defaults, flag every undecided call loudly at the top of your report, and never
silently mint a convention — folder or category placement especially.

## Scope — what this covers, and the boundary

In scope: owning the **base body + underwear** into a clean starting avatar. Stop there.

Deferred — if the package needs any of these, do the in-scope part and **surface the boundary to the operator**
rather than improvising:
- **Copying Modular Avatar / VRCFury / NDMF** systems off the base. That arc reuses the **same**
  CopyComponents / MoveComponents tools with MA/VRCFury/NDMF type-names (conservative tier — that reuse is
  the payoff), and `GraftHierarchy` pulls authoring/menu subtrees wholesale — but that orchestration is its
  own arc (the base's global systems, not a mergeable's own seam), not this one.
- **Outfit / hair / accessory owning** → `own-mergeable`.
- **Reproportioning** the clean base is a follow-on operation, not part of owning — hand off to the
  `reproportion` skill once the base is built.

## Phase 1 — Graph and decide

Run the **package-graph** tool on the vendor folder first. It is read-only and its report *is* the
verification — work from it, don't eyeball the prefabs. The one exception is its head/body call, which
the tool itself flags as a guess (`headGuess`/`bodyGuess`, a most-blendshapes heuristic): confirm those
two meshes before Phase 2's non-negotiable rename hangs on them. (Import health is `import-vendor-asset`'s job —
its `CheckPackage` PASS is this phase's precondition; re-run it if health isn't already known-good.) A
shared base-model family imported whole (e.g. Plum/Chiffon/Chocolat) is graphed whole, but the keep-set
and superset decision scope to the **one avatar being owned** — sibling avatars stay untouched vendor.

From the graph, establish: each FBX's mesh inventory, which mesh is the **head** vs the **body**, which FBX is
the **superset** of variations, which meshes are **optional** (a mesh that belongs to a vendor `_OFF`/toggle is
a removable part), the constraint count, and whether **MA / VRCFury / NDMF** are present on the base.

Then make these decisions and **surface them to the operator**:

- **Vendor FBX import settings that differ from our preferred ones** — raise them; do not silently "fix". The
  operator decides whether the vendor's setting is deliberate.
- **No single FBX is a superset** (variations split across files) — surface it, then build the superset by
  merging the relevant FBX armatures in Phase 2 (avatarprep `compare_armatures` + `merge_armatures`). Note which
  FBX is the merge base (the most complete) and which are merged in.
- **MA / VRCFury / NDMF present** — note that copying those systems is deferred; the owned base won't be
  functionally equivalent to the vendor until that later arc. Proceed with the base body only.

**Which body to own:** the keep-set is **every non-identical body mesh** — an owned base stays
outfit-agnostic, so keep all body/underwear variants and let the prefab's consumer disable the unwanted ones
per outfit. Prefer the **superset FBX**: build straight from it when it already holds the whole keep-set;
reach for the Phase-2 merge only when the keep-set is split across FBXs.

Imitate the operator's known-good bases when judging what "normalized" looks like (machine-local —
ask the operator for where they live).

## Phase 2 — Blender normalize (round-trip)

**Single superset FBX:** import it with the **avatarprep import** function.

**No single superset (Phase-1 merge case):** build the superset first, in place of that single import. Import the
N relevant FBX, then run **avatarprep `compare_armatures`** (base vs each merge-in, read-only) and **read its
report** before merging — it surfaces renames/restructures the union can't reconcile blindly. Supply
`rename_map` / `force` from what the report shows, then run **`merge_armatures`** to union them into one skeleton.
It FAILs loud rather than producing a doubled skeleton; resolve the named offender and re-run. Do this **before**
the observe → drop → rename → prune → export steps below — never after. The result is one armature named
`Armature`; the avatar's armature is **always** `Armature` (the merge enforces this — mergeables
deliberately differ with `Armature.<Name>`; the naming pair and its why: `docs/nondestructive.md`).

**Keep-rule for the merge:** a distinct body option is **not** a duplicate — keep it. Pre-delete only redundant
*identical* copies before merging, and **echo each deletion by name**. When unsure whether two bodies differ,
keep both.

**Observe and sanity-check before changing anything** — the import-observer reports the cheap "this one's off,
re-import" signal (counts, scale/height, pose, unparented meshes). Authoritative correctness comes from the
Unity round-trip in Phase 3; this is just a gut-check.

Normalize down to just the avatar:

- **Drop every clothing mesh**, keeping only the underwear/base. The graph's toggle membership (renderers a
  clip drives via `m_IsActive`, often the vendor's `_OFF` meshes) tells you which meshes are removable parts.
- **Rename so the head mesh is `Body` and the primary body mesh is `Body_Base`.** This is non-negotiable:
  third-party systems key off these two exact names. **Additional body options** (kept by the merge keep-rule)
  become `Body_Base_<Variant>` — only `Body` / `Body_Base` are load-bearing; the extras just need stable,
  distinct names.
- **Renaming a mesh breaks name-based matching** — two consequences. (1) The material-copy step matches
  renderers by name, so hand it the `{ourName → sourceName}` mapping for anything you renamed. (2) If you rename
  the **head** mesh, its facial-gesture clips almost certainly need to be copied and re-pathed to the new name.
  (Keeping the head as `Body` — when the vendor already uses it — avoids both.)
- **Author at world origin** — transform (0,0,0); never bake a position offset into the owned asset
  (reproportion pivots about origin; the coherence checks compare world positions).
- **`stamp_base` the armature with the base's own canonical identity** (e.g. `chocolat`, `shinano`,
  `plum`) so it's baked into the authored `.blend`. This identity is the prerequisite every later
  fit-test and compose gate resolves against — without it, no outfit for this base is checkable, and
  `reproportion`'s later apply (once the base is built) hard-offends on an absent base stamp.

After dropping meshes, run the **avatarprep prune** function to delete the now-orphaned zero-weight bone chains.
It keeps physbone tips, attachment parents, and ancestors of weighted bones, and preserves only depth-1
zero-weight leaves (over-pruning is unrecoverable post-export, so it errs toward keeping). It prunes aggressively by design:
weights alone can't distinguish dead clothing chains from a rare load-bearing helper chain (an intentionally
unweighted chain used as a constraint target). Don't second-guess it from weights — if it removes a load-bearing
bone, that surfaces in Phase 3 as a **flagged-missing host** (PASS, named) — `force` it (scaffold) or re-add
the transform in Blender and re-export.

Export back to Unity with the **avatarprep CATS-recipe export** (reuses the vendor materials rather than
re-embedding).

## Phase 3 — Unity rebuild

Build up from the **scene instance** of our freshly-exported FBX, in order, and convert to a prefab only at the
end. Each step below is one tool that emits a PASS/FAIL diagnostic and a RunLog under
`Assets/Agent/RunLogs/`.

**Treat the diagnostics as gates — but read what each count *means*.** A **FAIL** is always stop-and-investigate
(a vendor-source leak, an `AddComponent`/scaffold failure, an unresolved type), as is a **vendor-source leak** or
a **nulled reference on a component we actually copied** ("verify — may block build": a null VRCF `propBone` or
constraint source aborts the downstream build, it does not degrade). Read that tool's RunLog before continuing —
such counts usually mean a name/path mismatch (a rename the map missed, a `Body_Base`/`Body_base` case slip); fix
and re-run, or surface a structural one to the operator.

A **flagged-missing *host*** is **not** a gate — it is the expected subset case (PASS). The transplant tools list,
by name, every component whose host bone/GO was pruned out of our rig; you read that list and **decide**: `force`
it (scaffold the missing chain), re-prune in Blender and re-export, or accept the loss. Don't treat a nonzero
flagged-missing count as a stop signal.

First, apply our **standard FBX import settings** (Read/Write on; Normals = Import, blend-shape normals = None —
or match the vendor when the graph flagged a deliberate difference). **Do not assign materials at the
FBX-importer level** — that spawns junk local material copies; materials go on at the scene/prefab level.

Then, on the scene instance, in this order:

1. **Conform the humanoid rig** to the vendor's exact bone mapping (the **rig** tool). It builds a fresh
   humanoid from **our own model's** skeleton (the bind pose — never the vendor's, so it survives
   reproportioning) and applies the vendor's bone mapping + muscle settings (per-bone limits and the global
   muscle fields), fixing auto-mapper mistakes (e.g. Chest dropped, Jaw mapped to a hair bone). **Re-run
   this tool after any reproportion or re-export** — the stored bind does not self-update (see
   `unity.md`'s geometry-change reconcile).
2. **Assign vendor materials by mesh name** and **normalize** every renderer's bounds and anchor (the
   **materials** tool). Bounds are normalized to our floor — ensured ≥ the standard (center 0,0,0 /
   extents 1,1,1), grown never shrunk, **not copied** from the vendor (they get these wrong); the Anchor
   Override is repaired to Hips only when invalid, and a valid internal anchor is preserved. A fresh FBX
   whose bounds fit the standard normalizes as before; one already exceeding it is kept larger (flagged).
   Expect 0 null/default material slots. Note: the
   head→`Body` / body→`Body_Base` rename **unlinks** any prefab-persisted SMR blendshape weights (they
   reset to 0) — re-verify and re-apply any driven blendshape weights after the rename (see `unity.md`).
3. **Transplant the avatar descriptor** (the **descriptor** tool). It **gates first** on scale/orientation and
   face-blendshape parity, then remaps all scene references to our rig and installs a **fresh PipelineManager**.
   **Never reuse the vendor's blueprint ID.**
4. **Reproduce the dynamics** (the **CopyComponents** tool): copy the vendor's dynamics onto our rig **in
   place**, additively and idempotently (it never destroys; a re-run is a no-op by count parity). Drive it
   with a **list of component type-names**. For a faithful base-body reproduction list the closed VRC
   dynamics set **plus the Unity built-in constraint types your graph found** — VRC physbone / collider /
   contact / VRC-constraint go through the typed deep tier (dependency-follow, `Col_*` leaf-anchor
   recreate, hard/soft criticality); **Unity built-in `RotationConstraint`/`PositionConstraint`** and
   anything non-VRC (MA/VRCFury/NDMF on the outfit arc) go through the type-blind conservative tier
   (`CopySerialized` + generic ref remap, leave-missing-missing). A vendor's "constraints" are usually
   those built-ins, **not** `VRCConstraintBase` — which alone matches none of them — so name the
   built-in types explicitly. The **reach root** is
   `(vendorSource, ownedRoot)` — refs to objects under the vendor source rebind to our counterparts;
   out-of-reach refs (assets, other objects) are left for placement.

   **What-if first, then one real run.** Call with `whatIf:true`, read the full plan (copies, leaf
   recreates, scaffolds, flagged-missing hosts, hard-dep nulls); add any flagged-missing entries you want
   to keep to `force` (key = `vendorRelativePath :: ComponentType`) and/or adjust `typeNames`, re-run
   what-if until the plan is what you want, then execute **one** real run (preview == execute by
   construction — the plan is replayed). Run **on the scene instance, before any prefab conversion.**

   A finished, grouped avatar as the *source* is `reproportion`'s twin/copy flow, not owning — here, on
   the vendor→owned path, a flagged `[holder]` may be content you pruned on purpose, so the
   flagged-missing default (force / re-prune / accept) stands; never blanket-force the `[holder]`s.

5. **Group the dynamics** (the **MoveComponents** tool), called once per region — pure relocation, your
   discretion supplies the regions; **also driven by a type-name list** (no more `mode`). Rule: **physbones
   group by their chain-root bone region**; colliders and contacts each take one call targeting the avatar
   root; **VRC constraints** group the same way. **Unity built-in constraints are never relocated** — they
   drive their own GameObject and stay on their bone (and Relocate refuses any type with no anchor in the
   VRC table — MA/VRCF/NDMF and Unity built-in constraints all FAIL loud rather than move). Each call mints
   holder GOs under `AvatarDynamics/<folder>`, pins each component's anchor to its original bone
   (behavior-neutral — no bone is moved), and echoes matches by name+count; reconcile the invariant
   **Σ(moved) + intentionally-left == total Copy reproduced** so a missing chain is computed, not missed.
   **Grouping is operator preference, not a gate** — ask whether to relocate the reproduced dynamics
   under `AvatarDynamics/` (`MoveComponents`) before prefabbing; the avatar is valid and uploadable
   after CopyComponents alone, so a skipped Relocate is ungrouped-but-valid, not a failure.
   (`own-mergeable` takes the same ask.) **Must run before prefab conversion** (it removes the
   original component, unreliable on a prefab instance). What-if is available here too.

The CopyComponents run and **all** Relocate calls must complete **before** prefab conversion. Then **convert the
built-up scene FBX into a prefab variant**, and move the FBX itself into the avatar's `Models/` folder.

**Ask the operator to test-drive the avatar in-game** before the final cleanup.

Final cleanup: produce a **clean FX** (the **CleanController** tool). It keeps only the layers you name in
`keepLayerNames`; choose them with the **hand-gesture-relative heuristic** — locate the Left/Right Hand
gesture layers, keep them plus every layer **at or above** them, drop the outfit/visibility toggles below
(base layer 0 is always kept). The tool FAILs loud if a named layer is absent or ambiguous. If the head
mesh was renamed, the kept facial layers' clips bind it by its old name and stay **inert** — repath them
with the **UC2** clip phase (`OwnControllerClips → RepathClips`, `animator.md`), here or deferred to compose
where `CheckAvatar` surfaces the break; note it, don't block. Empty expression parameters + menu, wired into
the descriptor.

## Tools

Reach for these by role; open the tool to learn its exact entry point.

- **Unity package `com.ryan6vrc.avatar-tools`** (Editor tools, run via Unity MCP `execute_code`): a package-graph
  reporter; a humanoid-rig conformer; a materials-by-name + bounds/anchor setter; a descriptor transplanter; the
  component-transplant kit (`CopyComponents`, `MoveComponents`, `GraftHierarchy` over a shared transplant
  core); the `CleanController` builder.
- **Blender extension `avatarprep` core**: an FBX importer + import-observer; a read-only armature-compat
  reporter + a name-based armature merger (for the multi-FBX superset case); a zero-weight-bone pruner; the
  CATS-recipe Unity-FBX exporter.
