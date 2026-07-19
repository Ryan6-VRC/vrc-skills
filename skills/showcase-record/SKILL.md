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
Every step reads/writes one on-disk take manifest, so any session — or the operator, later —
can resume from its path.

**Dependencies.** `ffmpeg`/`ffprobe` on PATH, Python 3 (stdlib only), Windows (ddagrab).
`showcase.py` sits beside this file; run `python showcase.py <cmd> --help` for exact flags.
Outputs are public: nothing personal may appear on the staged monitor, and no take files
belong inside a repo — use a scratch/output dir.

## The flow

1. **Stage & find the monitor.** The operator tiles the workshop windows — terminal plus Unity
   (and Blender if the venue needs it) — on one monitor (Do-Not-Disturb, neutral wallpaper) and
   says go. Find that monitor — ask, or discover it: `showcase.py check --monitor N` for
   candidate N, Read each frame, pick the one showing the staged layout. Never assume an index;
   it is machine- and cabling-specific.

   A task prompt may or may not come with "go." If none did, once the monitor is found **ask**:
   give the prompt now, or start recording and type it into the live terminal? That answer
   decides step 3.
2. **Roll.** `showcase.py start --monitor N --out <take-dir> --grab-dir <dir>` — pass every
   candidate dir where stamped grabs could land; extra dirs are harmless (Unity
   `Application.temporaryCachePath` for RenderAvatar; Blender render_mesh's
   `<tempfile.gettempdir()>/avatarprep_rendermesh`; add others as they exist). Resolve the Unity
   dir from the editor actually on the staged monitor — a mis-pinned MCP instance hands you
   another project's cache — and when the task's first stamped grab lands, confirm it arrived
   under a registered dir; a miss is repaired by registering the real dir in the manifest,
   mid-take. Then
   `showcase.py check --manifest <path>` and **Read the frame as an image**: confirm it shows
   the staged monitor with no taskbar intruding. Wrong frame, black frame, or a visible taskbar:
   stop and tell the operator before any work is spent. Use the default GPU capture (ddagrab);
   `--gdigrab` is the fallback only where ddagrab won't run. Those grab dirs — and any RunLog dir
   the task's tools stamp into — are shared caches other sessions' work also lives in: **never
   delete from them**. Foreign files don't ride into the edit — every grab and log is
   filename-stamped, and `beats` flags anything outside the recording window for the edit to drop.
3. **Pin the tail, then proceed.** Create a persistent task now — "stop capture + dispatch edit
   — manifest=<path>" — so the obligation survives compaction. Then follow the prompt path from
   step 1: if you already hold the prompt, go straight to the work. If the operator chose to
   record first, tell them you're rolling and wait for the prompt to land in the live terminal —
   it opens the film and is the one moment you wait for input.
4. **Work normally.** With the prompt in hand, run the avatar task under its own skill and go
   fully autonomous — from here never wait for input; decide everything and checkpoint as usual.
   Let a little more of your thinking show than a private run would, but *show* it, don't
   announce it: no labeled preambles ("My plan:", "voiced before I act:"), no talking to the
   camera. Think out loud the way you already would — when a choice has live alternatives, weigh
   them and say why you picked, in the ordinary flow of the work. Don't manufacture deliberation,
   slow the work, or grab where the work doesn't genuinely want a visual check; those diagnostic
   moments *are* the hero shots. The take's only image beats are the avatar task's own stamped
   grabs (RenderAvatar / Blender render_mesh) landing in the grab-dir — never stand up your own
   capture camera or screenshot the screen, which land outside it, stay invisible to `beats`, and
   fabricate shots the take doesn't have. A failure on camera is honest; keep going — first take,
   no re-shoots. The take is self-contained: re-run every check on camera, never citing a prior
   run's cached result (a stale CheckSeam/lint log, an earlier PASS) in its place.
5. **Wrap.** After the final commit: `showcase.py stop --manifest <path>`, then dispatch the
   edit subagent (below) with the manifest path and a target duration (30–120s by task
   complexity). Relay its returned cut path and verify frame to the operator; run
   `showcase.py teaser` if a ≤10MB embed is wanted. Done — hosting/upload is not this skill's
   job.
6. **Offer to restore the venue.** The take left the project mutated, and a re-attempt starts by
   untangling it — so offer (don't assume) to put it back roughly as you found it, reading your own
   transcript for what the work created. Aim at the wall a fresh agent would hit: assets that
   contradict the state they claim, and the RunLogs asserting them — delete outright, since anything
   merely moved aside still turns up in a grep. Confirm the list before removing (these venues are
   untracked), then say plainly what you left behind.

## The edit subagent

Dispatch a general-purpose subagent with exactly this contract — inputs `(manifest path,
target seconds)`, returns `(cut path, one verify frame path, duration)`:

1. Run `showcase.py beats --manifest <path>`. The stamped grabs, in offset order, are the
   take's timeline — the grab dir is shared across sessions, so use only those inside the
   recording window (beats flags the rest `[outside recording]`). Any RunLogs in the grab dirs
   caption the beats, but the stills alone carry the story (Unity `execute_code` work leaves
   none).
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
