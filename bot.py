import os
import re
import uuid
import yt_dlp
import ffmpeg
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# جلب بيانات البوت من متغيرات البيئة
API_ID = int(os.getenv("API_ID"))  # متغير بيئة API_ID
API_HASH = os.getenv("API_HASH")   # متغير بيئة API_HASH
BOT_TOKEN = os.getenv("BOT_TOKEN") # متغير بيئة BOT_TOKEN
DEVELOPER_NAME = "\U0001F451 المطور: @Hfddhht"  # اسم المطور أو حسابه

# تخزين بيانات المستخدم
chat_data = {}

# تشغيل البوت
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# رسالة الترحيب مع الأزرار
@bot.on_message(filters.command("start"))
def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F4F9 YouTube", callback_data="youtube"),
         InlineKeyboardButton("\U0001F4F7 Instagram", callback_data="instagram")],
        [InlineKeyboardButton("\U0001F3A5 TikTok", callback_data="tiktok"),
         InlineKeyboardButton("\U0001F4FB Facebook", callback_data="facebook")],
        [InlineKeyboardButton("\U0001F426 Twitter", callback_data="twitter"),
         InlineKeyboardButton("\U0001F4FC Vimeo", callback_data="vimeo")],
        [InlineKeyboardButton("\U0001F39E️ Dailymotion", callback_data="dailymotion"),
         InlineKeyboardButton("\U0001F4E2 Reddit", callback_data="reddit")]
    ])

    message.reply_text(
        f"\U0001F44B أهلا بك {message.from_user.first_name}!\n\n"
        "أنا بوت تحميل الفيديوهات بدون علامة مائية \U0001F3AC.\n"
        "اختر المنصة التي تريد التحميل منها ⬇️",
        reply_markup=keyboard
    )

# استقبال اختيار الموقع
@bot.on_callback_query(filters.regex("^(youtube|instagram|tiktok|facebook|twitter|vimeo|dailymotion|reddit)$"))
def query_handler(client, query):
    site = query.data
    chat_data[query.message.chat.id] = {"site": site, "url": None}
    query.message.reply_text(f"✅ اخترت {site.capitalize()}، أرسل رابط الفيديو الآن!")

# استقبال الرابط وفحصه
@bot.on_message(filters.text & filters.private)
def receive_link(client, message):
    chat_id = message.chat.id
    user_data = chat_data.get(chat_id)

    if not user_data or user_data["site"] is None:
        message.reply_text("⚠️ يرجى اختيار الموقع أولاً من القائمة.")
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

# تحميل الفيديو
@bot.on_callback_query(filters.regex("^(hd|sd|audio)\|\d+\|[a-zA-Z0-9]+$"))
def download_video(client, query):
    quality, chat_id, request_id = query.data.split("|")
    chat_id = int(chat_id)
    user_data = chat_data.get(chat_id, {})
    url = user_data.get("url")

    if not url or user_data.get("request_id") != request_id:
        query.message.reply_text("❌ حدث خطأ، لم يتم العثور على الرابط.")
        return

    query.message.reply_text("🔄 جارٍ تنزيل الفيديو، يرجى الانتظار...")

    output_file = f"video_{request_id}.mp4"
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": output_file,
        "quiet": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            query.message.reply_text("❌ فشل تحميل الفيديو، يرجى المحاولة مرة أخرى.")
            return

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
        ffmpeg.input(input_file).output(output_file, acodec='libmp3lame').run(overwrite_output=True)
    except Exception as e:
        print(f"❌ خطأ أثناء تحويل الصوت: {e}")

# تشغيل البوت
bot.run()
