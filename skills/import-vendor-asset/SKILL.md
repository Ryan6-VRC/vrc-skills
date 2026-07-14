---
name: import-vendor-asset
description: Use when bringing a vendor VRChat avatar, outfit, hair, or accessory into the Unity AvatarProject — "import this avatar", "get X into the project", a `.unitypackage` from the asset library (often zipped, sometimes with a separate MaterialPack).
---

# Import a vendor asset

Get a vendor package into `AvatarProject` cleanly: untouched under `Assets/Vendor/<Category>/<Name>`, verified, gitignored. Layout rationale lives in `docs/LAYOUT.md` — this is the per-import flow, its gates, and its gotchas.

## Gates — hard stops, ask the operator

Resolve each **as it comes up** — not every asset hits every gate, and there is no silent default; if the option exists, ask.

**No operator to ask?** A gate you can't put to an operator (a dispatched worker, a headless run)
is expected, not a blocker: surface it to whoever dispatched you and wait. With no channel at all,
take the derivable defaults, flag every undecided call loudly at the top of your report, and never
silently mint a convention — folder or category placement especially.

- **Which version / avatar base** — applies to outfits, hair, accessories (and sometimes systems), not base avatars. If the source offers several, ask which to import. If there's only one, take it — **except** when its target avatar isn't already in the project (**check the project for the target — don't infer its presence from the prompt**; e.g. a Manuka outfit with no Manuka present): always confirm first.
- **Prune a combined package** — ask **only** when it's a full-set of *distinct* avatars (offer to drop the non-targets). A shared base-model family — cross-compatible bodies packaged together, e.g. Plum/Chiffon/Chocolat — is kept whole; don't ask.
- **Alternate / edit (`kaihen`) FBX** — ask. If kept, place it with the other FBXes in Unity (inside the vendor `FBX/` folder).
- **Non-linked PSDs / texture packs** — ask; if kept they go to `Photoshop/<Avatars|Outfits>/<Name>/` (our work, outside `Assets/`). A PSD a material actually links to is required — bring it in without asking; confirm the no-link case from the verify step's `0 .psd` material dependencies.
- **Folder placement** — drop into an existing `Vendor/<Category>/` when it's an obvious match (hair → `Hair`). Ask before creating a new category, or when the right one isn't obvious; dispatched with no one to ask, mirror the nearest existing `Vendor/<Category>/` precedent and say loudly which you followed.
- **Running a vendor executable / patcher** — a DLC that ships a binary patcher or installer (`hpatchz` + `.hdiff`, a setup `.bat`) to mutate the base before it's usable. **Ask before running any vendor executable.** The copy-on-write reconstruction and the containment discipline live under *Patch a vendor-mutated asset* below.

## Take the right files

- **Take only the `.unitypackage`** — it almost always contains the FBX even when a loose FBX sits beside it. Confirm: a `.unitypackage` is a gzip tar; list its `pathname` files. Source a loose FBX only if none is inside.
- **Zips → extract to a temp/scratch workspace first**, never into the project. Materials and PSDs sometimes ship as their own zip/unitypackage. Clean the scratch workspace when done and **re-list it to confirm empty** — a "cleaned" claim is only true if you listed it.
- **Outfits often ship a separate MaterialPack** (sometimes very large) — the costume alone has no materials, so import both. A single all-avatars package exists but is rare.
- **Windows path/quoting traps.** GNU `tar` needs `--force-local` to read a `C:`-drive path (the colon parses as a remote host) and cannot read `Y:`-style asset-library paths at all — copy the package to scratch before listing or extracting. Backslash-before-quote bash quoting mangles copies; prefer forward slashes.

## Import + organize (drive via Unity `execute_code`)

1. `AssetDatabase.ImportPackage(path, false)` is **asynchronous** — it returns before the import settles. Confirm the package's top folder exists before continuing; don't chain the move in the same call.
2. Import any companion MaterialPack the same way. After a large pack the import can still be settling even when `editor_state` reads idle and `external_changes_dirty` is stale — confirm material/prefab counts before judging it incomplete.
3. **Relocate + flatten** with `AssetDatabase.MoveAsset` (GUID-preserving) into the target `Vendor/<Category>/<Name>`. Flatten the seller/author wrapper folders; assets shared across that seller's packages go to `Assets/Vendor/_Common/`. Delete the emptied wrappers via the `manage_asset` **delete** door — `execute_code`'s `safety_checks` blocks the delete family; `safety_checks=false` unblocks it, but the door keeps the guard up for that call. **Verify the relocate by `CheckPackage` on the destination plus confirming the source wrapper is drained — never a self-counted `moved:N`** (a hand-written move loop's own success count misreads).
4. Moves are GUID-based and **never break references** — don't re-verify just because you moved something.
5. **Settle external-material remaps (separate-MaterialPack outfits).** Once every package is in and relocated, force-reimport the costume FBX models: `AssetDatabase.ImportAsset(fbxPath, ImportAssetOptions.ForceUpdate)`. An FBX using external materials (`materialLocation: External`) applies its `.mat` remap **only at import time**, so a model imported before its materials existed caches **empty** slots — and the later MaterialPack import does *not* re-trigger it. Skip this and the default colorway plus shared weapon/chain render untextured, silently (it reads as harmless "empty", not "missing").

## Patch a vendor-mutated asset (copy-on-write)

Some DLCs ship a patcher that rewrites a base FBX **in place** so their variant prefab — which references that FBX by GUID — picks up the new mesh. **Never patch the base in place**: it destroys the original, and a later base re-import silently reverts it and breaks the variant. Reconstruct the parallel-patched layout a careful vendor would ship instead. Doctrine is `docs/LAYOUT.md` §*Vendor mutation*; this is the procedure:

1. **Containment** (this is the gate — ask before running any vendor executable). Read the script before running it. Run the patcher against a **copy** of the base FBX (`AssetDatabase.CopyAsset` → a sibling path inside the package), never the base itself and never anything under the asset library (`Y:\`). Verify the output's size + semantics after.
2. **Repoint the variant.** Identify the prefab(s) the DLC ships that reference the base FBX — those are the variant; the base package's own prefabs stay vanilla. Repoint each by swapping the base FBX's GUID → the copy's GUID **everywhere in that prefab's YAML** (one swap catches the mesh and avatar references together — a copy preserves sub-asset fileIDs). A DLC that ships *no* prefab of its own can't preserve coexistence by repointing — stop and ask (fork vs. replace).
3. **Provenance.** Write a sidecar beside the copy recording the replay recipe: patcher, `.hdiff`, source FBX (path + GUID), output, date. It is both the recipe and the marker that flags a base re-import having reverted the patch.
4. **Confirm the split.** Enumerate every reference to the base FBX's GUID across the project; confirm the split (variant prefab → copy, vanilla prefab → base) is intentional and both variants load. The base FBX and the base package's own prefabs stay byte-identical.

## Verify

- `Ryan6Vrc.AgentTools.Editor.CheckPackage.VerifyFolder("Assets/Vendor/...")` → expect `PASS`, and check `read_console` is clean.
- **Null material slots are not failures.** A healthy costume has hundreds of intentionally-empty submesh slots; what fails is *missing* references (a broken GUID), missing meshes, missing scripts, a **stale FBX remap**, or a `loadErrors` count (a prefab that throws on load). Don't hand-count nulls — that's the trap CheckPackage exists to avoid.
- **Benign importer non-determinism is not a fail.** A self-intersecting source polygon makes an `Error`-typed `FBXImporter generated inconsistent result` recur on *every* reimport while CheckPackage stays PASS. Judge it via CheckPackage + slot inspection and record the console line — don't abort on it, and don't let it train you to wave off console errors wholesale.
- A `remapSTALE` FAIL means an FBX's external-material remap resolves but the model imported empty — force-reimport that FBX (step 5) and re-verify.

## gitignore

No per-import change — `/Assets/Vendor/` and `/Photoshop/` already cover every new import. (One-time meta-rule: those lines sit after the stock `!*.meta` un-ignore line; see `docs/LAYOUT.md`.)

So a clean import commits **only** the pre-commit `STRUCTURE.md` regen — `Vendor/` content is untracked by design. Its git trace is a one-line `STRUCTURE.md` diff, nothing under `Vendor/`; don't expect (or hunt for) tracked asset files.
