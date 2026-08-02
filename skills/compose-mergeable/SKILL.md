---
name: compose-mergeable
description: Use when placing a ready-made outfit, hair, accessory, or gimmick module (vendor or already-owned) onto an avatar base — "put this outfit on my avatar", "add this hair to the base", "compose/wear this mergeable". Not owning or creating a mergeable's geometry, and not adding a seam to a bare prefab (both own-mergeable); not cross-base refitting (mochifit).
---

# Compose a mergeable onto an avatar base

Place one seam-authored mergeable (outfit / hair / accessory / gimmick module) onto an avatar base, non-destructively. The mergeable already carries its own Modular Avatar / VRCFury seam; you **drop it in, verify the seam resolves, de-conflict the meshes it replaces, and reconcile shape coherence** — then hand off. The seam resolves at build (MA/VRCFury merge on a clone at upload/play); nothing here bakes it down. A **gimmick/behavior module** (a prop, a contact / physbone / constraint system) composes on the same spine but is gated on behavior integrity, not geometry — the fork is step 3, and steps 4–5 fall away.

**Source-agnostic.** A vendor mergeable and a mergeable produced by `own-mergeable` are treated identically — that a correctly-owned mergeable composes here with zero special-casing is the proof `own-mergeable` did its job. Never branch on where the prefab came from.

**Fit is gated mechanically where it can be; cosmetic look is the operator's.** For a mergeable that skins across the humanoid skeleton (clothing), alignment is decided by a **mechanical seam check** (`CheckSeam`, step 3) — a model can't judge fit from a render (`verify.md`). An offset-tolerant **bone-proxy** (hair, an accessory bound to one bone) `CheckSeam` **refuses** to score: fit there is operator-positioned, not bone-determined, and joins the cosmetic (clipping, wrong shape) as the operator's eye. So this skill's programmatic job is: run cheap static **tripwires** for the *non-cosmetic silent* failures a human can't eyeball, gate fit on the seam check where it scores, do the mechanical in-scene repairs, then get out of the way so the operator looks. **"Merges without error" ≠ "composed"** — a wrong-base mergeable merges with a clean console (MA silently auto-creates phantom bones), so a green console proves nothing.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## Scope — what this owns, and where it routes out

Owns: the cheap, non-destructive, **in-scene** work — drop, seam verification, scene-ref repath, mesh de-conflict, blendshape/baked coherence. Does **not** choose or add seams, own geometry, or refit across bases. When a compose needs any of those, do the in-scope part and **surface the boundary to the operator** rather than improvising:

- **Bare mergeable** (armature but no MA/VRCFury attach component) → `own-mergeable`. This skill never *adds* a seam; it only verifies an authored one. Choosing MA vs VRCFury is `own-mergeable`'s job.
- **Wrong-base mergeable** (armature seam doesn't resolve — see step 3) → a **refit**, not a compose. Route to `mochifit`. Do not try to force it.
- **Mergeable missing a shape the base needs** (step 5 can't reconcile) → `own-mergeable` to bake it.
- **Menu / animator / parameter coherence** → `author-menu` (step 7). Required, but out of scope here. Step 4's runtime-owned residue routes there too: flipping a shipped parameter default changes the avatar's menu defaults — the operator's call, never composed in silently.
- **Gimmick/behavior module** → composed here whole, on the behavior-integrity gates of step 3. Editing its behavior — trim, param surgery, a with/without variant — is `own-gimmick`; grafting new behavior is `author-gimmick`. This skill places a finished module; it never re-authors one.

## The flow

Work on an **in-scene instance** of the avatar base. Converting the result to a prefab variant is the operator's call, at the end.

### 1. Precondition — the mergeable is seam-authored

Confirm the mergeable prefab carries its own seam: MA `MergeArmature` / `BoneProxy`, or VRCFury `ArmatureLink`. A bare prefab (armature, no attach component) is **out of scope** → route to `own-mergeable`.

### 2. Drop

Instantiate the **standalone vendor/owned prefab** (never a placed instance) as a child of the avatar root, **leaving the prefab's own root transform untouched — untouched, not identity**: vendors bake the per-avatar fit into the prefab root (a real hair shipped root scale `1.051` plus a position offset; zeroing them to identity seated the whole assembly 6.5 cm low while every mechanical gate passed). The root transform is authoring, not mess — **never normalize its scale or position** as cleanup: normalizing a vendor root scale like `0.9512` to `1:1:1` after placement manufactures a per-bone offset gradient that reads as a gross misfit and bakes straight through (the merge is identity-preserving — `nondestructive.md`). **After the drop, before any operator-directed placement, diff the instance root's local position/rotation/scale against the prefab asset's own values** — a difference there is an unintended override; revert it, don't re-author it. A later deliberate, flagged positioning of a bone-proxy mergeable is the operator's (step 3's proxy REFUSE route) and is not what this check reverts. A mergeable authored for this base auto-targets the base's `Armature` — you do not wire the seam by hand.

### 3. Verify the seam — mechanical gates

All cheap and mechanical, each catching a silent failure a green console hides. Run them right after the drop, before de-conflict or coherence: a wrong base caught here saves the wasted strip-and-reconcile of steps 4–5.

**The module class forks the gates.** A mergeable that skins the humanoid skeleton (clothing; the humanoid-weighted part of a body accessory) is gated on geometry — the bullets below. A **gimmick/behavior module** (a world prop, a contact / physbone / constraint system, an accessory carrying behavior but **no weighted humanoid bones**) gives `CheckSeam` nothing to score, so it REFUSEs — the **expected** path here, not a misfit, **when the REFUSE names an abstain reason** (no humanoid bones / bare prop / proxy). A REFUSE citing a seam-resolution or reflect/API failure is a tool break, class-independent — never waved off as the gimmick case. Its seam anchors to one bone or the avatar root and its fit is authored; what a compose silently breaks instead is **behavior integrity**, gated by two reads in place of `CheckSeam`:

- **`ReportGimmick`** — read the module's subtree topology (receivers, PB chains, constraint rigs, params) and compare it to the module's standalone shape: the drop should carry the whole system intact, and a piece left behind or a param that didn't come across shows against that baseline.
- **`CheckAvatar`** (the broken-ref bullet below, run the same way) — a re-root moves the paths the module's contacts / drivers / clips bind to; `CheckAvatar` names what the move left unresolved, routed by class exactly as for geometry.

Firing (does it trigger, latch, release) is **not gated here**: the module's author already proved it in the emulator, so the compose confirms only that placement didn't break it statically, then names an **emulator smoke** as the play-mode handoff (step 7) — consistent with step 6's operator's-call stance. A cross-base placement is a refit, out of scope (`Scope`), so world-space contact re-verification never arises in a compose. The geometry bullets below apply to the humanoid-skinned case; a gimmick module runs only the two reads above plus the broken-ref and physbone-collider bullets.

- **Seam fit + resolution — `CheckSeam` (the mechanical gate).** `CheckSeam.Check(baseRoot, mergeableRoot)` — mechanism and verdict grammar in `unity-tools.md`. Because it reflects the real resolver, the wrong-base merge MA hides by auto-creating phantom bones (`nondestructive.md`) — a clean console while the outfit skins to bones that never move — surfaces here as NOT-PASS or a won't-resolve REFUSE. Route the three outcomes:
  - **PASS** — the humanoid skeleton coincides; fit is certified, proceed to de-conflict. It certifies
    *only* the humanoid skeleton — not physics-cage / bust / hair / accessory placement, which stay the
    operator's eye (step 6). PASS carries `maxWithinEps`, the largest sub-ε bone offset: a peripheral bone
    (a hand/finger) sitting near ε is the ambiguous pose-drift-vs-edit-bump case the NOT-PASS bullet
    describes, now under the widened tolerance — **flag it to the operator, change nothing**; the widen
    absorbs base-inherent drift, it does not license swallowing a real one.
  - **NOT-PASS** — humanoid bones offset past ε. A large offset, or one across most bones, is the **wrong
    base or a real misfit** (an agent-normalized root — the step-2 trap — is this signature): surface it,
    route out (`Scope`), don't force it. **A few peripheral bones just over ε** (a hand or finger, sub-mm)
    is ambiguous and **not yours to fix blind**: `CheckSeam` measures position only, so it can't tell a
    pose-mode bake drift (re-aligning the bone fixes it) from an edit-mode bump where the mesh is already
    aligned to the moved bone (re-aligning drags the mesh *off*) — opposite handling, indistinguishable
    from the number. **Flag it to the operator and change nothing.** Correct only a misfit whose cause you
    know, with a **deliberate, flagged, re-verified** edit — never the reflexive normalization step 2
    forbids.
  - **REFUSE** — can't certify this seam, for a reason it names, and the reason picks the route. An
    offset-tolerant proxy (≤1 humanoid bone — hair/accessory), or a *VRCFury-scales-at-bake* seam
    (`forceOneWorldScale` / non-unit scale — legitimate authoring the edit-time pose can't certify), routes
    to the **operator's eye and a baked-result check**, not a refit. A *seams-disagree* or
    *won't-resolve-onto-this-base* reason is the **wrong base** → route to refit (`Scope`), not a fit you force.
- **Provenance routing (owned mergeables only).** `CheckSeam` detects the misfit; the provenance stamps say *which side to fix*. For an owned mergeable (asset path under `Assets/…`, not `Assets/Vendor/…`), read its mirrored `(base, state)` via avatarprep **`report_stamps`** (Decision 2's mirror):
  - **Refit bucket first** (a provenance sidecar beside the prefab, no `.blend` mirror — `docs/LAYOUT.md`):
    stamps are absent **by design**, never the re-stamp case — read the sidecar instead. Its target base
    must equal the base being composed onto; a mismatch means the refit served a different base — route
    back to `mochifit` for a re-run, not to a scene fix or a stamp repair.
  - **Owned base** (own blend under `Assets/…`): read the base's `(base, state)` too. An exact mismatch, or
    a genuinely-absent stamp on an owned side, is a **loud may-block WARNING — write nothing**: a
    missing/mismatched *outfit* stamp is `own-mergeable`'s re-stamp-and-refile loop, a missing *base* stamp
    is `own-base`'s `stamp_base` seed (Decision 3) — route to whichever side is off.
  - **Vendor base** (under `Assets/Vendor/…`, no blend or stamp — expected): a vendor base is
    `unproportioned` by construction. A mergeable in state `unproportioned` is the blessed "own the outfit,
    not the base" case; a **`reshaped`** mergeable can't fit a stock base → route to `own-base` (own +
    reproportion the base). This is the same misfit `CheckSeam` flags as NOT-PASS — `reshaped` moves the
    rest pose without renaming bones — named at the stamp level so the fix routes to the right side.
- **Broken refs — classify with `CheckAvatar`, then route by class.** Run `CheckAvatar.Inspect(<avatar root>)` on the placed avatar (contract in `unity-tools.md`): against the placed scene it names every MA scene ref and clip/controller binding a rename left unresolved. The usual cause is a **renamed seam**: `own-base` may rename the primary body mesh (recommended `Body_Base`; vendors ship `Body_base`). CheckAvatar classifies and names; you route (a deliberately-null toggle target or a portability-redundant path where several point at one object is a legitimate non-offender — judge, don't blindly repath):
  - **`MA-scene-ref`** → **repath in-scene**: retarget the reference to the renamed object — a scene edit,
    **no asset write**; non-aborting.
  - **`clip-binding`** → asset surgery, routed by the offender's **`clipAssetPath`** (not its scene `path`,
    which always looks writable): an **owned/writable** `.anim` is repathed **inline** (the
    `OwnControllerClips → RepathClips` clip phase, `animator.md` UC2); an **unowned vendor** clip (`clipAssetPath`
    under `Assets/Vendor/`|`Packages/`) needs a geometry round-trip compose can't do — **abort the compose and
    route to `own-mergeable`**, but **only when the compose introduced the break.** A vendor binding already
    dangling on the bare base (it shows in a `CheckAvatar` run *before* you compose — e.g. a base's own
    `Breast_Size → Costume_*` ref) is vendor-shipped, not your regression — flag it and proceed; only a
    break a rename or move in *this* compose created routes out.
- **Physbone collider refs — relink null base-collider slots.** A placed physbone whose `colliders[]` holds a **null** slot collided against a *base-owned* collider the mergeable doesn't carry (`own-mergeable` leaves it null by design — the collider is the base's). Re-point each null at the base's collider on the physbone's anchor bone (`execute_code` on the placed instance; in-scene, no asset write) — left null, the physbone collides against nothing. Act on the null slot, not on provenance: a vendor mergeable has none, so this is a no-op for it.

### 4. De-conflict the meshes — delegate, then dispose

A whole gimmick/behavior module replaces nothing and keeps all its layers — steps 4–5 don't apply to it (a *partial* take is an `own-gimmick` fork, not a compose). The rest of this step is the geometry case.

A full outfit replaces base clothing; overlapping meshes clip. Disabling those meshes looks like a one-line in-scene edit and is not. A base garment is often **coupled to body blendshapes** (`outfits.md`): disable the mesh alone and the pre-collapsed region it covered stays collapsed. The coupling lives in FX clips and MA `ShapeChanger` reactions, on a **body-morph mesh that is not the one named `Body`**, and reads **weight 0 at edit time** — invisible to any scan you would run here. Deciding which garments are overlapped, ruling on each shape, and gathering the evidence for a contested keep is `map-outfit-shapes`' domain, not this skill's.

So whenever this step disables or deletes base clothing, **delegate to `map-outfit-shapes`, scoped to the composed outfit and the base clothing layers it could replace** (the full-avatar map stays opt-in) — naming which of those are actually overlapped is map's call, not this step's — and require two artifacts back before the geometry-path compose is done. A gimmick module has neither:

1. its **`ReportShapeOverlap` resolution artifact**, every `MISMATCH` row accepted, overridden (a `shared-morph` category override included), or left explicitly **OPEN**, whose RunLog records the census ran; and
2. the **named runtime-owned residue** — every edge an always-on FX layer drives from an expression parameter — or, when the map ran and the FX read came back clean, the literal line **`RESIDUE: none — nothing routes out`**: an empty residue is a completed delegation and a compose that is runtime-wearable as delivered, not a skipped step, and it still cites the RunLog.

**This delegation is the step that gets skipped.** Every recorded skip substituted a cheaper edit-time read and rationalized it; two shipped defects. A justification matching a row below is wrong for the stated reason — run the map:

| Rationalization | Why it fails |
|---|---|
| "No `ShapeChanger`, zero edit-time weights — no coupling" | Weight-0 under FX drive is the exact invisible case; "no coupling" is a conclusion only after the FX read also comes up empty, and that read is the map's. |
| "The render will catch a collapsed region" | NDMF preview resolves the driven state into the render — it shows fine while masking the residue. |
| "It matches the base's parameter default — leave it worn" | A worn-but-undeclared shape resolves declared-or-zero, never from a default or a render. |
| "Proportionate for a non-shipped / trivial compose" | The recorded defects shipped on exactly such composes; non-shipping changes nothing the map checks. |
| "I scanned the FX myself — no delegation needed" | A clean scan is the map's *empty outcome*, not a waiver of the map: the same read done inside the delegation produces the artifact and the `RESIDUE: none — nothing routes out` line. A scan that leaves neither artifact nor `MAP SKIPPED: <reason>` line is the skip, however real the scan was. |

**Claiming the read is not running it.** The compose checkpoint takes one of three sanctioned forms: the `ReportShapeOverlap` RunLog path plus the named-residue list, the RunLog path plus `RESIDUE: none — nothing routes out`, or the literal line `MAP SKIPPED: <reason>` — always the operator's to see, never silent. A checkpoint with none of them is an unfinished compose. A genuine deviation takes the form in `workflow.md` §Deviating from a mandated step.

**What this skill does with them.** `map-outfit-shapes` commits the statics on unowned edges; what comes back here is what it could not. Runtime-owned residue forks on what the runtime edge *targets*:

- **Targets the overlapped garment itself** (a toggle that re-enables the mesh, shapes on the garment) — the **sanctioned delete** below resolves it structurally: a deleted GameObject has nothing for the FX to re-enable, and its bindings become silent runtime no-ops.
- **Targets a surviving mesh** (the body-shape coupling under the removed garment) — **residue this skill must not fix**: what ships there is the **parameter default**, so a static disable is edit-time cosmetics invisible to every gate and render — the default flip is `author-menu`'s, FX-layer surgery `own-gimmick`'s. Name it in the checkpoint (params, meshes, shapes, off values) with the line **the compose is not runtime-wearable until the routed follow-up lands**, and carry every OPEN call across with its evidence, for the operator or the play-mode build. Never a derivable default: with no operator channel, name it and stop.

- **Prefer the kisekae (undressed) base variant.** Many vendors ship a dedicated `<Name>_kisekae` prefab — body + underwear, no costume — beside the regular clothed base (`<Name>.prefab`); compose onto that and there is little to strip (`outfits.md`). If the vendor ships only a clothed base (or only shader variants of it), strip it here. A base locked in a complete *fixed* outfit with no toggle surface is the refuse case — ask for the kisekae variant.
- **Disable by default; delete where the FX can undo a disable.** A garment the map names overlapped *and* a runtime edge re-enables (the garment-targeting residue above) cannot be held off by a static disable — **delete its GameObject on the packed instance**, flagged to the operator like any contested call. Deleting a child of a packed prefab instance works and is **revertible**: Unity records it as a removed-GameObject override (the Overrides dropdown, or `PrefabUtility.GetRemovedGameObjects()[i].Revert()`), and the vendor asset on disk stays byte-identical — no unpack; the reparent no-op (`unity.md`) does not extend to deletes. Delete only meshes the map named, and record every removal in the checkpoint.
- **Report the FX the deletions strand.** A removed mesh's bindings are silent runtime no-ops — harmless, but dead weight the operator should know about. After deleting, run `CheckAvatar` + `ReportController` and name the now-useless FX sections: layers whose every binding targeted a removed mesh, params driving only those layers, and the menu controls behind them. Informational only — controller cleanup is `own-gimmick`'s surgery, a parameter-default flip `author-menu`'s.
- **Suppressing an unwanted piece of the mergeable itself** (the vendor ships style variants or optional accessories active — extra ears, a selectable twintail style): a parameter default decides what ships only for an edge an always-on layer actually drives (the runtime-owned fork above); a **statically-active** mesh ships active regardless of any default. Suppress with a **static disable** — or the sanctioned delete above, where an FX layer can undo a disable; a parameter-default flip is `author-menu`'s, never yours. Then check each piece's `activeInHierarchy` on the scene instance against intent, including the vendor's style selectors (they bake to *some* default state, not necessarily a coherent one), and name the built-clone confirmation in the step-7 handoff — the mechanical seam gates say nothing about this; they certified a double-eared compose as fine.
- **Partial use of a module carrying `MergeAnimators`:** stripping its menu leaves the merged layers' **default-active params** free to re-enable the meshes you just disabled at runtime (invisible to every gate). Don't need the merged controller? Remove it with the menu. Need part of it? That's an `own-gimmick` fork (decompile + surgery), not an in-scene strip.

### 5. Shape coherence (blendshape / baked)

A body morph (breast size, a proportion tweak) is a **same-set coherence value**: every mergeable on the base must reach it — **one value per morph**, the invariant whose authority is `reproportion` (*Realizing shapekeys*); honor it there, don't re-derive it. The map's `shared-morph` rows are these morphs' live carriers — a row kept-as-authored there is the value this reconcile holds every side to. The value lives in one of two forms:

- **Live** — a non-zero shape-key *value* on the body mesh. An MA `BlendshapeSync` mirrors it onto the identically-named shape on the mergeable at runtime — coherent automatically only where a sync exists. Many real mergeables carry none: there, confirm the mergeable carries the shapes and set the matching live weight yourself.
- **Baked** — folded into Basis by `shapekey_bake`. The bake leaves the morph block behind with its live weight zeroed, so there is **no in-scene signal** — the provenance stamp is the only truth.

**The baked read.** For each owned side (asset path under `Assets/…`, not `Assets/Vendor/…` — vendor sides are never baked and have no blend; skip them): resolve its co-located provenance blend — an **outfit** is base-first, `Blender/Outfits/<Base>/<Outfit>/<Outfit>.blend`; an **avatar** stays `Blender/Avatars/<Name>/<Name>.blend` — and read it via avatarprep **`report_stamps`** (`cli/report_stamps.py --in <blend>`, or `report_stamps(bpy.context.scene)` live over the Blender MCP). It groups each baked mesh under its owning armature (`armatures[].meshes[]`); meshes with no single owner fall to top-level `unbound`.

**Key the read by the side's own armature — never "every baked mesh in the blend."** A mergeable's blend also holds the appended fit-reference base body (`own-mergeable`), a second armature whose morphs a read-everything would fuse into the mergeable's. The handle: a **mergeable (Outfits)** is the entry named `Armature.<Outfit>` (the blend path's own leaf token — the `<Outfit>` name, not the `<Base>` folder segment it sits under); a **base (Avatars)** is the lone `Armature` entry — an `Armature.<Name>` lookup there matches nothing and silently drops the base's own morph.

**Collapse that entry's `meshes[]` to the side's obligation** — the coherence reasoning the tool leaves to this skill. Reduce each same-named baked shape over the meshes that *carry* it — absence is not disagreement (a shoe with no `Chest` is not a conflict) — to one value per morph. Carriers agree to ghost-kill tolerance (~`1e-6`, borrowed from `shapekey_bake`'s float-ghost slop): the tolerance bounds representation drift of the *same* value, not a budget for distinct ones, and this agreement check — not the bake — scopes it to **non-negative** cumulatives (a negative is the sanctioned fit-proxy below).

**Tripwires — surface, never reconcile past:**

- A **visible** disagreement (`0.80` vs `0.83`) is a different bake history: surface it, don't pick one.
- A `baked: None, corrupt: <repr>` entry is a broken stamp: set it aside; don't let it fault the side's other valid meshes.
- **No entry matches the handle** yet the report carries baked content (any `meshes[]` or `unbound` non-empty): stop — a rename/provenance mismatch, never an empty baked set. The only silent skip is a miss against a wholly-empty report (an unbaked side).
- A baked mesh in `unbound` **within the side's own blend** — bound to no armature, or ambiguously owned by ≥2 — is a binding anomaly.

If the side's collapsed obligation includes a baked morph: **flag it to the operator, then match it.** A baked morph's *live* weight is 0, so `BlendshapeSync` would drive the mergeable to 0 while the baked body shows the shape — **strip the `BlendshapeSync` for that shape and set the mergeable's live weight to the baked cumulative.** Top up with live weight **only upward** — Unity has no negative blendshapes, so a side baked *higher* than the target cannot be walked back. A **negative** baked cumulative is not a shortfall to top up: it's a **fit-time proxy** bake (`reproportion`'s opposite-morph substitution, standing in for an absent morph) — **flag-only, do not auto-reconcile** it as a same-named base obligation. (The practical rule the operator will already know: if you bake, bake to match.)

### 6. The operator's look

Fit is settled mechanically at step 3 (`CheckSeam`); what's left is cosmetic and the operator's.

- **Clipping / look — the operator's, not a verdict.** Does it clip, sit right, read as the vendor intended? `RenderAvatar` from the angles the check needs (`top` for hair seating, `bottom` for shoes) is a resolved-fit look for the operator (NDMF preview applied), not a baked-upload proof or an agent fit verdict; the operator's eye and a play-mode build are the bar.

### 7. Hand off

The mergeable's menu / parameters / animator merge at build, but this skill does **not** verify they cohere. Whether a menu pass is even needed forks on what the avatar already ships: a vendor base arrives **menu-complete** — menu / params / FX on the `VRCAvatarDescriptor`, where absent MA/VRCFury components is the normal vendor state, **not** an empty menu (`outfits.md`). If the operator only wants to exercise existing controls, that is a **play-mode drive of the shipped menu** (`verify.md`), not authoring — do not reach for `author-menu`. Flag an `author-menu` follow-up only for the **new** controls the operator asked for. Then ask the operator to eyeball the result: the spot-check is the real verification bar. A **play-mode build** is the operator's call at a suitable time, **not** a gate here — the runtime-owned residue's driven-state verify belongs to the skill it routed to (step 4).

For a **gimmick/behavior module**, the static integrity gates (step 3) prove placement didn't break it; that it still **fires** is an **emulator smoke** the operator drives in play mode — named as a handoff, the firing counterpart to the outfit's clipping look, not a gate here.

## Tools

Reach for these by role; open each to learn its exact entry point.

- **Unity MCP `execute_code`** — all in-scene work: drop the prefab, read the seam/scene-refs, repath a broken reference, disable or delete a conflicting mesh, set a static blendshape weight. Raw MA component edits via `SerializedObject`; no dedicated compose tool exists (and none is warranted — this is judgment, not mechanics).
- **`RenderAvatar`** (agent-tools, via `execute_code`) — the operator-facing resolved-fit look for step 6; contract and freshness rules in `unity-tools.md`. Never an agent fit verdict (`verify.md`) — fit is `CheckSeam`'s. Its `CaptureDiff` differential door is `map-outfit-shapes`' to drive, not this skill's.
- **avatarprep `report_stamps`** (Blender, via MCP or `cli/report_stamps.py`) — the baked-morph read in step 5, and also step 3's provenance routing: the same call returns each armature's `avatarprep_base`/ `avatarprep_state` pair alongside the bound-mesh `avatarprep_baked` map grouped **under its owning armature** (+ an `unbound` bucket); step 5 keys on the side's own armature handle and does the cross-mesh collapse. The provenance blend is the source of truth.
- **Modular Avatar / VRCFury** — the vendors' frameworks. This skill *drives* the seam they authored; it never re-authors it.
- **`CheckAvatar`** (agent-tools, via `execute_code`) — the step-3 broken-ref classifier: `PASS`/`CLASSIFY` with per-offender class + `clipAssetPath`. Inspection-only; you apply the remedy it routes to.
- **`ReportGimmick`** (agent-tools, via `execute_code`) — the gimmick-module integrity read at step 3: subtree topology (receivers, PB chains, constraint rigs, params) to diff a placed module against its standalone shape. Inspection-only.
- **`CheckSeam`** (agent-tools, via `execute_code`) — the step-3 mechanical fit gate; contract in `unity-tools.md`.
