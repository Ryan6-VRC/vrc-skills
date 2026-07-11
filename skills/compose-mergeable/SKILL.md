---
name: compose-mergeable
description: Use when placing a ready-made outfit, hair, or accessory (vendor or already-owned) onto an avatar base — "put this outfit on my avatar", "add this hair to the base", "compose/wear this mergeable". Not owning or creating a mergeable's geometry, and not adding a seam to a bare prefab (both own-mergeable); not cross-base refitting.
---

# Compose a mergeable onto an avatar base

Place one seam-authored mergeable (outfit / hair / accessory) onto an avatar base, non-destructively.
The mergeable already carries its own Modular Avatar / VRCFury seam; you **drop it in, verify the seam
resolves, de-conflict the meshes it replaces, and reconcile shape coherence** — then hand off. The seam
resolves at build (MA/VRCFury merge on a clone at upload/play); nothing here bakes it down.

**Source-agnostic.** A vendor mergeable and a mergeable produced by `own-mergeable` are treated
identically — that a correctly-owned mergeable composes here with zero special-casing is the proof
`own-mergeable` did its job. Never branch on where the prefab came from.

**Fit is gated mechanically; cosmetic look is the operator's.** Alignment and seam correctness are decided
by a **mechanical seam check** (`CheckSeam`, step 6) — a model can't judge fit from a render (`verify.md`).
The rest (clipping, wrong shape) is visual and the operator's eye is the bar, so this skill's programmatic
job is: run cheap static **tripwires** for the *non-cosmetic silent* failures a human can't eyeball, gate
fit on the seam check, do the mechanical in-scene repairs, then get out of the way so the operator looks.
**"Merges without error" ≠ "composed"**
— a wrong-base mergeable merges with a clean console (MA silently auto-creates phantom bones), so a
green console proves nothing.

**No operator to ask?** A gate you can't put to an operator (a dispatched worker, a headless run)
is expected, not a blocker: surface it to whoever dispatched you and wait. With no channel at all,
take the derivable defaults, flag every undecided call loudly at the top of your report, and never
silently mint a convention — folder or category placement especially.

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

### 3. Verify the seam resolves (static tripwires)

Two seams to resolve, plus the owned-side collider gap to close — all cheap, each catching a silent
failure a green console hides.

- **Provenance fit gate (owned mergeables only).** For an owned mergeable (asset path under `Assets/…`,
  not `Assets/Vendor/…`), read its own mirrored `(base, state)` via avatarprep **`report_stamps`**
  (Decision 2's mirror), then check it against the base it is landing on — which forks on whether that
  base is owned or vendor:
  - **Owned base** (own blend under `Assets/…`): read the base's `(base, state)` too. An exact mismatch,
    or a genuinely-absent stamp on an owned side, is a **loud may-block WARNING — write nothing**. This is
    not a compose-side repair: a missing/mismatched *outfit* stamp is `own-mergeable`'s re-stamp-and-refile
    loop, a missing *base* stamp is `own-base`'s `stamp_base` seed (Decision 3) — route to whichever side is off.
  - **Vendor base** (under `Assets/Vendor/…`, no blend and no stamp — expected, not an error): a vendor base
    is `unproportioned` by construction. If the mergeable's **state is `unproportioned`**, the fit is
    plausible — the blessed "own the outfit, not the base" case — so fall through to the hit-rate check to
    confirm the base *family*. If the mergeable's state is **reshaped** (≠ `unproportioned`), that is the real
    mismatch a stock base can't satisfy *and the hit-rate can't see* (reproportion doesn't rename bones, so
    names still resolve while the rest pose is wrong): **loud may-block WARNING, route to `own-base`** (own +
    reproportion the base), not `own-mergeable`.
  A **vendor mergeable** carries no stamp and skips this gate outright, falling through to the hit-rate check
  below — which is why that check stays as the vendor/confirmatory fallback.
- **Armature seam — core-body-bone hit-rate.** Do the mergeable's core humanoid bones resolve by name
  against the base armature? A mergeable authored for *this* base matches by contract. A **wrong-base**
  mergeable matches only a handful and MA auto-creates the rest as phantom bones (`nondestructive.md`) —
  it merges with **no error** while the outfit skins to bones that never move. If the core hit-rate is catastrophic, this is
  the wrong base: **fail loud, surface, route to refit** (step "Scope"). Do not repair it — MA's own
  adjust-names + reset-position can rough-fit it, but that is a refit and out of scope.
- **Broken refs — classify with `CheckAvatar`, then route by class.** Run `CheckAvatar.Inspect(<avatar root>)`
  on the placed avatar: against the placed scene it names every MA scene ref and every clip/controller
  binding a rename left unresolved (`PASS`/`CLASSIFY`) — the whole reactive family included (`ShapeChanger`,
  `ObjectToggle`, `MaterialSetter`/`Swap`, `MeshDeleter`, `BlendshapeSync`, `BoneProxy`). The usual cause is
  the **renamed seam**: `own-base` normalizes the primary body mesh to `Body_Base`, vendors ship `Body_base`.
  CheckAvatar classifies and names; you route (a deliberately-null toggle target or a portability-redundant
  path where several point at one object is a legitimate non-offender — judge, don't blindly repath):
  - **`MA-scene-ref`** → **repath in-scene**: retarget the reference to the renamed object — a scene edit,
    **no asset write**; non-aborting.
  - **`clip-binding`** → asset surgery, routed by the offender's **`clipAssetPath`** (not its scene `path`,
    which always looks writable): an **owned/writable** `.anim` is repathed **inline** (the
    `OwnControllerClips → RepathClips` clip phase, `unity.md` UC2); an **unowned vendor** clip (`clipAssetPath`
    under `Assets/Vendor/`|`Packages/`) needs a geometry round-trip compose can't do — **abort the compose and
    route to `own-mergeable`**.
- **Physbone collider refs — relink null base-collider slots.** A placed physbone whose `colliders[]`
  holds a **null** slot collided against a *base-owned* collider the mergeable doesn't carry
  (`own-mergeable` leaves it null by design — the collider is the base's). Re-point each null at the
  base's collider on the physbone's anchor bone (`execute_code` on the placed instance; in-scene, no asset
  write) — left null, the physbone collides against nothing. Act on the null slot, not on provenance: a
  vendor mergeable has none, so this is a no-op for it.

### 4. De-conflict the meshes (quick pass)

A full outfit replaces base clothing; overlapping meshes clip. Disabling those meshes is the quick,
in-scope pass. But a base garment is often **coupled to body blendshapes** (`outfits.md`) — disable
the mesh alone and the pre-collapsed body region it covered stays collapsed, a missing limb you won't
see until you look. This step commits the mesh disables only; the coupled-blendshape reconcile is the
opt-in **`map-outfit-shapes`** skill. Flag that follow-up whenever you disable a coupled garment —
don't run the full reconcile inline unless the operator asks, and don't silently ship a half-strip.

- **Prefer the kisekae (undressed) base variant.** Many vendors ship a dedicated `<Name>_kisekae`
  prefab — body + underwear, no costume — beside the regular clothed base (`<Name>.prefab`); compose
  onto that and there is little to strip (`outfits.md`). If the vendor ships only a clothed base (or
  only shader variants of it), strip it here. A base locked in a complete *fixed* outfit with no
  toggle surface is the refuse case — ask for the kisekae variant.
- **Disable, never delete.** A later optimizer strips unused mesh; disabling is reversible, deletion is
  not.
- **Commit only the unambiguous disables** — underwear and costume under a full outfit, across **both
  layers** (base stockings overlap a stockinged outfit as much as the base dress does). **Enumerate**
  the uncertain overlaps (bandages, shoes, wings, creature parts) for the operator; do not disable on a
  low-confidence spatial guess. Judge overlap by garment coverage and role, not names; `RenderAvatar` is an
  operator-facing look, not an agent clipping verdict (`verify.md`). A limb that **vanishes** when a base
  garment goes is a coupled blendshape — the `map-outfit-shapes` reconcile, not a clipping call.

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

### 6. Fit gate — mechanical first, then the operator's eyes

Bone-*name* resolution is step 3; this is whether the resolved seam *sits right*. **The fit gate is
mechanical, not a render read** (`verify.md`).

- **Seam alignment — `CheckSeam` (the agent fit gate).** It compares the mergeable's bones against the
  base's matched bones in **world space** (a compensating root scale is legitimate authoring, so
  world-space is the honest frame) and verdicts on **spread and direction-uniformity**: a *uniform*
  translation across all bones is possibly benign (the mesh may carry an equal-and-opposite offset), while
  *differing* magnitude or direction is a mechanically-certain misfit. It gates **before any render**, and
  an agent-modified root transform is itself a flag. A large or non-uniform delta is a **refit signal** —
  surface it, route out (`Scope`), don't force it; a genuine small misfit you correct with a **deliberate,
  flagged, `CheckSeam`-re-verified** transform edit, never the reflexive normalization step 2 forbids.
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
controls the operator asked for (and a `map-outfit-shapes` follow-up if step 4 left coupled blendshapes
unreconciled). Then ask the operator to eyeball the result: the spot-check is the real verification
bar. A **play-mode build** is the operator's call at a suitable time, **not** a gate here.

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
  Grab in a separate call from any edit — a same-call grab shows the pre-edit proxy; the summary's
  `note=` flags an in-flight rebuild but cannot catch the same-call case.
- **avatarprep `report_stamps`** (Blender, via MCP or `cli/report_stamps.py`) — the baked-morph read in
  step 5, and also step 3's provenance fit gate: the same call returns each armature's `avatarprep_base`/
  `avatarprep_state` pair alongside the bound-mesh `avatarprep_baked` map grouped **under its owning
  armature** (+ an `unbound` bucket); step 5 keys on the side's own armature handle and does the
  cross-mesh collapse. The provenance blend is the source of truth.
- **Modular Avatar / VRCFury** — the vendors' frameworks. This skill *drives* the seam they authored; it
  never re-authors it.
- **`CheckAvatar`** (agent-tools, via `execute_code`) — the step-3 broken-ref classifier: `PASS`/`CLASSIFY`
  with per-offender class + `clipAssetPath`. Inspection-only; you apply the remedy it routes to.
- **`CheckSeam`** (agent-tools, via `execute_code`) — the step-6 mechanical fit gate: per-bone world-space
  delta between mergeable and base + a spread/direction-uniformity verdict, gating before any render;
  inspection-only.
