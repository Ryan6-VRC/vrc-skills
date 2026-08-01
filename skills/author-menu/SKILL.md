---
name: author-menu
description: Use when authoring NEW expression-menu controls on a composed avatar (outfit/prop toggles, gimmick fronts) or placing a gimmick's shipped menu. Not for testing controls the avatar already ships — drive those in play mode, don't author. Not placing the mergeable (compose-mergeable) or a gimmick's internals (author-gimmick / own-gimmick).
---

# Author expression menus on a composed avatar

Generate the menu controls, expression parameters, and their wiring for a composed avatar, non-destructively — MA-first, escalating to VRCFury per `docs/menus.md`, which is the domain model this skill executes (where menus live, control vocabulary, defaults, substrate rules). **Read it first.** The output is authoring components on the in-scene avatar; everything compiles to FX/menu/params on the build clone.

**No operator to ask?** Follow the no-operator protocol (`workflow.md`).

## Scope — what this owns, and where it routes out

Owns: control planning with the user, dependency closure, the MA/VRCFury authoring, and verification. Menus are authored **on the avatar, after composition** — never onto outfit/mergeable prefabs (`menus.md`).

- **Mergeable not yet placed** → `compose-mergeable` first.
- **Gimmick internals** (state machines, constraints, contacts) → `author-gimmick` (new from intent) or `own-gimmick` (cutting/changing an existing module), out of scope here. This skill fronts an existing module; a generated gimmick arrives as the same thing — a module, with or without its own menu — so the gimmick mode below is the whole interface.
- **Custom animator logic beyond what toggle actions/reactions express** (chained drivers, bespoke layers) → operator/controller work; flag, don't improvise. Whether that lands as an inline edit to the owned FX or a separate merged controller is `docs/animator.md`'s gate.
- **The avatar already ships its menu and the operator only wants to test it** → **not an authoring task.** A vendor base carries menu / params / FX on the `VRCAvatarDescriptor`; absent MA/VRCFury components does **not** mean absent menu (`outfits.md`). Exercising shipped controls is a play-mode drive (`verify.md`) — never author to "make something testable."

## The flow

### 1. Survey

Read what exists before adding: the descriptor's menu/params assets (a vendor base's shipped menu lives here, not in MA/VRCFury components), every MA menu/reactive component and VRCFury feature already on the avatar and its composed mergeables (in the **live scene**, not prefab YAML — `menus.md` §Reading), gimmick subtrees (`ReportGimmick`), and the FX controller's params (`ReportController`) — orphaned vendor params may be re-exposable instead of new. If a recent bake exists, read the true synced-bit count from it; the authored assets under-count (`runtime.md`).

### 2. Plan with the user

One table, before writing anything: control · type · proposed menu path · parameter · saved/synced/default · substrate (MA or VRCFury, per `menus.md` rules) · dependency edges found. An unguided proposal is **modest** (`menus.md`): no toggle that can strand the wearer undressed, and few controls — the user expands from there; their explicit asks always win. Modesty bounds what you *include*, not what you *surface*: scan the whole avatar for candidates beyond the ask — vendor-carried features (ears, tail, hair variants) and blendshape options on the target meshes (a dress-length morph — radial or toggle? ask) — and offer them as a separate "available extras" list in the plan. Propose the submenu grouping — taxonomy is user preference, not canon — and let them reshape it; a menu page holds **8 controls**, so a submenu that would exceed 8 is restructured in the plan (split by region/type, minor toggles into an accessories group), never left to the frameworks' auto-"More" chaining (both MA and VRCFury paginate, visibly only in the baked menu). When existing menu authoring on the avatar conflicts with this skill's conventions (placement, naming, idiom), surface the conflict in the plan and ask which wins: an established system is worth conforming to, but the precedent may itself be a test artifact — don't silently imitate either way. Icons only if the user supplies them. Confirm, then apply; a returning user with an approved plan shape can skip re-confirmation for additions that match it.

### 3. Close each toggle's dependencies

A toggle is a dependency closure (`menus.md`): which body shapes the garment drives, resolved in authority order, is exactly the `map-outfit-shapes` read — produce or reuse that map rather than re-deriving the edges here. Re-deriving "no coupling" from zero edit-time weights or absent reactions is the recorded failure mode — weight-0 under FX drive reads as absence (`compose-mergeable` step 4's rationalization table); the map, or an existing map artifact, is the only admissible source. Unresolvable edges go in the plan as open questions, not guesses. Duplicated blendshape names across meshes are driven in lockstep; whole-outfit edges attach to the outfit root's node, not a piece toggle.

### 4. Write

MA default (install mechanism and shape: `menus.md` §Substrate): group nodes under an **`AvatarMenu`** container (create it under the avatar root if absent, like `AvatarDynamics`) — but that container installs nothing. Each top-level category is a GO with a `ModularAvatarMenuInstaller` (target unset → root) + a SubMenu `MenuItem`(`Children`), its toggles as installer-less children; a lone root control is a GO with an installer + a Toggle `MenuItem`. A toggle `MenuItem` (`automaticValue`, empty parameter; set `isSynced`/`isSaved`/`isDefault` per plan — `isSynced` defaults **true**, so a control planned local silently costs a synced bit if unset) plus `ObjectToggle`/`ShapeChanger` entries on the same node — via `execute_code` + `SerializedObject`. **Hiding a default-visible object takes the inverted closure** (`Inverted=true`, entry `Active=false` — `menus.md`); the naive entry is a silent no-op. `MenuSource` governs only where a SubMenu gets its children; it is inert on a leaf toggle. VRCFury `Toggle`/`FullController` are authored via the **public `com.vrcfury.api`** (`FuryComponents.CreateToggle` / `CreateFullController`); reflection only for what the API doesn't surface (`VF.Model` is `internal`). Escalate per `menus.md`: a control needing exclusive tags / material-prop sliders / global params / transitions becomes a VRCFury `Toggle` component (actions carry the dependency edges); a module escalates wholly when most of its controls did.

### 4b. Overriding shipped defaults — the compose residue

A base garment an always-on FX layer drives from an expression parameter ships its **parameter default**, so stripping it under a composed outfit means flipping that default to the off value — the residue `compose-mergeable` step 4 routes here. Author it as an `MA Parameters` entry on the composed avatar with an explicit default: at merge it overrides the descriptor param's default (MA `RenameParametersHook.ResolveParameter`), vendor assets untouched. No new controls are minted, but it **changes the avatar's shipped menu defaults** — operator-gated like any plan item, and the shipped toggle stays live (a wearer can still re-enable the garment; removing the control is a separate plan item). Verify in step 6's play drive: each stripped garment inactive at spawn, its coupled shapes at their off values. MA ORs `saved`, so on a `saved` param a value stored from an earlier wearing of this blueprint outlives the new default — a deliberate re-enable or your own test history, cleared by one toggle-off; name it, don't chase it.

### 5. Gimmick mode

A well-built gimmick ships its menu — *place* it (MA installer target, or VRCFury FullController menu + install prefix) and verify it landed; don't re-author. Author a front only where one is missing, to `gimmicks.md`'s pattern: unsaved synced enable as master gate (off = reset), options, explicit recall only if state persists beyond the avatar. First ask whether the gimmick should be frontless (passive FX, OSC contract) — adding no control is a valid outcome.

### 6. Verify

**The play-entry gate is enforced** (`verify.md`): a mis-set scene is refused on entry, naming the offender and its fix — clear it and re-enter before trusting anything the session shows. **Play mode is the bake**: entering play runs the non-destructive build on the transient play copy (removed on exit), so one play session is both the baked read and the live drive — read the **baked** menu tree, params, and true synced-bit count from the play copy, then drive each new control (in the emulator, `verify.md`): param changes, mesh/blendshape response, dependency edges firing. All driving *and observation* happens inside the play session — `RenderAvatar` in play mode captures the driven state; after exit the scene reverts to authoring state, where a grab can verify only static baseline/clipping, never a toggle. `RenderAvatar` both states of any toggle whose dependency closure was uncertain — clipping in the off state means a missed edge. Authoring components are cheap to edit; loop until the baked result matches the plan.

## Traps

- **A `MenuItem` installs nothing on its own** — its parameter generates unconditionally, but a control lands only when a `Menu Installer` roots the node (on its GO, or via an installed SubMenu/`Menu Group` above it). *Params present, menu empty* is a missing installer, not a bake failure — there is no child-of-root auto-install. (`menus.md` §Substrate has the mechanism.)
- **`automaticValue` mints a hashed internal param, not the GameObject name** — it bakes as `__MA/AutoParam/<GO>$<hash>` (`menus.md`), so an OSC/remote/saved binding can't target the friendly node name at all. The hash is taken over the node's **avatar-root path**, so re-parenting the node changes the baked name just as a rename does — and re-parenting leaves the friendly name intact, so nothing on screen reflects the break. **Need a stable, predictable param name (an OSC contract, portable saved state)? Set an explicit `parameter`** rather than relying on `automaticValue`; name nodes finally at plan time either way.
- **A radial that must be precise remotely can't be**: synced floats reach remotes as 8-bit [-1,1] regardless of local precision (`runtime.md`).
- Prefab-internal reaction paths are only correct **after instance overrides** — read and write against the scene instance.
- Vendor menu assets serialize control types as ~100-offset ints — identify by shape (`menus.md` §Reading).
- The pre-build parameter asset under-counts; only a bake shows the real bit total.

## Tools

- **Unity MCP `execute_code`** — all authoring and reading on the scene instance; MA components via `SerializedObject`. No dedicated menu tool exists, deliberately — the deterministic slice is small and the formats are moving targets.
- **`AgentInspector`** — generic JSON snapshot of any subtree (MA + VRCFury components included); the survey workhorse.
- **`ReportController` / `ReportClip`** — animator/clip digests for step 1 and the vendor-clip dependency read.
- **`ReportGimmick`** — gimmick subtree digest for step 5.
- **`RenderAvatar`** — both-states visual check for dependency closure (NDMF preview resolves reactive components). Grab in a separate call from any edit — a same-call grab shows the pre-edit proxy; the summary's `note=` flags an in-flight rebuild but cannot catch the same-call case.
- **av3emulator** — drive the new controls live for step 6 via its runtime lists (`unity.md` sharp edges); Gesture Manager stays disabled per the play-entry gate.
