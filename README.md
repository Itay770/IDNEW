# Telegram ID Link Bot

כל משתמש שלוחץ `/start` מקבל כפתור לפתיחת שיחה איתו לפי Telegram ID.

## Render

סוג שירות: Web Service

Build Command:
```bash
pip install -r requirements.txt
```

Start Command:
```bash
python bot.py
```

Environment Variables:
```text
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
```

אין צורך להגדיר `WEBHOOK_URL` ב-Render. הקוד משתמש אוטומטית ב-`RENDER_EXTERNAL_URL`.

## איך זה עובד

משתמש שולח `/start`, והבוט מזהה את ה-Telegram ID שלו ומציג כפתור לפתיחת שיחה.

## בדיקה

פתח:
```text
https://YOUR-SERVICE.onrender.com/health
```

צריך לקבל `OK`.

אל תעלה את Bot Token ל-GitHub.
