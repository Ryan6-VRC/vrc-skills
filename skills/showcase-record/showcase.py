#!/usr/bin/env python3
"""showcase.py -- capture + cut mechanics for the showcase-record skill.

Pure core over ffmpeg/ffprobe; every subcommand reads/writes one take manifest so
any session can resume any step from disk. One-line summaries with in-band path
trailers; FAIL never carries a path to something not on disk.

    start   launch a detached screen recording, write the manifest
    check   extract a frame to Read: from the live take, or one-shot from a monitor (discovery)
    stop    end the recording, probe + stamp the real duration
    beats   list stamped artifacts in the grab dirs as recording offsets
    cut     assemble the showcase cut: stills as 1x segments, ramped footage between
    teaser  re-encode the cut under a size budget

Stamps everywhere are the family grammar: yyyyMMdd_HHmmss_fff, local clock --
the same DateTime.Now domain AvatarGrab/RunLogFormat write into filenames.
"""

import argparse
import ctypes
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

STAMP_FMT = "%Y%m%d_%H%M%S_%f"  # parse: pad the 3-digit ms to microseconds
STAMP_RE = re.compile(r"(\d{8}_\d{6}_\d{3})\.[A-Za-z0-9]+$")
T0_FMT = "%Y-%m-%dT%H:%M:%S.%f"


# ---------------------------------------------------------------- envelope

def ok(cmd, detail, note=None, **trailers):
    line = f"[showcase] {cmd} {detail} => OK"
    if note:
        line += f" | note={note}"
    for k, v in trailers.items():
        line += f" | {k}={v}"
    print(line)
    sys.exit(0)


def fail(cmd, reason):
    print(f"[showcase] {cmd} => FAIL: {reason}")
    sys.exit(1)


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


# ---------------------------------------------------------------- manifest

def load_manifest(path, cmd):
    p = Path(path)
    if not p.is_file():
        fail(cmd, f"no manifest at {p} (run start, or pass the manifest= path start printed)")
    return json.loads(p.read_text(encoding="utf-8")), p


def save_manifest(manifest, path):
    Path(path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def parse_stamp(name):
    m = STAMP_RE.search(name)
    if not m:
        return None
    s = m.group(1)
    return datetime.strptime(s[:-3] + s[-3:] + "000", STAMP_FMT)


def parse_t0(manifest):
    return datetime.strptime(manifest["t0"], T0_FMT)


# ---------------------------------------------------------------- process (Windows)

STILL_ACTIVE = 259


def pid_alive(pid):
    kernel32 = ctypes.windll.kernel32
    h = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    alive = kernel32.GetExitCodeProcess(h, ctypes.byref(code)) and code.value == STILL_ACTIVE
    kernel32.CloseHandle(h)
    return bool(alive)


def kill_pid(pid, expect_ffmpeg=False):
    if expect_ffmpeg:
        # manifests resume across sessions; Windows recycles PIDs -- never
        # tree-kill a stored PID unless it is still an ffmpeg
        r = run(["tasklist", "/FI", f"PID eq {int(pid)}", "/FO", "CSV", "/NH"])
        if "ffmpeg" not in r.stdout.lower():
            return False
    run(["taskkill", "/PID", str(pid), "/T", "/F"])
    return True


# ---------------------------------------------------------------- ffmpeg helpers

def ffprobe_stream(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)])
    if r.returncode != 0:
        return None
    info = json.loads(r.stdout)
    stream = info.get("streams", [{}])[0]
    try:
        num, _, den = stream.get("r_frame_rate", "30/1").partition("/")
        fps = float(num) / float(den) if float(den or 0) else 0.0
    except ValueError:
        fps = 0.0
    try:
        duration = float(info.get("format", {}).get("duration") or 0)  # absent/"N/A" on unfinalized MKV
    except ValueError:
        duration = 0.0
    return {"width": stream.get("width"), "height": stream.get("height"),
            "fps": fps, "duration": duration}


def capture_input_args(grabber, monitor, fps):
    if grabber == "gdigrab":
        # whole-desktop fallback (CPU); ddagrab is the per-monitor default
        return ["-f", "gdigrab", "-framerate", str(fps), "-i", "desktop"]
    return ["-init_hw_device", "d3d11va", "-filter_complex",
            f"ddagrab=output_idx={monitor}:framerate={fps},hwdownload,format=bgra"]


ENCODE = ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an"]


# ---------------------------------------------------------------- subcommands

def cmd_start(a):
    take = Path(a.out)
    manifest_path = take / "manifest.json"
    if manifest_path.exists():
        fail("start", f"{take} already holds a take (manifest exists); pass a fresh --out dir")
    take.mkdir(parents=True, exist_ok=True)
    mkv = take / "recording.mkv"
    log = take / "ffmpeg.log"

    grabber = "gdigrab" if a.gdigrab else "ddagrab"
    # stop force-kills the recorder, so flush per-packet with 1s clusters --
    # otherwise the muxer's buffered tail (the take's final moments) dies with it
    args = (["ffmpeg", "-y"] + capture_input_args(grabber, a.monitor, a.fps)
            + ENCODE + ["-crf", str(a.crf),
                        "-flush_packets", "1", "-cluster_time_limit", "1000", str(mkv)])
    t0 = datetime.now()
    with open(log, "w") as lf:
        proc = subprocess.Popen(
            args, stdin=subprocess.DEVNULL, stdout=lf, stderr=lf,
            creationflags=0x00000008 | 0x00000200)  # DETACHED | NEW_PROCESS_GROUP

    # liveness: pid + frame= progress in the log. File size lies early -- x264
    # buffers a few seconds before the muxer flushes anything to the MKV.
    encoding = False
    for _ in range(8):
        time.sleep(1)
        if not pid_alive(proc.pid):
            break
        if re.search(r"frame=\s*[1-9]", log.read_text(errors="replace")):
            encoding = True
            break
    if not encoding:
        if pid_alive(proc.pid):
            kill_pid(proc.pid)  # never leave an orphan recorder behind a FAIL
        tail = "\n".join(log.read_text(errors="replace").splitlines()[-5:])
        fail("start", f"ffmpeg produced no frames within 8s (monitor {a.monitor} valid? ffmpeg on PATH?) -- log tail:\n{tail}")

    manifest = {
        "mkv": str(mkv.resolve()),
        "t0": t0.strftime(T0_FMT)[:-3],
        "monitor_idx": a.monitor,
        "grabber": grabber,
        "fps": a.fps,
        "grab_dirs": a.grab_dir or [],
        "ffmpeg_pid": proc.pid,
        "stopped": None,
        "cut": None,
    }
    save_manifest(manifest, manifest_path)
    ok("start", f"monitor={a.monitor} grabber={grabber} pid={proc.pid}",
       manifest=manifest_path.resolve(), mkv=mkv.resolve())


def cmd_check(a):
    if a.manifest:
        manifest, mpath = load_manifest(a.manifest, "check")
        mkv = Path(manifest["mkv"])
        pid = manifest.get("ffmpeg_pid")
        if manifest["stopped"] or not pid:
            fail("check", "take already stopped; check reads a live recording (use cut's verify frames instead)")
        if not pid_alive(pid):
            fail("check", f"recorder pid {pid} is dead -- the take is not recording; restart with start")
        # muxer flushes clusters lazily (seconds apart on a static screen) -- watch
        # up to 8s and pass on first growth, so a quiet desktop doesn't false-FAIL
        size1 = mkv.stat().st_size if mkv.exists() else 0
        for _ in range(8):
            time.sleep(1.0)
            if mkv.exists() and mkv.stat().st_size > size1:
                break
        else:
            fail("check", f"{mkv.name} is not growing after 8s -- recorder alive but writing nothing (see ffmpeg.log)")
        elapsed = (datetime.now() - parse_t0(manifest)).total_seconds()
        frame = mpath.parent / "check_frame.png"
        # a live MKV is unfinalized -- ffprobe reads no duration, so seek from EOF:
        # -sseof grabs a frame near the write head without needing a container duration
        r = run(["ffmpeg", "-y", "-sseof", "-1.0", "-i", str(mkv),
                 "-frames:v", "1", "-update", "1", str(frame)])
        if r.returncode != 0 or not frame.exists():
            fail("check", f"could not extract a frame from the live MKV: {r.stderr.strip()[-200:]}")
        ok("check", f"pid={pid} elapsed={elapsed:.1f}s growing=yes -- Read the frame and confirm it shows the staged monitor",
           frame=frame.resolve())
    else:
        # discovery mode: one-shot frame from a monitor index, no take needed
        out = Path(a.out or ".") / f"monitor_{a.monitor}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        grabber = "gdigrab" if a.gdigrab else "ddagrab"
        r = run(["ffmpeg", "-y"] + capture_input_args(grabber, a.monitor, 30)
                + ["-frames:v", "1", str(out)])
        if r.returncode != 0 or not out.exists():
            fail("check", f"no frame from monitor {a.monitor} ({grabber}): {r.stderr.strip()[-200:]}")
        ok("check", f"monitor={a.monitor} one-shot -- Read the frame to identify this monitor", frame=out.resolve())


def cmd_stop(a):
    manifest, mpath = load_manifest(a.manifest, "stop")
    if manifest["stopped"]:
        ok("stop", "already stopped (idempotent)", note="no-op",
           manifest=mpath.resolve())
    pid = manifest["ffmpeg_pid"]
    if pid and pid_alive(pid):
        if kill_pid(pid, expect_ffmpeg=True):
            time.sleep(1.5)
    mkv = Path(manifest["mkv"])
    if not mkv.exists() or mkv.stat().st_size == 0:
        fail("stop", f"no usable recording at {mkv} -- the take is lost (see ffmpeg.log beside it)")
    # a killed recorder never finalizes the MKV header (no duration, no cues);
    # the frames are fine -- remux to a finalized file and adopt that
    final = mkv.with_name("recording_final.mkv")
    r = run(["ffmpeg", "-y", "-i", str(mkv), "-c", "copy", str(final)])
    if r.returncode != 0 or not final.exists() or final.stat().st_size == 0:
        fail("stop", f"remux of the unfinalized recording failed: {r.stderr.strip()[-300:]}")
    info = ffprobe_stream(final)
    if not info or info["duration"] <= 0:
        fail("stop", f"{final.name} still has no readable duration after remux -- the take may be corrupt")
    mkv.unlink()
    manifest["mkv"] = str(final.resolve())
    expected = (datetime.now() - parse_t0(manifest)).total_seconds()
    note = None
    if abs(info["duration"] - expected) > max(10.0, expected * 0.1):
        note = f"probed {info['duration']:.0f}s vs ~{expected:.0f}s wall clock -- recording may be truncated"
    manifest["stopped"] = {"time": datetime.now().strftime(T0_FMT)[:-3],
                           "duration_s": info["duration"]}
    manifest["ffmpeg_pid"] = None
    save_manifest(manifest, mpath)
    ok("stop", f"duration={info['duration']:.1f}s", note=note, manifest=mpath.resolve())


def cmd_beats(a):
    manifest, _ = load_manifest(a.manifest, "beats")
    t0 = parse_t0(manifest)
    end = manifest["stopped"]["duration_s"] if manifest["stopped"] else None
    rows = []
    for d in manifest["grab_dirs"]:
        for f in sorted(Path(d).glob("*")):
            stamp = parse_stamp(f.name)
            if not stamp:
                continue
            off = (stamp - t0).total_seconds()
            flag = "" if (0 <= off and (end is None or off <= end)) else "  [outside recording]"
            rows.append((off, f"{off:9.3f}s  {f}{flag}"))
    if not rows:
        ok("beats", f"0 stamped files under {len(manifest['grab_dirs'])} grab dir(s)",
           note="no grabs -- the cut will be footage-only")
    print("\n".join(line for _, line in sorted(rows)))
    ok("beats", f"{len(rows)} stamped file(s), offsets from t0={manifest['t0']}")


def cmd_cut(a):
    manifest, mpath = load_manifest(a.manifest, "cut")
    if not manifest["stopped"]:
        fail("cut", "take not stopped -- run stop first")
    mkv = Path(manifest["mkv"])
    D = manifest["stopped"]["duration_s"]
    t0 = parse_t0(manifest)
    info = ffprobe_stream(mkv)
    if not info:
        fail("cut", f"cannot probe {mkv}")
    W, H, FPS = info["width"], info["height"], round(info["fps"]) or 30

    stills = []
    for s in a.still or []:
        p = Path(s)
        if not p.is_file():
            fail("cut", f"still not on disk: {p}")
        stamp = parse_stamp(p.name)
        if not stamp:
            fail("cut", f"{p.name} has no yyyyMMdd_HHmmss_fff stamp -- cut places stills by filename stamp")
        off = (stamp - t0).total_seconds()
        # t0 is stamped before ddagrab init, so real frame offsets skew a few
        # seconds early -- clamp near-edge stills instead of rejecting them
        if not (-3.0 <= off <= D + 3.0):
            fail("cut", f"{p.name} is at {off:.1f}s, outside the 0-{D:.1f}s recording")
        stills.append((min(max(off, 0.0), D), p))
    stills.sort()

    footage_budget = a.target - len(stills) * a.still_duration
    if footage_budget <= 0:
        fail("cut", f"{len(stills)} stills x {a.still_duration}s leave no footage inside --target {a.target}s "
                    f"(fewer stills or a longer target)")
    factor = D / footage_budget
    note = None
    if factor < 1.0:
        factor = 1.0
        note = f"recording ({D:.0f}s) is shorter than the footage budget -- plays 1x, cut runs under target"
    elif factor > a.max_ramp:
        factor = a.max_ramp
        note = f"ramp clamped to {a.max_ramp}x -- cut will exceed --target {a.target}s"

    tmp = mpath.parent / "segments"
    tmp.mkdir(exist_ok=True)
    bounds = [0.0] + [off for off, _ in stills] + [D]
    segs = []

    def render(args, out):
        r = run(args + [str(out)])
        if r.returncode != 0:
            fail("cut", f"segment render failed ({out.name}): {r.stderr.strip()[-300:]}")
        segs.append(out)

    for i in range(len(bounds) - 1):
        start, end = bounds[i], bounds[i + 1]
        if end - start > 0.25:
            render(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(mkv),
                    "-vf", f"setpts=PTS/{factor:.4f},fps={FPS},scale={W}:{H}"]
                   + ENCODE + ["-crf", "18"], tmp / f"seg_{len(segs):03d}.mp4")
        if i < len(stills):
            still = stills[i][1]
            render(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", str(a.still_duration),
                    "-i", str(still),
                    "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                           f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"]
                   + ENCODE + ["-crf", "18"], tmp / f"seg_{len(segs):03d}.mp4")

    listfile = tmp / "concat.txt"
    # bare filenames: concat resolves relative to the listfile, sidestepping quote escaping
    listfile.write_text("".join(f"file '{s.name}'\n" for s in segs), encoding="utf-8")
    cut = mpath.parent / "cut.mp4"
    r = run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(cut)])
    if r.returncode != 0:
        fail("cut", f"concat failed: {r.stderr.strip()[-300:]}")

    out_info = ffprobe_stream(cut)
    if not out_info or out_info["duration"] <= 0:
        fail("cut", "concat wrote an unprobeable file")
    frames = []
    for i in range(4):
        f = mpath.parent / f"cut_verify_{i}.png"
        run(["ffmpeg", "-y", "-ss", f"{out_info['duration'] * (i + 0.5) / 4:.2f}",
             "-i", str(cut), "-frames:v", "1", str(f)])
        if f.exists():
            frames.append(str(f.resolve()))
    manifest["cut"] = {"path": str(cut.resolve()), "duration_s": out_info["duration"],
                       "stills": [str(p.resolve()) for _, p in stills], "ramp": round(factor, 2)}
    save_manifest(manifest, mpath)
    ok("cut", f"{out_info['duration']:.1f}s = {len(stills)} still(s) @1x + footage ramped {factor:.1f}x",
       note=note, cut=cut.resolve(), frames=";".join(frames))


def cmd_teaser(a):
    manifest, mpath = load_manifest(a.manifest, "teaser")
    if not manifest.get("cut"):
        fail("teaser", "no cut in the manifest -- run cut first")
    src = Path(manifest["cut"]["path"])
    out = mpath.parent / "teaser.mp4"
    budget = a.max_mb * 1024 * 1024
    for crf, scale in [(28, 1.0), (32, 1.0), (36, 0.75), (40, 0.5)]:
        vf = f"scale=trunc(iw*{scale}/2)*2:trunc(ih*{scale}/2)*2" if scale < 1.0 else "null"
        r = run(["ffmpeg", "-y", "-i", str(src), "-vf", vf]
                + ENCODE + ["-crf", str(crf), str(out)])
        if r.returncode != 0:
            fail("teaser", f"encode failed at crf={crf}: {r.stderr.strip()[-200:]}")
        if out.stat().st_size <= budget:
            ok("teaser", f"crf={crf} scale={scale} size={out.stat().st_size / 1e6:.1f}MB",
               teaser=out.resolve())
    fail("teaser", f"still {out.stat().st_size / 1e6:.1f}MB over {a.max_mb}MB at crf=40/0.5x -- "
                   f"trim the cut or raise --max-mb")


# ---------------------------------------------------------------- CLI doors

def main():
    p = argparse.ArgumentParser(prog="showcase.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start", help="launch a detached recording + write the manifest")
    s.add_argument("--monitor", type=int, required=True, help="ddagrab output_idx (discover with check --monitor N)")
    s.add_argument("--out", required=True, help="fresh take directory")
    s.add_argument("--grab-dir", action="append", help="dir of stamped grab PNGs (repeatable; Unity temporaryCachePath etc.)")
    s.add_argument("--gdigrab", action="store_true", help="CPU whole-desktop fallback if ddagrab contends")
    s.add_argument("--fps", type=int, default=30)
    s.add_argument("--crf", type=int, default=18)
    s.set_defaults(fn=cmd_start)

    s = sub.add_parser("check", help="extract a frame to Read: live take (--manifest) or monitor discovery (--monitor)")
    s.add_argument("--manifest")
    s.add_argument("--monitor", type=int)
    s.add_argument("--gdigrab", action="store_true")
    s.add_argument("--out", help="dir for the discovery frame")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("stop", help="end the recording, stamp the probed duration")
    s.add_argument("--manifest", required=True)
    s.set_defaults(fn=cmd_stop)

    s = sub.add_parser("beats", help="list stamped grab files as offsets from t0")
    s.add_argument("--manifest", required=True)
    s.set_defaults(fn=cmd_beats)

    s = sub.add_parser("cut", help="stills at 1x + uniformly ramped footage, to --target seconds")
    s.add_argument("--manifest", required=True)
    s.add_argument("--target", type=float, required=True, help="target duration in seconds")
    s.add_argument("--still", action="append", help="stamped PNG to splice (repeatable)")
    s.add_argument("--still-duration", type=float, default=2.5)
    s.add_argument("--max-ramp", type=float, default=30.0, help="legibility ceiling on the fast-forward factor")
    s.set_defaults(fn=cmd_cut)

    s = sub.add_parser("teaser", help="re-encode the cut under a size budget")
    s.add_argument("--manifest", required=True)
    s.add_argument("--max-mb", type=float, default=10.0)
    s.set_defaults(fn=cmd_teaser)

    a = p.parse_args()
    if a.cmd == "check" and not (a.manifest or a.monitor is not None):
        fail("check", "pass --manifest (live take) or --monitor N (discovery)")
    a.fn(a)


if __name__ == "__main__":
    main()
