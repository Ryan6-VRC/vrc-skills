---
name: map-outfit-shapes
description: Use when mapping how a body's blendshapes couple to its clothing meshes — hiding base clothing under a composed outfit, merging pieces from two outfits on one base, closing a toggle's dependencies, or checking body-morph coherence. The shape↔mesh interaction map; not composing an outfit (compose-mergeable) or authoring menus (author-menu).
---

# Map how an outfit interacts with a body's shapes

Produce the map of how an avatar's **body blendshapes couple to its meshes** — which garment drives
which body shape, to what worn and off values, and which morphs several meshes must agree on — then
act on it. The map is the reusable core; hiding overlapped clothing, closing a toggle, and checking
coherence are all reads of it.

**A reasoning task, not a parse.** Creators wire FX layers, VRCFury features, MA reactions, and
blendshape names every which way; no deterministic script maps them. You read the graph across those
idioms and reason — the method below is authority order and fallbacks built for exactly that variety.

**No operator to ask?** A gate you can't put to an operator (a dispatched worker, a headless run)
is expected, not a blocker: surface it to whoever dispatched you and wait. With no channel at all,
take the derivable defaults, flag every undecided call loudly at the top of your report, and never
silently mint a convention — folder or category placement especially.

## Scope

Owns: producing the interaction map, and the in-scene acts that consume it (disable an overlapped
mesh, set a body shape to its off value). Read-first and non-destructive — disable never delete,
weights are reversible sets. Does **not** compose/place the outfit (`compose-mergeable`), author menu
controls (`author-menu`), or reconcile proportions (`reproportion`) — it *feeds* those.

**Opt-in.** The mapping is slow, so `compose-mergeable`'s quick de-conflict commits only the obvious
mesh disables and routes here for the full coupling read.

## The map

A table of **edges**, each carrying its **source** and **confidence** — the sources vary and
disagree, so an edge without its provenance can neither be trusted nor rechecked:

- **Coupling edge** — `garment mesh → body blendshape(s) it drives`, with the **worn value** and the
  **off/removed value** (e.g. `underwear_stocking → Shrink_stocking: worn 100, off 0`).
- **Shared-morph edge** — a body morph several meshes must hold at one value (breast size, a
  proportion tweak): the value and its carriers.
- **Toggle edge** — an existing FX/MA/VRCFury control → what it drives (mesh active-state + shape
  values).
- **Source / confidence** — `FX-clip | MA/VRCFury-reaction | naming-hint | asked-user | visual`,
  high→low authority (below).

Hold it in-context as you work; write it to `Assets/Agent/Scratch/` only when a later session or a
human will reuse it.

## Building the map

### 1. Inventory

Identify the body mesh(es) — vendor-named, `Body`, `<Name>_body`. Enumerate every blendshape on them,
and every garment mesh: the base's own clothing layers **and** every piece of each composed outfit.
This is the surface you reason over.

### 2. Resolve each edge in the authority order

Follow the base-coupling authority order (`outfits.md` §The FX controller), reading each tier with its
tool: **FX clips** (`ReportController` / `ReportClip`) over **MA/VRCFury reactions** on the composed
pieces (`AgentInspector`) over **naming** (a hint, never acted on alone) over **asking the user**
(first-class when the graph is silent — a garment with no declared coupling has none until confirmed;
don't invent one).

**Reading a `ShapeChanger` raw** (`AgentInspector` / SerializedProperty): its `ShapeChangeType` prints
as an enum index — **Delete=0, Set=1** — so a bare `enum[0]` is *Delete* (geometry deletion), the more
consequential mode, not the harmless-looking default. Resolve the name before acting on it.

**Vision is a check, not a source.** If the graph and the user leave an edge open, `RenderAvatar`
confirms it only by **before/after comparison** — the shape worn vs. zeroed, the mesh on vs. off; read
the *difference*, never a single capture. Vision confirms a hypothesis, it doesn't originate one.

### 3. Emit

The edge table, every edge tagged with its source and confidence. Low-confidence edges are flagged,
not hidden.

## Applications — acting on the map

### Deconflict & merge — the overlap set

Overlap is **any clothing source covering a region another source also covers** — base-under-outfit
and outfit-under-outfit are one problem:

- **Outfit on a clothed base** — the base garments the outfit's coverage replaces.
- **Merge pieces from two outfits** ("top from X, bottom from Y") — each outfit often ships full-body
  pieces, so the pieces you did *not* ask for from each (X's bottom, Y's top) are the overlap set.
  Watch for two kept pieces driving **one body shape to different values** — a coherence conflict;
  surface it, don't silently pick.

Find the overlap set by **coverage reasoning**: a base garment is in the set when the outfit covers
its region — whether it hides *under* the outfit or clips *over* it. "Wear only the outfit" means only
the outfit's clothing remains, so **a base garment still visible over the outfit is in the set, not
exempt** — don't read "still visible" as "additive." A coarse `Renderer.bounds` AABB test
(`Bounds.Intersects`, a few lines of `execute_code`) is a weak prefilter only — a full garment's AABB
overlaps almost everything, so a hit means "look here," never proof.

Where the graph is silent on whether the outfit covers a region, settle it with the **coverage
question, not an occlusion one**: turn the base piece *off* and check whether the outfit leaves that
region **exposed or gapped** (`RenderAvatar` before/after, §2). Exposure → the outfit doesn't cover it
(keep it, or ask); clean coverage → the base piece is a hidden overlap (strip it). Asking "is the base
garment still visible?" is the trap — an over-layered garment is visible *because* it is the thing to
remove.

Then, per overlapped garment: **disable the mesh** (never delete) and **set its coupled body shapes to
their off values** from the map. A limb that vanishes means a coupled shape you left worn.

**Confirm a suspected shrink double-subtraction mechanically.** A base `Shrink_*` left worn while a kept
outfit `ShapeChanger` shrinks the same region stacks into an inverted limb the render sheet and the fit
gates never show. Feed the co-active shapes on the body mesh — the base worn `Shrink_*` plus the outfit
`ShapeChanger`'s targets — to `ReportShapeOverlap`; it reports which pairs deform the **same vertices**
(containment `|A∩B| / min`). It locates the collision, it doesn't rule on it: release the base shrink
where the outfit owns that region, keep it where they are independent.

**Conform to the mechanism already in play — don't double-drive.** If the composed outfit already
declares a reaction for an overlap (an MA `ObjectToggle` hiding the base underwear, a `ShapeChanger`
setting a body shape at build), let that reaction own it — do **not** also apply the change
statically. Match the substrate the avatar/outfit already uses; driving one state two ways is the bug,
not the fix. Act statically only where nothing already handles it.

**A base accessory the outfit supersedes** (a base bracelet under the outfit's wrist belt, a base
hairpin under its hat) — **default to dropping it**; it is trivially re-enabled. But when an
`author-menu` pass will follow, leave it in place as a toggle candidate instead of disabling — don't
pre-empt a choice the menu will offer.

### Close a toggle's dependencies

A toggle's coupling edges **are** its dependency closure — hand them to `author-menu`, which drives
the shapes with the mesh (a hidden garment must release its coupled shape, or the wearer is stranded
deformed).

### Shape coherence

The map's shared-morph edges are the one-value-per-morph obligation `compose-mergeable` §5 reconciles
across the outfit and body.

### Standalone

Emit the map as the answer, no mutation — the QA read of how an avatar's toggles and body shapes
interrelate.

## Tools

- **Unity MCP `execute_code`** — inventory blendshapes, the AABB prefilter, disable a mesh, set a
  weight.
- **`ReportController` / `ReportClip`** (agent-tools, via `execute_code`) — the FX-graph read of
  step 2.
- **`AgentInspector`** — MA/VRCFury reactions and the mesh/component layout.
- **`ReportShapeOverlap`** (agent-tools, via `execute_code`) — same-mesh blendshape overlap: does a base
  worn `Shrink_*` deform the same vertices an outfit `ShapeChanger` also shrinks (the double-subtraction)?
  Feed it the co-active set you named; it locates the collision, you rule on it.
- **`RenderAvatar`** (agent-tools, via `execute_code`) — visual *confirmation* by before/after
  comparison (§2); NDMF preview-resolved; grab in a separate call from any edit.
