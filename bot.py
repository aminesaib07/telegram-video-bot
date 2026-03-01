import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ---------------------------
TOKEN = os.getenv("TOKEN")  # ضع توكن البوت هنا كمتغير بيئة
OWNER_ID = 7075889236        # ضع رقمك في Telegram
# ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("👋 أرسل رابط الفيديو")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    context.user_data["url"] = update.message.text

    keyboard = [
        [InlineKeyboardButton("360p", callback_data="360")],
        [InlineKeyboardButton("720p", callback_data="720")],
        [InlineKeyboardButton("1080p", callback_data="1080")],
        [InlineKeyboardButton("1440p", callback_data="1440")],
        [InlineKeyboardButton("2160p", callback_data="2160")],
        [InlineKeyboardButton("أفضل جودة 🔝", callback_data="best")],
        [InlineKeyboardButton("MP3 🎵", callback_data="mp3")]
    ]

    await update.message.reply_text(
        "اختر الجودة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ جاري التحميل...", show_alert=False)
    await query.edit_message_reply_markup(reply_markup=None)

    if query.from_user.id != OWNER_ID:
        return

    url = context.user_data.get("url")
    choice = query.data
    await query.edit_message_text("⏳ جاري التحميل...")

    if choice == "mp3":
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif choice == "best":
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'video.%(ext)s',
        }
    else:
        height = int(choice)
        ydl_opts = {
            'format': f'bestvideo[height<={height}]+bestaudio/best',
            'outtmpl': 'video.%(ext)s',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for file in os.listdir():
            if file.startswith("video"):
                await query.message.reply_video(video=open(file, "rb"))
                os.remove(file)
                break
            elif file.startswith("audio"):
                await query.message.reply_audio(audio=open(file, "rb"))
                os.remove(file)
                break

    except Exception as e:
        await query.message.reply_text("❌ حدث خطأ أثناء التحميل")
        print(e)

# ---------------------------
PORT = int(os.environ.get("PORT", 8000))
RAILWAY_URL = os.environ.get("RAILWAY_STATIC_URL")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

# تشغيل Webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=RAILWAY_URL
)
