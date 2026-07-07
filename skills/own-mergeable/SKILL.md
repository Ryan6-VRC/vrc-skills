---
name: own-mergeable
description: Use when making our own owned copy of a mergeable's geometry — outfit, hair, ears/tail, or accessory — so it composes onto a base like a vendor one — "own this outfit", "turn just the clothing/hair into a mergeable", "extract the outfit from a full avatar", "add an MA/VRCFury seam to a bare outfit". Not placing a ready-made mergeable (compose-mergeable), not the base body (own-base), not reshaping alone (reproportion).
---

# Own a mergeable

Build our own owned copy of a mergeable — an operator-chosen geometry subset (outfit, hair, ears+tail,
accessory) — so it is **drop-in-equivalent** to the vendor's and composes onto a base with no
special-casing. This mirrors `own-base`'s three-phase spine over the same tools, minus the
body-only steps; the sequence and gates are fixed, the work inside each phase is judgment because
you never know how a creator built the asset. Open each tool to learn its entry point.

**Own for a durable geometry change** (usually reproportioning to a custom base) **or to author/copy a
seam the mergeable is missing.** A piece that needs neither — already seam-authored *and* geometrically
fine, like a rigid accessory that just follows its bone — is not owned here; **compose the vendor
prefab** (`compose-mergeable`).

## Scope — what this owns, and the boundary

In scope: own an **operator-designated geometry subset** as a standalone mergeable. The subset is the
operator's choice — clothing, hair, hair+ears+tail, a whole vendor mergeable, or a superset merged
from several FBX (`avatarprep merge_armatures` — rare, drive it from the tool; the merge force-names
its result `Armature`, a base-body invariant, so Phase 1's `Armature.<Name>` rename must follow it).
It is the **same operation regardless of what's in the set.**

- **Topo-equivalent bases are the enabling contract.** Extracting from one avatar to wear on another
  works when the two bases are topo-equivalent — the same base, or distinct bases bridged by an explicit
  equivalency profile (Plum/Chiffon/Chocolat are *distinct* bases so bridged, not one shared body) —
  because the seam matches by name; the cross-base mechanics are `reproportion`'s (*Cross-base*). A
  genuinely different (non-topo) base is a **refit** (roadmap: `docs/mochifitter.md`), out of scope.
- Placing the finished mergeable on a base → `compose-mergeable`.
- Reshaping proportions is `reproportion`'s engine — this skill *drives* it, never reimplements it.
- Seam morph-follow (MA BlendshapeSync / VRCFury blendshape-link) is **deliberately skipped** — too
  fragile to later base renames/bakes; a separate task if the operator asks.

## Phase 0 — Graph & decide

Inventory the source (`AvatarPackageGraph` on its vendor folder — the same read-only graph `own-base`
Phase 1 works from; its per-FBX mesh inventory and MA/VRCFury detection carry over, the head/body/superset
questions don't). As in `own-base`, `import-vendor-asset`'s `ImportVerify` PASS is this phase's
precondition — re-run it if health isn't already known-good. Then **surface these to the operator** —
each decides a later branch:

- **The subset** — which meshes become this mergeable. A standalone vendor mergeable is all of it; a
  monolithic avatar is the operator's pick.
- **Dynamics layout** — physbones/colliders on the armature bones (→ `CopyComponents`) or grouped in
  organizational holder GOs like `PB/…`, `Collider/…` (→ `GraftHierarchy`). This picks the transplant tool.
- **Modular or bare** — does it carry its own MA/VRCFury seam (→ *copy* it) or none (→ *author* it)?
- **Morph name-variants** — meshes carrying a `<Mesh>_<morph>` variant of a body morph the target base
  drives (e.g. `Dress_Breasts_small` vs the base's `Breasts_small`); coherence is `reproportion`'s job.
- **Target base reproportioned?** — if so, the edge/recipe to apply in Phase 1.

## Phase 1 — Blender: own the geometry (+ reproportion)

- **Import** the source FBX (the whole avatar, if extracting from a monolithic one).
- **`stamp_base` the armature with the target base's canonical lineage name** (e.g. `chocolat` — the
  base you're fitting to; if the vendor cut is a different-but-equivalent base, stamp its native base
  and let an equivalency profile carry it across). Seed this **here, right after import — not after the
  later `Armature.<Name>` rename below** — `apply_profile` hard-offends on an absent base stamp, so it
  must be in place before the Reproportion step.
- **Keep the subset's meshes, delete the rest.** For a standalone vendor mergeable nothing is dropped.
  Do **not** rename meshes or hunt for a `Body`/`Body_Base` (those are base-body conventions).
- **Reproportion, if the target base is reshaped — before pruning.** This is `reproportion`'s
  Outfit-fit: apply the target base's edge/recipe to this armature (`pivot="origin"`), skip base-only
  morphs, propagate name-variant morphs. **Ordering is a hard gate:**
  the edge references full-body seam bones (Head/Neck/Hand) the subset may not weight, so pruning first
  aborts the apply on missing bones.
- **Prune** zero-weight bones. Over-pruning is safe — a pruned component anchor resurfaces later as
  flagged-missing and is `force`-added or accepted. The **dropped meshes'** bones go here; the kept
  subset's own bones (a tail's chain, a skirt's) survive because its meshes weight them.
- **Name the armature distinctively** (`Armature.<Name>`) — set **here, in Blender**, a durable
  property of the owned FBX (collision avoidance against the base's `Armature` at the attach seam;
  the naming pair's home is `docs/nondestructive.md`).
- **Author at world origin** — transform (0,0,0); never bake a position offset into the owned asset
  (reproportion pivots about origin; the coherence checks compare world positions).
- **Bring in the target base body as a disposable reference.** Append the target base's body mesh (+ its
  armature) into the `.blend` for clipping / sculpt / weight-paint checks against the fitted mergeable —
  it is **never merged or exported**, just a shape to check against (the renamed mergeable armature means
  no collision). On a later reproportion, discard it and append the new target. The reference makes the
  scene two-armature, so scope every avatarprep call to the owned rig: apply/validate run before it's
  appended and fail loud if unscoped in a two-armature scene — but the export CLI only **warns** and
  exports the whole scene, which ships the reference body. Always pass `--armature`.
- **Export scoped to the mergeable's armature** (`export_unity_fbx --armature Armature.<Name>`: that
  armature + the meshes it deforms, selection-only) to **`Assets/Outfits/<Base>/<Outfit>/Models/`**,
  reusing vendor materials (embed textures off). The disposable reference body is a *different*
  armature, so it stays in the `.blend`, out of the FBX — a whole-scene export would ship it. The
  source `.blend` lives at the mirrored **`Blender/Outfits/<Base>/<Outfit>/<Outfit>.blend`** — this
  `Assets/` ↔ `Blender/` mirror is **load-bearing**: the compose provenance fit gate resolves the
  `.blend` from it.

## Phase 2 — Unity: materials + dynamics

Work on the **scene instance** of the owned FBX; prefab only at the end (Phase 3).

- **Import Generic** — a mergeable is not humanoid, so **no rig-conform and no descriptor** (the base
  owns both). Assign vendor materials + standard bounds/anchor by renderer name (the materials tool).
- **Reproduce only the kept subset's own dynamics; exclude everything else.** The discriminator is
  **whose the dynamic is**, not where its anchor sits: reproduce a physbone/collider only if it belongs to
  a **kept** mesh (a skirt's sway, a tail's bounce *if you're owning the tail*). **Exclude** anything
  whose source isn't in the subset — **base-owned body** jiggle (breast/butt/thigh/stomach; the base
  already has it, and you know what it carries because you separated from that same body) *and* a
  **dropped mesh's** dynamic sitting on a bone the subset also weights (a dropped cape's sway bone on a
  shared spine bone survives the prune and copies clean in whatIf — it will *not* self-exclude). When the
  vendor **groups** dynamics (`PB/Costume` vs `PB/Breast`) the grouping is the clean signal; else map each
  dynamic to its **owning mesh**, not merely its anchor bone.
- **Layout picks the tool:** on-bones → `CopyComponents`; grouped in holder GOs → `GraftHierarchy` the
  holder subtree(s), scoped to the mergeable's own. **whatIf first, then one real run.**
- **Grouping is operator preference, not a gate — the same ask as `own-base`:** relocate the reproduced
  dynamics under `AvatarDynamics/` (`RelocateComponents`) before prefabbing, or skip; a graft that already
  brought the vendor's holder GOs is grouped as-is, and skipping is ungrouped-but-valid.
- A kept physbone referencing a **base-owned** collider (one you excluded) lands its `colliders[]` entry
  **null**. This is a real gap, not cosmetic — the physbone would collide against nothing — so **surface
  it as a may-block diagnostic**, don't silently leave it. The fix is a placement-time **collider relink**
  in `compose-mergeable` (re-point the entry at the base's collider on the physbone's anchor bone).
- **Component-drift sanity-scan** (`reproportion`'s shared process): copied physbone/collider radii are
  sized to the source and don't track the rescale. Accumulate the recipe magnitude, report it; a
  single-digit % is below notice (copy as-is); escalate only at large magnitude. Scaling the source
  does *not* fix it — only an explicit radius-field scale would.

## Phase 2B — Establish the seam

- **Modular vendor mergeable → copy its seam** (the conservative tier of the same transplant). A
  correctly copied seam auto-targets the base exactly like the vendor's — that *is* drop-in-equivalence.
- **Bare / non-modular → author the seam.** Choose MA vs VRCFury by the robustness rule in
  `docs/nondestructive.md` (MA by default). **Default component settings**, setting only the required
  linkage — MA MergeArmature's merge target, VRCFury ArmatureLink's prop bone. **One prefab, one seam.**
  - **Placement:** MA `MergeArmature` on the armature GO + `MeshSettings` on the root; VRCFury
    `ArmatureLink` on the **armature GO**.
  - **VRCFury only:** turn **off** align position/rotation/scale — we already proportioned the geometry,
    so VRCFury must not re-align it.
  - **Initialize through the component's real add-path**, not a hand-built instance — a raw construction
    leaves required defaults (e.g. the link target list) empty and silently breaks.
  - Two variants (MA *and* VRCFury) are a deliberate exception: build a dynamics-only base prefab and
    make each seam a thin variant of it, so the dynamics aren't grafted twice.

## Phase 3 — Verify

Structural and basic — **the real proof is a compose**, so hand off after:

- **Seam hit-rate** — the core seam bones resolve by name against the target base.
- **Reproportion coherence** — the owned mergeable's bones land on the target base's reshaped world
  positions (compare a few; the vendor piece would sit off).
- **Clean transplant diagnostics** — flagged-missing 0 for kept hosts, anchors bound, no vendor leak.

If a later compose finds the provenance stamp missing or mismatched against the base, the fix
re-enters **this skill** (re-stamp + refile) — it is not patched in the Unity scene.

Then convert to a **prefab variant** of the FBX and hand to `compose-mergeable` + the operator's
playmode for the visual/behavioral bar. Grab in a separate call from any edit — a same-call grab shows
the pre-edit proxy; the summary's `note=` flags an in-flight rebuild but cannot catch the same-call case.

## Tools

Reach by role; open each for its entry point.

- **`avatarprep` (Blender):** FBX import + observe, zero-weight prune, the proportion engine (edge/recipe
  apply — driven via `reproportion`), CATS FBX export, `merge_armatures` (superset case).
- **`com.ryan6vrc.avatar-tools` (Unity):** the transplant kit (`CopyComponents` / `GraftHierarchy` /
  `RelocateComponents` over a shared core), materials-by-name + bounds/anchor.
- **Modular Avatar / VRCFury:** the seam frameworks — copy their components, or author one.
