import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ---------------------------
TOKEN = os.getenv("TOKEN")  # ضع توكن البوت في Variables على Railway
# ---------------------------

# التأكد من وجود ffmpeg قبل أي تحميل
if os.system("which ffmpeg") != 0:
    print("🔧 تثبيت ffmpeg تلقائيًا...")
    os.system("apt update && apt install -y ffmpeg")

# دالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 مرحبا! أرسل رابط الفيديو.")

# دالة استقبال الرابط
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "اختر الجودة أو MP3:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# دالة التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # حماية الرد على الزر من الأخطاء
    try:
        await query.answer("⏳ جاري التحميل...", show_alert=False)
    except Exception as e:
        print(f"⚠️ خطأ في الرد على الزر: {e}")

    # إزالة أزرار الرسالة بعد الضغط
    await query.edit_message_reply_markup(reply_markup=None)

    url = context.user_data.get("url")
    choice = query.data
    await query.edit_message_text("⏳ جاري التحميل...")

    # إعدادات التحميل
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
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }
    else:
        height = int(choice)
        ydl_opts = {
            'format': f'bestvideo[height<={height}]+bestaudio/best',
            'outtmpl': 'video.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # التحقق من الحجم وضغط الفيديو إذا كبير
        for file in os.listdir():
            if file.startswith("video") and os.path.getsize(file) > 50 * 1024 * 1024:
                compressed_file = f"compressed_{file}"
                os.system(f"ffmpeg -i {file} -vcodec libx264 -crf 28 -preset fast {compressed_file}")
                os.remove(file)
                file = compressed_file

            if file.startswith("video"):
                await query.message.reply_video(video=open(file, "rb"))
                os.remove(file)
                break
            elif file.startswith("audio"):
                await query.message.reply_audio(audio=open(file, "rb"))
                os.remove(file)
                break

    except Exception as e:
        await query.message.reply_text(f"❌ حدث خطأ أثناء التحميل.\n{e}")
        print(e)

# ---------------------------
# تشغيل البوت عبر Polling (أفضل على Railway)
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
