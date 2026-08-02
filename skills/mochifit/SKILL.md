---
name: mochifit
description: Use when refitting an outfit authored for one base body onto a genuinely different (non-topo) base — "put this Beryl outfit on Nouvelle", "mochifit this dress to X", "refit this outfit across bases" — with the MochiFitter vendor tool doing the warp; also installing MochiFitter or a conversion profile ("set up MochiFitter", "install the Milltina profile"). Covers route choice through the profile graph, the unattended drive, and owning + verifying the warped output. Not a topo-bridgeable base change (equivalency edge — reproportion), not owning geometry or authoring a seam (own-mergeable), not placing the finished piece (compose-mergeable), not the clothing↔blendshape map (map-outfit-shapes).
---

# Refit an outfit across bases

Take a garment authored for base A and land it owned, seamed, and verified on a non-topo base B, with MochiFitter doing the warp. Tool facts — the profile model, the UI traps, the measured modal and backend behavior — live in `docs/mochifitter.md` and are the required reading; `docs/outfits.md` owns the coupling model the shape choices feed on; `docs/LAYOUT.md` owns where the output files. This skill owns the sequence, its gates, and the judgment: route choice, the reflection drive, and what "verified" means for baked geometry.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## Scope — what this owns, and the boundary

- Entry is gated on **genuinely non-topo**: when the two bases are the same or bridged by an equivalency edge, route to `reproportion` — a refit takes minutes and bakes geometry an edge would leave live.
- The deliverable is a mergeable **drop-in-equivalent to an owned one** (`own-mergeable`'s bar), filed in `docs/LAYOUT.md`'s refit bucket. Placing it is `compose-mergeable`; reconciling the clothing↔blendshape coupling on the composed avatar is `map-outfit-shapes`.
- The output lands at the **stock** target base's proportions — profiles describe vendor bases, not our reshapes. A reshaped target takes the in-place own (`own-mergeable`) plus `reproportion`'s outfit-fit afterward, never a re-run against geometry no profile describes; sculpt or weight-paint touch-up is the same in-place own, later, not a leg of this flow.

## The flow

### 1. Dependencies, detected loud

The tool and each conversion profile are detected dependencies: absent, fail loud naming exactly what is missing — never degrade, never substitute.

- Detect the tool by its window type loading; detect a route in step 2's graph, not by grepping filenames.
- **Install the tool from the operator's asset library** (a zip wrapping a `.unitypackage`; extract to scratch first — `import-vendor-asset` owns the zip hygiene and the `ImportPackage` door). Import **over** any existing install and never clean the tool's folder first: installed profiles are not all reproducible from the library (community profiles exist), and an over-import leaves profile-class files untouched (measured).
- **A profile is a `.unitypackage` that installs into the tool's own scan folder** — `docs/mochifitter.md`'s placement rule; relocating it blinds the tool. Some avatars ship sibling shape-variant packages because the tool holds only two shape slots at a time — which sibling to install is a route decision, step 2's.
- The installed tool version is whatever is on disk: record it in step 6's sidecar and don't chase the vendor's release cadence — step 3's re-derivation is what absorbs it.

### 2. Resolve the route

- Read the conversion graph from the window's own route-record list, or from each config's contents — never from filenames (`docs/mochifitter.md`; shipped names contain typos the tool itself ignores).
- **Direction is a gate**: dressing a base needs its inbound config, undressing one its outbound, and most profiles ship one way only — confirm the direction exists before promising the conversion.
- Multiple viable routes: **fewest hops wins** (every hop is a full warp; warps compound), tie broken by newest profile version. Shape-variant siblings are not hop arithmetic — derive the needed variants from the target base's driven morphs (`docs/outfits.md`) and **surface the choice to the operator with the differences named**; a silent default is a silent fidelity loss.
- No route after installing what the library offers → fail loud naming the missing profile and direction.

### 3. Configure by reflection, verify every write

- Reach the live window instance and **re-derive its state model by reflection each run** — match members by name and role at runtime, and keep every discovered member name out of tracked files: they are vendor internals, and committed names would churn with the vendor's release cadence where re-derivation does not.
- Set the target avatar, then the source route, driving the window's own update path after each selection — the two-fields trap is `docs/mochifitter.md`'s, and a run configured target-only succeeds while producing the wrong conversion.
- **Blendshape selections are an operator gate.** The offered list is source-side; selections are inputs to the solve, and a wrong one is a silent fidelity loss, not an error. Derive a default from the target's coupling needs, present it, and record the final selection for step 6.
- A write is proven only by state the window derived itself — the config path it resolved, the base asset it swapped, the shape list it repopulated. A poke that had not taken effect could not produce those.

### 4. Fire and observe

- Pre-fire gate: the tool's folder is clean of `_temp.json` (`docs/mochifitter.md` — a failed run's leftovers are consumed silently).
- The execute entry point is async and returns immediately: poll the window's progress state and watch the output folder — **completion is the finalized prefab landing on disk**, not a callback.
- The completion modal wedges the Editor's tool queue (`docs/mochifitter.md` has the measured identity): pre-arm the vendor's static result-dialog suppression flag by reflection, or dismiss it with `tools/unity-dialog.ps1`. Budget ~5 minutes for a ~10-mesh outfit and poll rather than block.

### 5. Verify the warp

- **Humanoid-bone coincidence before any render**: compare output-vs-target-body `Animator.GetBoneTransform` world positions by bone name — sub-millimeter agreement is the healthy signature (a verified run measured ~0.001 mm). `CheckSeam` refuses the raw output (`docs/mochifitter.md`); it scores later, placed on the real base at compose.
- Then sweep poses per `docs/verify.md` — rest pose proves nothing here, and mesh reads go through `BakeMesh`, never `renderer.bounds`.
- Blendshape census: the source's shapes minus the consumed shape fields, plus the target's variant additions, exact names per mesh — diff against the selection recorded in step 3.
- **The orphan report is a duty, not a fix**: name each source bone the target base lacks and the meshes whose weights renormalized away — a property of the base pair (`docs/mochifitter.md`); surface it and stop.

### 6. Own the output

- File the FBX + finalized prefab into `Assets/Outfits/<TargetBase>/<Outfit>/` — `docs/LAYOUT.md`'s refit bucket; never `Vendor/`, never a refit-specific tree.
- **Write the provenance sidecar** beside it: tool version, profile packages + versions, route taken, shape selections, date. It is the bucket's recovery artifact in place of a `.blend` mirror, and what `compose-mergeable`'s provenance routing reads.
- **Independence gate**: `AssetDatabase.GetDependencies` on the prefab reaches nothing under the tool's folder — the refit must survive uninstalling MochiFitter. Both backend settings pass this today (`docs/mochifitter.md`); assert it anyway.
- The output has carried its MA seam across on every verified run — **confirm the seam rather than author it**; a bare output routes to `own-mergeable` Phase 2B.
- Prefab hygiene as in `own-mergeable` Phase 3: gate on `PrefabUtility.GetPrefabAssetType` rather than assuming the vendor's reconstruction is a Variant, and zero any staging offset before saving.

### 7. Hand off

`compose-mergeable` places it (reading the sidecar where the bucket has no `.blend` stamps); `map-outfit-shapes` reconciles the coupling on the composed avatar; cosmetic fit is the operator's playmode eye. Report what was refitted, the route and selections, the orphan report, and the measured coincidence — a hand-off the next skill can gate on, not a "done".
