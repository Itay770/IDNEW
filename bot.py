import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_PATH = "/telegram"

# Render Web Service supplies this automatically.
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip().lstrip("@")

if not BOT_USERNAME:
    raise RuntimeError("BOT_USERNAME לא מוגדר. לדוגמה: my_bot")

application = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None:
        return

    user_id = user.id
    name = user.full_name or "המשתמש"

    # Every user gets a unique deep-link to this bot.
    # The link identifies the user but does not bypass Telegram privacy.
    personal_link = f"https://t.me/{BOT_USERNAME}?start=u_{user_id}"

    await update.message.reply_text(
        f"שלום {name} 👋\n\n"
        f"🆔 ה-Telegram ID שלך:\n`{user_id}`\n\n"
        "🔗 הקישור הייחודי שלך:\n"
        f"{personal_link}\n\n"
        "שלח את הקישור הזה למי שאתה רוצה."
        "\n"
        "כאשר מישהו יפתח אותו, הבוט יזהה שהקישור שייך אליך.",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def open_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # /start u_123456789
    if not update.message:
        return

    args = context.args
    if not args:
        return

    ref = args[0]

    if not ref.startswith("u_"):
        return

    owner_id = ref[2:]

    if not owner_id.isdigit():
        return

    await update.message.reply_text(
        "הקישור זוהה ✅\n\n"
        f"🆔 Telegram ID של בעל הקישור: `{owner_id}`\n\n"
        "שים לב: Telegram לא מאפשר לבוט לעקוף הגדרות פרטיות "
        "ולפתוח צ'אט ישיר עם משתמש לפי ID בלבד.",
        parse_mode="Markdown",
    )


async def health(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def telegram_webhook(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        return web.Response(text="OK")
    except Exception as exc:
        print(f"Webhook error: {exc}", flush=True)
        return web.Response(status=400, text="Bad Request")


async def main() -> None:
    global application

    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN לא מוגדר.")

    if not BASE_URL:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL לא זמין. "
            "הרץ את הקוד כ-Render Web Service."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .updater(None)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start", open_link))

    await application.initialize()
    await application.start()

    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"

    await application.bot.set_webhook(
        url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
    )

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_post(WEBHOOK_PATH, telegram_webhook)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"Service is live on port {PORT}", flush=True)
    print(f"Webhook: {webhook_url}", flush=True)
    print(f"Bot: @{BOT_USERNAME}", flush=True)

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
