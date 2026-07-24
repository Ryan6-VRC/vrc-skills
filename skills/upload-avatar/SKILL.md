---
name: upload-avatar
description: Use when driving a VRChat upload — "upload this avatar", "re-upload these", or the batch re-upload after a base-prefab change that N avatars inherit. First upload (mint blueprint/name/thumbnail) or re-upload of already-live avatars. NOT correctness validation (the play-mode bake already did that), NOT authoring menus/gimmicks.
---

# Upload an avatar to VRChat

The last mile: a composed avatar from "works in play mode" to live on VRChat — a first upload (mint blueprint ID, name, thumbnail) or a re-upload of already-live avatars, the batch case being the point (change one base prefab that 10+ avatars inherit → all need re-uploading).

**Not a validator.** The play-mode bake and the earlier gates (`CheckAvatar`, `CheckSeam`, the compose skills) already proved the avatar works. This skill assumes a working avatar and does only what remains: read blueprint state, optionally bring the avatar to the safe optimizer stack, and drive the operator-authorized upload. Asked to upload a broken avatar, it says so and changes nothing.

**The agent pulls the trigger.** No human clicks the upload button — the skill calls `UploadAvatar` programmatically. So the operator's explicit go *is* the button. That shapes the whole flow: the ask that starts a session authorizes *readiness*, never execution; execution needs its own distinct word (step 4). Getting this wrong publishes something the operator never approved.

**No operator to ask?** The no-operator protocol (`workflow.md`); an irreversible publish has no derivable default, so run every readiness step (`whatIf`) and then stop at the execution gate and report — never upload unattended.

**Public-repo hygiene (firm).** No `blueprintId` and no account identifier lands in anything tracked — tool output, RunLogs, this SKILL, commits. The tool redacts IDs from its own output and keys rows by substrate handle (scene / prefab path) and `state` (`first-upload`/`update`), never the ID; don't reintroduce one when you relay a report.

## The flow

### 1. Readiness — `whatIf`

Call `UploadAvatar` with `whatIf: true` on the batch. It runs every precondition and, per avatar, classifies `first-upload` vs `update` and surfaces the literal publish name — uploading nothing. There is no separate readiness ritual; this preflight is it. Surface the per-avatar would-do report.

A **REFUSE** means the *environment* isn't ready, not that an avatar is bad — not in Play mode, not logged into the SDK, the Build Control Panel window closed, wrong build target, or **CAU absent**. Fix the named condition and re-run. CAU (`com.anatawa12.continuous-avatar-uploader`) is an optional dependency: absent, the tool can't self-drive → **fall back to a manual SDK-panel handoff** (hand the operator the avatar and the panel; the rest of this skill's judgment steps still apply to what they do).

### 2. Optimizer pre-step (opt-in) — below

Offer before the batch settles, or skip entirely. Never after a failure (step 4).

### 3. Batch composition — confirm the *scope*

The operator names the avatars, or — for a changed base — enumerate the avatars that inherit it (prefab-variant / nested-prefab references) and propose the list. The operator confirms the scope. v1 is a manual list plus a best-effort "dependents I found"; say which avatars you found by inheritance and which you're unsure of, and let the operator close the set. Confirming this list is a **scope** judgment — it is *not* permission to upload.

### 4. Authorization — two steps, not one

After the list settles, require a **distinct, explicit "upload now"** before calling `UploadAvatar` for real. Neither "get these ready" nor "yes, those are the right ones" is an execution go — the first authorizes readiness, the second settles scope. Only an explicit execute word pulls the trigger.

**Confirm the literal published name** for each first-upload before that go: surface the exact string that will be published (CAU defaults it to the GameObject name) and get explicit confirmation. A placeholder or persona-bearing name must not go public unnoticed — "a name is set" is vacuous (always true); the operator must see and approve the actual string.

### 5. Upload

When the operator gives the go, call `UploadAvatar.Run` (no `whatIf`) on the confirmed batch. The upload is **async-driven**: `Run` fires the batch and returns immediately (`batch started; poll Status()`) — it does NOT block for the result (blocking would deadlock the editor). **Poll `UploadAvatar.Status()`** until it stops reporting `running…`; it then returns the final verdict + RunLog path. Expect the **build phase to make the editor briefly unresponsive** to MCP (an asset-bundle build is heavy main-thread work) — that is normal, not a hang; keep the editor window focused (a backgrounded editor throttles its update loop and stalls the pump) and keep polling. The governing rule:

> When asked to upload, upload. If a failure is transient (server / timeout), retry two or three
> times; a rate-limit is not a transient — back off and inform, don't retry. Never loop, and never
> edit the avatar to work around a failure — a broken avatar is reported broken, not fixed.

The tool stops the batch on the first failure and classifies it (`transient` / `rate-limit` / `real`). On a retry, **re-feed the failed avatar AND every avatar the batch left `not-attempted`** (the RunLog rows mark them) — not just the one failed handle, or the tail of the batch is silently dropped. A `reserved-no-bundle` result means a record was minted but no bundle uploaded — relay it, don't hide it.

**Optimization is never a post-failure remedy.** A "bundle too large" (or any failure) does **not** trigger an optimize. Optimization is only a fresh, operator-initiated pre-step (step 2) *before* a new upload attempt — the same capability pointed the allowed direction. A failed upload ends the attempt; re-optimizing is a new, separately-authorized session.

## Optimizer pre-step

An availability-driven menu: detect which optimizer/fix packages are installed and offer **only those**, opt-in. **Only ever ADD a component that is absent.** A pre-existing optimizer/fix component is left **untouched** — the operator placed and configured it deliberately; don't second-guess it. When you *add* one, set it to the profile below and **read the fields back to confirm** (a mistyped field is caught here, not shipped). All apply at build (`ApplyOnUpload`-style), so the on-disk prefab stays editable.

### d4rkAvatarOptimizer — package present, none already on the avatar

Add it and set the empirically-safe profile (fields live on the nested `component.settings.X`; `MergeSkinnedMeshesWithShaderToggle` is an **int** — set `= 0`, not `false`):

**OFF** (avatar-breakers): `OptimizeFXLayer`, `WritePropertiesAsStaticValues`, `MergeSameDimensionTextures`, `MergeMainTex`, `MergeDifferentPropertyMaterials`, `MergeSkinnedMeshesWithShaderToggle`, `CombineApproximateMotionTimeAnimations`, `NaNimationAllow3BoneSkinning`. `OptimizeFXLayer` is OFF **unconditionally** — too aggressive on its own, can change animator/toggle behavior; not contingent on VRCFury.

**ON:** `ApplyOnUpload`, `MergeSkinnedMeshes`, `MergeSkinnedMeshesSeparatedByDefaultEnabledState`, `DisablePhysBonesWhenUnused`, `MergeSameRatioBlendShapes`, `DeleteUnusedComponents`.

Leave the component defaults for the per-avatar-judgment fields (`DeleteUnusedGameObjects`, `UseRingFingerAsFootCollider`, `MergeStaticMeshesAsSkinned`, `MMDCompatibility`) — the operator tunes those.

### Limitex Avatar Compressor (LAC) — package present, no TextureCompressor already on the avatar

Add `dev.limitex.avatar.compressor.TextureCompressor`, set `Preset = CompressorPreset.HighQuality` (int 0), then call `ApplyPreset(CompressorPreset.HighQuality)` to cascade its concrete fields. The fields are flat on the component (no nested settings object), and setting `Preset` alone does **not** cascade — the `ApplyPreset` call (or a fresh add's `Reset`) is what writes them.

### VRCFury optimizer features — VRCFury present

`DirectTreeOptimizer` and `BlendshapeOptimizer` are safe to add if absent. **`FixWriteDefaults`:** VRCFury pops a blocking WD-mismatch dialog only when no `FixWriteDefaults` feature exists — so if none is present, add one in the **non-forcing `Disabled` mode** (`FixWriteDefaultsMode.Disabled` = int `3`): it silences the dialog and conforms only VRCFury's own layers, never force-changing the avatar's Write Defaults. The forcing modes (`ForceOff`=1 / `ForceOn`=2) change behavior and are an explicit expert-only opt-in. These are VRCFury `FeatureModel`s carried as `content` on the internal `VF.Model.VRCFury` component (one feature per component; reach the internal types by reflection).

### AAO

This step **notes — never force-removes** — a present-but-unplaced AAO component (AAO stays installed; d4rk is the standard). Coexistence is proven: d4rk with `OptimizeFXLayer` OFF alongside VRCFury's `DirectTreeOptimizer` is a shipped config.

## Tools

- **`UploadAvatar`** (avatar-tools, via `execute_code`) — `Ryan6Vrc.AvatarTools.Editor.UploadAvatar.Run(GameObject[] avatars, bool whatIf = false)` + `UploadAvatar.Status()`. The CAU-driving door: `whatIf: true` is the synchronous readiness preflight (step 1); no `whatIf` fires the async upload (step 5) and returns `batch started; poll Status()` — then poll `Status()` (`running…` → final summary) until done. REFUSE = environment not ready; FAIL = a genuine upload rejection; PASS = uploaded. Verdicts and rows are ID-redacted. CAU absent → REFUSE → manual SDK-panel fallback.
- **Unity MCP `execute_code`** — the optimizer pre-step: detect installed packages, write the optimizer-component fields, and read them back to assert the hard-OFF set (d4rk fields on nested `component.settings.X`).
