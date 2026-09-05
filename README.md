# Telegram Unique Link Bot

הבוט נותן לכל משתמש קישור Telegram ייחודי המבוסס על Telegram ID.

## מה קורה ב-/start

הבוט מציג:
- Telegram ID של המשתמש
- קישור אישי בפורמט `https://t.me/BOT_USERNAME?start=u_ID`

כאשר מישהו פותח את הקישור, הבוט מקבל את ה-ID המקודד בקישור ויכול לזהות למי הקישור שייך.

## חשוב

הקישור הייחודי פותח את הבוט, לא צ'אט ישיר עם המשתמש.

Telegram חוסמת שימוש ב-`tg://user?id=...` במקרים שבהם הגדרות הפרטיות של המשתמש לא מאפשרות זאת. אי אפשר לעקוף את ההגבלה באמצעות הבוט.

## Render

Service type:
Web Service

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
TELEGRAM_BOT_TOKEN=YOUR_NEW_BOT_TOKEN
BOT_USERNAME=YOUR_BOT_USERNAME
```

למשל אם הבוט הוא `@my_example_bot`:

```text
BOT_USERNAME=my_example_bot
```

אין צורך להגדיר `PORT` או `WEBHOOK_URL`.

## בדיקה

פתח:
```text
https://YOUR-SERVICE.onrender.com/health
```

צריך לקבל:
```text
OK
```

ואז שלח `/start` לבוט.

## Security

אל תעלה Bot Token ל-GitHub.
