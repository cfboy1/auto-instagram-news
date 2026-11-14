# راه‌اندازی بخش اینستاگرام — tg365-service

> ترتیب دقیق وابسته به هم است: اول دامنه (Railway)، بعد اپ متا، بعد اتصال.

## مرحله ۰ — پیش‌نیازها

- [ ] اکانت اینستاگرام متعلق به خودت (Business یا Creator — مرحله ۱)
- [ ] توکن بات تلگرام از [@BotFather](https://t.me/BotFather) (بات جدید بساز → `/newbot`)
- [ ] اکانت GitHub + اکانت [Railway](https://railway.app)

## مرحله ۱ — اکانت اینستاگرام Professional

در اپ اینستاگرام: **Settings and privacy → Account type and tools → Switch to professional account → Business**

(Creator هم قبول است؛ برای خبر Business بهتر است.)

## مرحله ۲ — دیپلوی روی Railway (دامنه‌ی HTTPS لازم است)

1. ریپو را به GitHub بفرست (private) — می‌توانم انجام دهم، بگو.
2. Railway → **New Project → Deploy from GitHub repo** → انتخاب ریپو
3. **Variables** این‌ها را ست کن:
   | کلید | مقدار |
   |---|---|
   | `BOT_TOKEN` | توکن BotFather |
   | `EMBEDDED` | `0` |
   | `IG_APP_ID` / `IG_APP_SECRET` | از مرحله ۳ (فعلاً خالی یا placeholder) |
   | `PUBLIC_BASE_URL` | بعد از گرفتن دامنه (قدم ۴) |
4. **Settings → Networking → Generate Domain** → مثلاً `https://xxx.up.railway.app`
5. `PUBLIC_BASE_URL=https://xxx.up.railway.app` را ست کن تا سرویس redeploy شود

## مرحله ۳ — اپ متا (developers.facebook.com)

1. **My Apps → Create App** → نوع **Business**
2. در Use cases / Add product: **Instagram** را اضافه کن و گزینه‌ی
   **«Instagram API with Instagram Login»** را انتخاب کن
   (نه Facebook Login — با این مسیر نیازی به Page فیسبوک نیست)
3. **App settings → Basic**:
   - `Instagram App ID` → این همان `IG_APP_ID`
   - `Instagram App Secret` → این همان `IG_APP_SECRET` (در Railway ست کن)
4. **Instagram settings → Authentication → Valid OAuth Redirect URIs:**
   ```
   https://xxx.up.railway.app/oauth/callback
   ```
   ⚠️ باید دقیقاً با `PUBLIC_BASE_URL` + `/oauth/callback` یکی باشد.
5. **App roles → Instagram Testers → Add Instagram Testers** → یوزرنیم خودت را اضافه کن
   - چون فقط اکانت خودت را وصل می‌کنی، **App Review لازم نیست** (حالت Development)

## مرحله ۴ — قبول دعوت تستر در اینستاگرام

اپ اینستاگرام → **Settings → Website permissions → Apps and websites → Tester invites** → Accept

## مرحله ۵ — اتصال از بات

1. در بات تلگرام: `/connect_insta`
2. صفحه OAuth اینستاگرام باز می‌شود → لاگین با همان اکانت Business → Authorize
3. کال‌بک می‌آید به Railway → توکن ۶۰ روزه در SQLite ذخیره می‌شود (خودکار تازه‌سازی می‌شود)

### خطاهای رایج

| خطا | علت |
|---|---|
| `redirect_uri mismatch` | URI در متا با `PUBLIC_BASE_URL` فرق دارد (slash/http‑s را چک کن) |
| `account is not a tester` | دعوت مرحله ۴ قبول نشده |
| `invalid app secret` | `IG_APP_SECRET` اشتباه در Railway |

## مرحله ۶ — انتشار تستی

1. `/publish_mode` در بات
2. یک پست کانال را فوروارد کن → رییل ساخته می‌شود → **پیش‌نمایش + دکمه تأیید**
3. تأیید → انتشار REELS روی اینستاگرام

## محدودیت‌ها

- سقف رسمی انتشار: **۲۵ پست در ۲۴ ساعت**
- دانلود مدیا از تلگرام: سقف **۲۰MB** (ویدیوی بزرگ‌تر → رییل بدون مدیا)
- موزیک لایسنس‌دار اینستاگرام در API در دسترس نیست → فقط فایل صوتی خودت (آزاد/لایسنس‌دار)
- اسکوپ‌ها: `instagram_business_basic` + `instagram_business_content_publish`
