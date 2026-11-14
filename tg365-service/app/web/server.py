"""FastAPI: OAuth callback + public file hosting (Instagram needs public video URLs)."""
import html

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app import config, db
from app.instagram import client as ig

SUCCESS_HTML = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<style>body{{font-family:Tahoma;display:flex;min-height:100vh;align-items:center;justify-content:center;background:#EEF3F5;color:#1A2440}}
.box{{background:#fff;border-radius:16px;padding:40px 60px;text-align:center;box-shadow:0 8px 30px rgba(0,0,0,.12)}}
h1{{color:#D0201F}}</style></head><body><div class="box"><h1>{title}</h1><p>{msg}</p></div></body></html>"""


def build_web_app() -> FastAPI:
    app = FastAPI(title="tg365news")
    app.mount("/files", StaticFiles(directory=config.PUBLISHED_DIR), name="files")

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/oauth/callback")
    def oauth_callback(code: str = "", state: str = "", error: str = "", error_description: str = ""):
        if error:
            return HTMLResponse(
                SUCCESS_HTML.format(title="اتصال ناموفق", msg=html.escape(error_description or error)),
                status_code=400,
            )
        st = db.pop_state(state)
        if not st:
            return HTMLResponse(
                SUCCESS_HTML.format(title="خطا", msg="درخواست نامعتبر یا منقضی شده است."), status_code=400
            )
        uid = st["telegram_id"]
        redirect_uri = f"{config.PUBLIC_BASE_URL}/oauth/callback"
        try:
            short = ig.exchange_code(config.IG_APP_ID, config.IG_APP_SECRET, redirect_uri, code)
            ll = ig.long_lived_token(config.IG_APP_SECRET, short)
            me = ig.me(ll["token"])
            db.upsert_account(uid, me.get("username", ""), ll["token"], str(me.get("user_id", "")))
        except Exception as e:  # noqa: BLE001
            return HTMLResponse(
                SUCCESS_HTML.format(title="اتصال ناموفق", msg=html.escape(str(e))), status_code=500
            )
        return HTMLResponse(
            SUCCESS_HTML.format(title="حساب متصل شد ✅", msg="می‌توانی این صفحه را ببندی و به بات برگردی.")
        )

    return app
