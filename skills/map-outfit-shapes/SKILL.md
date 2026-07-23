---
name: map-outfit-shapes
description: Use when mapping how a body's blendshapes couple to its clothing meshes — hiding base clothing under a composed outfit, merging pieces from two outfits on one base, closing a toggle's dependencies, or checking body-morph coherence. The shape↔mesh interaction map; not composing an outfit (compose-mergeable) or authoring menus (author-menu).
---

# Map how an outfit interacts with a body's shapes

Produce the map of how an avatar's **body blendshapes couple to its meshes** — which garment drives which body shape, to what worn and off values, and which morphs several meshes must agree on — then act on it. The map is the reusable core; hiding overlapped clothing, closing a toggle, and checking coherence are all reads of it.

**A reasoning task, not a parse.** Creators wire FX layers, VRCFury features, MA reactions, and blendshape names every which way; no deterministic script maps them. You read the graph across those idioms and reason — the method below is authority order and fallbacks built for exactly that variety.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## Scope

Owns: producing the interaction map, and the in-scene acts that consume it (disable an overlapped mesh, set a body shape to its off value). Read-first and non-destructive — disable never delete, weights are reversible sets. Does **not** compose/place the outfit (`compose-mergeable`), author menu controls (`author-menu`), or reconcile proportions (`reproportion`) — it *feeds* those.

**Scoped by caller.** The full-avatar map is slow and opt-in. `compose-mergeable`'s de-conflict invokes this skill on every base-clothing strip, scoped to just the garments it disables — map their edges, release their coupled shapes, return.

## The map

A table of **edges**, each carrying its **source** and **confidence** — the sources vary and disagree, so an edge without its provenance can neither be trusted nor rechecked:

- **Coupling edge** — `garment mesh → body blendshape(s) it drives`, with the **worn value** and the **off/removed value** (e.g. `underwear_stocking → Shrink_stocking: worn 100, off 0`).
- **Shared-morph edge** — a body morph several meshes must hold at one value (breast size, a proportion tweak): the value and its carriers.
- **Toggle edge** — an existing FX/MA/VRCFury control → what it drives (mesh active-state + shape values).
- **Source / confidence** — `FX-clip | MA/VRCFury-reaction | naming-hint | asked-user | visual`,
  high→low authority (below).
- **Runtime owner** — what drives the edge's target at runtime: `FX-layer (← param ← expression
  default) | none`. Decides whether a static apply ships (§Deconflict).

Hold it in-context as you work; write it to `Assets/Agent/Scratch/` only when a later session or a human will reuse it.

## Building the map

### 1. Inventory

Identify the body-morph mesh(es) — the ones carrying the coupling cage (`Shrink_*`/`Breast*`/`Hip*`/ `Stocking*`), **not** the mesh named `Body`, which by VRChat convention is the viseme mesh (the descriptor's `VisemeSkinnedMesh`) and often carries no cage (`outfits.md`). Both can be full-body skinned, so humanoid weighting can't disambiguate — the cage's shapes do, and during de-conflict the outfit's `ShapeChanger` targets name the mesh outright. The cage may span more than one mesh (identify the set) or coincide with the viseme mesh. Enumerate every blendshape on the body-morph mesh(es), and every garment mesh: the base's own clothing layers **and** every piece of each composed outfit. This is the surface you reason over.

### 2. Resolve each edge in the authority order

Follow the base-coupling authority order (`outfits.md` §The FX controller), reading each tier with its tool: **FX clips** (`ReportController` / `ReportClip`) over **MA/VRCFury reactions** on the composed pieces (`AgentInspector`) over **naming** (a hint, never acted on alone) over **asking the user** (first-class when the graph is silent — a garment with no declared coupling has none until confirmed; don't invent one).

**Reading a `ShapeChanger` raw** (`AgentInspector` / SerializedProperty): its `ShapeChangeType` prints as an enum index — **Delete=0, Set=1** — so a bare `enum[0]` is *Delete* (geometry deletion), the more consequential mode, not the harmless-looking default. Resolve the name before acting on it.

**Vision is a check, not a source.** If the graph and the user leave an edge open, `RenderAvatar` confirms it only by **before/after comparison** — the shape worn vs. zeroed, the mesh on vs. off; read the *difference*, never a single capture. Vision confirms a hypothesis, it doesn't originate one.

### 3. Emit

The edge table, every edge tagged with its source and confidence. Low-confidence edges are flagged, not hidden.

## Applications — acting on the map

### Deconflict & merge — the overlap set

Overlap is **any clothing source covering a region another source also covers** — base-under-outfit and outfit-under-outfit are one problem:

- **Outfit on a clothed base** — the base garments the outfit's coverage replaces.
- **Merge pieces from two outfits** ("top from X, bottom from Y") — each outfit often ships full-body pieces, so the pieces you did *not* ask for from each (X's bottom, Y's top) are the overlap set. Watch for two kept pieces driving **one body shape to different values** — a coherence conflict; surface it, don't silently pick.

Find the overlap set by **coverage reasoning**: a base garment is in the set when the outfit covers its region — whether it hides *under* the outfit or clips *over* it. "Wear only the outfit" means only the outfit's clothing remains, so **a base garment still visible over the outfit is in the set, not exempt** — don't read "still visible" as "additive." A coarse `Renderer.bounds` AABB test (`Bounds.Intersects`, a few lines of `execute_code`) is a weak prefilter only — a full garment's AABB overlaps almost everything, so a hit means "look here," never proof.

**A disable is safe when the outfit fills the same coverage role — commit those.** Role is purpose and coverage, never name or exact class: spats, a swimsuit bottom, or a leotard fill the underwear-bottom slot; a swimsuit top or a wrap fills the bra's — but a shirt or sweater does not (right region, wrong coverage: loose over formed); a stockinged outfit fills the base stockings', outfit shoes the base shoes'; the costume under a full outfit is the plain case. Judge per slot, across **both layers** (base stockings overlap a stockinged outfit as much as the base dress does). **Enumerate** the roleless unknowns (bandages, wings, creature parts) for the operator; never disable on a low-confidence spatial guess.

Where the graph is silent on whether the outfit covers a region, settle it with the **coverage question, not an occlusion one**: turn the base piece *off* and check whether the outfit leaves that region **exposed or gapped** (`RenderAvatar` before/after, §2). Exposure → the outfit doesn't cover it (keep it, or ask); clean coverage → the base piece is a hidden overlap (strip it). Asking "is the base garment still visible?" is the trap — an over-layered garment is visible *because* it is the thing to remove.

Then, per overlapped garment: **disable the mesh** (never delete) and **set its coupled body shapes to their off values** from the map. A limb that **vanishes** when a base garment goes is a coupled shape left worn — the reconcile below, not a clipping call.

**"No coupling" is a conclusion, not a default** — it holds only when the reaction read *and* the FX read both come up empty; a 0-weight audit over a driven mesh is residue to name, never absence.

#### The census — `ReportShapeOverlap`, not a hand-listed set

Pass the body-morph mesh **and the outfit root** — reaction ingestion is gated on that second argument. Omit it and the analysed set silently narrows to caller-passed ∪ worn-nonzero, dropping **exactly the weight-0 reactions** the census exists to surface; the summary's `reacted=0` is the tell. With it, the tool reads the outfit's `ShapeChanger` reactions itself — those targeting *this* mesh; rows aimed at a sibling mesh are filtered out, so their absence is not drift — and emits the resolution table: per shape, its reaction (`Set=<v>`/`Delete`/none), current weight, **resolved-target** (declared value; a `Delete` bakes to 100; undeclared → 0), same-vertex overlap (the double-subtraction locator,
`|A∩B| / min`), and a **MISMATCH** on any worn-but-undeclared shape.

**`MISMATCH` is `worn ∧ undeclared`, never `current ≠ resolved-target`.** A reaction-declared row is never flagged however far its edit-time weight sits from its target, because the reaction owns it at runtime; reading the column as a diff manufactures offenders the build resolves on its own.

Two cells are **not dispositionable**: two reactions declaring different `(type, value)` for one shape render `CONFLICT: …` with resolved-target `conflict`, and an unmodelled `ShapeChangeType` renders `UNKNOWN(n)`. Neither has a presumption to discharge — **surface it, never pick**. `CONFLICT` is the merge case above (two kept pieces driving one body shape to different values) caught mechanically.

A name in the analysed set that isn't on the mesh reports **`MISSING`**, and the rest still analyse. When it's a *reaction-targeted* name, that is the finding: a `ShapeChanger` still pointing at a renamed or deleted shape.

Add the FX-clip-tier co-active shapes the tool can't see (§2) to the set you pass. It reports; you rule — and a shape that is neither overlapped nor coupled to a garment you disabled is independent: appearing in the table is not a reason to touch it. Its RunLog records that the census ran.

**Each MISMATCH row's resolved-target is a defeasible presumption — discharge it, never eyeball it.** A worn-but-undeclared shape resolves toward its target unless you **override with a named `CaptureDiff` differential** showing the target value defects — the base foot piercing the outfit sole, a gap, a clip over the region. **A render *look* is never override currency** (it reads clean over a real clip). Accept or override, both logged; an un-dispositioned MISMATCH stays **OPEN**. It cuts both ways: a footwear outfit that declares no foot-pose shape (`Heel_Feet`/`Foot_heel`) resolves it to 0, releasing a base heel a scan left worn — the observed `Heel_Feet=100`-kept-on-a-render failure, not a constructed illustration; a heeled outfit that *forgot* the declaration also resolves to 0, overridden back to 100 only when a `CaptureDiff` at 0 shows the flat foot piercing the sole.

**Shrink/hide over shared vertices are almost never both on** (`outfits.md`). Hiding a base mesh should flip its paired `Shrink_*` off — the pair travels together — and a kept outfit `ShapeChanger` shrinking the *same* vertices double-subtracts to an inverted mesh if the base shape stays worn. Absence of the shape on the outfit's own `ShapeChanger` is the tell it doesn't need it.

#### Evidence for the calls the graph doesn't settle

A value the outfit's own `ShapeChanger` or FX layer legibly drives is **settled as mechanism** — the mapping is authoritative over any render; spend nothing re-checking the value it drives. But an FX layer drives to whatever its parameter says, so the shipped **default** is still a judgment call whenever the outfit changed what's worn. And evidence settles only the avatar it lives on: another avatar's outfit declaring a value transfers nothing.

For the rest, fall through to evidence: **default keep**, certified with a `CaptureDiff` toggle-diff — toggle the element off/on and exact-compare the pair over the region in question, angle chosen from where the element lives (feet read from `bottom`).

- A **non-empty diff** shows the element drawing where it's questioned (a proven clip) — hide only under a garment that credibly covers in motion (form-fitting), else keep and flag the call OPEN. Argue from the diff *region*, never from magnitude.
- An **empty diff with freshness certified** proves only **sampled-view pixel immateriality** — that toggling changed no composited pixels from that angle — NOT that the renderer is invisible: an element coplanar with, or same-material as, geometry beneath it draws yet diffs empty. Treat empty as harmless-here; where actual renderer visibility must be certified, keep the call OPEN.
- A diff whose **freshness is not certified** proves nothing — OPEN.

An eyeballed render is no proof, and `RenderAvatar` is an operator-facing look, not an agent clipping verdict (`verify.md`). Coverage never creates a hide obligation.

**When keep and hide trade risks, the order is `exposure > hole > clip`**: an uncovered avatar is worst, a visible absence (a hollow shoe glimpsed through a gap) next, a clip cheapest — the one failure the diff proves statically and a play-mode build catches in motion, so defaults push residual risk toward clip. Perf is no tiebreaker: a kept occluded layer's triangles are the optimizer's, not a hide obligation. Two hard edges: **never shrink or hide body geometry (a foot, the torso) that no vendor authoring drives** — garment layers are yours to disable, the body underneath is not; hole risk is motion-unknowable, so propose it with evidence instead — and never *close* a motion-dependent call: apply the ranking's default and return the call **OPEN** with its diff counts, for the caller's checkpoint, the operator, or the play-mode build.

**Conform to the mechanism already in play — don't double-drive.** If the composed outfit already declares a reaction for an overlap (an MA `ObjectToggle` hiding the base underwear, a `ShapeChanger` setting a body shape at build), let that reaction own it — do **not** also apply the change statically. Match the substrate the avatar/outfit already uses; driving one state two ways is the bug, not the fix. Act statically only where nothing already handles it. **The base's FX is a mechanism in play too**: a garment or shape an always-on FX layer drives from an expression parameter ships whatever the **parameter default** says — a static edit there is overwritten at runtime (`outfits.md` §The FX controller). Tag every edge with its runtime owner; apply static edits only on unowned edges, and hand the runtime-owned set back to the caller as **named residue** (param, mesh, shape, off value) — the fix, a shipped-default flip, is `author-menu`'s to author and the operator's to call, not a static apply here.

**A base accessory the outfit supersedes** (a base bracelet under the outfit's wrist belt, a base hairpin under its hat) — **default to dropping it**; it is trivially re-enabled. But when an `author-menu` pass will follow, leave it in place as a toggle candidate instead of disabling — don't pre-empt a choice the menu will offer.

### Close a toggle's dependencies

A toggle's coupling edges **are** its dependency closure — hand them to `author-menu`, which drives the shapes with the mesh (a hidden garment must release its coupled shape, or the wearer is stranded deformed).

### Shape coherence

The map's shared-morph edges are the one-value-per-morph obligation `compose-mergeable` §5 reconciles across the outfit and body. The split is by evidence, not by depth: **live** coupling — what the reaction and FX graph declares — is this skill's, and this skill emits the carriers and their values. Whether a morph was **baked** into Basis leaves no in-scene signal at all; only the Blender provenance stamp knows, so that read and the reconcile it feeds stay in `compose-mergeable`. Don't infer a bake from a zero weight here. Invoked standalone on a coherence question, say so: a live-only answer is incomplete until the provenance stamp is read.

### Standalone

Emit the map as the answer, no mutation — the QA read of how an avatar's toggles and body shapes interrelate.

## Tools

- **Unity MCP `execute_code`** — inventory blendshapes, the AABB prefilter, disable a mesh, set a weight.
- **`ReportController` / `ReportClip`** (agent-tools, via `execute_code`) — the FX-graph read of step 2.
- **`AgentInspector`** — MA/VRCFury reactions and the mesh/component layout.
- **`ReportShapeOverlap`** (agent-tools, via `execute_code`) — the de-conflict census. Given the body-morph mesh **and the outfit root**, it ingests the outfit's `ShapeChanger` reactions (the weight-0 coupling a scan misses) and emits a per-shape resolution table (reaction, current weight, resolved-target, overlap, and a `MISMATCH` disposition on worn-but-undeclared rows). The outfit root is optional in the signature and load-bearing in practice — omit it and ingestion never runs. A Report, not a verdict; you disposition each row. Contract: `unity-tools.md`.
- **`RenderAvatar`** (agent-tools, via `execute_code`) — two doors. `Capture` is visual *confirmation* by before/after comparison (§2), never a source. `CaptureDiff` is the pinned-camera differential this section's keep/hide calls are argued from — exact compare, `gate=armed` certifying freshness. Both NDMF preview-resolved; grab in a separate call from any edit.
