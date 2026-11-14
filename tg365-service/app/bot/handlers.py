"""Bot handlers — add these to tg-translator (embed) or run standalone."""
import asyncio
import os
import shutil
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)

from app import config, db
from app.instagram import client as ig
from app.pipeline import audio as audio_mod
from app.pipeline.build_reel import build

_pending_oauth = {}
TELEGRAM_DL_LIMIT = 20_000_000  # Bot API file download cap

HELP = (
    "🤖 دستورها:\n"
    "/connect_insta — اتصال حساب اینستاگرام (OAuth رسمی)\n"
    "/publish_mode — ورود به حالت انتشار\n"
    "/exit_publish — خروج از حالت انتشار\n"
    "/add_audio — افزودن صدا به پول (فایل صوتی بفرست)\n"
    "/audios — تعداد صداهای موجود\n\n"
    "در حالت انتشار، هر پیامی که فوروارد کنی به رییلز اینستاگرام تبدیل می‌شود."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(HELP)


async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = uuid.uuid4().hex
    db.save_state(state, uid)
    url = ig.authorize_url(
        config.IG_APP_ID,
        f"{config.PUBLIC_BASE_URL}/oauth/callback",
        state,
    )
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔗 ورود به اینستاگرام", url=url)]]
    )
    await update.effective_message.reply_text(
        "برای اتصال حساب، روی دکمه بزن و در صفحه‌ی خود اینستاگرام لاگین کن.\n"
        "پسوردت هرگز به سرور ما نمی‌رسد؛ به سرویس فقط اجازه‌ی انتشار داده می‌شود.",
        reply_markup=kb,
    )


async def cmd_mode_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_publish_mode(update.effective_user.id, True)
    await update.effective_message.reply_text(
        "✅ حالت انتشار فعال شد.\nهر خبری که فوروارد کنی ساخته می‌شود؛"
        " خروجی اول پیش‌نمایش است و با تأیید تو منتشر می‌شود.\n"
        "خروج: /exit_publish"
    )


async def cmd_mode_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_publish_mode(update.effective_user.id, False)
    await update.effective_message.reply_text("❌ حالت انتشار غیرفعال شد.")


async def cmd_add_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    on = not db.get_audio_mode(update.effective_user.id)
    db.set_audio_mode(update.effective_user.id, on)
    await update.effective_message.reply_text(
        "🎧 حالت افزودن صدا روشن شد — فایل صوتی بفرست." if on
        else "🎧 حالت افزودن صدا خاموش شد."
    )


async def cmd_audios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = len(audio_mod.pool())
    await update.effective_message.reply_text(f"🎧 {n} فایل صوتی در پول موجود است.")


def _save_audio_sync(src_path: str) -> str:
    ext = os.path.splitext(src_path)[1] or ".mp3"
    dest = os.path.join(config.AUDIOS_DIR, f"aud_{uuid.uuid4().hex[:8]}{ext}")
    shutil.copy(src_path, dest)
    return dest


async def _handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, tgm):
    file = await (tgm.audio or tgm.voice or tgm.document).get_file()
    tmp = os.path.join(config.WORK_DIR, f"dl_{uuid.uuid4().hex}")
    await file.download_to_drive(tmp)
    dest = await asyncio.to_thread(_save_audio_sync, tmp)
    os.remove(tmp)
    await update.effective_message.reply_text(
        f"✅ صدا اضافه شد. ({len(audio_mod.pool())} فایل در پول)"
    )


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.effective_message

    # audio capture mode
    if msg.audio or msg.voice or (msg.document and msg.document.mime_type or "").startswith("audio"):
        if db.get_audio_mode(uid):
            await _handle_audio(update, context, msg)
            return
        await msg.reply_text("برای افزودن این صدا اول /add_audio را بزن.")
        return

    if not db.get_publish_mode(uid):
        await msg.reply_text(HELP)
        return

    # media extraction (photo/video/document)
    media_path = None
    tmp = os.path.join(config.WORK_DIR, f"in_{uuid.uuid4().hex}")
    if msg.photo:
        f = await context.bot.get_file(msg.photo[-1].file_id)
        media_path = tmp + ".jpg"
        await f.download_to_drive(media_path)
    elif msg.video:
        if (msg.video.file_size or 0) > TELEGRAM_DL_LIMIT:
            await msg.reply_text(
                "⚠️ ویدیو بزرگ‌تر از سقف ۲۰ مگابایتی Bot API است؛"
                " رییلز بدون مدیا ساخته می‌شود یا ویدیوی سبک‌تر بفرست."
            )
        else:
            f = await context.bot.get_file(msg.video.file_id)
            media_path = tmp + ".mp4"
            await f.download_to_drive(media_path)
    elif msg.document and (msg.document.mime_type or "").startswith(("image/", "video/")):
        if (msg.document.file_size or 0) <= TELEGRAM_DL_LIMIT:
            f = await context.bot.get_file(msg.document.file_id)
            media_path = tmp + ("." + (msg.document.file_name or "file").split(".")[-1])
            await f.download_to_drive(media_path)

    text = msg.caption or msg.text or ""
    if not text.strip() and not media_path:
        await msg.reply_text("چیزی برای ساخت پیدا نکردم — متن یا عکس/ویدیو بفرست.")
        return

    status = await msg.reply_text("⏳ در حال ساخت رییلز… (چند لحظه)")
    try:
        res = await asyncio.to_thread(build, text, media_path)
    except Exception as e:  # noqa: BLE001
        await status.edit_text(f"❌ خطا در ساخت: {e}")
        return

    job_id = db.add_job(uid, res["path"], res["caption"])
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ انتشار در اینستاگرام", callback_data=f"pub:{job_id}")],
        [InlineKeyboardButton("❌ رد", callback_data=f"rej:{job_id}")],
    ])
    await status.delete()
    with open(res["path"], "rb") as f:
        await msg.reply_video(
            video=f,
            caption=f"🎬 پیش‌نمایش ({res['total']:.0f} ثانیه)\n\n{res['caption'][:800]}",
            reply_markup=kb,
        )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action, _, jid = q.data.partition(":")
    job = db.get_job(int(jid))
    if not job:
        await q.edit_message_caption("این پیش‌نمایش منقضی شده است.")
        return

    if action == "rej":
        await q.edit_message_caption("رد شد 🗑")
        return

    acc = db.get_account(q.from_user.id)
    if not acc:
        await q.edit_message_caption("اول حساب را وصل کن: /connect_insta")
        return

    await q.edit_message_caption("⏳ در حال انتشار در اینستاگرام…")
    name = f"reel_{uuid.uuid4().hex[:10]}.mp4"
    dest = os.path.join(config.PUBLISHED_DIR, name)
    shutil.copy(job["path"], dest)
    video_url = f"{config.PUBLIC_BASE_URL}/files/{name}"

    try:
        media_id = await asyncio.to_thread(
            ig.publish_reel,
            acc["access_token"], acc["ig_user_id"], video_url, job["caption"],
        )
        permalink = await asyncio.to_thread(
            ig.get_permalink,
            acc["access_token"], media_id,
        )
        await q.edit_message_caption(f"✅ منتشر شد!\n{permalink}")
    except Exception as e:  # noqa: BLE001
        await q.edit_message_caption(f"❌ خطا در انتشار: {e}")


def register(app: Application):
    """Embed into an existing python-telegram-bot Application (tg-translator)."""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("connect_insta", cmd_connect))
    app.add_handler(CommandHandler("publish_mode", cmd_mode_on))
    app.add_handler(CommandHandler("exit_publish", cmd_mode_off))
    app.add_handler(CommandHandler("add_audio", cmd_add_audio))
    app.add_handler(CommandHandler("audios", cmd_audios))
    app.add_handler(CallbackQueryHandler(on_button, pattern=r"^(pub|rej):\d+$"))
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND,
            on_message,
        )
    )
