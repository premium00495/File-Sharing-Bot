import os
import json
import asyncio
import string
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")
OWNER_ID = 7285840925
STORAGE_CHANNEL = -1003832658884

FORCE_CHANNELS = ["CrazyTechOp", "CrazyTechOpChat"]

DATA_FILE = "data.json"


# ---------------- DATA ---------------- #

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "banned": [], "files": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# ---------------- FORCE JOIN ---------------- #

async def check_join(user_id, context):
    for channel in FORCE_CHANNELS:
        try:
            member = await context.bot.get_chat_member(f"@{channel}", user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()

    if user_id in data["banned"]:
        await update.message.reply_text("🚫 You are banned.")
        return

    if not await check_join(user_id, context):
        await update.message.reply_text("🔒 Join required channels first.")
        return

    if context.args:
        code = context.args[0]
        if code in data["files"]:
            msg_id = data["files"][code]
            sent = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=STORAGE_CHANNEL,
                message_id=msg_id
            )
            await asyncio.sleep(30)
            await sent.delete()
            return

    await update.message.reply_text(
        "👋 Send files and use /finish to generate link.\n\n"
        "Commands:\n"
        "/finish\n"
        "/myfiles"
    )


# ---------------- FILE RECEIVE ---------------- #

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()

    if not await check_join(user_id, context):
        await update.message.reply_text("🔒 Join required.")
        return

    forwarded = await update.message.copy(chat_id=STORAGE_CHANNEL)

    context.user_data.setdefault("queue", [])
    context.user_data["queue"].append(forwarded.message_id)

    await update.message.reply_text(
        f"✅ Added to queue. Total: {len(context.user_data['queue'])}\nSend /finish"
    )


# ---------------- FINISH ---------------- #

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()

    queue = context.user_data.get("queue", [])
    if not queue:
        await update.message.reply_text("No files in queue.")
        return

    code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    data["files"][code] = queue[0]
    save_data(data)

    context.user_data["queue"] = []

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={code}"

    await update.message.reply_text(
        f"🔗 Shareable Link:\n{link}\n\n"
        f"⚠ File auto deletes after 30 sec when opened."
    )


# ---------------- MYFILES ---------------- #

async def myfiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use your generated links to access files.")


# ---------------- APP ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("finish", finish))
app.add_handler(CommandHandler("myfiles", myfiles))
app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))

app.run_polling()
