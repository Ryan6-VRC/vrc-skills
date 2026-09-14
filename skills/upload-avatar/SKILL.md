---
name: upload-avatar
description: Use when driving a VRChat upload — "upload this avatar", "re-upload these", or the batch re-upload after a base-prefab change that N avatars inherit. First upload (mint blueprint/name/thumbnail) or re-upload of already-live avatars. NOT correctness validation (the play-mode bake already did that), NOT authoring menus/gimmicks, NOT editing an already-uploaded avatar's name/description/tags (an upload cannot rename — that is UpdateAvatarRecord).
---

# Upload an avatar to VRChat

The last mile: a composed avatar from "works in play mode" to live on VRChat — a first upload (mint blueprint ID, name, thumbnail) or a re-upload of already-live avatars, the batch case being the point (change one base prefab that 10+ avatars inherit → all need re-uploading).

**Not a validator.** The play-mode bake and the earlier gates (`CheckAvatar`, `CheckSeam`, the compose skills) already proved the avatar works. This skill assumes a working avatar and does only what remains: read blueprint state, optionally bring the avatar to the safe optimizer stack, and drive the operator-authorized upload. Asked to upload a broken avatar, it says so and changes nothing.

**The agent pulls the trigger.** No human clicks the upload button — the skill calls `UploadAvatar` programmatically. So the operator's explicit go *is* the button. That shapes the whole flow: the ask that starts a session authorizes *readiness*, never execution; execution needs its own distinct word (step 4). Getting this wrong publishes something the operator never approved.

**No operator to ask?** The no-operator protocol (`workflow.md`); an irreversible publish has no derivable default, so run every readiness step (`whatIf`) and then stop at the execution gate and report — never upload unattended.

**Public-repo hygiene (firm).** No `blueprintId` and no account identifier lands in anything tracked — tool output, RunLogs, this SKILL, commits. The tool redacts IDs from its own output and keys rows by substrate handle (scene / prefab path) and `state` (`first-upload`/`update`), never the ID; don't reintroduce one when you relay a report.

## The flow

### 1. Readiness — `whatIf`

Call `UploadAvatar` with `whatIf: true` on the batch. It runs every precondition and, per avatar, classifies first-upload vs update and surfaces the literal publish name — uploading nothing. There is no separate readiness ritual; this preflight is it. Surface the per-avatar would-do report. Alongside it, `ConformImportSettings.Run(<avatar root>, whatIf: true)` per avatar previews the SDK panel's importer errors with the paths the panel's own error text omits — **read its would-conform row list, not the verdict token.** The SDK runs those validations inside the build too, so an offender left here is a multi-minute build spent to learn a `.meta` setting; conform it before the go (`docs/unity-tools.md` owns the door).

A **REFUSE** means the *environment* isn't ready, not that an avatar is bad — not in Play mode, not logged into the SDK, the Build Control Panel window closed, wrong build target, or **CAU absent**. Fix the named condition and re-run. CAU (`com.anatawa12.continuous-avatar-uploader`) is an optional dependency: absent, the tool can't self-drive → **fall back to a manual SDK-panel handoff** (hand the operator the avatar and the panel; the rest of this skill's judgment steps still apply to what they do).

### 2. Optimizer pre-step (opt-in) — below

Offer before the batch settles, or skip entirely. Never after a failure (step 4).

### 3. Batch composition — confirm the *scope*

The operator names the avatars, or — for a changed base — enumerate the avatars that inherit it (prefab-variant / nested-prefab references) and propose the list. The operator confirms the scope. v1 is a manual list plus a best-effort "dependents I found"; say which avatars you found by inheritance and which you're unsure of, and let the operator close the set. Confirming this list is a **scope** judgment — it is *not* permission to upload.

### 4. Authorization — two steps, not one

After the list settles, require a **distinct, explicit "upload now"** before calling `UploadAvatar` for real. Neither "get these ready" nor "yes, those are the right ones" is an execution go — the first authorizes readiness, the second settles scope. Only an explicit execute word pulls the trigger.

**Confirm the literal published name** for each first-upload before that go: surface the exact string that will be published (CAU defaults it to the GameObject name) and get explicit confirmation. A placeholder or persona-bearing name must not go public unnoticed — "a name is set" is vacuous (always true); the operator must see and approve the actual string.

**A first upload is the only moment an upload can set a name**, and a re-upload silently republishes under the old one (`unity-tools.md` §Publish owns why). So the scene never tells you what is actually published: read it with `ReportAvatarRecord`. Asked to change a live avatar's name, description, tags or thumbnail, do not re-upload — that is `UpdateAvatarRecord`.

**The thumbnail an upload mints is CAU's own camera shot.** Neither CAU nor this door reads an external image, so a rendered one reaches a live avatar only through `UpdateAvatarRecord`'s `newImagePath`, as its own call after the upload — and until that call runs, CAU's shot is what is public.

### 5. Upload

When the operator gives the go, call `UploadAvatar.Run` (no `whatIf`) on the confirmed batch. The upload is **async-driven**: `Run` fires the batch and returns immediately — it does NOT block for the result, since blocking would deadlock the editor — so **poll `UploadAvatar.Status()`** until it stops reporting a run in progress. Expect the **build phase to make the editor briefly unresponsive** to MCP (an asset-bundle build is heavy main-thread work) — that is normal, not a hang; keep the editor window focused (a backgrounded editor throttles its update loop and stalls the pump) and keep polling. The governing rule:

> When asked to upload, upload. If a failure is transient (server / timeout), retry two or three
> times; a rate-limit is not a transient — back off and inform, don't retry. Never loop, and never
> edit the avatar to work around a failure — a broken avatar is reported broken, not fixed.

The tool stops the batch on the first failure and classifies it (`transient` / `rate-limit` / `real`). On a retry, **re-feed the failed avatar AND every avatar the batch left `not-attempted`** (the RunLog rows mark them) — not just the one failed handle, or the tail of the batch is silently dropped. A `reserved-no-bundle` result means a record was minted but no bundle uploaded — relay it, don't hide it.

**Optimization is never a post-failure remedy.** A "bundle too large" (or any failure) does **not** trigger an optimize. Optimization is only a fresh, operator-initiated pre-step (step 2) *before* a new upload attempt — the same capability pointed the allowed direction. A failed upload ends the attempt; re-optimizing is a new, separately-authorized session.

## Optimizer pre-step

An availability-driven menu: detect which optimizer packages are installed and offer **only those**, opt-in. **Only ever ADD a component that is absent.** A pre-existing optimizer component is left **untouched** — the operator placed and configured it deliberately; what each optimizer is for, and the profile a fresh d4rk gets, is `docs/optimization.md` §Division of labour. When you add one, set that profile and **read the fields back to confirm** (a mistyped field is caught here, not shipped); d4rk's fields sit on the nested `component.settings.X`, `MergeSkinnedMeshesWithShaderToggle` is an int (set `= 0`), and `OptimizeFXLayer` is OFF unconditionally. All apply at build (`ApplyOnUpload`-style), so the on-disk prefab stays editable.

Limitex present and no `TextureCompressor` on the avatar: add `dev.limitex.avatar.compressor.TextureCompressor` and call `ApplyPreset(CompressorPreset.HighQuality)` — setting `Preset` alone cascades nothing.

`DirectTreeOptimizer` and `BlendshapeOptimizer` are safe to add if absent. **`FixWriteDefaults`:** VRCFury pops a blocking WD-mismatch dialog only when no `FixWriteDefaults` feature exists — so if none is present, add one in the **non-forcing `Disabled` mode** (`FixWriteDefaultsMode.Disabled` = int `3`): it silences the dialog and conforms only VRCFury's own layers, never force-changing the avatar's Write Defaults. The forcing modes (`ForceOff`=1 / `ForceOn`=2) change behavior and are an explicit expert-only opt-in. These are VRCFury `FeatureModel`s carried as `content` on the internal `VF.Model.VRCFury` component (one feature per component; reach the internal types by reflection).

A present-but-unplaced AAO component is **noted, never force-removed** — AAO stays installed beside d4rk; the doc owns the split.

