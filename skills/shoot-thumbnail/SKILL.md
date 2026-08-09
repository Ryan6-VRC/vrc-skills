---
name: shoot-thumbnail
description: Use when taking a portrait/thumbnail shot of a composed avatar — "take a thumbnail", "shoot a portrait", "render an upload thumbnail", or producing the image an upload needs. Picks a body pose, facial expression, and backdrop that suit the avatar, then renders the PNG. Not correctness verification (RenderAvatar/CheckAvatar), not the upload itself (upload-avatar).
---

# Shoot an avatar thumbnail

`RenderThumbnail` (edit mode) and `RenderThumbnailPlay` (play mode) do the capture — one caller vocabulary across both, contracted in `docs/unity-tools.md` §Thumbnails. Everything before the call is selection, and selection is the job.

## Draw, don't choose

Left to yourself you pick the same face every time: no memory between sessions means the same avatar yields the same "best" candidate. Both halves are required —

1. **Shortlist 3–5, conditioned on the avatar.** A gothic avatar's shortlist should not equal a pastel one's. Your judgment; the half only you can do.
2. **Let code draw** from that shortlist: `Get-Random -InputObject $shortlist` — the state names you enumerated, never assumed slots like a bare `Open` (which vendors ship as `Open_1/_2/_3`).

Shortlist fewer than 3 only when the corpus holds fewer. **The ceiling:** this yields N faces instead of one, not unpredictability — the shortlist itself stays largely fixed. On a re-roll, widen the shortlist rather than redrawing the same set.

## Read the character

**Expression clip names are the strongest free signal** — vendor facial clips are named for the feeling (`*_doya*` smug, `*kirakira*` sparkle, `heart_eye`, `*guruguru*` dizzy spiral, Japanese as often as English). A vocabulary heavy on smug and sparkle implies a different avatar from one that is all soft smiles.

If that and the mesh/material names come up thin, look with `RenderAvatar` — **stale-tolerant**, since reading vibe is not asserting a fact, so skip the `gate=armed` ritual. Never bake one just to look.

## Enumerate

`ReportController` on the avatar's FX, then `ReportClip` on the states whose **names read as feelings** — the name is the signal, not the curve shape. A real expression moves a whole face and usually carries finger/muscle curves too (the gesture layers bake the hand pose into the same clip), so do **not** filter for blendshape-only clips — that test drops the real faces and keeps the wrong ones:
- a lone accent shape (`Heart eye`, `Sweat`, `Tear`, a single eye toggle) is blendshape-only yet is an additive overlay, not a face — shot alone it moves the eyes over a neutral mouth and reads broken. Don't draw it as the expression; the tool renders one clip and can't layer an accent over a base, so pick an enumerated state that already carries the whole look.
- a gesture slot can alias a named clip you already hold (`Open` resolving to the same clip as `Joy`), so two "different" draws render one face.

Vendors scatter expressions across several FX layers and ship suffixed variants (`Open_1/_2/_3`), so read the whole controller, not the first layer. **The tool holds no opinion about what an expression is** — the filtering is yours; only you can tell `Peace` from `Shirt`.

**Poses:** pass a bare **token**, not a clip path — the tool owns the vocabulary (the `RTPose_*.anim` glob in the avatar-tools `Editor/Poses/`, so it drifts as files are added). **To see the current set, don't read source** — a `RenderThumbnail.Render(target, pose: "?", whatIf: true)` resolves the pose before any bake and fails fast listing every bundled name, free. That junk-token whatIf is the list; run it once up front to shortlist against. Matching ignores case and punctuation — but not a dropped letter.

## Pass the state name

Pass a state **name from the enumeration above**, not a clip path. The bake runs the full SDK preprocess, so optimizers rewrite the blendshape namespace — a state name survives that, a pre-bake clip's bindings may not. The name carries vendor suffixes (`Open_1`, not a bare `Open`), so it is only knowable from the enumeration, never assumed. A path/GUID is an escape hatch, and a FAIL that the expression *moved no blendshape* usually means you used one.

An expression **cannot be previewed**: it resolves against the *baked* controller, so a `whatIf` preflight accepts any string and only the real bake reports a wrong name. Reading the name off the enumeration is the only cheap check — a pose token, by contrast, does fail fast.

**An avatar with no facial clips is a normal pose-only shot**, not an abstain.

## Pick the backdrop

`bg` takes `#RRGGBB` or a vertical two-stop gradient `#TOP:#BOTTOM`; null is the default dark grey. Choose for **contrast, not taste** — a dark-haired avatar in a black outfit on the default backdrop loses its outline, and a VRChat thumbnail is read at menu size.

**Nothing in the verdict measures contrast.** Pick against the avatar's dominant hair and outfit tone, and when the call is close, shoot it and show the operator — rendering is cheap, and a backdrop that fails is obvious in the image and invisible in a number.

A gradient is the answer when no single tone clears the whole palette: a light-to-dark ramp keeps a dark crown and a pale hem legible in one frame.

Shortlist and draw as for pose and expression, conditioned on the avatar's palette.

## Pick the mode

Both front-ends run the **full SDK bake** — that is the constant, not the differentiator. What differs:

- **edit** (`RenderThumbnail`) — one synchronous call, one bake **per shot**, on a private clone in a preview scene. The operator's live scene is never touched.
- **play** (`RenderThumbnailPlay`) — one build at play entry, then **N shots amortized on it**, with the real physbone solver running and FX toggles/materials **resolved**. It mutates the operator's live scene — deactivates the other avatars, mints the emulator control, overrides the Enter-Play-Mode Options — and only `End()` puts that back.

**Ask the operator** (`AskUserQuestion`), edit first and recommended. **What play actually buys is the colliders:** with the solver running, hair and cloth get pushed out of the body instead of intersecting it, and that resolves in the first frames. So argue for play when an edit shot shows a fringe through the cheek or a skirt through a thigh — or when the look only exists once FX resolves. Otherwise edit. A request that already names the mode ("settled", "in play") **is** the answer; don't re-ask it.

**No operator to ask?** The no-operator protocol (`workflow.md`); the derivable default is **edit**, disclosed as play-not-attempted.

**Never enter play unattended.** It is global editor state, it trips PlayGate, and it mutates a live scene — three things nobody is there to watch.

## Shoot

Draw a **compatible set** rather than each independently — a demure pose under a manic grin is two good choices pairing badly, and a pastel backdrop behind a gothic avatar is three.

**With an operator present, shoot a set and let them pick.** The shortlist draw already produced N candidates; rendering one and discarding the rest throws the selection work away. Present them together, each labelled with its drawn pose, expression, and backdrop, so the pick is one word.

- **Play defaults to a set** — 2–3 across the shortlist, unprompted. One build serves them all, so this is where the mode earns its cost; a single play-mode frame leaves the amortization unspent.
- **Edit offers a set** — the same 2–3, but each one re-bakes, so name that cost rather than assuming it.
- **No operator ⇒ one shot.** A set nobody picks from is just N bakes.

**Read at menu size, so the face has to dominate — default to `bust`.** Frame for what the pose puts in the shot, not the pose's category: reach for `half` only when the hands or a held gesture ARE the subject (a clasp, heart-hands), knowing it shrinks the face. `full` is almost never a thumbnail — a whole-body figure's face vanishes at menu size, and the bundled clips carry no root translation, so a standing pose hovers there anyway. None of this is gated: shoot it, open the PNG, re-crop tighter if the subject swims.

**Edit** — one call per shot:

```
RenderThumbnail.Render(target, pose: <token>, expression: <slot>, framing: <paired>, bg: <hex>,
                       fov: <deg>, yaw: <deg?>)
```

**Play** — a session around that same vocabulary:

```
Begin(target)                        → READY-TO-PLAY  (refuses if any loaded scene is unsaved)
manage_editor play                   → blocks for minutes while the SDK build runs
Shoot(pose, expression, framing, …)  → STARTED tag=RTP-xxxxxxxx
   poll Status() (or read_console on the tag) until it stops reporting "still settling"
   …repeat Shoot for the rest of the set — one Begin serves many…
manage_editor stop
End()                                → reopens the venue scene from disk
```

`End()` is **mandatory on every path, including failure.** `Begin` overrode the operator's Enter-Play-Mode Options and deactivated the other avatars; only `End` restores them. Once `Begin` returns READY the exit is `stop` → `End()`, whatever happened in between.

The venue is the **active scene**, lit by its own lights — not a generated one, and not edit's fixed rig. Two expression cases refuse in play and belong in edit: an avatar with **no FX controller**, and an FX slot holding an **override controller** the compositor cannot clone. Both fail loud and name edit mode.

`fov` is vertical degrees (default ~30, [10,90]); distance is solved from it, so it changes the look, not the framing. `yaw` null is an automatic flattering oblique — a number is an **offset added to head tracking**, not an absolute heading (`yaw: 0` means "no oblique", not "frontal"), positive orbiting toward screen-left. An explicit `yaw` carries the composition with it: the subject shifts opposite the way the camera swung, to leave the gaze somewhere to go, and `yaw: 0` centres it. Both are taste dials: leave them alone unless the shot asks for it.

**Serialize the calls** — the bake and play entry both drive global editor state, and the tool refuses a second session or an overlapping `Shoot` outright. Never two at once, never parallelized across subagents.

**A render that times out has probably wedged the editor on a modal dialog**, not hung: the bake runs the full SDK chain, and VRCFury prompts per build on an avatar with a broken Write Defaults mix. Read it with `unity-dialog.ps1 -List` — it lives in the **Atelier workspace root's** `tools/`, the session cwd, not this repo's — and press by label; never retry blindly. Don't take an avatar-mutating option (`Auto-Fix`) or a persistent one (`Skip and stop asking`) on the operator's behalf — the prompt is reporting a real defect that is theirs to decide about.

## Read the verdict

```
... expression=Open (F_smile_1) framing=bust fov=30 headYaw=11.9 camYaw=24.9 head=(0.54,0.62) => OK | png=... | log=...
```

- **`(F_smile_1)`** — the clip the slot resolved to post-bake; the only place the drawn face is named. A VRCFury-merged FX prints it as `(Copied from <layer>/<clip>)` — same meaning, longer form.
- **`headYaw`** — what the *pose* did, measured off the posed head. Zero on an unposed render.
- **`camYaw`** — the *resolved* camera angle: `headYaw` plus the oblique, so it names the shot you got. The pair is what makes it decomposable — `camYaw − headYaw` is the offset to pass as `yaw` to reproduce the shot, and a gap wider than that offset means tracking saturated its ±60° clamp.
- **`head=(x,y)`** — the view point in viewport coords, origin bottom-left, centre `(0.5,0.5)`. Reported, never gated; an off-centre head is something you can see in the PNG. A blank frame does fail loud, so an `OK` verdict means something was rendered.
- **`| log=`** — the session RunLog, written by every verb but `Status`. `png=` stays ahead of it: that is the token an upload reads.
- A FAIL saying the expression *moved no blendshape* means the clip and the baked avatar disagree — usually a path/GUID escape hatch pointing at pre-bake shape names. Pass the slot instead.

Play adds `settled=<N>f moving=[…]` — frames waited, and any chains still swinging at capture. Neither is a gate and neither is usually worth acting on: a named chain means the hair is still in motion, which in a portrait reads as life, not a defect. Raise `settleFrames` only if the operator wants it stiller.

Name the mode, the drawn pose, and the expression when you show the PNG, so a re-roll is one sentence.
