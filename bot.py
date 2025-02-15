import os
import re
import uuid
import yt_dlp
import ffmpeg
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# جلب بيانات البوت من متغيرات البيئة
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEVELOPER_NAME = "\U0001F451 المطور: @Hfddhht"

# تخزين بيانات المستخدم
chat_data = {}

# تشغيل البوت
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# رسالة الترحيب مع الأزرار
@bot.on_message(filters.command("start"))
def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F4F7 صور", callback_data="image"),
         InlineKeyboardButton("\U0001F3B5 أغاني", callback_data="music")],
        [InlineKeyboardButton("\U0001F4C4 ملفات", callback_data="file"),
         InlineKeyboardButton("\U0001F4F2 تيك توك", callback_data="tiktok")],
        [InlineKeyboardButton("\U0001F4FB فيسبوك", callback_data="facebook"),
         InlineKeyboardButton("\U0001F426 تويتر", callback_data="twitter")],
        [InlineKeyboardButton("\U0001F4FC فيميو", callback_data="vimeo"),
         InlineKeyboardButton("\U0001F4E2 ريديت", callback_data="reddit")],
        [InlineKeyboardButton("\U0001F39E ديلي موشن", callback_data="dailymotion"),
         InlineKeyboardButton("\U0001F4F9 انستغرام", callback_data="instagram")]
    ])

    message.reply_text(
        f"\U0001F44B أهلا بك {message.from_user.first_name}!\n\n"
        "أنا بوت تحميل متعدد الوسائط \U0001F3AC.\n"
        "اختر نوع التحميل الذي تريده ⬇️",
        reply_markup=keyboard
    )

# استقبال اختيار المستخدم
@bot.on_callback_query(filters.regex("^(image|music|file|tiktok|facebook|twitter|vimeo|reddit|dailymotion|instagram)$"))
def query_handler(client, query):
    category = query.data
    chat_data[query.message.chat.id] = {"category": category, "url": None}
    query.message.reply_text(f"✅ اخترت {category.capitalize()}، أرسل الرابط الآن!")

# استقبال الرابط وفحصه
@bot.on_message(filters.text & filters.private)
def receive_link(client, message):
    chat_id = message.chat.id
    user_data = chat_data.get(chat_id)
    if not user_data:
        message.reply_text("⚠️ يرجى اختيار نوع التحميل أولاً من القائمة.")
        return

    url = message.text.strip()
    if not re.match(r'https?://', url):
        message.reply_text("❌ الرابط غير صالح، يرجى إدخال رابط صحيح!")
        return

    request_id = str(uuid.uuid4())[:8]
    chat_data[chat_id]["url"] = url
    chat_data[chat_id]["request_id"] = request_id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 HD", callback_data=f"hd|{chat_id}|{request_id}"),
         InlineKeyboardButton("📹 SD", callback_data=f"sd|{chat_id}|{request_id}")],
        [InlineKeyboardButton("🎵 صوت فقط", callback_data=f"audio|{chat_id}|{request_id}")]
    ])

    message.reply_text("🎥 اختر الجودة التي تريد تحميلها:", reply_markup=keyboard)

# تحميل المحتوى مع نسبة التحميل
@bot.on_callback_query(filters.regex("^(hd|sd|audio)\\|\\d+\\|[a-zA-Z0-9]+$"))
def download_content(client, query):
    quality, chat_id, request_id = query.data.split("|")
    chat_id = int(chat_id)
    user_data = chat_data.get(chat_id, {})
    url = user_data.get("url")

    if not url:
        query.message.reply_text("❌ حدث خطأ، لم يتم العثور على الرابط.")
        return

    query.message.reply_text("🔄 جارٍ تنزيل الملف، يرجى الانتظار...")
    output_file = f"media_{request_id}.mp4"
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d['_percent_str'].strip()
            query.message.reply_text(f"📊 تقدم التحميل: {percent}")

    ydl_opts = {
        "format": "bestvideo+bestaudio/best" if quality != "audio" else "bestaudio",
        "outtmpl": output_file,
        "quiet": False,
        "progress_hooks": [progress_hook]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if quality == "audio":
            audio_file = f"audio_{request_id}.mp3"
            convert_audio(output_file, audio_file)
            query.message.reply_audio(audio_file, caption=f"🎵 الصوت فقط 🎧\n\n{DEVELOPER_NAME}")
            os.remove(audio_file)
        else:
            query.message.reply_video(output_file, caption=f"🎬 الفيديو جاهز ✅\n\n{DEVELOPER_NAME}")

        os.remove(output_file)
    except Exception as e:
        query.message.reply_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}")

# تحويل الصوت
def convert_audio(input_file, output_file):
    try:
        ffmpeg.input(input_file).output(output_file, format='mp3', acodec='libmp3lame', audio_bitrate='192k').run(overwrite_output=True)
    except Exception as e:
        print(f"❌ خطأ أثناء تحويل الصوت: {e}")

# تشغيل البوت
bot.run()
