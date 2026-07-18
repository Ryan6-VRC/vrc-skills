---
name: compose-mergeable
description: Use when placing a ready-made outfit, hair, accessory, or gimmick module (vendor or already-owned) onto an avatar base — "put this outfit on my avatar", "add this hair to the base", "compose/wear this mergeable". Not owning or creating a mergeable's geometry, and not adding a seam to a bare prefab (both own-mergeable); not cross-base refitting.
---

# Compose a mergeable onto an avatar base

Place one seam-authored mergeable (outfit / hair / accessory / gimmick module) onto an avatar base,
non-destructively. The mergeable already carries its own Modular Avatar / VRCFury seam; you **drop it in,
verify the seam resolves, de-conflict the meshes it replaces, and reconcile shape coherence** — then hand
off. The seam resolves at build (MA/VRCFury merge on a clone at upload/play); nothing here bakes it down.
A **gimmick/behavior module** (a prop, a contact / physbone / constraint system) composes on the same
spine but is gated on behavior integrity, not geometry — the fork is step 3, and steps 4–5 fall away.

**Source-agnostic.** A vendor mergeable and a mergeable produced by `own-mergeable` are treated
identically — that a correctly-owned mergeable composes here with zero special-casing is the proof
`own-mergeable` did its job. Never branch on where the prefab came from.

**Fit is gated mechanically where it can be; cosmetic look is the operator's.** For a mergeable that skins
across the humanoid skeleton (clothing), alignment is decided by a **mechanical seam check** (`CheckSeam`,
step 3) — a model can't judge fit from a render (`verify.md`). An offset-tolerant **bone-proxy** (hair, an
accessory bound to one bone) `CheckSeam` **refuses** to score: fit there is operator-positioned, not
bone-determined, and joins the cosmetic (clipping, wrong shape) as the operator's eye. So this skill's
programmatic job is: run cheap static **tripwires** for the *non-cosmetic silent* failures a human can't
eyeball, gate fit on the seam check where it scores, do the mechanical in-scene repairs, then get out of
the way so the operator looks. **"Merges without error" ≠ "composed"** — a wrong-base mergeable merges with
a clean console (MA silently auto-creates phantom bones), so a green console proves nothing.

**No operator to ask?** A gate you can't put to an operator is expected, not a blocker. A
dispatched worker or background job still **has a channel** — the dispatcher — so surface the
gate by ending the turn with `needs input:` and wait; a background job is not "no operator." Only
with no channel at all do you take the derivable defaults, and even then the disclosure leads the
report — every undecided call flagged at the top, never a silently minted convention (folder or
category placement especially).

## Scope — what this owns, and where it routes out

Owns: the cheap, non-destructive, **in-scene** work — drop, seam verification, scene-ref repath, mesh
de-conflict, blendshape/baked coherence. Does **not** choose or add seams, own geometry, or refit across
bases. When a compose needs any of those, do the in-scope part and **surface the boundary to the
operator** rather than improvising:

- **Bare mergeable** (armature but no MA/VRCFury attach component) → `own-mergeable`. This skill never
  *adds* a seam; it only verifies an authored one. Choosing MA vs VRCFury is `own-mergeable`'s job.
- **Wrong-base mergeable** (armature seam doesn't resolve — see step 3) → a **refit**, not a compose.
  Route to the refit path (roadmap: `docs/mochifitter.md`; or manual Blender work). Do not try to
  force it.
- **Mergeable missing a shape the base needs** (step 5 can't reconcile) → `own-mergeable` to bake it.
- **Menu / animator / parameter coherence** → `author-menu` (step 7). Required, but out of scope here.
  Step 4's runtime-owned residue routes there too: flipping a shipped parameter default changes the
  avatar's menu defaults — the operator's call, never composed in silently.
- **Gimmick/behavior module** → composed here whole, on the behavior-integrity gates of step 3. Editing
  its behavior — trim, param surgery, a with/without variant — is `own-gimmick`; grafting new behavior is
  `author-gimmick`. This skill places a finished module; it never re-authors one.

## The flow

Work on an **in-scene instance** of the avatar base. Converting the result to a prefab variant is the
operator's call, at the end.

### 1. Precondition — the mergeable is seam-authored

Confirm the mergeable prefab carries its own seam: MA `MergeArmature` / `BoneProxy`, or VRCFury
`ArmatureLink`. A bare prefab (armature, no attach component) is **out of scope** → route to
`own-mergeable`.

### 2. Drop

Instantiate the **standalone vendor/owned prefab** (never a placed instance) as a child of the avatar
root, at identity local transform. The prefab's **root transform is load-bearing** — place it unmodified
and **never normalize its scale or position** as cleanup: a vendor root scale like `0.9512` is authoring,
not mess, and normalizing it to `1:1:1` after placement manufactures a per-bone offset gradient that reads
as a gross misfit and bakes straight through (the merge is identity-preserving — `nondestructive.md`). A
mergeable authored for this base auto-targets the base's `Armature` — you do not wire the seam by hand.

### 3. Verify the seam — mechanical gates

All cheap and mechanical, each catching a silent failure a green console hides. Run them right after the
drop, before de-conflict or coherence: a wrong base caught here saves the wasted strip-and-reconcile of
steps 4–5.

**The module class forks the gates.** A mergeable that skins the humanoid skeleton (clothing; the
humanoid-weighted part of a body accessory) is gated on geometry — the bullets below. A **gimmick/behavior
module** (a world prop, a contact / physbone / constraint system, an accessory carrying behavior but **no
weighted humanoid bones**) gives `CheckSeam` nothing to score, so it REFUSEs — the **expected** path here,
not a misfit, **when the REFUSE names an abstain reason** (no humanoid bones / bare prop / proxy). A REFUSE
citing a seam-resolution or reflect/API failure is a tool break, class-independent — never waved off as
the gimmick case. Its seam anchors to one bone or the avatar root and its fit is authored; what a compose
silently breaks instead is **behavior integrity**, gated by two reads in place of `CheckSeam`:

- **`ReportGimmick`** — read the module's subtree topology (receivers, PB chains, constraint rigs, params)
  and compare it to the module's standalone shape: the drop should carry the whole system intact, and a
  piece left behind or a param that didn't come across shows against that baseline.
- **`CheckAvatar`** (the broken-ref bullet below, run the same way) — a re-root moves the paths the
  module's contacts / drivers / clips bind to; `CheckAvatar` names what the move left unresolved, routed by
  class exactly as for geometry.

Firing (does it trigger, latch, release) is **not gated here**: the module's author already proved it in
the emulator, so the compose confirms only that placement didn't break it statically, then names an
**emulator smoke** as the play-mode handoff (step 7) — consistent with step 6's operator's-call stance.
A cross-base placement is a refit, out of scope (`Scope`), so world-space contact re-verification never
arises in a compose. The geometry bullets below apply to the humanoid-skinned case; a gimmick module runs
only the two reads above plus the broken-ref and physbone-collider bullets.

- **Seam fit + resolution — `CheckSeam` (the mechanical gate).** `CheckSeam.Check(baseRoot, mergeableRoot)`
  reflects the seam's own MA/VRCFury bone mapping and gates the **world-space coincidence** of the
  mergeable's *weighted humanoid bones* against the base's (world-space, because a compensating root scale
  is legitimate authoring). A correctly authored mergeable duplicates the base armature, so those bones
  land coincident; a real offset is a misfit MA ships as-is and VRCFury snaps at bake. Because it reflects
  the real resolver, it subsumes a naive name-match: the wrong-base merge that MA hides by auto-creating
  phantom bones (`nondestructive.md`) — a clean console while the outfit skins to bones that never move —
  surfaces here as NOT-PASS or a won't-resolve REFUSE. Three outcomes, routed differently:
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
- **Provenance routing (owned mergeables only).** `CheckSeam` detects the misfit; the provenance stamps say
  *which side to fix*. For an owned mergeable (asset path under `Assets/…`, not `Assets/Vendor/…`), read its
  mirrored `(base, state)` via avatarprep **`report_stamps`** (Decision 2's mirror):
  - **Owned base** (own blend under `Assets/…`): read the base's `(base, state)` too. An exact mismatch, or
    a genuinely-absent stamp on an owned side, is a **loud may-block WARNING — write nothing**: a
    missing/mismatched *outfit* stamp is `own-mergeable`'s re-stamp-and-refile loop, a missing *base* stamp
    is `own-base`'s `stamp_base` seed (Decision 3) — route to whichever side is off.
  - **Vendor base** (under `Assets/Vendor/…`, no blend or stamp — expected): a vendor base is
    `unproportioned` by construction. A mergeable in state `unproportioned` is the blessed "own the outfit,
    not the base" case; a **`reshaped`** mergeable can't fit a stock base → route to `own-base` (own +
    reproportion the base). This is the same misfit `CheckSeam` flags as NOT-PASS — `reshaped` moves the
    rest pose without renaming bones — named at the stamp level so the fix routes to the right side.
- **Broken refs — classify with `CheckAvatar`, then route by class.** Run `CheckAvatar.Inspect(<avatar root>)`
  on the placed avatar: against the placed scene it names every MA scene ref and every clip/controller
  binding a rename left unresolved (`PASS`/`CLASSIFY`) — the whole reactive family included (`ShapeChanger`,
  `ObjectToggle`, `MaterialSetter`/`Swap`, `MeshDeleter`, `BlendshapeSync`, `BoneProxy`). The usual cause is
  a **renamed seam**: `own-base` may rename the primary body mesh (recommended `Body_Base`; vendors ship `Body_base`).
  CheckAvatar classifies and names; you route (a deliberately-null toggle target or a portability-redundant
  path where several point at one object is a legitimate non-offender — judge, don't blindly repath):
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
- **Physbone collider refs — relink null base-collider slots.** A placed physbone whose `colliders[]`
  holds a **null** slot collided against a *base-owned* collider the mergeable doesn't carry
  (`own-mergeable` leaves it null by design — the collider is the base's). Re-point each null at the
  base's collider on the physbone's anchor bone (`execute_code` on the placed instance; in-scene, no asset
  write) — left null, the physbone collides against nothing. Act on the null slot, not on provenance: a
  vendor mergeable has none, so this is a no-op for it.

### 4. De-conflict the meshes (quick pass)

A whole gimmick/behavior module replaces nothing and keeps all its layers — steps 4–5 don't apply to it
(a *partial* take is an `own-gimmick` fork, not a compose). The rest of this step is the geometry case.

A full outfit replaces base clothing; overlapping meshes clip. Disabling those meshes is the quick,
in-scope pass. But a base garment is often **coupled to body blendshapes** (`outfits.md`) — disable
the mesh alone and the pre-collapsed region it covered stays collapsed, a stuck shrink you won't see
until you look. The coupling lives in FX clips and MA `ShapeChanger` reactions, on a **body-morph mesh
that is not the one named `Body`** (identify it first — `map-outfit-shapes` step 1), and reads **weight
0 at edit time**, invisible to a scan. So whenever this step disables base clothing, **delegate to
`map-outfit-shapes` scoped to the disabled garments** (the full-avatar map stays opt-in). Two outputs
are required before the geometry-path compose is done, both geometry-path only — a gimmick module has
neither:

1. its **`ReportShapeOverlap` resolution artifact** — the per-shape table (reaction / weight /
   resolved-target / same-vertex overlap / MISMATCH), whose RunLog records the census ran; and
2. the **named runtime-owned residue** (the runtime-ownership bullet below).

**"No coupling" is a conclusion, not a default** — it holds only when the reaction read *and* the FX
read both come up empty; a 0-weight audit over a driven mesh is residue to name, never absence.

**Each MISMATCH row's resolved-target is a defeasible presumption — discharge it, never eyeball it.** A
worn-but-undeclared shape resolves toward its target (declared value; a `Delete` bakes to 100;
undeclared → 0) unless you **override with a named `CaptureDiff` differential** showing the target value
defects — the base foot piercing the outfit sole, a gap, a clip over the region. **A render *look* is
never override currency** (it reads clean over a real clip). Accept or override, both logged; an
un-dispositioned MISMATCH stays **OPEN**. It cuts both ways: a footwear outfit that declares no foot-pose
shape (`Heel_Feet`/`Foot_heel`) resolves it to 0, releasing a base heel a scan left worn (the exact
`Heel_Feet=100`-kept-on-a-render failure); a heeled outfit that *forgot* the declaration also resolves to
0, overridden back to 100 only when a `CaptureDiff` at 0 shows the flat foot piercing the sole. Inherits
`CaptureDiff`'s caveats (empty-diff ≠ invisible, freshness certified — `verify.md`).

- **Prefer the kisekae (undressed) base variant.** Many vendors ship a dedicated `<Name>_kisekae`
  prefab — body + underwear, no costume — beside the regular clothed base (`<Name>.prefab`); compose
  onto that and there is little to strip (`outfits.md`). If the vendor ships only a clothed base (or
  only shader variants of it), strip it here. A base locked in a complete *fixed* outfit with no
  toggle surface is the refuse case — ask for the kisekae variant.
- **Runtime ownership decides whether a static edit ships — act statically only where statics hold.**
  An always-on FX layer (weight 1, WD ON) gated on an expression parameter re-applies the garment's
  `m_IsActive` and coupled shapes every frame: what ships is the **parameter default**, so a static
  disable there is edit-time cosmetics, invisible to every edit-time gate and render (`outfits.md`
  §The FX controller). The scoped `map-outfit-shapes` read carries each edge's runtime owner: commit
  the statics on unowned edges; everything runtime-owned is **residue this skill must not fix** — the
  default flip is `author-menu`'s, FX-layer surgery `own-gimmick`'s. Name it in the checkpoint
  (params, meshes, shapes, off values) with the line **the compose is not runtime-wearable until the
  routed follow-up lands**. Never a derivable default: with no operator channel, name it and stop.
- **Disable, never delete** — a later optimizer strips unused mesh; disabling is reversible. The
  exception is an **operator-sanctioned** delete (a gimmick-subtree strip, a dangling menu item): it
  requires **unpacking** the vendor prefab instance in-scene first (a packed instance no-ops structural
  deletes — `unity.md`), which is fine — the build unpacks a clone regardless and the vendor asset on
  disk stays byte-identical.
- **A disable is safe when the outfit fills the same coverage role — commit those.** Role is purpose
  and coverage, never name or exact class: spats, a swimsuit bottom, or a leotard fill the
  underwear-bottom slot; a swimsuit top or a wrap fills the bra's — but a shirt or sweater does not
  (right region, wrong coverage: loose over formed); a stockinged outfit fills the base stockings',
  outfit shoes the base shoes'; the costume under a full outfit is the plain case. Judge per slot, across **both layers**
  (base stockings overlap a stockinged outfit as much as the base dress does). Where no high-confidence
  role match exists and no legible mapping drives the value (the settled case below), fall through to
  evidence: **default keep**, and certify it with a `CaptureDiff` toggle-diff — toggle the element
  off/on and exact-compare the pair over the region in question. A **non-empty diff** over that region
  shows the element drawing where it's questioned (a proven clip) — hide only under a garment that
  credibly covers in motion (form-fitting), else keep and flag the call OPEN. An **empty diff with
  freshness certified** proves only **sampled-view pixel immateriality** — that toggling the element
  changed no composited pixels from that angle — NOT that the renderer is invisible: an element
  coplanar with, or same-material as, geometry beneath it draws yet diffs empty. Treat empty as
  harmless-here; where actual renderer visibility must be certified, keep the call OPEN. A diff whose
  freshness is not certified proves nothing — OPEN. Coverage never creates a hide obligation.
  An eyeballed render is no proof, and
  `RenderAvatar` is an operator-facing look, not an agent clipping verdict (`verify.md`). **Enumerate**
  the roleless unknowns (bandages, wings, creature parts) for the operator; never disable on a
  low-confidence spatial guess. A limb that
  **vanishes** when a base
  garment goes is a coupled blendshape — the `map-outfit-shapes` reconcile, not a clipping call.
- **Shrink/hide over shared vertices are almost never both on** (`outfits.md`; reconciled in
  `map-outfit-shapes`). Hiding a base mesh should flip its paired `Shrink_*` off — the pair travels
  together — and a kept outfit `ShapeChanger` shrinking the *same* vertices double-subtracts to an
  inverted mesh if the base shape stays worn (invisible to the sheet and every `Check*`). Absence of the
  shape on the outfit's own `ShapeChanger` is the tell it doesn't need it.
- **Partial use of a module carrying `MergeAnimators`:** stripping its menu leaves the merged layers'
  **default-active params** free to re-enable the meshes you just disabled at runtime (invisible to
  every gate). Don't need the merged controller? Remove it with the menu. Need part of it? That's an
  `own-gimmick` fork (decompile + surgery), not an in-scene strip.

**Before the checkpoint, every judgment-call keep or release above — a kept live weight, a kept
should-be-hidden layer, a released shrink — gets its mechanical check.** A value the outfit's own
`ShapeChanger` or FX layer legibly drives is already settled *as mechanism* — the mapping is
authoritative over any render; spend nothing re-checking the value it drives. But an FX layer drives
to whatever its parameter says, so the shipped **default** is still the compose's to judge when the
outfit changed what's worn — and evidence settles only the avatar it lives on: another avatar's outfit
declaring a value transfers nothing. For the rest: `CaptureDiff` toggling the element, angle chosen from
where the element lives (feet read from `bottom`); a keep defended as "covered" takes a `CaptureDiff`
toggle-diff over the questioned region. A non-empty diff proves the element materially visible — argue
the keep/release from the diff region, never from magnitude; an empty diff with freshness certified
proves it immaterial (`verify.md`).

When keep and hide trade risks, the order is **exposure > hole > clip**: an uncovered avatar is worst, a
visible absence (a hollow shoe glimpsed through a gap) next, a clip cheapest — the one failure the diff
proves statically and a play-mode build catches in motion, so defaults push residual risk toward clip.
Perf is no tiebreaker: a kept occluded layer's triangles are the optimizer's, not a hide obligation. Two
hard edges: **never shrink or hide body geometry (a foot, the torso) that no vendor authoring drives** —
garment layers are yours to disable, the body underneath is not; hole risk is motion-unknowable, so
propose it with evidence instead — and never *close* a motion-dependent call:
apply the ranking's default and list the call **OPEN** in the checkpoint with its diff/occlusion counts,
for the operator or the play-mode build.

### 5. Shape coherence (blendshape / baked)

A body morph (breast size, a proportion tweak) is a **same-set coherence value**: every mergeable on the
base must reach it — **one value per morph**, the invariant whose authority is `reproportion` (*Realizing
shapekeys*); honor it there, don't re-derive it. The value lives in one of two forms:

- **Live** — a non-zero shape-key *value* on the body mesh. An MA `BlendshapeSync` mirrors it onto the
  identically-named shape on the mergeable at runtime — coherent automatically only where a sync exists.
  Many real mergeables carry none: there, confirm the mergeable carries the shapes and set the matching
  live weight yourself.
- **Baked** — folded into Basis by `shapekey_bake`. The bake leaves the morph block behind with its live
  weight zeroed, so there is **no in-scene signal** — the provenance stamp is the only truth.

**The baked read.** For each owned side (asset path under `Assets/…`, not `Assets/Vendor/…` — vendor
sides are never baked and have no blend; skip them): resolve its co-located provenance blend — an
**outfit** is base-first, `Blender/Outfits/<Base>/<Outfit>/<Outfit>.blend`; an **avatar** stays
`Blender/Avatars/<Name>/<Name>.blend` — and read it via avatarprep **`report_stamps`**
(`cli/report_stamps.py --in <blend>`, or `report_stamps(bpy.context.scene)` live over the Blender MCP).
It groups each baked mesh under its owning armature (`armatures[].meshes[]`); meshes with no single
owner fall to top-level `unbound`.

**Key the read by the side's own armature — never "every baked mesh in the blend."** A mergeable's blend
also holds the appended fit-reference base body (`own-mergeable`), a second armature whose morphs a
read-everything would fuse into the mergeable's. The handle: a **mergeable (Outfits)** is the entry named
`Armature.<Outfit>` (the blend path's own leaf token — the `<Outfit>` name, not the `<Base>` folder
segment it sits under); a **base (Avatars)** is the lone `Armature` entry — an `Armature.<Name>` lookup
there matches nothing and silently drops the base's own morph.

**Collapse that entry's `meshes[]` to the side's obligation** — the coherence reasoning the tool leaves
to this skill. Reduce each same-named baked shape over the meshes that *carry* it — absence is not
disagreement (a shoe with no `Chest` is not a conflict) — to one value per morph. Carriers agree to
ghost-kill tolerance (~`1e-6`, borrowed from `shapekey_bake`'s float-ghost slop): the tolerance bounds
representation drift of the *same* value, not a budget for distinct ones, and this agreement check — not
the bake — scopes it to **non-negative** cumulatives (a negative is the sanctioned fit-proxy below).

**Tripwires — surface, never reconcile past:**

- A **visible** disagreement (`0.80` vs `0.83`) is a different bake history: surface it, don't pick one.
- A `baked: None, corrupt: <repr>` entry is a broken stamp: set it aside; don't let it fault the side's
  other valid meshes.
- **No entry matches the handle** yet the report carries baked content (any `meshes[]` or `unbound`
  non-empty): stop — a rename/provenance mismatch, never an empty baked set. The only silent skip is a
  miss against a wholly-empty report (an unbaked side).
- A baked mesh in `unbound` **within the side's own blend** — bound to no armature, or ambiguously owned
  by ≥2 — is a binding anomaly.

If the side's collapsed obligation includes a baked morph: **flag it to the operator, then match it.** A
baked morph's *live* weight is 0, so `BlendshapeSync` would drive the mergeable to 0 while the baked body
shows the shape — **strip the `BlendshapeSync` for that shape and set the mergeable's live weight to the
baked cumulative.** Top up with live weight **only upward** — Unity has no negative blendshapes, so a side
baked *higher* than the target cannot be walked back. A **negative** baked cumulative is not a shortfall
to top up: it's a **fit-time proxy** bake (`reproportion`'s opposite-morph substitution, standing in for
an absent morph) — **flag-only, do not auto-reconcile** it as a same-named base obligation. (The
practical rule the operator will already know: if you bake, bake to match.)

### 6. The operator's look

Fit is settled mechanically at step 3 (`CheckSeam`); what's left is cosmetic and the operator's.

- **Clipping / look — the operator's, not a verdict.** Does it clip, sit right, read as the vendor
  intended? `RenderAvatar` from the angles the check needs (`top` for hair seating, `bottom` for shoes) is
  a resolved-fit look for the operator (NDMF preview applied), not a baked-upload proof or an agent fit
  verdict; the operator's eye and a play-mode build are the bar.

### 7. Hand off

The mergeable's menu / parameters / animator merge at build, but this skill does **not** verify they
cohere. Whether a menu pass is even needed forks on what the avatar already ships: a vendor base
arrives **menu-complete** — menu / params / FX on the `VRCAvatarDescriptor`, where absent MA/VRCFury
components is the normal vendor state, **not** an empty menu (`outfits.md`). If the operator only wants
to exercise existing controls, that is a **play-mode drive of the shipped menu** (`verify.md`), not
authoring — do not reach for `author-menu`. Flag an `author-menu` follow-up only for the **new**
controls the operator asked for. Then ask the operator to eyeball the result: the spot-check is the real verification
bar. A **play-mode build** is the operator's call at a suitable time, **not** a gate here — the
runtime-owned residue's driven-state verify belongs to the skill it routed to (step 4).

For a **gimmick/behavior module**, the static integrity gates (step 3) prove placement didn't break it;
that it still **fires** is an **emulator smoke** the operator drives in play mode — named as a handoff,
the firing counterpart to the outfit's clipping look, not a gate here.

## Tools

Reach for these by role; open each to learn its exact entry point.

- **Unity MCP `execute_code`** — all in-scene work: drop the prefab, read the seam/scene-refs, repath a
  broken reference, disable a conflicting mesh, set a static blendshape weight. Raw MA component edits via
  `SerializedObject`; no dedicated compose tool exists (and none is warranted — this is judgment, not
  mechanics).
- **`RenderAvatar`** (agent-tools, via `execute_code`) — drives the Scene View to render **one** avatar
  in isolation, headlight-lit, **NDMF preview-resolved** (reactive fit applied), from named axis angles
  to a temp contact-sheet PNG. An **operator-facing** resolved-fit look (steps 4 and 6) — not a
  baked-upload proof and not an agent fit verdict (`verify.md`); fit is gated mechanically (`CheckSeam`).
  Grab in a separate call from any edit — a same-call edit either settles in-call or the grab FAILs
  transiently (re-grab), never a silent stale sheet; OK carries `gate=armed` (rendered-current) or
  `gate=exempt` (nothing to certify). Its `CaptureDiff` door carries step 4's decision checks
  (`unity-tools.md`).
- **avatarprep `report_stamps`** (Blender, via MCP or `cli/report_stamps.py`) — the baked-morph read in
  step 5, and also step 3's provenance routing: the same call returns each armature's `avatarprep_base`/
  `avatarprep_state` pair alongside the bound-mesh `avatarprep_baked` map grouped **under its owning
  armature** (+ an `unbound` bucket); step 5 keys on the side's own armature handle and does the
  cross-mesh collapse. The provenance blend is the source of truth.
- **Modular Avatar / VRCFury** — the vendors' frameworks. This skill *drives* the seam they authored; it
  never re-authors it.
- **`CheckAvatar`** (agent-tools, via `execute_code`) — the step-3 broken-ref classifier: `PASS`/`CLASSIFY`
  with per-offender class + `clipAssetPath`. Inspection-only; you apply the remedy it routes to.
- **`ReportGimmick`** (agent-tools, via `execute_code`) — the gimmick-module integrity read at step 3:
  subtree topology (receivers, PB chains, constraint rigs, params) to diff a placed module against its
  standalone shape. Inspection-only.
- **`CheckSeam`** (agent-tools, via `execute_code`) — the step-3 mechanical fit gate:
  `Check(baseRoot, mergeableRoot)` reflects the MA/VRCFury seam mapping and gates world-space coincidence
  of weighted humanoid bones → PASS / NOT-PASS / REFUSE, before any render; inspection-only.
