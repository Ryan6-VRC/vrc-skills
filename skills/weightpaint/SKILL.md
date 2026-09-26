---
name: weightpaint
description: Use when a garment or hair needs its skin weights fixed in Blender — "transfer weights from the body", "the shorts tear toward the leg", "the cuff slides through the wrist", "skin pokes through the bodysuit when I bend", "reweight this outfit", "fold the ribbon bones into the hair" — on demand, never as a step of owning a garment. Skin weights, not blendshape weights. Not the Unity-side dynamics fix or the triage of a reported clip (fix-clipping), not seating a body morph or coverage deletion (own-mergeable), not shrink shapes (map-outfit-shapes).
---

# Fix a garment's skin weights

Fix how a skinned garment or hair follows the body, in Blender: transfer the body's skin weights while every garment bone keeps its own, push a skin-poke region off the body by a millimetre or less, or fold a bone chain into its neighbours; then measure, put the variants in front of the operator in the Editor, and record the pick. The doors, the algorithm and their traps are `blender.md`'s weight-and-fit paragraphs and its §Measuring mesh clipping, the required reading; the metric meanings are `report_fit`'s printed legend. This skill owns the diagnosis, the one gate, and the judgment calls.

**On demand only.** The operator: "own-mergable should transfer blendshapes when the body uses one the mergable does not support. Otherwise weightpainting should only be done on demand." Nothing in owning or composing a garment runs this skill. Who runs the doors is a lean, and stays one: "My lean is that you do the weight transfers yourself but as mentioned you have to be a bit careful when physbones are involved and sometimes the settings need tweaking."

## Scope — what this owns, and the boundary

Skin weights (transfer, fold) and the sub-millimetre rest push that follows a transfer, on any skinned mesh, garment or hair. Two entrances: `fix-clipping`'s pose-overlap and skin-poke rows, which hand over their Turn 1 answers and take the task back after step 7; or a direct ask.

- A garment cut against another body configuration, floating or sinking at rest → the seat, `own-mergeable`'s `transfer_shapekeys` step. It is a precondition; `transfer_weights` refuses an unseated garment.
- Skin removed under cloth → coverage deletion, `own-mergeable` (`mark_coverage`), and only as the operator's last resort (below).
- A shrink shape → `map-outfit-shapes`.
- Chains, colliders, reactive components, FX state, and the triage of a reported clip → `fix-clipping`.

## What counts as a defect

The operator judges, and the measurements only locate and rank: "you are not a good judge of when clipping is acceptable." Intersection is never a pass/fail gate (`blender.md` §Measuring mesh clipping). What the operator counts, in their words:

- "the final edges of clothing might intentionally intersect the body, so that like a cuff does not leave a visible gap and instead just crosses through normal to seal tightly. Intersections increasing on surface vertices during poses would be the real problem"
- "frills flipping is fine and unavoidable, we just need skintight cloth to avoid sinking under the body"
- "some clipping is desirable since in real life the fabric would get folded over but it cannot be completely static"

Two rules, as stated: "We are not deleting skin under cloth except as an absolute last resort due to future graphsphere/alphaclip work"; "Do not solve the glove seam by shrinking the hands because the gloves are transparent."

## The flow

Every door writes `--report`, and the fit doors `--render`, only when passed: pass paths under `test-output/weightpaint/<asset>/`.

### 1. State the row and the spot

On the `fix-clipping` entrance, inherit its answers: where, when, whether it is new, what is off limits. On a direct ask, take the operator's word for which meshes and where. The working file is the costume blend in the venue's `Blender/` mirror, with the body linked; read the venue's record for it first, since the constraints a previous pass left (which meshes follow the leg, which take no leg skin, what was pushed) bind this one. Read the row's prefab for its Set rows, unconditional Deletes and index-addressed `m_BlendShapeWeights` overrides, and carry them as `--shape` and `--cut-shape` on every door; `blender.md`'s `report_fit` paragraph has the reading rules.

### 2. Locate and classify

Run `report_fit --region` on the spot, without `--sweep` so the swept bones derive from it, then `compare_fit --simulate-transfer` with the same flags. Read them together:

- Penetration already there at rest is the seat (`own-mergeable`), a push, or a shape (`map-outfit-shapes`), never weights.
- A posed defect the simulation removes is weights: steps 3 and 4.
- A posed defect it leaves, on vertices already matched with a near-zero weight change (the contact `|dw|` on a `transfer_weights --whatif` line), is shape: a push, the operator's own corrective work, or accept.
- A defect on physbone-class vertices, which no metric covers, goes back to `fix-clipping`.

Never conclude "weights match" from a regional average or a fixed pose set: an average hides the band that tears, and a pose set misses the angle that pulls through. Rank what you find for the operator's eye.

### 3. Choose the transfer shape per mesh

Read it off the mesh's own geometry, never another garment's numbers: `--source-exclude-max` and the blend's centre and width are per garment, which is why none has a default.

- Upper-body pieces and leg-following pieces (tights, garter bands, side straps, leg holes seated on the thigh) take the whole body.
- A strip bridging the thighs takes no leg skin, by `--source-exclude` on the leg chains (the operator: "…or just exclude the two legs might be more general").
- A garment that is both takes `--exclude-blend` with `--exclude-blend-lateral` and `--exclude-blend-smooth`, centre and width read off `report_fit`'s printed frame and extents (the operator: "soften or stop the hip/leg threshold as we get further from the center plane").
- `--no-flip` where a band reaches where two limbs touch; a wide `--normal-angle` for a layer floating off its source; `--shape` for every key the row sets.

### 4. Transfer, then push

Record the venue blend's sha256, then run `transfer_weights --whatif` and read the boundary-band coverage and the unmatched loose parts (`blender.md`). The real run writes an `_ab_` sibling per variant with `--out`, never the venue blend before the pick. Measure each variant with the same `report_fit` flags and set them beside the venue blend with `compare_fit`.

Push only where the sweep shows skin coming through between garment vertices (the operator: "0.5 or 1mm move on the problem area … rotate the legs 90ish degrees forward and see where it pulls through"), once, after the transfer: `push_garment` on the transferred variant, written as its own `_ab_` sibling.

### 5. A/B in the Editor

Stage the variants beside the live mesh by [references/editor-ab.md](references/editor-ab.md). **Gate: the operator's pick** between the live mesh and the variants. The metrics rank them and never decide; a variant can top every metric and still lose to the eye.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`). This gate queues and never defaults: build and stage the variants, leave the venue blend unpromoted, and surface the pick.

Promote the pick by the reference's last step: its blend copied over the venue blend once the checksum shows the venue blend unchanged.

### 6. Record

In the venue's record for the blend, as the asset is (`VENUE.md`): each door's `recipe:` line in the order they ran (the doors also stamp them on the mesh, where `report_stamps` reads them back), and the standing constraints: which meshes follow the leg, which take no leg skin, what was pushed. No readings.

### 7. Verify

`report_fit` on the promoted blend with the same flags reads as the picked variant did. Then `export_unity_fbx` to the venue's `Models/` exactly as the blend's own export runs, `ConformImportSettings` on the folder (`unity-tools.md`), and the re-import diff (`blender.md`), where a weights-only change moves no vertex and a push moves each by at most its amount. The emulator or full-body-tracking pass through the joints the defect named is the operator's, a named handoff. On the `fix-clipping` entrance, hand back: its watch list and terminal handoff stay there.

## Bone-fold branch

A bone chain the operator wants gone (a hair's ribbon bones) folds rather than transfers. Run `fold_bones --map auto --map-out` and edit the table where a strand, not the scalp, should carry the weight: the auto split and a transfer from the surrounding mesh both give weight to the nearest surface's bone, which on hair is the scalp, and a ribbon knot on the scalp moves stiffly with the head instead of with the bun it is tied to. Run the fold with the edited `--map`, measure with `report_fit` sweeping the surviving bones, and record the table and the recipe line. PhysBone roots and ignore lists naming the removed bones break where the door cannot see (`blender.md`); the compose step re-checks them. A fold variant needs the bone rebinding the A/B reference describes.
