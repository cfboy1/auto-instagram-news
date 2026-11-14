"""Orchestrates: script → frames → PNGs → ffmpeg → reel mp4 (+cover, caption)."""
import os
import shutil
import subprocess
import uuid

from app import config
from app.pipeline import script as script_mod
from app.pipeline import audio as audio_mod
from app.render import ffmpeg_build, renderer

INTRO = [("i1_intro.html", 1.8), ("i2_intro.html", 1.8)]
OUTRO = ("outro.html", 3.0)


def build(text: str, media_path: str = None, out_dir: str = None) -> dict:
    """Sync (CPU-bound) — call via asyncio.to_thread. media_path may be None."""
    sc = script_mod.make_script(text)
    tag = uuid.uuid4().hex[:10]
    work = os.path.join(config.WORK_DIR, tag)
    os.makedirs(work, exist_ok=True)

    # مدیای ویدیویی در قالب <img> رندر نمی‌شود؛ یک فریم نمایش‌گر از آن به‌جای تصویر کاور می‌آید
    if media_path and media_path.lower().endswith((".mp4", ".mov", ".webm", ".mkv", ".avi")):
        # فریم ۰ اغلب کارت تیتر/پنل خالی است؛ حدود یک‌سوم ویدیو نمایش‌گر مطمئن‌تری است
        seek = "0"
        try:
            dur = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", media_path],
                check=True, capture_output=True, text=True,
            ).stdout.strip() or 0)
            if dur > 1:
                seek = f"{min(dur / 3, dur - 0.2):.2f}"
        except Exception:
            pass
        frame = os.path.join(work, "media_frame.jpg")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", seek, "-i", media_path,
             "-frames:v", "1", "-q:v", "2", frame],
            check=True, capture_output=True,
        )
        media_path = frame

    frames = []  # (png, dur)
    transitions = []

    # intro (اختصاصی)
    for tpl, dur in INTRO:
        png = os.path.join(work, f"{len(frames)}.png")
        renderer.render_frame(tpl, {}, png)
        frames.append((png, dur))
    transitions.append("circleopen")

    # گام ۱: کاور — اگر مدیا باشد، خودِ قالب با‌مدیا کاور است (مدیا + تیتر با هم)
    head_dur = script_mod.read_duration(sc["headline"], minimum=5.0, cap=8.0)
    cover_png = os.path.join(work, "2.png")
    if media_path:
        renderer.render_frame(
            "cover_media.html",
            {
                "HEADLINE": sc["headline"],
                "CATEGORY": sc["category"],
                "MEDIA": "file://" + media_path,
                "SUB": "جزئیات خبر 👇",
            },
            cover_png,
        )
    else:
        renderer.render_frame(
            "cover_nomedia.html",
            {"HEADLINE": sc["headline"], "CATEGORY": sc["category"]},
            cover_png,
        )
    frames.append((cover_png, head_dur))
    transitions.append("wipeleft")

    # گام‌های بعدی: به تعداد فکت‌ها (تابع طول پیام)
    n = len(sc["facts"])
    fact_pngs = []
    for i, fact in enumerate(sc["facts"]):
        png = os.path.join(work, f"{3 + i}.png")
        renderer.render_frame(
            "fact.html",
            {
                "TEXT": fact,
                # RLM + تیره در انتها تا در بستر RTL مثل مرجع، تیره سمت چپِ اسم بنشیند
                "SRC": "\u200f" + config.BRAND_NAME + " —",
                "PCT": str(int(100 * (i + 1) / max(1, n))),
            },
            png,
        )
        fact_pngs.append(png)
        frames.append((png, script_mod.read_duration(fact, minimum=4.0, cap=6.0)))
        transitions.append("slideup" if i == 0 else "wipeleft")

    # خروجی
    png = os.path.join(work, "outro.png")
    renderer.render_frame("outro.html", {"TEXT": config.OUTRO_TEXT}, png)
    frames.append((png, OUTRO[1]))
    transitions.append("slideup")

    # صدا: انتخاب تصادفی از پول + افکت‌های ریز
    durations = [d for _, d in frames]
    offsets, total = ffmpeg_build.calc_offsets(durations, transitions)
    audio_wav = os.path.join(work, "mix.wav")
    audio_wav = audio_mod.pick(offsets, total, audio_wav)

    out_dir = out_dir or config.WORK_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_mp4 = os.path.join(out_dir, f"reel_{tag}.mp4")
    ffmpeg_build.build(frames, transitions, audio_wav, out_mp4)

    cover_out = os.path.join(out_dir, f"cover_{tag}.png")
    shutil.copy(cover_png, cover_out)
    caption = (
        f"{sc['headline']}\n\n"
        f"{sc['category']} | {config.BRAND_NAME}\n{config.BRAND_HANDLE}"
    )
    shutil.rmtree(work, ignore_errors=True)

    return {
        "path": out_mp4,
        "cover": cover_out,
        "caption": caption,
        "total": total,
        "headline": sc["headline"],
        "category": sc["category"],
    }
