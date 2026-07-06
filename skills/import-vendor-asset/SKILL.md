---
name: import-vendor-asset
description: Use when bringing a vendor VRChat avatar, outfit, hair, or accessory into the Unity AvatarProject — "import this avatar", "get X into the project", a `.unitypackage` from the asset library (often zipped, sometimes with a separate MaterialPack).
---

# Import a vendor asset

Get a vendor package into `AvatarProject` cleanly: untouched under `Assets/Vendor/<Category>/<Name>`, verified, gitignored. Layout rationale lives in `docs/LAYOUT.md` — this is the per-import flow, its gates, and its gotchas.

## Gates — hard stops, ask the operator

Resolve each **as it comes up** — not every asset hits every gate, and there is no silent default; if the option exists, ask.

- **Which version / avatar base** — applies to outfits, hair, accessories (and sometimes systems), not base avatars. If the source offers several, ask which to import. If there's only one, take it — **except** when its target avatar isn't already in the project (e.g. a Manuka outfit with no Manuka present): always confirm first.
- **Prune a combined package** — ask **only** when it's a full-set of *distinct* avatars (offer to drop the non-targets). A shared base-model family — cross-compatible bodies packaged together, e.g. Plum/Chiffon/Chocolat — is kept whole; don't ask.
- **Alternate / edit (`kaihen`) FBX** — ask. If kept, place it with the other FBXes in Unity (inside the vendor `FBX/` folder).
- **Non-linked PSDs / texture packs** — ask; if kept they go to `Photoshop/<Avatars|Outfits>/<Name>/` (our work, outside `Assets/`). A PSD a material actually links to is required — bring it in without asking; confirm the no-link case from the verify step's `0 .psd` material dependencies.
- **Folder placement** — drop into an existing `Vendor/<Category>/` when it's an obvious match (hair → `Hair`). Ask before creating a new category, or when the right one isn't obvious.

## Take the right files

- **Take only the `.unitypackage`** — it almost always contains the FBX even when a loose FBX sits beside it. Confirm: a `.unitypackage` is a gzip tar; list its `pathname` files. Source a loose FBX only if none is inside.
- **Zips → extract to a temp/scratch workspace first**, never into the project. Materials and PSDs sometimes ship as their own zip/unitypackage.
- **Outfits often ship a separate MaterialPack** (sometimes very large) — the costume alone has no materials, so import both. A single all-avatars package exists but is rare.

## Import + organize (drive via Unity `execute_code`)

1. `AssetDatabase.ImportPackage(path, false)` is **asynchronous** — it returns before the import settles. Confirm the package's top folder exists before continuing; don't chain the move in the same call.
2. Import any companion MaterialPack the same way. After a large pack the import can still be settling even when `editor_state` reads idle and `external_changes_dirty` is stale — confirm material/prefab counts before judging it incomplete.
3. **Relocate + flatten** with `AssetDatabase.MoveAsset` (GUID-preserving) into the target `Vendor/<Category>/<Name>`. Flatten the seller/author wrapper folders; assets shared across that seller's packages go to `Assets/Vendor/_Common/`. Delete the emptied wrappers — `execute_code`'s `safety_checks` blocks `AssetDatabase.DeleteAsset`, so pass `safety_checks=false` for that step only.
4. Moves are GUID-based and **never break references** — don't re-verify just because you moved something.
5. **Settle external-material remaps (separate-MaterialPack outfits).** Once every package is in and relocated, force-reimport the costume FBX models: `AssetDatabase.ImportAsset(fbxPath, ImportAssetOptions.ForceUpdate)`. An FBX using external materials (`materialLocation: External`) applies its `.mat` remap **only at import time**, so a model imported before its materials existed caches **empty** slots — and the later MaterialPack import does *not* re-trigger it. Skip this and the default colorway plus shared weapon/chain render untextured, silently (it reads as harmless "empty", not "missing").

## Verify

- `Ryan6Vrc.AgentTools.Editor.ImportVerify.VerifyFolder("Assets/Vendor/...")` → expect `PASS`, and check `read_console` is clean.
- **Null material slots are not failures.** A healthy costume has hundreds of intentionally-empty submesh slots; what fails is *missing* references (a broken GUID), missing meshes, missing scripts, a **stale FBX remap**, or a `loadErrors` count (a prefab that throws on load). Don't hand-count nulls — that's the trap ImportVerify exists to avoid.
- A `remapSTALE` FAIL means an FBX's external-material remap resolves but the model imported empty — force-reimport that FBX (step 5) and re-verify.

## gitignore

No per-import change — `/Assets/Vendor/` and `/Photoshop/` already cover every new import. (One-time meta-rule: those lines sit after the stock `!*.meta` un-ignore line; see `docs/LAYOUT.md`.)
