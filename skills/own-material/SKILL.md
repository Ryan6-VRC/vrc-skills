---
name: own-material
description: Use when making our own owned, editable copy of a vendor material or texture — "recolor this dress", "repaint this texture", "add an emission mask", "convert this to Poiyomi" — or when any task must write to a material under Assets/Vendor/ or Packages/ (materialize the owned copy first). Not picking a vendor-shipped colorway (assignment), not geometry (own-base / own-mergeable).
---

# Own a material

Build our own owned, editable copy of a vendor material: a standalone `.mat` deep copy in the
owned bucket plus **only the textures actually being changed** — every untouched slot keeps its
vendor GUID reference (normal maps and masks usually stay vendor; the commonest real
customization forks exactly one albedo). This is `docs/LAYOUT.md`'s selective-owning rule
applied to materials, and the executable half of its read-only policy: `Assets/Vendor/` and
`Packages/` are never edited in place — a task that needs to change a vendor material there enters
this skill to materialize the owned copy first.

**No operator to ask?** A gate you can't put to an operator (a dispatched worker, a headless run)
is expected, not a blocker: surface it to whoever dispatched you and wait. With no channel at all,
take the derivable defaults, flag every undecided call loudly at the top of your report, and never
silently mint a convention — folder or category placement especially.

## Scope — what this covers, and the boundary

In scope: customizing a material's look (recolor, repaint, mask edit, shader conversion) and the
materialize-before-mutate prerequisite for any other task. Route out:

- **Picking a vendor-shipped colorway** (vendors ship whole PNG/JPG variant sets and parallel
  color `.mat`s) is assignment, not owning — swap the reference (`RemapMaterials`, or the
  renderer slot in-scene) and stop. It enters this skill only when the chosen variant then
  gets edited.
- **Geometry** → `own-base` / `own-mergeable`. Owning a material never requires owning the
  geometry it sits on, and vice versa — a composed vendor outfit can wear an owned material.
- **Menu-driven material swaps** (a toggle that switches materials) → `author-menu`; this skill
  only produces the owned materials such a control points at.

## Decisions — surface these to the operator

- **Which vendor edition to own.** Some vendors ship both lilToon and Poiyomi editions of the
  same asset; which to own is the operator's call (poi-exclusive features vs the lilToon-default
  ecosystem). Absent any channel, lilToon is the derivable default — flag it. When the operator
  wants Poiyomi and a vendor poi edition exists, own that edition directly; it beats converting
  (see the converter's fidelity limits below).
- **Never a Unity material variant (`m_Parent`) — always a standalone deep copy.** Three
  mechanisms, all from shader-package source: Poiyomi locking silently redirects a variant to
  its **root** material (variants can't carry a locked shader); the lil→poi converter severs a
  variant's parent, flattening it; and lilToon's variant/preset semantics batch-rewrite linked
  properties with no back-link, which misleads humans and agents alike. A vendor or legacy
  variant encountered on the way in is flattened into the owned copy.
- **Naming.** The owned `.mat` keeps the vendor material's name — the bucket namespaces it; no
  `_Custom` token. A deliberate new look (not a 1:1 ownership) takes a variant token
  (`<Name>_White`). Forked textures mirror their slot's vendor name.

## Filing — the two-tree mirror

- **`Assets/Materials/<Outfits|Avatars>/<Name>/`** — the owned `.mat`s and their exported
  textures. Outfit-first / base-independent (texture art doesn't change with proportions), so
  one bucket serves every base wearing the outfit. When the geometry is *also* owned, file the
  materials with it (`Assets/Outfits/<Base>/<Outfit>/Materials/`) instead — one logical asset,
  one home.
- **`Photoshop/<Outfits|Avatars>/<Name>/`** — the layered source art (`docs/LAYOUT.md`). The
  two trees mirror by name, like `Blender/` ↔ `Assets/`.

## The copy — `OwnMaterial`

The **`OwnMaterial`** tool (avatar-tools; being built — until it lands, reproduce its contract
via `execute_code` under the same invariants) does the deterministic mechanics: deep-copy the
`.mat` into the owned bucket; fork exactly the named texture slots, carrying each texture's
`.meta` import settings (sRGB/normal-map type/max size — the vendor's import profile is usually
right); leave every other slot as a vendor GUID reference; refuse any write under
`Assets/Vendor/` or `Packages/`; handle a **locked Poiyomi source** (below) without touching the
vendor asset. `whatIf` first; the RunLog's **slot-provenance table** (forked vs vendor-ref per
slot) is the verification gate — read it, don't eyeball the material.

Which slots to fork is the judgment this skill holds: fork what the customization will edit,
nothing else. Deciding that requires knowing what the vendor shipped — check the package for a
layered source (PSD trees, companion `PSD.zip`s, per-color folders) before painting over a
flattened export.

## PSD sidecar — source outside, PNG inside

The layered source (`.psd`; `.clip` is archival, keep beside it) lives in
`Photoshop/<Outfits|Avatars>/<Name>/`, never under `Assets/` — the same contract as
`.blend` → `.fbx`: what enters Unity is a **flattened PNG export**. When owning a slot whose
vendor texture is a `.psd` inside `Assets/` (vendors ship these linked), the owned slot is
converted: PSD source copied to the Photoshop tree, PNG export lands in the bucket, slot
repointed. An owned material referencing a `.psd` inside `Assets/` is a defect. The tool never
flattens — the PNG export is this skill's work, enforced here.

**The operator paints; the agent orchestrates.** Layer work in Photoshop is the operator's:
adopt the source into the Photoshop tree (pair separately-shipped PSD zips with their package),
hand the operator the file plus the export target path and expected import settings, then wire
the exported PNG and verify. Vendor recolor PSDs often carry ready layer groups — tell the
operator what the layers offer, don't guess a repaint where a group-toggle exists.

## lilToon

The ecosystem baseline — vendor texture sets (shadow/rim/outline/emission masks, matcaps) are
authored to lilToon's slots. An owned lilToon copy is inert and safe:

- **Presets are one-time copies** — applying one writes property values with no back-link, so a
  copied material carries no live coupling to any preset asset. Don't use presets or the
  rendering-mode switch as an "inheritance" mechanism; both batch-rewrite linked properties
  (stencil/blend/queue/keywords) in one action.
- **Build-time optimization rewrites shader files, not your `.mat`** — and resets them after.
  The one exception: a **lilToonMulti** material can get keywords enabled *and saved* during a
  build. Expected churn, not corruption; don't chase it as a bug.

## Poiyomi

Poiyomi materials carry a **locking** lifecycle (Thry ShaderOptimizer) that changes what a copy
even means:

- **Locking bakes property values into a generated shader** (`Hidden/Locked/...`, written under
  `OptimizedShaders/<MatName>/` beside the `.mat`) and repoints the material at it. Edits to a
  locked material's non-`Animated`-tagged properties are silent no-ops.
- **Never filesystem-copy a locked `.mat`.** Locked materials with equal property hashes share
  one generated shader, tracked by a GUID list tag the raw copy is absent from — unlocking or
  deleting the original then removes the shader out from under the copy (pink material). The
  owning path for a locked vendor source: copy first, **unlock the copy** (its restore tags
  travel with it), never the vendor original — `OwnMaterial`'s job.
- **Author unlocked.** Keep owned poi materials unlocked while working so edits take effect;
  the VRChat upload hook auto-locks every material on the avatar — accept that as the ship
  step. It **rewrites `.mat` assets on disk and generates `OptimizedShaders/` folders**:
  expected churn (the generated shaders are regenerable, gitignored).
- Programmatic lock state: `Thry.ThryEditor.ShaderOptimizer.LockMaterials` /
  `UnlockMaterials(IEnumerable<Material>)`; `material.IsLocked()`.

## lil→poi conversion

Only when the operator explicitly wants poi-exclusive features **and no vendor poi edition
exists**. The converter ships in the Poiyomi package
(`Poi.Tools.ShaderTranslator.Translations.LiltoonToPoiyomiToonTranslation`
`.Translate(mat, ".poiyomi/Poiyomi Toon")`; gate with `.CanTranslateMaterial`). It converts
**in place**, so run it only on a fresh copy minted for the conversion — the owned lilToon
material **stays in place as the durable original**, and the poi edition lands beside it as a
twin (`<Name>_Poi`). Never point it at a vendor material or at the lil copy itself.

**Fidelity is imperfect by construction** (from its source): the blend-op block is untranslated,
some decal alpha modes are unmapped, and any lilToon property without a table entry is silently
dropped. Treat the result as a starting point: have the operator compare against the lilToon
original (`RenderAvatar` before/after is the operator-facing look) and expect poi-side fixup.

## Verify

The mechanical gate is the tool diagnostic: `OwnMaterial` PASS with a slot-provenance table
matching intent (forked exactly the slots the customization needs, zero vendor-tree writes, no
reference to another material's generated locked shader). The look is the operator's eye — a
render is evidence for them, never the agent's verdict.

## Tools

Reach by role; open each for its entry point.

- **`OwnMaterial`** (avatar-tools, being built) — the deep-copy mechanics above. Until it
  lands: `execute_code` reproducing its contract, invariants unchanged.
- **`RemapMaterials`** (avatar-tools) — point a hierarchy's renderers at the owned materials
  once they exist (swap by asset path); also the whole of the "pick a colorway" case this
  skill routes out.
- **Unity MCP `execute_code`** — slot inspection (`.mat` YAML or `Material` API), the Thry
  lock/unlock calls, the lil→poi translator.
- **Photoshop tree + operator** — the layered-source edit loop; the agent owns adoption,
  export wiring, and verification around it.
