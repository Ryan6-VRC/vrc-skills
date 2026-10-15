---
name: rig-skirt
description: Use when redoing the physics of a skirt or apron on an owned costume — "redo the skirt physics", "make the skirt flow better", "put hinges on this skirt", "group the back strands", "cross-link the strands", a vendor skirt or apron that clips, reads stiff, grabs badly or costs too much in physbones. Diagnose, offer costed arrangements of physbones, constraints and colliders, build the operator's pick. Not clipping triage or a collider fix on a rig you keep (fix-clipping), not skin weights or a garment tearing at a joint (weightpaint).
---

# Rig a skirt

Primary reader: an agent with a venue open, one owned costume with a skirt or apron in front of it, that venue's Editor pinned. This skill owns the forms, what each costs, the tables you derive, the order and the gates; `WriteDynamics`, `DrivePhysBones`, `GrabPhysBone`, `ReportClearance` and `ReportClipping` do the mechanics (`unity-tools.md`), and none of them knows what a skirt is. Required reading: `runtime.md` §PhysBones and §Constraints (VRC), `optimization.md` §PhysBones and §Measuring, `verify.md`, and `fix-clipping` §The dynamics fix. Every edit lands on the costume prefab (or its blend and FBX), never on an avatar variant that wears it or on the scene.

**The pick is the operator's**: the design space is too open to go straight from a diagnosis to a build. **No operator to ask?** Follow the no-operator protocol (`workflow.md`); with no channel at all, the derivable default is to stop after step 2 with the diagnosis, the unanswered style questions and the arrangements written up, and build nothing.

**One active avatar per play session, toggled in edit mode only**; the play-entry gate refuses a scene with more (`verify.md` §The play-entry gate). A toggle issued while play mode is still tearing down reverts silently, and the next session then drives the other avatar: an inactive avatar reads zero jitter, zero travel and carries no `$`-suffixed merged bones, so check both before trusting a play reading. Which costume bones survive the build as `$` children differs by avatar, so read the skirt root's and the legs' play paths on each avatar before a live table or a pose (`nondestructive.md` §Merge behaviours that change what you author).

## The flow

### 1. Diagnose

Read the costume's rig (strands, azimuths, bones per strand, which bones skin, physbone and collider fields against the vendor prefab's) and the costume's record. `ReportClearance` scoped to the skirt root gives rest overlap and `lateralLocked`. Drive the vendor rig as stage `old` with the battery (§Driving and the gates); it is the yardstick, driven again in this session and never borrowed from another. If the prefab no longer carries the vendor rig, rebuild it on an unpacked in-scene duplicate of an avatar wearing the costume, with the vendor physbones copied from the vendor's prefab, drive and bake that, then delete it. Bake the avatar for its counts (`optimization.md` §Measuring owns the recipe). Name what clips and why: the panel or the band, gravity, limit direction, collider placement, chording segments.

### 2. Read the style, then offer two or three arrangements and wait

The arrangements turn on calls that belong to the venue, not to this skill. Settle each before offering:

- grab and pose policy for the strand and hinge physbones, and whether the strands take hand collision;
- the lock mechanism, if any, and what it covers;
- hinge policy: a first-pass arrangement, or an escalation offered only on evidence (§Hinges);
- the minimum simulated bones a strand keeps below a constraint;
- the cap on the neighbour share;
- a donor prefab per form;
- the test motion and the stopping rule;
- which layer's clipping counts;
- obstacles that meet the skirt (a tail, a held prop), with any key names the venue reserves for them.

A venue's root README may answer these, each answer carrying its weight; absent, ask. A rule is applied; a lean is offered beside the pick and never applied silently.

Check each named obstacle where it meets the skirt at rest. An obstacle's root crossing a tight garment where it must is not a clip; a skirt the obstacle's body clips takes the venue's reserved key in this run's Blender pass, and its weight on the costume prefab is the value the operator's eye settles.

Each arrangement is a form from §The forms (plus the grouping route where it pays), with the group map if grouped, a cost line (components, transforms, constraints, collision checks, by `optimization.md` §PhysBones's counting rule against the bake), what it buys in motion, what it risks, any Blender pass it needs, and every field value that comes from no donor (§Deriving the table). Name the protection each leg-fed form carries (§Hinges). Recommend one. Put the open settings beside the pick: gravity, the limit type and tilt, a leg weight. **Build nothing before the operator's pick.**

### 3. Back up

Back up the prefab, and for a Blender pass the blends, FBX and `.meta`, under `test-output/<run>/backup/`. The external backup is not the in-session rollback.

### 4. Build the pick

Blender pass first when the pick needs one (§Grouping). Derive the table (§Deriving the table) as one JSON table: node rows, then moves, physbone field sets and constraint rows, paths relative to the costume prefab root, a field set on a moved physbone naming its new root. `WriteDynamics.Run(prefabPath, table, whatIf)`, what-if first, then real. After every write that touches a constraint, read each top bone's `RotationOffset` off the written prefab: a mean under about 20° is right, near 90° is the frame trap (§Deriving the table), fixed before any drive. An existing collider's fields are the table's `colliders` rows; a new collider is a `nodes` row's.

### 5. Relock and cut

Re-run the venue's lock mechanism if it has one, since a lock generated over the old chains is stale after the write. Run §The free component cut, and relock again if a merged chain sits under the skirt root.

### 6. Drive and settle

Drive as `new`, same poses and arguments as `old` (§Driving and the gates); for a constraint form, find the cliff and settle the share. Every drive and sweep is yours and runs unattended (`fix-clipping` §The loop runs unattended): the operator is never asked to drag the model between candidates, and what reaches them is the settled result. An addendum asked for at step 8 (a leg feed, a weight bump) runs as its own small loop: derive, write, frame-trap read, drive, offer the value as a choice.

### 7. Record

One bullet in the costume's record naming the form, every added node, group top, proxy and collider path, the share and any leg formula, as the constraint on the next edit and never a reading (`VENUE.md`); a Blender pass adds a line on the new bones and the command that made them.

### 8. Verify, then put it to the operator

At the final head (table written, lock regenerated, cut run), the last drive is of that head; any write after it takes one more. Re-run `ReportClearance` on the skirt root: every chain a collider should cover prints `restContactCm=` and none reads a major deflection. Bake old against new. Then put it to the operator: the drive rows old against new, the `ReportClipping` split per region, the bake, the grab, anything that failed a gate, and what the next step up would cost. Render nothing; a render is not evidence here (`verify.md`). **Sign-off is the operator's word in the session on the rig as tabled.** Then commit the venue's repo if it carries one (`LAYOUT.md` §Principles): stage the paths you changed by name, since another session's files may sit in `git status`, with a one-line message.

## The forms

- **Settings and colliders only.** One physbone per chain, no constraints: the single-sheet form (an apron, free panels). The limit type, its lateral allowance and `limitRotation` are settings the offer states; hold `limitRotation` at 0 unless the panels' bone rolls agree, since opposed rolls lean one group into the body under any tilt, and a Blender pass can unify them. The work is the colliders (§Colliders). Gravity is an open setting (step 2), never kept or changed silently.
- **Neighbours-only.** Each strand's top bone stops simulating: its physbone moves down to the second bone, and the top carries a `VRCRotationConstraint` over its two ring neighbours' second bones at 0.5 each, `GlobalWeight` at the share. No hinge, no plane.
- **Neighbours plus a small leg feed.** Neighbours-only, and every front top also reads both upper legs through per-top proxy nodes (§Deriving the table). Carries a protection (§Hinges).
- **Hinged.** Leg hinges beside the skirt root lead the front strands ahead of a raised leg. A hinge is a node under the root's parent bone carrying a leg-sourced `VRCRotationConstraint`, with a child carrying a single-bone physbone (nonzero endpoint, Hinge limit, World immobile) that collides with a plane on Hips, so it leads the leg forward and never trails it back; each front top reads both hinge physbones by azimuth.
- **Spine-rooted.** A skirt hanging from Spine or Chest: the hinged form with three deltas (§Deriving the table).
- **Grouped**, a route any constraint form can take: strands grouped under one new top bone that carries the constraint, one physbone per group with multi-child Ignore (§Grouping).

A top-bone constraint sources simulated bones, so it solves post-physbone and its strand sees the rotation on the next solve; that is why the constrained bone sits above its own chain root, never inside it (`runtime.md` §Constraints (VRC)). What the constraint forms buy: strands turn through their limit cone instead of a locked hinge, a grab carries its neighbours falling off with ring distance, and the neighbour whose cone admits the pull follows while the other barely does. A strand keeps at least the venue's minimum of simulated bones below its top (step 2); one with fewer needs its top doubled (§Grouping) before a constraint form fits. A strand driven only by constraint interpolation between simulated neighbours has no physbone of its own and collides with nothing, so a leg passes between the simulated ones; reduce strands by a Blender re-weight or a grouping instead.

**What each form costs**, by `optimization.md` §PhysBones's counting rule:

- Replacing a strand's top bone with a constrained one gives back one physbone transform and adds one constraint.
- Doubling a top bone is net zero on transforms, and every doubled strand needs a physbone of its own, so a ring one component covered gains a component per strand less one.
- The hinged form adds two components, two transforms, two constraints, one collider and two collision-check rows.
- Grouping cuts components by members minus one per group, and each new top adds a transform; it is how a doubled top stops costing components.
- Thinned collider lists cut collision checks (§Deriving the table).
- Every constraint counts toward `constraintsCount`, priced against its line like any other stat (`optimization.md` §The line).

The offer weighs what each form buys in full-body motion against these counts; the weighing is the operator's.

## Hinges

A top that reads the legs swings with them, so a leg moved back can pull the skirt into the body; neighbours-only and settings-only tops never read the legs and need no protection. A leg-fed form carries one: a hinge, or a collider that catches the chain when the rotation pushes it back through the torso. A collider guards every segment only when the constrained top is a transform inserted above the strand (a doubled top), since a replaced top's own segment is not simulated and no collider stops it. The offer says which protection a leg-fed form carries and where.

A small leg feed can ride on the leg colliders alone when the skirt has margin: it projects directly out from the waist, so a leg source bending it back has room; the physbone colliders help; and it originates low, unlike a chest-rooted skirt, where a small backward deflection has large leverage against the torso. All three sit on top of a very small leg weight. A leg-feed offer names which of those its skirt meets; a chest- or Spine-rooted skirt meets the last least.

Where the venue's hinge policy makes the hinged form an escalation, its evidence is a drive of a built constraint form whose extension rows (each upper leg pitch −30) clip; offer it then, priced by its components.

## Deriving the table

**Donor or derivation.** The venue's record may name a donor prefab per form (step 2); read the one your form follows before writing its first table, and copy field values off it rather than from this file. Absent a donor, derive the strand and hinge fields from the vendor rig as below and state each value in the offer as a setting the operator can move. The venue's policies (step 2) hold whatever a donor reads, and a strand physbone is always multi-child Ignore.

**Azimuth and ring order.** A strand's azimuth is its top bone's position about the skirt root in Unity avatar space, `atan2(x, z)`: 0° is front centre, negative is the avatar's left (−X; a Blender dump's −Y-forward frame flips it). Order the ring by azimuth, never by name; vendor numbering skips around the side. Neighbours are the adjacent strands in that order, wrapping at the back; a group's neighbours are the strands either side of the group.

**The neighbour share.** Neighbours carry no more of a top's drive than the venue's cap (step 2). Build at 0.3, or the cap if lower, find this ring's cliff (the share above which one kick sets off a sustained oscillation; §Driving and the gates), and settle a tenth under it, held under the cap. Cliffs are not portable between rings or between a ring before and after a regroup; never copy a share.

**The frame trap.** A top bone blending sources whose frames sit far apart is ill-conditioned: baked offsets read 80–90° and any kick sets off an oscillation no share cures (`runtime.md` §Constraints (VRC) owns the measurement). Every non-neighbour source therefore sits in a frame matched to the tops.

- **Leg proxies** (the leg-feed form): one node per fed top per leg, `SkirtLeg_<L|R>_<top>`, under the costume's upper-leg bone (the one that merges onto the humanoid upper leg), each framed to its top's rest world rotation, since the legs sit tens of degrees from the tops. A proxy's frame follows any later change to its top's rest. Weights: neighbours hold 0.5 absolute; the legs add `L = Lmax × max(0, 1 − |az|/120)`, split to the near leg by `0.5 + 0.3 × min(1, |az|/90)`; `GlobalWeight` is `0.5 + L` with the source weights normalised to sum to 1. Build at `Lmax` 0.1, sweep it live and offer the steps.
- **Hinge frame** (the hinged form): each hinge node at its parent bone's origin with X the front strand's top-bone X flattened to horizontal, Y straight down, Z = X × Y; set the hinge physbone's `limitRotation.x` to the sign that makes a rotation about the node's +X swing its down vector toward the avatar's forward. On a ring whose strands' X axes do not all run along the ring with one sense, only the baked offsets show the trap.

**Hinged front feed.** A strand within 92° of the front is a front strand: `GlobalWeight` 1, its neighbours' second bones at half the share each, the two hinge physbones carrying the rest, split with the near hinge's fraction `0.5 + 0.3 × min(1, |az| / 90)`. Beyond 92° a strand is a rear strand: neighbours at 0.5 each, `GlobalWeight` at the share. Hinge rows per side: node `Skirt_Hinge_<L|R>` under the root's parent bone with a `VRCRotationConstraint` sourcing that side's costume upper leg; child `Skirt_Phys_<L|R>` at identity with the hinge physbone, colliding with the plane `Col_Hinge` under Hips and nothing else. Every field on those three, the constraint weight included, is the donor's; absent one, the hinge physbone is one bone with a nonzero endpoint, a Hinge limit and World immobile, grab and pose as the policy says, and its limit, endpoint and the constraint weight are values the offer states.

**Spine-rooted deltas.** Each hinge constraint blends the leg with `Hips_Anchor` (an empty node under Hips) so the hinge follows the pelvis; the hinge physbone collides with a capsule of its own on the root's parent bone; and each top also carries a position-only `VRCParentConstraint` over the skin bones of the body face nearest it at their skin-weight ratios, which holds the hem on the body where the Spine-hung root and the Hips-hung body part company. Haï's Skinned Mesh Constraint Builder (`dev.hai-vr.constraint-tools`) finds the face and writes those sources at those ratios. The blend weights and endpoint are the donor's, or values the offer states.

**Collider thinning.** A strand within 40° of front centre or beyond 150° lists both leg colliders; every other strand the near leg only; a group takes the union of its members' bands. Hinge physbones list only the plane. Park every new node beside a chain, never under a chain bone: any child transform of a chain bone joins the chain.

**Strand physbone** (on the second bone or the group top): the donor's skirt strand physbone, not its other physbones, whose settings differ; keep the donor's `limitRotation.x` magnitude with the vendor's own sign on this rig (outward), and start radius, its curve and the endpoint from the vendor's; §Colliders may resize or curve the radius. Absent a donor, every field starts as the vendor strand physbone's.

## Grouping and other structural changes

**Precondition shapes.** A multi-child component over several strands, or one shared root chain (a top inside it is post-physbone and loses the drive), is split by one move row from the shared root to every strand's second bone it covers; name each result by its host, since components partitioned by `ignoreTransforms` share a root. A strand too short to keep the venue's minimum below its top needs a new top bone above it, which is a Blender pass.

**Group sizes are part of the pick.** Offer the maps (front singles and back groups, mirror pairs, per strand) each with its cost line, keeping mirror symmetry.

**The Blender pass.** [`group_bones.py`](group_bones.py) beside this file adds one unweighted top bone per group under the members' shared parent, head at the mean of their first-bone heads, frame the normalised mean of their rest rotations (a one-member group doubles that strand's top in its own frame), reparents the members under it and asserts zero drift of every existing bone; its docstring carries the command line and its refusals. `--whatif` first. Its `PATH` lines are every bone whose hierarchy path changes, the inventory the next paragraph needs. The re-export chain is the costume's record's to name; follow it, what-if first.

**An FBX bone reparent silently deletes every prefab-variant component on the moved bones and below.** `unity.md` §Geometry-change reconcile owns the mechanism and what else it costs; here it means the constraints, physbones and baked constraint rests on the moved strands vanish with no refusal, warning or console line. Before the real re-export, list the prefab's components on the `PATH` bones, import the new FBX to `Assets/Agent/Scratch/` and rebase a copy of the costume prefab onto it to see what is lost; after it, rebuild the whole table on the new hierarchy.

**The group physbone.** Create it on each group top with a `WriteDynamics` `physbones` row carrying `create: true` and a `copy` naming a vendor strand physbone as donor; the copy keeps the donor's colliders, so the same row sets the group's own `colliders`.

**Curves after grouping.** A group physbone adds a depth, so each strand's joints sample every keyed curve at shifted positions: on a group chain of n segments, the joint k links below the group top sits at t=k/n. Re-key the group's curves to hold the root value through the depth of the joint the ungrouped strand physbone rooted at, as `WriteDynamics` curve field sets (`radiusCurve=0:<root>,<k/n>:<root>,1:<tip>`).

**Rewrites after a structural write** carry only the rows that change (constraint weights, field sets): a full table's move row does not re-run once applied.

## Colliders

The sizing rules are `fix-clipping`'s (§The dynamics fix, the pairing of large chain radii with body colliders shrunk to match, and the apron-versus-layered tolerance), and the joint-radius clearance is `runtime.md` §PhysBones's. What is a skirt's here: oversize freely along axes that never cross the garment, since a leg capsule can run up into the buttock and a hips capsule can be huge; and curve the chain radius, since strands fan apart toward the hem, so a radius that grows along the chain closes the gap there without inflating the waist, where the body is closest. A curve is a `radiusCurve=` field set (`unity-tools.md` owns the syntax); on a grouped chain mind the depth shift (§Curves after grouping).

**Place by tilting.** In play, Hips pitch 90 lays the avatar on its back: slide the capsule up and forward through `WriteDynamics`' live collider rows until nothing crosses, and a leg capsule the same way against a raised or crossed leg. Keep the capsule's outer surface at the body mesh or beneath it and put the reach in the joint radius (`runtime.md` §PhysBones): two-segment panels chord through a round thigh with both joints clear, and a larger joint radius is what closes it. Report every rest contact with its reading; one that visibly deflects the chain at rest is refitted before it goes to the operator.

## The free component cut, for any costume

Sibling chains that each carry their own physbone with identical settings under one parent (cuffs, ribbon sets, tail pairs) collapse to one component on that parent with multi-child Ignore: components fall by children-minus-one, transforms rise by one, and grab, colliders and checks do not change. Each chain sits one depth deeper, so a keyed curve resamples (§Curves after grouping) and a curved chain is not a free cut. The candidates are every transform with two or more direct children that each root a physbone. [`merge_sibling_chains.cs.txt`](merge_sibling_chains.cs.txt) beside this file does it, and its header names its refusals; a refused parent is left alone, not normalised. It is a complete execute_code body: copy it whole, edit every parameter, paste the whole text as the `code` argument, `WHAT_IF = true` then `false`; never retype or condense it, since its refusals are the gates. Report the candidates and the outcome, including none.

## Driving and the gates

**The poses**, each held 2.5 s after the `rest` row the drive always takes first, in the drive's own senses (+pitch swings what hangs below a bone forward, +yaw swings what points forward toward the avatar's right, +roll swings what hangs below toward the right; ops apply in order). Name bones by humanoid name (`LeftUpperLeg`), which resolves on every avatar (`unity-tools.md`, `DrivePhysBones`). Upper leg L pitch 90; the same plus yaw −45 (out); the same plus yaw 30 (in); the right leg's three with the yaw signs flipped; each upper leg pitch −30 (extension, the leg back, the hinge escalation's evidence); `sit`, both upper legs pitch 90 then both lower legs pitch −90; Hips pitch +90 and −90 and roll +90 and −90, the full tilts that show gravity (small Hips nudges and a spine lean move the avatar rigidly and prove nothing); a closing pose with no ops. The kick set is upper leg L pitch 90, and pitch 90 plus yaw −45, each held 6 s.

**The arguments.** `bodies` are the play-time renderers that show the legs: the renderer d4rk merged the body into, where that optimizer runs, and whatever carries the costume's stockings, which d4rk can merge into another costume renderer, so list the renderers in play and narrow that one to the stocking's material with `#`; `garments` is the layer whose clipping counts (step 2; `fix-clipping` §Measuring a crossing in motion names the pair); `chains` the skirt root; `views: []`; stage names unique to this session. Then poll `DrivePhysBones.Status()`.

**The gates.**

- Jitter reads zero in every pose.
- Tip travel is compared in root space; a physbone move changes the chain's frame, so in-frame travel is not comparable across it.
- Clipping is each pose's change from its own drive's `rest` row, tabled old against new for the operator; never compare raw counts across drives or modes. A rise over `old` is evidence for the operator's eye, not an automatic FAIL. Read `edgeNearest` beside the behind count and gate nothing on it. Table it per body region and per chain from the drive's region-by-group table; the door groups by physbone root, so where one physbone roots the whole skirt, pass the strand roots as `groups`. A total mixes regions the operator weighs differently, and a fix that moves clipping from one region to another reads as no change.
- On a short hanging panel (a two-segment single sheet), a one-frame snap of a thigh through it pushes it out the back, so the leg and sit rows are gated ramped, each pose carrying `ramp: 1` before its hold. Everywhere else the snaps are the gate.
- The cliff, for a constraint form: sweep the share upward from the built one by live `WriteDynamics.Run(avatarRoot, table, false)` weight writes alternated with kick-set drives on an `EditorApplication.update` pump (a foreground sleep is blocked). The drive reports one jitter figure per hold, so a nonzero share is read twice: a jitter that decays to zero across two holds is stable, one that stays flat is a limit cycle. Oscillation carries into the next drive, so a rest row after an unstable share is contaminated. Settle a tenth under the lowest unstable share, held under the cap, and rewrite it on the prefab in edit mode.
- The grab, for a grabbable form: pull the front strand's tip about 12 cm outward along its azimuth and hold, read the ring's tip and top positions directly before `Release`, then repeat with every top-bone `GlobalWeight` at 0 for the no-cross-link floor. Outside the drive nothing holds the Animator off, so a direct read includes whatever the animator moves.
- The sweep, for a leg-clip report: an upper leg raised to pitch 90 and swept in yaw, out to in and back, slowly and fast, then on to the full side raise. `fix-clipping` §Measuring a crossing in motion owns the method and why the number is the crossing length. Its [`sweep_leg90.poses.json`](../fix-clipping/sweep_leg90.poses.json) is that sweep as a `DrivePhysBones` pose program, and [`sweep_leg90_short.poses.json`](sweep_leg90_short.poses.json) beside this file is its first leg to the first in-sweep, for the control and for screening candidates; both name humanoid bones, and a venue's own test motion (step 2) is a new file beside its skills. Drive the short program with `control` first, where the raised leg must read a long crossing, then the rig as found, then each candidate with the found stage as `baseline`, whose rest row is what a radius, endpoint or collider grown too far pays. Of the levers `fix-clipping` §The dynamics fix lists, a leg capsule's upper end grown toward the skirt root pushes the hem out at rest. Settle by the stopping rule step 2 settled.
- The bake, old against new.

## Traps

Each routes to `unity-tools.md`'s contract for the door named, which owns the mechanics.

- **A live physbone field set cycles its host GameObject** (`WriteDynamics`): the current pose becomes rest and a held grab drops. Run a trial from rest; restart play between trials taken in a loaded pose.
- **Tune an existing collider through `WriteDynamics`' collider row**, the one live route that reaches the solver; write the settled fit to the prefab after.
- **`DrivePhysBones` refuses with no garment**, and a `Run` issued right after play entry can be lost to a timeout while `Status()` still shows the previous record: confirm the stage and log you read are this run's.
- **`GrabPhysBone` takes one step per call**, and its bone index comes from the chain's bone list: a one-bone chain grabs at its origin, and a multi-child Ignore group flattens its members' indices after the root.
