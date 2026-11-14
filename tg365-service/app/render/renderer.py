"""HTML template → PNG via Playwright (sync API, serialized for low-RAM hosts)."""
import os
import threading
import uuid

from app import config

_lock = threading.Lock()
_pw = None
_browser = None

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def _ensure_browser():
    global _pw, _browser
    if _browser is not None:
        return
    from playwright.sync_api import sync_playwright

    _pw = sync_playwright().start()
    _browser = _pw.chromium.launch(
        args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
    )


def render_frame(template: str, mapping: dict, out_png: str) -> str:
    """Fill {{KEY}} placeholders in `template`, render 1080x1920 PNG."""
    with _lock:
        _ensure_browser()
        with open(os.path.join(TEMPLATES_DIR, template), encoding="utf-8") as f:
            html = f.read()
        for key, val in mapping.items():
            html = html.replace("{{" + key + "}}", str(val))

        # قالب‌ها به _style.css (فونت‌ها، برندبار، دات‌ها) رفرنس relative دارند؛
        # چون صفحه‌ی رندر در WORK_DIR نوشته می‌شود، لینک را مطلق می‌کنیم تا
        # استایل‌شیت و فونت‌ها از پوشه‌ی قالب‌ها لود شوند.
        html = html.replace(
            'href="_style.css"',
            'href="file://' + TEMPLATES_DIR + '/_style.css"',
        )

        tmp = os.path.join(config.WORK_DIR, f"page_{uuid.uuid4().hex}.html")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(html)

        page = _browser.new_page(viewport={"width": 1080, "height": 1920})
        try:
            page.goto("file://" + tmp)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(700)
            page.screenshot(path=out_png)
        finally:
            page.close()
            try:
                os.remove(tmp)
            except OSError:
                pass
    return out_png
