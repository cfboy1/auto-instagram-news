"""Smoke test: render one reel locally without Telegram/Instagram.

Run:  .venv/bin/python scripts/smoke_render.py
Prints only paths + metadata — never reads media into context.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tg365-service"))

from app.pipeline.build_reel import build  # noqa: E402

SAMPLE_POST = (
    "ترامپ در سخنرانی امروز گفت که مذاکرات اقتصادی با کشورهای آسیایی به فاز تازه‌ای رسیده است. "
    "به گفته او، توافق جدید می‌تواند تعرفه‌ها را تا ۱۵ درصد کاهش دهد. "
    "تحلیل‌گران می‌گویند این تصمیم می‌تواند بازارهای جهانی را در هفته آینده متأثر کند. "
    "بازارهای آسیا واکنش فوری نشان دادند و شاخص‌های اصلی با رشد مواجه شدند."
)

if __name__ == "__main__":
    media = os.path.join(ROOT, "scripts", "assets", "trump.png")
    result = build(SAMPLE_POST, media_path=media if os.path.exists(media) else None)
    print(json.dumps({
        "path": result["path"],
        "cover": result["cover"],
        "caption": result["caption"],
        "total_sec": round(result["total"], 1),
        "headline": result["headline"],
        "category": result["category"],
        "size_mb": round(os.path.getsize(result["path"]) / 1e6, 2),
    }, ensure_ascii=False, indent=2))
