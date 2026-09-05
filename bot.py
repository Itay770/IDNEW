import os
import asyncio

from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))

# Render provides this automatically.
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")

# Optional override if needed
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip().rstrip("/")

# We use ROOT "/" for Telegram webhook.
# This fixes the 404 you were getting on /telegram.
WEBHOOK_PATH = "/"


# ============================================================
# GLOBAL
# ============================================================

application = None
BOT_USERNAME = ""


# ============================================================
# /start
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_USERNAME

    if update.message is None:
        return

    user = update.effective_user

    if user is None:
        return

    user_id = user.id
    name = user.full_name or "משתמש"

    # --------------------------------------------------------
    # User opened his own /start
    # --------------------------------------------------------

    if not context.args:

        personal_link = (
            f"https://t.me/{BOT_USERNAME}?start=u_{user_id}"
        )

        text = (
            f"שלום {name} 👋\n\n"
            f"🆔 ה-Telegram ID שלך:\n"
            f"{user_id}\n\n"
            f"🔗 הקישור האישי שלך:\n"
            f"{personal_link}\n\n"
            f"שלח את הקישור למי שאתה רוצה."
        )

        await update.message.reply_text(
            text,
            disable_web_page_preview=True
        )

        print(
            f"START received from {name} ({user_id})",
            flush=True
        )

        return

    # --------------------------------------------------------
    # Someone opened another user's personal link
    # Example:
    # /start u_123456789
    # --------------------------------------------------------

    code = context.args[0]

    if code.startswith("u_"):

        owner_id = code[2:]

        if owner_id.isdigit():

            await update.message.reply_text(
                "✅ הקישור האישי זוהה.\n\n"
                f"🆔 ID של בעל הקישור: {owner_id}\n\n"
                "הבוט זיהה למי הקישור שייך."
            )

            print(
                f"Referral opened: owner_id={owner_id}, "
                f"visitor_id={user_id}",
                flush=True
            )

            return

    await update.message.reply_text(
        "קישור לא תקין."
    )


# ============================================================
# HEALTH
# ============================================================

async def health(request: web.Request):

    return web.Response(
        text="OK"
    )


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

async def telegram_webhook(request: web.Request):

    try:

        data = await request.json()

        update = Update.de_json(
            data,
            application.bot
        )

        await application.update_queue.put(
            update
        )

        return web.Response(
            text="OK"
        )

    except Exception as exc:

        print(
            f"Webhook error: {exc}",
            flush=True
        )

        return web.Response(
            status=400,
            text="Bad Request"
        )


# ============================================================
# MAIN
# ============================================================

async def main():

    global application
    global BOT_USERNAME

    # --------------------------------------------------------
    # Check token
    # --------------------------------------------------------

    if not BOT_TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN לא מוגדר."
        )

    # --------------------------------------------------------
    # Get Render URL
    # --------------------------------------------------------

    base_url = WEBHOOK_URL or RENDER_URL

    if not base_url:

        raise RuntimeError(
            "לא נמצאה כתובת Render. "
            "RENDER_EXTERNAL_URL לא זמין."
        )

    # --------------------------------------------------------
    # Create application
    # --------------------------------------------------------

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .updater(None)
        .build()
    )

    # --------------------------------------------------------
    # Get bot info
    # --------------------------------------------------------

    me = await application.bot.get_me()

    BOT_USERNAME = me.username or ""

    if not BOT_USERNAME:

        raise RuntimeError(
            "לא ניתן לזהות את username של הבוט."
        )

    # --------------------------------------------------------
    # Add /start handler
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # --------------------------------------------------------
    # Initialize bot
    # --------------------------------------------------------

    await application.initialize()

    await application.start()

    # --------------------------------------------------------
    # IMPORTANT:
    # Set webhook to ROOT URL
    #
    # OLD:
    # https://idnew.onrender.com/telegram
    #
    # NEW:
    # https://idnew.onrender.com
    # --------------------------------------------------------

    webhook_url = base_url

    await application.bot.set_webhook(
        url=webhook_url,
        allowed_updates=Update.ALL_TYPES
    )

    print(
        f"Bot username: @{BOT_USERNAME}",
        flush=True
    )

    print(
        f"Webhook: {webhook_url}",
        flush=True
    )

    # --------------------------------------------------------
    # Create web server
    # --------------------------------------------------------

    web_app = web.Application()

    # Health check
    web_app.router.add_get(
        "/",
        health
    )

    web_app.router.add_get(
        "/health",
        health
    )

    # Telegram webhook MUST be /
    web_app.router.add_post(
        "/",
        telegram_webhook
    )

    # --------------------------------------------------------
    # Start server
    # --------------------------------------------------------

    runner = web.AppRunner(
        web_app
    )

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    print(
        f"Service is live on port {PORT}",
        flush=True
    )

    print(
        "Waiting for Telegram updates...",
        flush=True
    )

    # --------------------------------------------------------
    # Keep process alive
    # --------------------------------------------------------

    try:

        await asyncio.Event().wait()

    finally:

        await runner.cleanup()

        await application.stop()

        await application.shutdown()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
