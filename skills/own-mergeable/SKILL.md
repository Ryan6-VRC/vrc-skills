---
name: own-mergeable
description: Use when making our own owned copy of a mergeable's geometry — outfit, hair, ears/tail, or accessory that attaches through a seam (a base's own non-detachable ears/tail/hair is own-base) — so it composes onto a base like a vendor one — "own this outfit", "turn just the clothing/hair into a mergeable", "extract the outfit from a full avatar", "add an MA/VRCFury seam to a bare outfit". Not placing a ready-made mergeable (compose-mergeable), not the base body (own-base), not reshaping alone (reproportion), not a gimmick's animator/param system (own-gimmick).
---

# Own a mergeable

Build our own owned copy of a mergeable — an operator-chosen geometry subset (outfit, hair, ears+tail, accessory) — so it is **drop-in-equivalent** to the vendor's and composes onto a base with no special-casing. This mirrors `own-base`'s three-phase spine over the same tools, minus the body-only steps; the sequence and gates are fixed, the work inside each phase is judgment because you never know how a creator built the asset. Open each tool to learn its entry point.

**Own for a durable geometry change** (usually reproportioning to a custom base) **or to author/copy a seam the mergeable is missing.** A piece that needs neither — already seam-authored *and* geometrically fine, like a rigid accessory that just follows its bone — is not owned here; **compose the vendor prefab** (`compose-mergeable`).

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## Scope — what this owns, and the boundary

In scope: own an **operator-designated geometry subset** as a standalone mergeable. The subset is the operator's choice — clothing, hair, hair+ears+tail, a whole vendor mergeable, or a superset merged from several FBX (`avatarprep merge_armatures` — rare, drive it from the tool; the merge force-names its result `Armature`, a base-body invariant, so Phase 1's `Armature.<Name>` rename must follow it). It is the **same operation regardless of what's in the set.**

- **Topo-equivalent bases are the enabling contract.** Extracting from one avatar to wear on another works when the two bases are topo-equivalent — the same base, or distinct bases bridged by an explicit equivalency profile (Plum/Chiffon/Chocolat are *distinct* bases so bridged, not one shared body) — because the seam matches by name; the cross-base mechanics are `reproportion`'s (*Cross-base*). A genuinely different (non-topo) base is a **refit** (`mochifit`), out of scope.
- Placing the finished mergeable on a base → `compose-mergeable`.
- A base's **integral** ears, tail, or hair — carried by the vendor's own body as non-detachable identity rather than attaching through a seam — is the base, not a mergeable → `own-base`.
- The own here is **geometry-led**: the subset's meshes, rig, dynamics, and seam. An **animator/param system** — a gimmick riding the piece, or wanted out of it — is `own-gimmick`; this skill's animator ceiling is Phase 2C (repointing motion assets for a controller kept whole).
- Reshaping proportions is `reproportion`'s engine — this skill *drives* it, never reimplements it.
- Seam morph-follow (MA BlendshapeSync / VRCFury blendshape-link) is **deliberately skipped** — too fragile to later base renames/bakes; a separate task if the operator asks.

## Phase 0 — Graph & decide

Inventory the source (`ReportPackage` on its vendor folder — the same read-only graph `own-base` Phase 1 works from; its per-FBX mesh inventory carries over and the head/body/superset questions don't). Framework presence reads off **`nonSdkNs=`**, a verbatim namespace census that names no framework and claims no support — an entry means *go read that prefab*; a nonzero `unresolvedScripts=` means the census is incomplete, so resolve those before concluding a package is framework-free. As in `own-base`, `import-vendor-asset`'s `CheckPackage` PASS is this phase's precondition — re-run it if health isn't already known-good. Then **surface these to the operator** — each decides a later branch:

- **The subset** — which meshes become this mergeable. A standalone vendor mergeable is all of it; a monolithic avatar is the operator's pick.
- **Dynamics layout** — physbones/colliders on the armature bones (→ `CopyComponents`) or grouped in organizational holder GOs like `PB/…`, `Collider/…` (→ `GraftHierarchy`). This picks the transplant tool.
- **Modular or bare** — does it carry its own MA/VRCFury seam (→ *copy* it) or none (→ *author* it)?
- **Morph name-variants** — meshes carrying a `<Mesh>_<morph>` variant of a body morph the target base drives (e.g. `Dress_Breasts_small` vs the base's `Breasts_small`); coherence is `reproportion`'s job.
- **Target base reproportioned?** — if so, the edge (or edge chain) to apply in Phase 1.

## Phase 1 — Blender: own the geometry (+ reproportion)

A **seam-only own** (no geometry change — a bare piece that just needs a seam, or a copy onto the same base) skips reproportion, the reference-body append, and morph propagation below: it is a scoped re-export to carry or author the seam, nothing more.

- **Import** the source FBX (the whole avatar, if monolithic) with the **avatarprep import** function.
- **The FBX may not carry the whole fit.** A vendor *per-base variant* prefab can author its entire fit as Unity-side transform overrides — the root's full transform, rotation and position as readily as scale, plus per-bone pose deltas — over a generic shared FBX, leaving no Blender-visible trace. When the source is such a variant prefab (not a monolithic avatar), instantiate it in Unity and diff its transform overrides (the root's position, rotation and scale, plus humanoid-bone rotations) against the imported FBX's rest pose, then replicate any non-identity delta in Blender before export. Skip this and the owned copy ships the generic un-fitted geometry — a silent, hundreds-of-mm misfit that surfaces only on a `CheckSeam` against the vendor instance.
- **`stamp_base` the armature with the target base's canonical lineage name** (e.g. `chocolat` — the base you're fitting to; if the vendor cut is a different-but-equivalent base, stamp its native base and let an equivalency profile carry it across). Seed this **here, right after import — not after the later `Armature.<Name>` rename below** — `apply_proportion_edge` hard-offends on an absent base stamp, so it must be in place before the Reproportion step.
- **Keep the subset's meshes, delete the rest.** For a standalone vendor mergeable nothing is dropped. Do **not** rename meshes or hunt for a `Body`/`Body_Base` (those are base-body conventions).
- **Reproportion, if the target base is reshaped — before pruning.** This is `reproportion`'s Outfit-fit: apply the target base's edge (or edge chain) to this armature (`pivot="origin"`), skip base-only morphs, propagate name-variant morphs. **Ordering is a hard gate:** the edge references full-body seam bones (Head/Neck/Hand) the subset may not weight, so pruning first aborts the apply on missing bones.
- **Prune** zero-weight bones (`--whatif` first — it groups the removals into rooted chains, mutating nothing). Over-pruning a *bone* is recoverable: a pruned component anchor resurfaces later as flagged-missing and is `force`-added or accepted. The **dropped meshes'** bones go here; the kept subset's own bones (a tail's chain, a skirt's) survive because its meshes weight them. An *object* bone-parented to a doomed bone is the exception and makes the prune **refuse** — nothing catches that one later, since the object would be orphaned outright. Re-weight or re-parent it; see `own-base` for the contract.
- **Name the armature distinctively** (`Armature.<Name>`) — set **here, in Blender**, a durable property of the owned FBX (collision avoidance against the base's `Armature` at the attach seam; the naming pair's home is `docs/nondestructive.md`). No avatarprep door — rename inline: `bpy.data.objects['Armature'].name = 'Armature.<Name>'`.
- **Author at world origin** — `reproportion`'s origin-pivot rule (that skill owns the justification) applies to the owned asset too.
- **Bring in the target base body as a disposable reference.** Append the target base's body mesh (+ its armature) into the `.blend` for clipping / sculpt / weight-paint checks against the fitted mergeable — it is **never merged or exported**, just a shape to check against (the renamed mergeable armature means no collision). On a later reproportion, discard it and append the new target. The reference makes the scene two-armature, so scope every avatarprep call to the owned rig: apply/validate run before it's appended and fail loud if unscoped in a two-armature scene, and the export **refuses** a whole-scene export of it outright. Always pass `--armature`.
- **Export scoped to the mergeable's armature** (`export_unity_fbx --armature Armature.<Name>`: that armature + the meshes it deforms, selection-only) to **`Assets/Outfits/<Base>/<Outfit>/Models/`**, reusing vendor materials (embed textures off). The disposable reference body is a *different* armature, so it stays in the `.blend`, out of the FBX — a whole-scene export would refuse (two armatures in scope). A cm-unit source whose armature still hangs off the vendor's scaled root EMPTY refuses the *scoped* door too (out-of-scope ancestor) — clear/apply that EMPTY parent relation first; the refusal names it. The source `.blend` lives at the mirrored **`Blender/Outfits/<Base>/<Outfit>/<Outfit>.blend`** — this `Assets/` ↔ `Blender/` mirror is **load-bearing**: the compose provenance fit gate resolves the `.blend` from it.

## Phase 2 — Unity: materials + dynamics

Work on the **scene instance** of the owned FBX; prefab only at the end (Phase 3).

- **Import Generic** — a mergeable is not humanoid, so **no rig-conform and no descriptor** (the base owns both). Assign vendor materials + standard bounds/anchor by renderer name (the materials tool).
- **Scale parity is import settings, not export mimicry.** An owned export is the repo-canonical meter-unit FBX — `export_unity_fbx` enforces it (its default layout, plus a loud refusal on a scene whose unit scale would rewrite it), whatever unit class the vendor shipped. `import_fbx`'s snapshot `unit_scale_factor` names the vendor's class: 100 = meter-unit, 1 = cm-unit, other values (2.54, 30.48) = inch/foot-unit, `None` = unreadable (treat as unknown, don't guess). Unity's Convert Units normalizes them all, so leave the importer's scale at defaults; a wrong-unit landing is a loud ~100× miss at `CheckSeam`, and the fix is the importer's Scale Factor — never a re-export tuned to mimic the vendor's file layout.
- **Reproduce only the kept subset's own dynamics; exclude everything else.** The discriminator is **whose the dynamic is**, not where its anchor sits: reproduce a physbone/collider only if it belongs to a **kept** mesh (a skirt's sway, a tail's bounce *if you're owning the tail*). **Exclude** anything whose source isn't in the subset — **base-owned body** jiggle (breast/butt/thigh/stomach; the base already has it, and you know what it carries because you separated from that same body) *and* a **dropped mesh's** dynamic sitting on a bone the subset also weights (a dropped cape's sway bone on a shared spine bone survives the prune and copies clean in whatIf — it will *not* self-exclude). When the vendor **groups** dynamics (`PB/Costume` vs `PB/Breast`) the grouping is the clean signal; else map each dynamic to its **owning mesh**, not merely its anchor bone.
- **Layout picks the tool:** on-bones → `CopyComponents`; grouped in holder GOs → `GraftHierarchy` the holder subtree(s), scoped to the mergeable's own. **whatIf first, then one real run.**
- **Grouping is operator preference, not a gate — the same ask as `own-base`:** relocate the reproduced dynamics under `AvatarDynamics/` (`MoveComponents`) before prefabbing, or skip; a graft that already brought the vendor's holder GOs is grouped as-is, and skipping is ungrouped-but-valid.
- A kept physbone referencing a **base-owned** collider (one you excluded) lands its `colliders[]` entry **null**. This is a real gap, not cosmetic — the physbone would collide against nothing — so **surface it as a may-block diagnostic**, don't silently leave it. The fix is a placement-time **collider relink** in `compose-mergeable` (re-point the entry at the base's collider on the physbone's anchor bone).
- **Component-drift sanity-scan** (`reproportion`'s shared process): copied physbone/collider radii are sized to the source and don't track the rescale. Accumulate the chain magnitude, report it; a single-digit % is below notice (copy as-is); escalate only at large magnitude. Scaling the source does *not* fix it — only an explicit radius-field scale would.

## Phase 2B — Establish the seam

- **Modular vendor mergeable → copy its seam** (the conservative tier of the same transplant). A correctly copied seam auto-targets the base exactly like the vendor's — that *is* drop-in-equivalence.
- **Bare / non-modular → author the seam.** Choose MA vs VRCFury by the robustness rule in `docs/nondestructive.md` (MA by default). **Default settings, one prefab, one seam**; the shape follows what the piece binds to:
  - **Skins the humanoid skeleton (clothing)** → MA `MergeArmature` on the **armature GO** + `MeshSettings` on the prefab root. VRCFury alt: `ArmatureLink` on the armature GO with align position/rotation/scale **off** (the geometry is already proportioned; VRCFury applies align at build).
  - **Rides one bone (hair, hat, earring)** → MA `BoneProxy` on the **armature root, never the top-level prefab GO** (only the rig should reparent under the bone; the renderers stay at avatar-root level), `target` the humanoid bone, `attachmentMode = AsChildKeepWorldPose` — left `Unset` it builds as `AsChildAtRoot` and snaps the piece to the bone's origin — plus `MeshSettings` on the prefab root. Alternative on a topo-shared base: append the base armature into the accessory's `.blend`, delete the base geometry, prune to the accessory's own bones, and it then seams by `MergeArmature` like clothing.
  - **Build the MA components directly; do not drive the "Setup Outfit" UI add-path.** Set the fields a successful `SetupOutfit.SetupOutfitUI` writes (its source is the authority) — the load-bearing ones: `MergeArmature.mergeTarget` → the base `Armature` with `LockMode = BaseToMerge`, and `MeshSettings` in `SetOrInherit` (not `Inherit`: a vendor base has no parent settings to inherit from) with the probe anchor → Hips. The add-path's bone-rename and A-pose passes are no-ops on the rig Phase 1 already gave the base's bone names and a distinct `Armature.<Name>`, and its one headless hazard — a modal error window — fires only on a validation failure, never a valid setup; the internal-suppress reflection some workers reach for was treating a symptom, not the cause.
  - Two variants (MA *and* VRCFury) are a deliberate exception: build a dynamics-only base prefab and make each seam a thin variant of it, so the dynamics aren't grafted twice.

## Phase 2C — Own the seam's clips (skip if none)

Only when the seam carries its **own animator** (an MA MergeAnimator / VRCFury FullController with clips) — **skip the armature-link-only case, the common one.** A vendor seam's clips still bind **vendor `.anim` assets by GUID**, so owning the geometry without owning the clips leaves them vendor-coupled or inert. Run the `animator.md` **UC2** clip phase, `whatIf` first:

1. **`OwnControllerClips(controller, outDir)`** — materialize owned `.anim` copies and repoint the controller's motion slots (closes the CleanController GUID-coupling gap).
2. **`RepathClips(controller, oldPaths, newPaths)`** — rewrite the owned clips' binding paths. It is **frame-blind**: supply the moves in **this seam's frame** (MA `pathMode`/`relativePathRoot`; VRCFury mount-relative), the one thing the tool can't infer.

`compose-mergeable` invokes this same phase for the owned-outfit inline case — it is one named unit. It repoints motion assets for a controller **kept whole**; any cut, trim, or param surgery on the controller is `own-gimmick`.

## Phase 3 — Verify

Structural and basic — **the real proof is a compose**, so hand off after:

- **Seam fit — `CheckSeam`** — place onto the target base and run `CheckSeam.Run(base, mergeable)`. It reflects the seam mapping and gates world-position coincidence of the weighted humanoid bones, so a PASS proves the owned piece lands on the target base's (reshaped) skeleton — subsuming the by-name hit-rate and the eyeballed "compare a few". NOT-PASS is a reproportion/seam problem to fix before hand-off; a hair or single-bone accessory REFUSEs (offset-tolerant proxy) — its fit is the operator's at compose, as expected.
- **Clean transplant diagnostics** — flagged-missing 0 for kept hosts, anchors bound, no vendor leak.
- **Placement proof (`CheckAvatar`)** — place onto the target base and run `CheckAvatar.Run(<root>)`; expect `PASS`. A `CLASSIFY` names a seam scene-ref or a Phase-2C clip binding still unresolved against the placed scene — fix it before hand-off rather than eyeballing the pairing.

If a later compose finds the provenance stamp missing or mismatched against the base, the fix re-enters **this skill** (re-stamp + refile) — it is not patched in the Unity scene. (A refit bucket is the exception: it has no `.blend` mirror by design and `compose-mergeable` reads its sidecar instead — never this loop.)

Then convert to a **prefab variant** of the FBX — **never unpack the instance** during the build-up (a fully-unpacked instance saves as a silently-unlinked **Regular** prefab that a re-export then desyncs — `unity.md`); gate on `PrefabUtility.GetPrefabAssetType == Variant`.

**Zero the instance's root position and rotation before saving — unless the root carries a pose you established here.** Phase 1 replicated any vendor root delta into the geometry, so on an armature-merge piece the root holds nothing but staging offset, which bakes into the asset and surfaces later as a `CheckSeam` **NOT-PASS** carrying `maxOffset=`. The exception is a bone-proxy piece whose edit-time world pose against the target base you set here, at Phase 2B or 3. Decide it on the mode's **flags**, not its name: only `Unset` and `AsChildAtRoot` zero both localPosition and localRotation at build, so only there is the root's pose discardable — `AsChildKeepWorldPose`, `AsChildKeepPosition` and `AsChildKeepRotation` each preserve some of it. **Root scale is never zeroed by the build** unless `matchScale` is set, so leave an authored root scale alone in every mode. Record which case you have; `compose-mergeable`'s never-normalize rule protects a kept root downstream. Hand to `compose-mergeable` + the operator's playmode for the visual/behavioral bar. A `RenderAvatar` grab for that bar goes in a separate call from any edit — a same-call grab shows the pre-edit proxy; the summary's `note=` flags an in-flight rebuild but cannot catch the same-call case.

## Tools

Reach by role; open each for its entry point.

- **`avatarprep` (Blender):** FBX import + observe, zero-weight prune, the proportion engine (`apply_proportion_edge`, driven via `reproportion`), CATS FBX export, `merge_armatures` (superset case).
- **`com.ryan6vrc.avatar-tools` (Unity):** the transplant kit (`CopyComponents` / `GraftHierarchy` / `MoveComponents` over a shared core), materials-by-name + bounds/anchor.
- **Modular Avatar / VRCFury:** the seam frameworks — copy their components, or author one.
