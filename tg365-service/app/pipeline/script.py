"""Text → reel script: headline, facts, category, read-time durations."""
import re

CATEGORIES = [
    ("بین‌الملل", ["ترامپ", "آمریکا", "اسرائیل", "غزه", "غزة", "اوکراین", "روسیه", "چین",
                  "اروپا", "سازمان ملل", "بین الملل", "بین‌الملل", "واشنگتن", "تل آویو"]),
    ("اقتصادی", ["دلار", "تورم", "بورس", "طلا", "ارز", "نفت", "بودجه", "بانک مرکزی",
                 "یورو", "قیمت", "سکه", "بازار"]),
    ("سیاسی", ["مجلس", "دولت", "انتخابات", "وزیر", "رئیس جمهور", "رئیس‌جمهور",
               "مذاکره", "هیئت", "کابینه"]),
    ("ورزشی", ["فوتبال", "استقلال", "پرسپولیس", "لیگ", "المپیک", "تیم ملی", "بازیکن",
               "گل", "داور"]),
    ("فناوری", ["هوش مصنوعی", "گوشی", "اپل", "گوگل", "تلگرام", "اینترنت", "نرم افزار",
                "نرم‌افزار", "فناوری", "ربات"]),
    ("اجتماعی", ["زلزله", "تصادف", "آموزش", "سلامت", "هوا", "آب", "برق", "گاز", "اصفهان", "تهران"]),
]

DEFAULT_CATEGORY = "خبر فوری"


def guess_category(text: str) -> str:
    for name, kws in CATEGORIES:
        if any(k in text for k in kws):
            return name
    return DEFAULT_CATEGORY


def words(s: str) -> int:
    return len(s.split())


def read_duration(s: str, minimum: float = 4.0, cap: float = 9.0) -> float:
    """~1.5s per 8 Persian words, generous minimum so nothing is unreadable."""
    return round(min(cap, max(minimum, 1.5 * max(1, round(words(s) / 8)))), 1)


def _clean(text: str) -> str:
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def make_script(text: str) -> dict:
    flat = _clean(" ".join(text.splitlines()))
    raw = [s.strip() for s in re.split(r"(?<=[.!؟…])\s+", flat) if s.strip()]
    # جمله‌های خیلی کوتاه به قبلی می‌چسبند تا کلمه‌ای حذف نشود
    parts = []
    for s in raw:
        if parts and len(s) < 10:
            parts[-1] += " " + s
        else:
            parts.append(s)
    if not parts:
        parts = [flat[:200]] if flat else []

    headline = parts[0] if parts else ""
    facts = []
    # تیتر حداکثر ۱۴ کلمه؛ دنباله‌اش گم نمی‌شود — به کارت‌های فکت می‌رود
    head_w = headline.split()
    if len(head_w) > 14:
        facts += [" ".join(head_w[i:i + 40]) for i in range(14, len(head_w), 40)]
        headline = " ".join(head_w[:14]) + "…"

    for s in parts[1:]:
        # جمله‌ی بلند به‌جای حذف، به کارت‌های ≤۴۰ کلمه‌ای شکسته می‌شود
        w = s.split()
        for i in range(0, len(w), 40):
            facts.append(" ".join(w[i:i + 40]))
    # سقف ۸ کارت؛ مازاد به کارت آخر می‌چسبد تا چیزی از متن نیفتد
    if len(facts) > 8:
        facts = facts[:7] + [" ".join(facts[7:])]

    return {
        "headline": headline or "خبر فوری",
        "facts": [f for f in facts if f],
        "category": guess_category(flat),
    }
