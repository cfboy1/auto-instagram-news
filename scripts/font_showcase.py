"""Font showcase reel: renders every chat-selected font on real project templates.

Title fonts on cover_media, text fonts on fact.html (with per-variant
@font-face + family swap, reverted after each render). Output:
data/work/font_showcase.mp4 — audio from the pool (loops if short).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tg365-service"))

from app import config  # noqa: E402
from app.render import ffmpeg_build, renderer  # noqa: E402
from app.pipeline import audio as audio_mod  # noqa: E402

CSS = os.path.join(ROOT, "tg365-service/app/render/templates/_style.css")
FACT = os.path.join(ROOT, "tg365-service/app/render/templates/fact.html")
CAND = os.path.join(ROOT, "font-candidates")

HEADS = "h1,h2,.w1,.w2,.stay,.badge,.cat,.catstrip{font-family:'Plasma','Shazde',Tahoma,sans-serif;font-weight:400}"
TXT_OLD = ".txt{font-family:'Badkhat','Shazde',Tahoma,sans-serif;font-size:88px;font-weight:900;line-height:1.85;z-index:2;margin-top:40px}"

TITLE_FONTS = [
    ("CandBahman", "Bahman.ttf", "بهمن"),
    ("CandKalameh", "Kalameh-Black.ttf", "کلمه"),
    ("CandTitr", "Titr-Bold.ttf", "تیتر"),
    ("CandRokh", "Rokh-UltraBold.otf", "رخ"),
    ("CandAviny", "Aviny.ttf", "عوینی"),
    ("CandLalezar", "Lalezar-Regular.ttf", "لاله‌زار"),
]
TEXT_FONTS = [
    ("CandRosha", "Rosha-Regular.otf", "روشا"),
    ("CandPeyda", "Peyda-Regular.ttf", "پیدا"),
    ("CandIRANSansX", "IRANSansX-Regular.ttf", "ایران‌سنس"),
    ("CandDana", "Dana-Regular.ttf", "دانا"),
    ("CandDabir", "Dabir.ttf", "دبیر"),
    ("CandMirza", "Mirza-Regular.ttf", "میرزا"),
    ("CandAlef", "Alef-Regular.ttf", "علف"),
]

COVER_MAP = {
    "HEADLINE": "ترامپ: دموکرات‌ها فاسد و شرور هستند",
    "CATEGORY": "بین‌الملل",
    "MEDIA": "file://" + os.path.join(ROOT, "scripts/assets/trump.png"),
}
FACT_MAP = {"TEXT": "تحلیل‌گران می‌گویند این تصمیم می‌تواند بازارهای جهانی را در هفته آینده متأثر کند."}


def fc(fam, fname):
    return ("@font-face{font-family:'%s';"
            "src:url('file://%s/%s') format('truetype');font-weight:400;font-style:normal}\n"
            ) % (fam, CAND, fname)


def main():
    css_orig = open(CSS, encoding="utf-8").read()
    fact_orig = open(FACT, encoding="utf-8").read()
    frames, transitions = [], []

    def add(template, mapping, dur, trans=None):
        png = os.path.join(config.WORK_DIR, "show_%02d.png" % len(frames))
        renderer.render_frame(template, mapping, png)
        frames.append((png, dur))
        if trans:
            transitions.append(trans)

    try:
        add("i1_intro.html", {}, 1.8)
        add("i2_intro.html", {}, 1.8, "wipeleft")
        add("section.html", {"TAG": "⚡ تیترنویسی", "HEADLINE": "فونت‌های تیتر",
                             "SUB": "۶ گزینه از کانال + پلاسما (فعلی)"}, 1.6, "slideup")
        for fam, fname, label in TITLE_FONTS:
            write_css = fc(fam, fname) + css_orig.replace(
                HEADS, HEADS.replace("'Plasma','Shazde'", "'%s','Plasma','Shazde'" % fam))
            open(CSS, "w", encoding="utf-8").write(write_css)
            m = dict(COVER_MAP, SUB="فونت تیتر: " + label)
            add("cover_media.html", m, 2.6, "wipeleft")
        open(CSS, "w", encoding="utf-8").write(css_orig)
        m = dict(COVER_MAP, SUB="فونت تیتر: پلاسما (فعلی)")
        add("cover_media.html", m, 2.6, "wipeleft")

        add("section.html", {"TAG": "⚡ متن‌نویسی", "HEADLINE": "فونت‌های متن",
                             "SUB": "۸ گزینه — متن کارت فکت"}, 1.6, "slideup")
        add("fact.html", dict(FACT_MAP, SRC="فونت متن: بدخت (فعلی)", PCT="12"), 2.6, "wipeleft")
        for i, (fam, fname, label) in enumerate(TEXT_FONTS):
            write_fact = fact_orig.replace(
                "<style>", "<style>\n" + fc(fam, fname), 1).replace(
                TXT_OLD, (".txt{font-family:'%s','Shazde',Tahoma,sans-serif;"
                          "font-size:80px;font-weight:400;line-height:1.85;"
                          "z-index:2;margin-top:40px}") % fam)
            open(FACT, "w", encoding="utf-8").write(write_fact)
            add("fact.html", dict(FACT_MAP, SRC="فونت متن: " + label,
                                  PCT=str(12 + 12 * (i + 1))), 2.6, "wipeleft")
        open(FACT, "w", encoding="utf-8").write(fact_orig)

        add("outro.html", {"TEXT": config.OUTRO_TEXT}, 3.0, "slideup")
    finally:
        open(CSS, "w", encoding="utf-8").write(css_orig)
        open(FACT, "w", encoding="utf-8").write(fact_orig)

    durations = [d for _, d in frames]
    offsets, total = ffmpeg_build.calc_offsets(durations, transitions)
    work = os.path.join(config.WORK_DIR, "showcase")
    os.makedirs(work, exist_ok=True)
    wav = audio_mod.pick(offsets, total, os.path.join(work, "mix.wav"))
    out = os.path.join(config.WORK_DIR, "font_showcase.mp4")
    ffmpeg_build.build(frames, transitions, wav, out)

    for png, _ in frames:
        os.remove(png)
    print(json.dumps({"path": out, "total_sec": total,
                      "frames": len(frames), "size_mb": round(os.path.getsize(out) / 1e6, 2)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
