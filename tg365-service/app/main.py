"""Entry point.

Standalone (EMBEDDED=0, default): this service runs its own bot via long
polling + the web server (OAuth callback + /files hosting).

Embedded (EMBEDDED=1): tg-translator imports this package and registers the
handlers on its own Application; the web server is started by tg-translator
(or by running `python -m app.web.server` separately).
"""
import threading

from app import config


def main():
    import uvicorn
    from telegram.ext import Application

    from app.bot.handlers import register
    from app.web.server import build_web_app

    web = build_web_app()
    threading.Thread(
        target=lambda: uvicorn.run(
            web, host="0.0.0.0", port=config.PORT, log_level="warning"
        ),
        daemon=True,
    ).start()

    app = Application.builder().token(config.BOT_TOKEN).build()
    register(app)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
