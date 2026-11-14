"""Random (no-immediate-repeat) audio pick from the pool + micro-SFX mixing."""
import glob
import os
import random
import subprocess

from app import config

LAST_FILE = os.path.join(config.DATA_DIR, ".last_audio")

SFX_GAIN = 0.15  # افکت‌ها باید خیلی ریز باشند — فقط یک‌بار اعمال می‌شود


def _run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def whoosh_path() -> str:
    """نویز خام با پنجره‌ی fade — گین نهایی هنگام میکس در pick() اعمال می‌شود."""
    p = os.path.join(config.DATA_DIR, "sfx_whoosh.wav")
    if not os.path.exists(p):
        _run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "anoisesrc=d=0.35:c=pink:a=0.6",
            "-af",
            "aformat=channel_layouts=stereo,highpass=f=300,lowpass=f=1600,"
            "afade=t=in:st=0:d=0.10,afade=t=out:st=0.15:d=0.20",
            p,
        ])
    return p


def pool() -> list:
    files = []
    for ext in ("mp3", "wav", "m4a", "aac", "ogg", "opus"):
        files += glob.glob(os.path.join(config.AUDIOS_DIR, f"*.{ext}"))
    return sorted(files)


def pick(offsets: list, total: float, out_wav: str):
    """Random track != last used; mix subtle whooshes at every transition."""
    tracks = pool()
    if not tracks:
        return None
    last = ""
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, encoding="utf-8") as f:
            last = f.read().strip()
    choices = [t for t in tracks if t != last] or tracks
    track = random.choice(choices)
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(track)

    whoosh = whoosh_path()
    # -stream_loop: ترک کوتاه‌تر از رییل تا پایان لوپ می‌شود (به‌جای سکوت دنباله)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", track]
    fc = []
    labels = []
    for i, off in enumerate(offsets):
        cmd += ["-i", whoosh]
        ms = int(off * 1000)
        fc.append(f"[{i+1}]volume={SFX_GAIN},adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    mix_in = "".join(labels)
    fc.append(
        f"[0]{mix_in}amix=inputs={len(labels)+1}:normalize=0,"
        f"afade=t=out:st={max(0.0, total-0.6):.2f}:d=0.6[aout]"
    )
    cmd += ["-filter_complex", ";".join(fc), "-map", "[aout]", "-t", f"{total:.2f}", out_wav]
    _run(cmd)
    return out_wav
