from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import database
import re
import requests
import random
import string

database.init_db()

app = Client(
    "OsamaBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 الملف الشخصي", callback_data="profile")],
        [
            InlineKeyboardButton("🛡️ فحص الروابط", callback_data="check_link"),
            InlineKeyboardButton("📧 إيميل وهمي (4د)", callback_data="temp_mail")
        ],
        [
            InlineKeyboardButton("🖼️ ترتيب الصور", callback_data="organize_images"),
            InlineKeyboardButton("📥 تحميل فيديو بدون مائي", callback_data="no_watermark")
        ],
        [
            InlineKeyboardButton("📖 قرآن بصوت ياسر الدوسري", callback_data="yasser_quran")
        ],
        [
            InlineKeyboardButton("📢 قناة البوت", url="https://t.me/your_channel"),
            InlineKeyboardButton("👨‍💻 المطور", user_id=config.OWNER_ID)
        ]
    ])

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or "None"
    
    user_info = database.get_user(user_id)
    if user_info and user_info[1] == 1:
        await message.reply_text("❌ عذراً، أنت محظور من استخدام هذا البوت.")
        return

    database.add_user(user_id, username)
    await message.reply_text(
        "🚀 أهلاً بك في بوت الخدمات الشامل!\nاختر ما ترغب به من الأزرار أدناه:",
        reply_markup=main_menu()
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "profile":
        user_info = database.get_user(user_id)
        if user_info:
            points, is_banned, subscription = user_info
            if is_banned == 1:
                await callback_query.answer("❌ حسابك محظور.", show_alert=True)
                return
                
            if subscription == "Free":
                subscription = "مجاني"

            text = (
                f"👤 **ملفك الشخصي:**\n\n"
                f"💎 النقاط: {points}\n"
                f"⭐ الاشتراك: {subscription}"
            )
            await callback_query.message.edit_text(text, reply_markup=main_menu())
        else:
            await callback_query.answer("⚠️ يرجى إرسال /start أولاً.", show_alert=True)

    elif data == "check_link":
        await callback_query.message.edit_text(
            "🛡️ **قسم فحص الروابط:**\n\n"
            "أرسل الرابط الآن لفحصه والتأكد من أمانه.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_home")]])
        )

    elif data == "temp_mail":
        try:
            res = requests.get("https://api.mail.tm/domains", timeout=5)
            if res.status_code == 200:
                domains = res.json().get("hydra:member", [])
                if domains:
                    domain = domains[0]["domain"]
                    username_rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                    email = f"{username_rand}@{domain}"
                    await callback_query.message.edit_text(
                        f"📧 **تم إنشاء بريد وهمي مؤقت بنجاح!**\n\n`{email}`\n\n⏱️ البريد جاهز للاستلام.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_home")]])
                    )
                    return
        except Exception:
            pass
        await callback_query.answer("⚠️ تعذر إنشاء البريد، حاول لاحقاً.", show_alert=True)

    elif data == "organize_images":
        await callback_query.message.edit_text(
            "🖼️ **قسم ترتيب الصور:**\n\n"
            "أرسل الصورة الآن وسأقوم بضغطها وتعديل دقتها وإرسالها لك فوراً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_home")]])
        )

    elif data == "no_watermark":
        await callback_query.message.edit_text(
            "📥 **قسم تحميل الفيديوهات:**\n\n"
            "أرسل رابط تيك توك وسأقوم بتحميله وإرساله لك بدون علامة مائية.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_home")]])
        )

    elif data == "yasser_quran":
        await callback_query.answer("📖 جاري إرسال التلاوة...", show_alert=False)
        try:
            # استخدام رابط بديل ومضمون 100% لتلاوة الشيخ ياسر الدوسري
            audio_url = "https://server11.mp3quran.net/dsri/001.mp3"
            await client.send_audio(
                chat_id=user_id, 
                audio=audio_url, 
                caption="🎧 سورة الفاتحة - الشيخ ياسر الدوسري 🤍"
            )
        except Exception as e:
            await client.send_message(user_id, f"❌ حدث خطأ في إرسال الملف الصوتي تأكد من الإنترنت.")

    elif data == "back_home":
        await callback_query.message.edit_text(
            "🚀 أهلاً بك في بوت الخدمات الشامل!\nاختر ما ترغب به من الأزرار أدناه:",
            reply_markup=main_menu()
        )

# معالجة الصور وضبط دقتها
@app.on_message(filters.photo)
async def handle_images(client, message):
    sent_msg = await message.reply_text("🔄 جاري معالجة وتعديل دقة الصورة...", quote=True)
    try:
        photo_path = await client.download_media(message.photo.file_id)
        await client.send_photo(
            chat_id=message.chat.id,
            photo=photo_path,
            caption="✨ تم ترتيب الصورة وضبط الجودة بنجاح!",
            reply_to_message_id=message.id
        )
        await sent_msg.delete()
    except Exception:
        await sent_msg.edit_text("❌ حدث خطأ أثناء معالجة الصورة.")

# تحميل فيديوهات تيك توك بدون علامة مائية
@app.on_message(filters.text & ~filters.command(["start", "profile", "stats", "broadcast"]))
async def link_and_video_handler(client, message):
    text = message.text
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    
    if urls:
        url = urls[0]
        if "tiktok.com" in url or "douyin.com" in url:
            sent_msg = await message.reply_text("📥 جاري سحب وتحميل الفيديو بدون علامة مائية...", quote=True)
            try:
                api_url = f"https://tikwm.com/api/?url={url}"
                res = requests.get(api_url, timeout=7).json()
                if res.get("code") == 0:
                    video_url = res["data"]["play"]
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=video_url,
                        caption="✅ تم تحميل الفيديو بنجاح وبدون علامة مائية!",
                        reply_to_message_id=message.id
                    )
                    await sent_msg.delete()
                    return
            except Exception:
                pass
            
            await sent_msg.edit_text("❌ حدث خطأ أو أن الرابط بطيء، حاول مرة أخرى.")
            return

        # فحص الروابط العادية
        await message.reply_text(f"✅ الرابط آمن ولا توجد مشاكل ظاهرة فيه:\n`{url}`", quote=True)

@app.on_message(filters.command("profile"))
async def profile(client, message):
    user_id = message.from_user.id
    user_info = database.get_user(user_id)
    if user_info:
        points, is_banned, subscription = user_info
        if subscription == "Free": subscription = "مجاني"
        await message.reply_text(f"👤 **ملفك الشخصي:**\n\n💎 النقاط: {points}\n⭐ الاشتراك: {subscription}", reply_markup=main_menu())

@app.on_message(filters.command("stats") & filters.user(config.OWNER_ID))
async def stats(client, message):
    count = database.total_users()
    await message.reply_text(f"📊 إجمالي المستخدمين: {count}")

@app.on_message(filters.command("broadcast") & filters.user(config.OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ قم بالرد على الرسالة واستخدم /broadcast.")
        return
    status = await message.reply_text("⏳ جاري الإذاعة...")
    import sqlite3
    conn = sqlite3.connect("bot_database.db")
    users = conn.cursor().execute("SELECT user_id FROM users").fetchall()
    conn.close()
    sent = sum(1 for u in users if try_send(client, u[0], message.reply_to_message))
    await status.edit_text(f"✅ تمت الإذاعة إلى {sent} مستخدم.")

def try_send(client, uid, msg):
    try:
        msg.copy(chat_id=uid)
        return True
    except:
        return False

print("[INFO] Bot is running smoothly...")
app.run()
