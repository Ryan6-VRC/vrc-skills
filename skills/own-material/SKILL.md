---
name: own-material
description: Use when changing how a material looks in any way — "recolor this dress", "add glitter to the shirt", "make her eyes glow", "hue slider for the dress", "convert this to Poiyomi" — repaint a texture, enable a shader feature, or animate a shader property; also when any task must write to a material under Assets/Vendor/ or Packages/ (materialize the owned copy first). Covers the material groundwork for animated looks; the finished menu control is author-menu, after. Not picking a vendor-shipped colorway (assignment), not geometry (own-base / own-mergeable).
---

# Own a material

The entry point for changing how a material looks — a static recolor, a shader feature like glitter, a repainted texture, or a property a slider will drive. The first decision is the *mechanism*, and each mechanism carries its own ownership requirement; owning — a standalone `.mat` deep copy plus only the textures actually being changed — is `docs/LAYOUT.md`'s selective-owning rule applied to materials, and the executable half of its read-only policy: `Assets/Vendor/` and `Packages/` are never edited in place — a task that needs to change a vendor material there enters this skill to materialize the owned copy first.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## Scope — what this covers, and the boundary

In scope: any change to a material's look, static or animated, and the materialize-before-mutate prerequisite for any other task. Route out:

- **Picking a vendor-shipped colorway** (vendors ship whole PNG/JPG variant sets and parallel color `.mat`s) is assignment, not owning — swap the reference (`RemapMaterials`, or the renderer slot in-scene) and stop. It enters this skill only when the chosen variant then gets edited.
- **Geometry** → `own-base` / `own-mergeable`. Owning a material never requires owning the geometry it sits on, and vice versa — a composed vendor outfit can wear an owned material.
- **The finished menu control** → `author-menu`, after this skill's groundwork — including menu-driven material swaps; this skill only produces the owned materials and animated-ready properties such a control points at. Placing a vendor-shipped gimmick **module** (prefab with its controllers) is `compose-mergeable`; only its menu front is `author-menu`.

## The mechanism — decide before forking anything

- **(a) Edit the `.mat` asset** — most asks land here: property values, enabling a shader feature block, switching rendering mode/shader, filling a texture slot. Glitter, emission (AudioLink included), hue/HSV shift, decals, matcap, rim, and dissolve are **feature blocks** both shader families ship — a `_Use*`/`_Enable*` toggle plus a property group, not a texture to paint; read the shader package source for the exact properties. Shader-clock and AudioLink-driven effects land here too — they *look* runtime but are enabled by static writes; clips never drive them. **Any edit to the `.mat` asset requires owning it**; texture slots stay vendor.
- **(b) Repaint a texture** — only when the change lives in the texture itself. Own the `.mat` and fork exactly the slots being edited. Check what the vendor shipped before painting: color masks, matcap libraries, UV-layout PNGs, and layered PSD/CLIP sources (these ship beside the package in the vendor library, almost never inside `Assets/`). Reading a vendor texture's pixel data goes through `Graphics.Blit` → temporary `RenderTexture` → `ReadPixels` — never `TextureImporter.isReadable`, whose toggle + reimport round-trip is a vendor write (`unity.md` §Sharp edges).
- **(c) Clip-driven property** — an animation clip drives the value (defined by the driver — shader-clock/AudioLink effects are (a)). First check what the vendor shipped: complete anim grids and gimmick controllers are common, and placing one is placement work (`compose-mergeable` for the module, `author-menu` for the front), not construction. Ownership splits by shader family:
  - **lilToon — no fork, bounded.** The clip drives the renderer's material instance and the build keeps clip-driven uniforms alive (below); the vendor `.mat` is never written. The bound: this holds for properties of feature blocks the material already has enabled. Enabling a block the vendor never turned on, switching rendering mode, or filling a texture slot is a `.mat` write → (a). **lilToonMulti is excepted entirely** — the build can save keywords into the material asset, so own a Multi material before clip-driving it. A persistent look-change can ride this path as a constant always-on clip, when the `.mat` itself needs no edit.
  - **Poiyomi — fork required.** Marking a property animated is a write to the `.mat`, so own first; the owned copy carries the tags and stays unlocked while authoring (see Poiyomi).
- Real asks compose and cascade: "add glitter" = (a) + a (b) mask only if the look needs a custom one; a slider that also needs a new default = (a) + (c) — owned either way.

## Decisions — surface these to the operator

- **Which vendor edition to own.** Some vendors ship both lilToon and Poiyomi editions of the same asset; which to own is the operator's call (poi-exclusive features vs the lilToon-default ecosystem). Absent any channel, lilToon is the derivable default — flag it. When the operator wants Poiyomi and a vendor poi edition exists, own that edition directly; it beats converting (see the converter's fidelity limits below).
- **Never a Unity material variant (`m_Parent`) — always a standalone deep copy.** Three mechanisms, all from shader-package source: Poiyomi locking silently redirects a variant to its **root** material (variants can't carry a locked shader); the lil→poi converter severs a variant's parent, flattening it; and lilToon's variant/preset semantics batch-rewrite linked properties with no back-link, which misleads humans and agents alike. A vendor or legacy variant encountered on the way in is flattened into the owned copy — `OwnMaterial` does this.
- **Naming.** A deliberate new look (not a 1:1 ownership) takes a variant token (`<Name>_White`). A 1:1 ownership keeps the vendor material's name — the bucket namespaces it; no `_Custom` token. Forked textures keep their source texture's filename — the material's subfolder is the namespace.

## Filing — the two-tree mirror

- **`Assets/Materials/<Outfits|Avatars>/<Name>/`** — the owned `.mat`s. Outfit-first /
  base-independent (texture art doesn't change with proportions), so one bucket serves every base wearing the outfit. When the geometry is *also* owned, file the materials with it (`Assets/Outfits/<Base>/<Outfit>/Materials/`) instead — one logical asset, one home.
- **Forked textures live in the owned material's own subfolder** (`<mat folder>/<mat name>/`) — `OwnMaterial`'s namespace rule. Two owned materials forking one vendor texture get independent copies, never a silent share.
- **Shared-source forks file per-consuming-material.** A texture from a shared vendor library (a `_Common` matcap, a `Packages/` ramp) forks into each consuming material's subfolder like any other slot — duplication is fine, forks decouple. No owned `_Common` bucket exists or gets minted.
- **`Photoshop/<Outfits|Avatars>/<Name>/`** — the layered source art (`docs/LAYOUT.md`). The
  two trees mirror by name, like `Blender/` ↔ `Assets/`.

## The copy — `OwnMaterial`

The **`OwnMaterial`** tool (avatar-tools) does the deterministic mechanics in three modes, routed by target identity: **own** (vendor source → new owned `.mat`), **branch** (owned source → a second look that inherits every edit, diverging only forked slots), **augment** (no `outDir` — fork additional slots into an existing owned material in place). It deep-copies the `.mat`, forks exactly the named texture slots (carrying each texture's `.meta` import settings — the vendor's import profile is usually right — with streaming mipmaps enabled on the owned copy as a perf default, never on the vendor source *as part of owning a material* — correcting it on a vendor texture that blocks an upload is `ConformImportSettings`' job at the import door, not this skill's), leaves every other slot as a vendor GUID reference, flattens variants, and unlocks a locked Poiyomi copy without breaking the vendor original. `whatIf` first; the RunLog's **slot-provenance table** is the verification gate — read it, don't eyeball the material.

The table is also the working map: `vendor-ref` rows are the menu of still-forkable slots — the full slot set a customization needs is rarely known up front, and coming back with `OwnMaterial(ownedMat, forkTextureSlots: [newSlot])` (no `outDir`) forks the extra mask mid-work, idempotently. `owned-elsewhere` rows are the branch-coupling signal: the material still shares another material's owned texture — fork it to decouple. A forked slot whose source is an in-`Assets/` `.psd` lands with a Warning naming this skill's PNG-export follow-up.

Dispositions are **present-state, re-derived from disk each run** (which GUID a slot references, where that asset lives) — not a history, so they read truthfully on any material regardless of origin. But the *map* readings assume our filing conventions: on a material not filed by them (hand-owned, or vendor content under a writable tree), a slot's own textures can show `owned-elsewhere`, and vendor textures outside `Vendor/`/`Packages/` under-report there instead of as `vendor-ref`. Then `owned-elsewhere` weakens to "writable, not this material's home" — check who actually references the texture before forking to decouple.

Which slots to fork is the judgment this skill holds: fork what the customization will edit, nothing else.

## PSD sidecar — source outside, PNG inside

The layered source (`.psd`; `.clip` is archival, keep beside it) lives in
`Photoshop/<Outfits|Avatars>/<Name>/`, never under `Assets/` — the same contract as
`.blend` → `.fbx`: what enters Unity is a **flattened PNG export**. When owning a slot whose vendor texture is a `.psd` inside `Assets/` (vendors ship these linked), the owned slot is converted: PSD source copied to the Photoshop tree, PNG export lands beside the material, slot repointed. An owned material referencing a `.psd` inside `Assets/` is a defect. The tool never flattens — the PNG export is this skill's work, enforced here.

**The operator paints; the agent orchestrates.** Layer work in Photoshop is the operator's: adopt the source into the Photoshop tree (pair separately-shipped PSD zips with their package), hand the operator the file plus the export target path and expected import settings, then wire the exported PNG and verify. Vendor recolor PSDs often carry ready layer groups — tell the operator what the layers offer, don't guess a repaint where a group-toggle exists.

## lilToon

The ecosystem baseline — vendor texture sets (shadow/rim/outline/emission masks, matcaps) are authored to lilToon's slots. An owned lilToon copy is inert and safe:

- **Presets are one-time copies** — applying one writes property values with no back-link, so a copied material carries no live coupling to any preset asset. Don't use presets or the rendering-mode switch as an "inheritance" mechanism; both batch-rewrite linked properties (stencil/blend/queue/keywords) in one action.
- **Build-time optimization rewrites shader files, not your `.mat`** — and resets them after. It scans the clips reachable through the avatar descriptor's animator layers and keeps every clip-driven uniform live, which is why mechanism (c) needs no fork — but a clip *not* reachable there at build time (added by a later build step, or driven outside the descriptor) can get its property baked. The one `.mat`-write exception: a **lilToonMulti** material can get keywords enabled *and saved* during a build. Expected churn on an owned Multi material, not corruption; on a vendor one, the reason (c) excepts Multi.

## Poiyomi

Poiyomi materials carry a **locking** lifecycle (Thry ShaderOptimizer) that changes what a copy even means:

- **Locking bakes property values into a generated shader** (`Hidden/Locked/...`, written under `OptimizedShaders/<MatName>/` beside the `.mat`) and repoints the material at it. Edits to a locked material's non-animated-tagged properties are silent no-ops.
- **Never filesystem-copy a locked `.mat`.** Locked materials with equal property hashes share one generated shader, tracked by a GUID list tag the raw copy is absent from — unlocking or deleting the original then removes the shader out from under the copy (pink material). The owning path for a locked vendor source: copy first, **unlock the copy**, never the vendor original — `OwnMaterial`'s job. Detect lock state from the shader name (`Hidden/Locked/` prefix), never the filename or the `AllLockedGUIDS` tag (stale on real vendor materials).
- **Author unlocked.** Keep owned poi materials unlocked while working so edits take effect; the VRChat upload hook auto-locks every material on the avatar — accept that as the ship step. It **rewrites `.mat` assets on disk and generates `OptimizedShaders/` folders**: expected churn (the generated shaders are regenerable, not kept).
- **Every clip-driven property needs its `Animated` tag set before lock, by hand.** The upload auto-lock does **not** detect animated properties from the avatar's clips (its clip scan is material-swap references only) — an animated-but-untagged property is baked at lock and the animation silently dies at upload. Tag value `"1"` keeps the uniform live under its own name; `"2"` also **renames** it (`<prop>_<suffix>`) — clips must then bind the renamed name, so prefer `"1"` unless materials sharing a locked shader must animate independently.
- **The tag keeps the uniform live; it does not resurrect stripped code.** Lock deletes the code of disabled feature blocks — the animated property's block must be enabled (toggle on) on the owned material when it locks, or the animation ships dead against a shader whose code is gone. Keep the tag set in sync with the actually-animated property set: stale tags cost lock optimization, missing tags kill animations.
- Tag storage, set/read API, and the rename-suffix mechanics: read the Thry `ShaderOptimizer` source in the poi package — it is the authority, and it moves.

## lil→poi conversion

Only when the operator explicitly wants poi-exclusive features **and no vendor poi edition exists**. The converter ships in the Poiyomi package (`Poi.Tools.ShaderTranslator.Translations.LiltoonToPoiyomiToonTranslation` `.Translate(mat, ".poiyomi/Poiyomi Toon")`; gate with `.CanTranslateMaterial`). It converts **in place**, so run it only on a fresh copy minted for the conversion — the owned lilToon material **stays in place as the durable original**, and the poi edition lands beside it as a twin (`<Name>_Poi`). Never point it at a vendor material or at the lil copy itself.

**Fidelity is imperfect by construction** (from its source): the blend-op block is untranslated, some decal alpha modes are unmapped, and any lilToon property without a table entry is silently dropped. Treat the result as a starting point: have the operator compare against the lilToon original (`RenderAvatar` before/after is the operator-facing look) and expect poi-side fixup.

Two traps when reading existing materials, converted or not: **filenames prove nothing about shaders** (a `-liltoon`-named file can be locked Poiyomi — trust `m_Shader` / the `OriginalShader` tag, never the name), and **serialized properties prove nothing either** — conversion leaves orphaned foreign-shader properties in the `.mat` that render nothing; the current shader's property set is the truth.

## Animated properties — groundwork here, control elsewhere

This skill's deliverable for mechanism (c) is the material side: the owned (or, lilToon, vendor-as-is) material, the chosen property name, and — Poiyomi — the `Animated` tags set. The control and construction route out: `author-menu` (with `docs/menus.md`'s escalation rules) builds or places the menu control; for animator constructions (a hue/color slider on the shader's own property, an HSV→RGB compute when the target shader lacks one), `docs/gimmicks.md` is the technique doc and routes to `vrc-patterns` as a whole — find the entry in that library's README "Find by pattern" table, keyed by capability. Match by capability, never a hardcoded path.

## Verify

The mechanical gate is the tool diagnostic: `OwnMaterial` PASS with a slot-provenance table matching intent — forked exactly the slots the customization needs, no reference to another material's generated locked shader. The gate is **intent-level, not byte-level**: owning a locked vendor poi source byte-touches the vendor `.mat` (Thry rewrites a tag with its own value — the tool asserts the source is still locked), so a git-dirty vendor `.mat` after a locked-poi own is expected, not a violation. The lilToon no-fork path produces no `OwnMaterial` run at all — its gate is that the clip binds the intended property on the intended path and no vendor asset was intent-mutated. For a Poiyomi animated property, "done" includes the `Animated` tag present and the feature block enabled — that pair is what survives lock. The look is the operator's eye — a render is evidence for them, never the agent's verdict.

## Tools

Reach by role; open each for its entry point.

- **`OwnMaterial`** (avatar-tools) — the own/branch/augment copy mechanics above; `whatIf` first, slot-provenance table as the gate.
- **`RemapMaterials`** (avatar-tools) — point a hierarchy's renderers at the owned materials once they exist (swap by asset path); also the whole of the "pick a colorway" case this skill routes out.
- **Unity MCP `execute_code`** — slot inspection (`.mat` YAML or `Material` API), the Thry `Animated`-tag and lock/unlock calls, the lil→poi translator.
- **Photoshop tree + operator** — the layered-source edit loop; the agent owns adoption, export wiring, and verification around it.
