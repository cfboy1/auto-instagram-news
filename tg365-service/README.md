# tg365-service — موتور ساخت و انتشار رییلز THE365NEWS

سرویس کامل: پیام کانال را می‌گیرد → اینترو + کاور (مدیا+متن) + کارت‌های نقل‌قول + خروجی می‌سازد → صدای رندوم از پول + افکت ریز → MP4 عمودی → با تأیید شما روی اینستاگرام منتشر می‌شود (Instagram API با لاگین رسمی OAuth).

```
┌──────────────── Railway (یک کانتینر Docker) ─────────────────┐
│  بات تلگرام (long polling)        ← دستورها + حالت انتشار     │
│  FastAPI  :8000                   ← /oauth/callback  + /files │
│  موتور رندر: HTML→PNG (Playwright) → ffmpeg (xfade+صدا)       │
│  انتشار: Instagram Graph API (REELS، سقف ۲۵ پست/۲۴ساعت)      │
└──────────────────────────────────────────────────────────────┘
```

## فایل‌ها
```
app/main.py                 نقطه‌ی اجرا (استقلال: بات + وب‌سرور)
app/config.py               تنظیمات از متغیر محیطی
app/db.py                   SQLite (اکانت/حالت‌ها/کارها)
app/bot/handlers.py         دستورهای بات — قابل register در ربات خودت
app/pipeline/script.py      متن → هوک + فکت‌ها + دسته‌بندی + زمان خواندن
app/pipeline/audio.py       انتخاب تصادفی صدا (بدون تکرار پشت‌سرهم) + ووش ریز
app/pipeline/build_reel.py  هماهنگ‌کننده‌ی ساخت کامل
app/render/renderer.py      Playwright: قالب→PNG (۱۰۸۰×۱۹۲۰)
app/render/ffmpeg_build.py  مونتاژ xfade (بدون zoompan = بدون لرزش)
app/render/templates/       قالب‌های برند (اینترو/کاور/فکت/خروجی)
app/instagram/client.py     OAuth + ساخت/انتشار REELS
app/web/server.py           /oauth/callback + هاست عمومی /files
```

## متغیرهای محیطی
| کلید | توضیح |
|---|---|
| `BOT_TOKEN` | توکن بات (اگر EMBEDDED=1 باشد می‌تواند خالی بماند) |
| `IG_APP_ID` / `IG_APP_SECRET` | از اپ متا (Instagram API with Instagram Login) |
| `PUBLIC_BASE_URL` | دامنه‌ی Railway، مثل `https://xxx.up.railway.app` |
| `EMBEDDED` | `0` = مستقل، `1` = داخل ربات خودت |

## راه‌اندازی روی Railway
1. ریپو را بساز و push کن؛ در Railway → New Service → از ریپو.
2. بعد از اولین دیپلوی، دامنه را از Settings → Networking بگیر.
3. متغیرها را ست کن (به‌خصوص `PUBLIC_BASE_URL` با همان دامنه) — سرویس دوباره دیپلوی می‌شود.
4. در اپ متا → Instagram API with Instagram Login → Client OAuth Redirect URI را بگذار: `https://دامنه/oauth/callback`
5. اکانت اینستاگرامت را به‌عنوان Instagram Tester به اپ اضافه کن (حالت Development — بدون App Review چون فقط اکانت خودت است).

## ست‌آپ متا (یک‌بار)
1. developers.facebook.com → Create App → نوع Business.
2. افزودن محصول **Instagram** → انتخاب **Instagram API with Instagram Login**.
3. از Instagram settings اپ: `IG_APP_ID` و `IG_APP_SECRET` را بردار.
4. اکانت اینستاگرام باید **Business/Creator** باشد.
5. OAuth scopes لازم: `instagram_business_basic` + `instagram_business_content_publish`.

## دستورهای بات
| دستور | کار |
|---|---|
| `/connect_insta` | اتصال حساب (OAuth — پسورد به سرور نمی‌آید) |
| `/publish_mode` | ورود به حالت انتشار |
| `/exit_publish` | خروج از حالت انتشار |
| `/add_audio` | حالت افزودن صدا (فایل صوتی بفرست) |
| `/audios` | شمارش پول صدا |

در حالت انتشار: پیام را فوروارد کن → ساخت خودکار (اینترو + کاور + کارت‌ها + صدا) → پیش‌نمایش + دکمه‌ی تأیید → انتشار.

## اتصال به ربات tg-translator
⚠️ یک توکن بات فقط یک پردازش polling می‌تواند داشته باشد. دو راه:
- **راه الف (توصیه‌شده) — embed:** داخل کد tg-translator (اگر python-telegram-bot v21 است):
  ```python
  from app.bot.handlers import register
  register(application)   # بعد از ساخت Application خودت
  ```
  و وب‌سرور را جدا اجرا کن: `uvicorn app.web.server:build_web_app --host 0.0.0.0 --port 8000` (یا `EMBEDDED=1`).
- **راه ب — مستقل با توکن جدید:** یک بات جدید از BotFather بساز، `BOT_TOKEN` آن را بده و `EMBEDDED=0`. هیچ تداخلی با tg-translator ندارد.

## محدودیت‌ها
- دانلود مدیا از تلگرام: سقف ۲۰MB (Bot API) — ویدیوی بزرگ‌تر → رییلز بدون مدیا.
- آلبوم: اولین عکس استفاده می‌شود.
- سقف انتشار: ۲۵ پست در ۲۴ ساعت (رسمی).
- رندر سریال است (برای RAM ۰.۵ گیگابایتی Railway) — هر رییلز ~۲۰-۴۰ ثانیه.
- صدای پول: فایل‌های mp3/wav/m4a در `data/audios` (با /add_audio). برای کپی‌رایت، ترک‌های آزاد پیشنهاد می‌شود.
