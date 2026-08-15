---
name: mochifit
description: Use when refitting an outfit authored for one base body onto a genuinely different (non-topo) base — "put this Beryl outfit on Nouvelle", "mochifit this dress to X", "refit this outfit across bases" — with the MochiFitter vendor tool doing the warp; also installing MochiFitter or a conversion profile ("set up MochiFitter", "install the Milltina profile"). Covers route choice through the profile graph, the unattended drive, and owning + verifying the warped output. Not a topo-bridgeable base change (equivalency edge — reproportion), not owning geometry or authoring a seam (own-mergeable), not placing the finished piece (compose-mergeable), not the clothing↔blendshape map (map-outfit-shapes).
---

# Refit an outfit across bases

Take a garment authored for base A and land it owned, seamed, and verified on a non-topo base B, with MochiFitter doing the warp. Tool facts — the profile model, the UI traps, the measured modal and backend behavior — live in `docs/mochifitter.md` and are the required reading; `docs/outfits.md` owns the coupling model the shape choices feed on; `docs/LAYOUT.md` owns where the output files. This skill owns the sequence, its gates, and the judgment: route choice, the reflection drive, and what "verified" means for baked geometry.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## Scope — what this owns, and the boundary

- Entry is gated on **genuinely non-topo**: when the two bases are the same or bridged by an equivalency edge, route to `reproportion` — a refit takes minutes and bakes geometry an edge would leave live.
- An **install-only ask** ("set up MochiFitter", "install the X profile") runs step 1 and stops: report what landed and which routes it opened. Steps 2–7 need a named outfit and target base.
- The deliverable is a mergeable **drop-in-equivalent to an owned one** (`own-mergeable`'s bar), filed in `docs/LAYOUT.md`'s refit bucket. Placing it is `compose-mergeable`; reconciling the clothing↔blendshape coupling on the composed avatar is `map-outfit-shapes`.
- The output lands at the **stock** target base's proportions — profiles describe vendor bases, not our reshapes. A reshaped target takes the in-place own (`own-mergeable`) plus `reproportion`'s outfit-fit afterward, never a re-run against geometry no profile describes; sculpt or weight-paint touch-up is the same in-place own, later, not a leg of this flow.

## The flow

### 1. Dependencies, detected loud

The tool, its Blender, and each conversion profile are detected dependencies: absent, fail loud naming exactly what is missing — never degrade, never substitute.

- Detect the tool by its window type loading; detect a route in step 2's graph, not by grepping filenames.
- **Install the tool from the operator's asset library** (a zip wrapping a `.unitypackage`; extract to scratch first — `import-vendor-asset` owns the zip hygiene and the `ImportPackage` door, but **not its relocate/flatten step: this tool stays at its native install path and is never moved under `Vendor/`**, `docs/LAYOUT.md`'s self-scanning-tool exception). Import **over** any existing install and never delete the tool's or profiles' own files first: installed profiles are not all reproducible from the library (community profiles exist), and an over-import leaves profile-class files untouched (measured).
- **A profile is a `.unitypackage` that installs into the tool's own scan folder** — `docs/mochifitter.md`'s placement rule; relocating it blinds the tool. Some avatars ship sibling shape-variant packages because the tool holds only two shape slots at a time — which sibling to install is a route decision, step 2's.
- **The tool's Blender is per-venue, and it installs its own** — under `<ProjectRoot>/BlenderTools/`, nothing to do with the machine's Blender (`docs/mochifitter.md`). A venue that has never run a refit holds `Execute Retargeting` disabled until it lands, so detect it by the window's own `Blender Status:` row before configuring anything, install from the `Download & Install` button beside that row, and report the download as a step of its own — a few hundred MB over the network, not a click.
- The installed tool version is whatever is on disk: record it in step 5's sidecar and don't chase the vendor's release cadence — step 3's re-derivation is what absorbs it.

### 2. Resolve the route

- Read the conversion graph from the window's own route-record list, or from each config's contents — never from filenames (`docs/mochifitter.md`; shipped names contain typos the tool itself ignores).
- **Direction is a gate**: dressing a base needs its inbound config, undressing one its outbound, and most profiles ship one way only (`docs/mochifitter.md`) — confirm the direction exists before promising the conversion. The route is decidable from the profile packages' contents alone (list the `.unitypackage`), so check it before installing the tool when the route is in doubt.
- Multiple viable routes: the graph is hub-and-spoke, so a pair normally has exactly one two-hop route — but a **direct profile beats via-template when one exists** (fewer warps compound less error), and ties break to the newest profile version. Shape-variant siblings are not hop arithmetic — derive the needed variants from the target base's driven morphs (`docs/outfits.md`) and **surface the choice to the operator with the differences named**; a silent default is a silent fidelity loss.
- No route after installing what the library offers → check the vendor library for sibling variants of the outfit before declaring blocked (a multi-variant package often ships other base targets, most of them routable); then fail loud naming the missing profile, direction, and any routable siblings found.

### 3. Configure by reflection, verify every write

- Reach the live window instance and **re-derive its state model by reflection each run** — match members by name and role at runtime, and keep every discovered member name out of tracked files: they are vendor internals, and committed names would churn with the vendor's release cadence where re-derivation does not.
- Set the target avatar, then the source route, driving the window's own update path after each selection — the two-fields trap is `docs/mochifitter.md`'s, and a run configured target-only succeeds while producing the wrong conversion.
- **Blendshape selections are an operator gate.** The offered list is source-side; selections are inputs to the solve, and a wrong one is a silent fidelity loss, not an error. Derive a default from the target's coupling needs, present it, and record the final selection for step 5.
- A write is proven only by state the window derived itself — the config path it resolved, the base asset it swapped, the shape list it repopulated. A poke that had not taken effect could not produce those.

### 4. Fire and observe

- Pre-fire gate: **delete every `_temp.json` under the tool's folder** — disposable residue every fire regenerates (`docs/mochifitter.md`); firing over leftovers risks a silently-consumed stale hop. Locate with Glob (the `*_temp.json` pattern under the tool root); `execute_code`'s `safety_checks` blocks `File.Delete` and Bash sweeps are denied by the harness classifier.
- The execute entry point is async and returns immediately: poll the window's progress state and watch the output folder — **completion is the finalized prefab landing on disk**, not a callback.
- The completion modal wedges the Editor's tool queue (`docs/mochifitter.md` has the measured identity): pre-arm the vendor's static result-dialog suppression flag by reflection, or dismiss it with `tools/unity-dialog.ps1`. Budget ~5 minutes for a ~10-mesh outfit and poll rather than block.

### 5. Own the output

- File the FBX into `Assets/Outfits/<TargetBase>/<Outfit>/Models/` and the finalized prefab at the bucket root — `docs/LAYOUT.md`'s refit bucket, the same shape as an owned one; never `Vendor/`, never a refit-specific tree.
- **Write the refit sidecar** (`refit-provenance.json`) beside the prefab, keys `target_base`, `target_state`, `source_base`, `outfit`, `tool_version`, `profiles[]`, `route[]`, `shape_selections[]`, `date` — this list is the canon (`compose-mergeable` reads it); fill every key from this run, the recorded shape selections included.
- **Independence gate**: `AssetDatabase.GetDependencies` on the prefab reaches nothing under the tool's folder — the refit must survive uninstalling MochiFitter. Both OMOCHI checkbox states pass this in the measured runs (`docs/mochifitter.md`); assert it anyway.
- The output has carried its MA seam across on every verified run — **confirm the seam rather than author it**; a bare output routes to `own-mergeable` Phase 2B.
- Read `PrefabUtility.GetPrefabAssetType` — don't assume Variant and don't force it; a `Regular` reconstruction is fine here, and only `Model`/`MissingAsset`/`NotAPrefab` fails. Zero any non-zero root transform on the asset before verifying — the seam you just confirmed is `MergeArmature`, so `own-mergeable` Phase 3's staging-offset rule applies and its bone-proxy exception cannot.

### 6. Verify

Run every check against an **instance of the saved prefab** — the delivered artifact, not the pre-filing output.

- **Humanoid-bone coincidence before any render**: `CheckSeam.CheckBare("<target body scene path>", "<instance scene path>", maxOffsetMm: 0.01f)` — both handles are **scene paths**, not objects or asset paths. It is the pre-seam door (`docs/unity-tools.md`), pairing by bone name because the raw output's `MergeArmature` has no base to resolve against yet and `CheckSeam.Run` rightly abstains. **The tolerance is this skill's to state, and 0.01 mm is it**: solver-noise scale, measured runs landing at ~0.001 mm — millimetre-scale is a wrong result, not slop.
  - `NOT-PASS` → the likeliest cause is step 3's two-fields trap: don't hand off, re-confirm the route against the window-derived config, re-fire, re-own.
  - `REFUSE` → the gate abstained rather than scored, and there is no fallback measurement to fall back to. Read which refusal it is — wrong roots, no shared bone names (the output kept its *source* base's names), a duplicated armature under the output (an inactive one counts), or too few shared weighted bones (a failed transfer, not a near miss) — and fix that before re-running. Never hand off on a REFUSE: nothing was certified.

  `Check` scores later, placed on the real base at compose.
- Then sweep poses per `docs/verify.md` — rest pose proves nothing here, and mesh reads go through `BakeMesh`, never `renderer.bounds`.
- Blendshape census: the source's shapes minus the consumed shape fields, plus the target's variant additions (`docs/mochifitter.md`), exact names per mesh — diff against the selection recorded in step 3.
- **The orphan report is a duty, not a fix**: name each source bone the target base lacks and the meshes whose weights renormalized away — a property of the base pair (`docs/mochifitter.md`); surface the report, attempt no repair, and continue to the hand-off.

### 7. Hand off

`compose-mergeable` places it (reading the refit sidecar where the bucket has no `.blend` mirror); `map-outfit-shapes` reconciles the coupling on the composed avatar; cosmetic fit is the operator's playmode eye. Report what was refitted, the route and selections, the orphan report, and the measured coincidence — a hand-off the next skill can gate on, not a "done".
