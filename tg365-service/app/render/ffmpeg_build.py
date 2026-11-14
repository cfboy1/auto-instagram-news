"""ffmpeg assembly: per-frame segments → xfade chain → mux with prepared audio.

Mirrors the approved demo pipeline exactly (no zoompan — zero jitter;
wipe/slide/circleopen transitions; fade in/out).
"""
import os
import subprocess

from app import config

FPS = 30
TRANSITION = 0.4
INTRO_TRANS = 0.5  # circleopen uses a slightly longer blend


def _run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def _seg(png: str, dur: float, out: str):
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-loop", "1",
        "-framerate", str(FPS), "-i", png, "-t", f"{dur:.2f}",
        "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", out,
    ])


def calc_offsets(durations: list, transitions: list):
    """Cumulative xfade offsets — same math as the approved demo."""
    offsets = []
    run = 0.0
    for i in range(len(transitions)):
        t = INTRO_TRANS if i == 0 else TRANSITION
        off = (durations[0] if i == 0 else run) - t
        run = off + durations[i + 1]
        offsets.append(round(off, 2))
    total = round(offsets[-1] + durations[-1], 2)
    return offsets, total


def build(frames: list, transitions: list, audio_wav, out_mp4: str) -> float:
    """frames: [(png_path, duration)] ; transitions: [name] ; audio_wav: path|None"""
    work = os.path.dirname(out_mp4)
    tag = os.path.splitext(os.path.basename(out_mp4))[0]
    segs = []
    for i, (png, dur) in enumerate(frames):
        s = os.path.join(work, f"{tag}_seg{i}.mp4")
        _seg(png, dur, s)
        segs.append(s)

    offsets, total = calc_offsets([d for _, d in frames], transitions)

    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for s in segs:
        cmd += ["-i", s]
    if audio_wav:
        cmd += ["-i", audio_wav]

    fc = []
    prev = "0:v"
    for i, (off, tr) in enumerate(zip(offsets, transitions)):
        label = f"v{i:02d}"
        fc.append(f"[{prev}][{i+1}:v]xfade=transition={tr}:duration={TRANSITION}:offset={off}[{label}]")
        prev = label
    fc.append(f"[{prev}]fade=t=in:st=0:d=0.25,fade=t=out:st={max(0.0, total-0.5):.2f}:d=0.5[vout]")

    maps = ["-map", "[vout]"]
    codecs = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
              "-pix_fmt", "yuv420p"]
    if audio_wav:
        ai = len(segs)
        fc.append(f"[{ai}:a]afade=t=out:st={max(0.0, total-0.6):.2f}:d=0.6[aout]")
        maps += ["-map", "[aout]"]
        codecs += ["-c:a", "aac", "-b:a", "128k"]
    else:
        codecs += ["-an"]

    cmd += ["-filter_complex", ";".join(fc)] + maps + codecs + [
        "-t", f"{total:.2f}", "-movflags", "+faststart", out_mp4,
    ]
    _run(cmd)
    for s in segs:
        os.unlink(s)
    return total
