---
name: showcase-record
description: Use when a work session should be filmed and cut into a short showcase video — "record this demo", "film this take", "make a trailer of the session". ffmpeg screen capture + edit. Not in-scene verification stills → RenderAvatar; the filmed avatar task itself runs normally under its own skill.
---

# Showcase-record

Film your own session with ffmpeg, then cut it into a short showcase: chosen grab stills
spliced at 1×, work footage fast-forwarded between them, no narration — the terminal and
checkpoint summaries are the text layer, and the final commit is the end card.

**Roles.** You (the top-level session) own capture and do the avatar task; your terminal is
the footage. A dispatched subagent owns the edit, so frame reads never crowd this context.
Every step reads/writes one take manifest on disk, so any session can resume any step — if
this session loses the thread, the operator saying "cut it" against the manifest is the same
operation.

**Dependencies.** `ffmpeg`/`ffprobe` on PATH, Python 3 (stdlib only), Windows (ddagrab).
`showcase.py` sits beside this file; run `python showcase.py <cmd> --help` for exact flags.
Outputs are public: nothing personal may appear on the staged monitor, and no take files
belong inside a repo — use a scratch/output dir.

## The flow

1. **Stage.** The operator tiles the task windows on one monitor (Do-Not-Disturb, neutral
   wallpaper) and says go. Tell them to **leave Unity as the focused window**
   when they step away. Find that monitor — ask, or discover it:
   `showcase.py check --monitor N` for candidate N, Read each frame, pick the one showing the
   staged layout. Never assume an index; it is machine- and cabling-specific.
2. **Roll.** `showcase.py start --monitor N --out <take-dir> --grab-dir <dir>` — pass every
   dir where stamped grabs will land (Unity `Application.temporaryCachePath` for RenderAvatar; a
   Blender task also passes render_mesh's `<tempfile.gettempdir()>/avatarprep_rendermesh`; add others
   as they exist). Then `showcase.py check --manifest <path>` and **Read the frame
   as an image**: confirm it shows the staged monitor and that no taskbar is
   intruding. Wrong frame, black frame, or a visible taskbar → stop and tell the operator
   before any work is spent. Always use the default GPU capture (ddagrab) — measured rock-solid
   30fps under a fully saturated Unity; `--gdigrab` exists only for a machine where ddagrab
   itself won't run.
3. **Pin the tail.** Create a persistent task now — "stop capture + dispatch edit —
   manifest=<path>" — so the obligation survives compaction. The manifest path is the only
   handle anything downstream needs.
4. **Work normally.** Run the avatar task under its own skill, fully autonomous: never wait
   for input, decide everything yourself, checkpoint as usual. The terminal is the video's text
   layer, so voice a little more of your real reasoning than a private run would: when a choice
   has live alternatives, name the ones you weighed and why you picked — a sentence, in the
   normal flow, before you act. That is externalizing thought you already had, not performing
   for the camera — don't manufacture deliberation, slow the work, or grab (RenderAvatar etc.)
   anywhere the work doesn't genuinely want a visual check; those diagnostic moments *are* the
   hero shots. A failure on camera is honest; keep going — first take, no re-shoots.
5. **Wrap.** After the final commit: `showcase.py stop --manifest <path>`, then dispatch the
   edit subagent (below) with the manifest path and a target duration (30–120s by task
   complexity). Relay its returned cut path and verify frame to the operator; run
   `showcase.py teaser` if a ≤10MB embed is wanted. Done — hosting/upload is not this skill's
   job.

## The edit subagent

Dispatch a general-purpose subagent with exactly this contract — inputs `(manifest path,
target seconds)`, returns `(cut path, one verify frame path, duration)`:

1. Run `showcase.py beats --manifest <path>`. The stamped grabs, in offset order, are the
   take's timeline — the grab dir is shared across sessions, so use only those inside the
   recording window (beats flags the rest `[outside recording]`). Unity `execute_code` work
   leaves no RunLogs; if the grab dirs hold any, their filenames and bodies caption the beats,
   but the grabs you Read in step 2 carry the story on their own.
2. Choose 2–3 stills that carry the story. Heuristics: a cluster of near-simultaneous grabs is
   one moment — keep the last; an isolated grab after a long gap earned its place. Read the
   candidates as images and keep only frames that visibly show something (a fit check, a
   working toggle) — visual judgment is yours, not the script's.
3. `showcase.py cut --manifest <path> --target <s> --still <png> [--still <png> ...]` — the
   script does all clock math, splices each still as its own 1× segment, and ramps the footage
   between them uniformly to fit the target (clamped; its `note=` names any compromise).
4. Read the `frames=` verify images and probe nothing by trust: a cut you haven't looked at
   is not verified. Return the paths.

## Failure discipline

Every `showcase.py` line ends `=> OK | key=path` or `=> FAIL: reason (fix)` — a FAIL never
carries a path to something not on disk. Trust the summary grammar; on FAIL do what the reason
says, don't improvise around it. The one silent risk the script can't see is a wrong-but-valid
monitor: only your Read of the check frame catches that, which is why step 2 is a gate.
