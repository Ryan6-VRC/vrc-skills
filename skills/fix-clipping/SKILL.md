---
name: fix-clipping
description: Use when a user reports clipping on a built avatar and wants it fixed — "my model clips", "the skirt kicks through the hips when I dance", "physbones go through the body", "legs poke through the dress when I sit", "hair clips through the shoulders" — and for the triage that decides which mechanism owns the fix. Owns the dynamics fix (colliders, chain settings) outright; routes static and slider clipping to map-outfit-shapes, weights and coverage deletion to own-mergeable, and whole-outfit fit mismatch to reproportion or mochifit. Not measuring coverage for a new costume, not the shape map on its own.
---

# Fix clipping

Turn "my model clips" into a classified cause, the cheapest reversible fix that addresses it, a number that shows the fix landed, and a watch list the user runs in the client.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## Turn 1: ask what no door can read

Classification is the hard step and the user often narrows it for free. One message, at most four short asks, each answerable in a line; take anything else offered. Never ask what a door reads (configuration name, chain names, which colliders exist, slider values). Do not ask for a screenshot: model vision on avatar renders is not evidence here, and the only image use in this skill is a deterministic diff.

1. **Where and when.** Which two things touch, and does it happen standing still, in a specific pose (sitting, arms up, crouch), while moving (dancing, walking), or only at a slider or toggle setting?
2. **Is this new?** If it worked before, the cause is an override, a toggle, a proportion change or a package bump, not physics.
3. **Is that skin ever meant to show?** Does the piece ever come off?
4. **Anything off limits?** Silhouette, mesh edits, a Blender round-trip, a rank budget.

The asks are a lean, not a gate: a user who has already said "the skirt clips through my hips when I dance" has answered 1, and you skip to the door.

## Classify: the door first, then the table

Pin the venue and run `Ryan6Vrc.AgentTools.Editor.ReportClearance.Run(avatarRoot, bodyMesh, chainPrefix)` on the region before choosing a branch (contract: `unity-tools.md`). The interview cannot tell a weight mismatch from a chain problem; the report can: it prints which bones weight the body and the garment near each chain, whether any chain is already inside the body at rest, which colliders reference which chains, and each chain's angle limits. Read `surface=` in its summary: `scene` means the composed reactions were not applied and the clearances are the raw instance's.

| Signal | Branch | Who writes |
|---|---|---|
| Everything clips a little, everywhere, after a base change or on a cross-base outfit | Fit mismatch: decline here | `reproportion` / `mochifit`; `CheckSeam` is the gate |
| Clips standing still, no slider involved | Static overlap: shrink shapes, Delete-mode `ShapeChanger`, `MeshCutter` | `map-outfit-shapes` |
| Clips only at some slider value | Slider follow: `BlendshapeSync` by name with a remap curve (`outfits.md`) | `map-outfit-shapes` |
| Garment through garment | Inner-garment shrink or Delete row authored on the outer piece; the body coverage carrier does not apply | `map-outfit-shapes`; a Blender shrink key is the user's |
| Clips in game but not in the editor | FX state: read the driven state in play before believing the editor (`outfits.md` parameter-default rule) | this skill, diagnosis only |
| Clips in a held pose, no chain involved; body and garment near the region ride different bones | Pose overlap: a shrink shape on the body under the garment often covers it and costs no round-trip; weight transfer only when the shrink cannot reach the pose | `map-outfit-shapes` first; `own-mergeable` for the weights, user-run or user-approved in Blender |
| Clips while moving, a physbone chain involved | Dynamics: §The dynamics fix | this skill |
| Skin permanently covered and the user wants the polygons gone | Occlusion deletion: `mark_coverage` carrier (`blender.md`) plus the Delete row declared on the costume prefab (`outfits.md`) | `own-mergeable` for the carrier, this skill for the row |

**Rest overlap goes first.** A chain the report shows inside the body at rest (`insideBodyAtRest` above zero) cannot be fixed by a collider, and a dynamics fix measured over a rest overlap reports a fake improvement. Take the cheapest reversible fix first and name the root cause you did not fix; the task stays here across a handoff, and re-running the report is how you re-enter the dynamics branch.

**Occlusion deletion is gated.** It is a Blender round-trip and a permanent cut, offered only after a reversible fix is ruled out and the operator has said to make it permanent. `mark_coverage` measures rest-pose cone coverage with a kin rule and reports its residue; it does not certify "never visible in any pose".

**A texture-mask cut is the reversible alternative**: an MA `MeshCutter` carrying `Vertex Filter - By Mask` components deletes the triangles an exact-black (or exact-white) mask region covers, at build, with no Blender round-trip. Set each filter's selection mode to `AllVertices`; its default `AnyVertex` takes every triangle with one vertex in the region, visible edge triangles included. A filter reads one material slot and the cutter's default `VertexIntersection` ANDs its filters per slot, so filters on different slots cut nothing: intersect only filters on one slot, one per material that can occupy it. The cutter runs before VRCFury (`nondestructive.md`), so a material a VRCFury swap puts in the slot needs its own filter, or the cut follows the bound material's mask and removes triangles the swapped one shows.

## The dynamics fix

0. **Audit the existing collider set** from the report's collider table. A region chain in a collider's `notReferencing` list is often the whole bug; so is a radius nobody sized. Fix the wiring before sizing anything.
1. **Read the cause.** The weight table: body riding one bone set and garment another is the relative motion that clips. The chain root's constraint sources: a skirt whose roots follow the chest over a body on the hips reaches the hips only through the constraint's weight. Angle limits: a chain flagged `lateralLocked` cannot be pushed sideways by any collider; loosening it may be the fix, and it is what a sitting pose usually needs.
2. **Ownership gate.** The prefab owning the chains and the prefab owning the collider bone can differ (hair chains in the hair prefab, collider on the base's shoulders). Either under `Assets/Vendor/` or `Packages/` routes to `own-mergeable` or `own-gimmick` first; never write there (`LAYOUT.md` §Vendor mutation). A collider referenced across prefabs needs an MA-side placement so the reference survives the merge.
3. **Choose, reversible first.**
   - **Resize the collider already on the bone the body region rides.** The operator's lean, quoted: "thinning chains just makes them likely to spread over a collider which lets things like legs slip between chains and clip massively so the best approach [is] just shrinking the body colliders."
   - **Add the colliders the region needs where none exist**: hips plus both upper legs for a skirt, chest plus shoulders for hair. Size for the measured effect, not the skin: a capsule sized to the body surface leaves residual overlap because collision resolution is partial per solver step, and the collider that fixed the source case was thinner and taller than the geometry. It must touch no chain at rest (the report's summary reads `restContact=0` after the write, and no chain prints `—` for a collider it should be measured against), and contact must land well below the chain root, since a touch near the root levers the hem. Capsule `height` is the core segment; the rounded ends add two radii, and the report prints `endToEnd` beside `height` so the two are never confused (the SDK's contact shapes count their caps inside `height`; physbone colliders do not).
   - **Chain settings**: `immobile` and its type (World for a hem that flies on walking, local otherwise); angle limits for the sitting case; the radius curve widened at the hem so legs cannot slip between chains; gravity and its falloff to make a hem hug; grab and stretch settings for a chain pulled through the body. Read `runtime.md` §PhysBones for what each force actually does.
   - **Re-weight the chain roots' constraint** toward the moving bone when the garment hangs from a different bone than the body. The root-cause fix, at the cost of the skirt following every hip motion.
   - Named only: a second inner chain set; a contact-driven corrective shape (`author-gimmick`).
4. **Apply** with `PrefabUtility.LoadPrefabContents` on the owning prefab, copying that prefab's existing collider idiom (where they sit, how they are named). Confirm the scene instance carries no override masking the write. Re-read the physbone stats and name the rank delta: chains times colliders is collision checks (`optimization.md`).
5. **Verify.** Re-run `ReportClearance`: the summary reads `restContact=0`, and every chain the collider should cover prints a `restContactCm=` token rather than `—` (a dash is an unmeasured chain, not a clean one). Then the play-mode harness ([references/play-penetration-probe.md](references/play-penetration-probe.md)), component off then on, for the motion number. Pass: `depthCm` lower at every motion pose with the component on, and zero tip movement in the `on | rest` row. Report the residual as a number, not as "fixed".
6. **Record** the collider in the venue's costume README as the standing constraint on the next edit, never as the readings (`VENUE.md`).

## Hand off with a watch list

The user's in-client test is the final verification, and "dance and watch" is not enough instruction. Emit the rows for the branch you took:

| Branch | Tell the user to |
|---|---|
| Dynamics | Run the motion that reproduced it; watch in third person from behind and below for a skirt; distinguish the two signatures, a smaller version of the old clip (residual) from new jitter or a hem kick (the collider touches at rest); stand still ten seconds; scale the avatar up and down; grab the chain; check in a real instance, not the mirror |
| Static, slider | Both extremes of every slider involved, and each toggle off |
| Weight | The specific joints: elbow full bend, arm overhead, knee to chest, spine twist |
| Deletion | Every pose and toggle combination that could expose the region, since the cut is permanent |
| FX state | The exact parameter default the editor was not showing, and the toggle that flips it |

Name what is still open the way the source case did: the extremes where clipping remains, in centimetres, and the assumption the measurement rested on (how far the hips really move).
