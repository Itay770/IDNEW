import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_BASE = (os.getenv("RENDER_EXTERNAL_URL", "").strip() or os.getenv("WEBHOOK_URL", "").strip()).rstrip("/")
WEBHOOK_PATH = "/telegram"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None or update.message is None:
        return
    user_id = user.id
    name = user.full_name or "המשתמש"
    chat_url = f"tg://user?id={user_id}"
    keyboard = [[InlineKeyboardButton("💬 פתח שיחה עם המשתמש", url=chat_url)]]
    await update.message.reply_text(
        f"👤 משתמש: {name}\n🆔 ID: {user_id}\n\nלחץ על הכפתור כדי לפתוח שיחה עם המשתמש:",
        reply_markup=InlineKeyboardMarkup(keyboard),
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

async def run() -> None:
    global application
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN לא מוגדר ב-Render.")
    if not WEBHOOK_BASE:
        raise RuntimeError("לא נמצאה כתובת Render (RENDER_EXTERNAL_URL).")

    application = Application.builder().token(BOT_TOKEN).updater(None).build()
    application.add_handler(CommandHandler("start", start))

    await application.initialize()
    await application.start()

    webhook_url = f"{WEBHOOK_BASE}{WEBHOOK_PATH}"
    await application.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_post(WEBHOOK_PATH, telegram_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"Service is running on port {PORT}", flush=True)
    print(f"Webhook set to: {webhook_url}", flush=True)

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(run())
