import os
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("8219008753:AAGHfE6fLAeo0vzX44ANUG8hCyAa-MyGZHA")
OWNER_ID = 7285840925  # ✅ Your Owner ID

FORCE_CHANNELS = [
    "CrazyTechOp",
    "CrazyTechOpChat"
]

DATA_FILE = "data.json"


# ---------------- DATA ---------------- #

def load_data():
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


def join_buttons():
    buttons = []

    for channel in FORCE_CHANNELS:
        buttons.append(
            [InlineKeyboardButton(
                f"🔐 Join {channel}",
                url=f"https://t.me/{channel}"
            )]
        )

    buttons.append(
        [InlineKeyboardButton("🔄 Try Again", callback_data="check_join")]
    )

    return InlineKeyboardMarkup(buttons)


# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()

    if user_id in data["banned"]:
        await update.message.reply_text("🚫 You are banned.")
        return

    if not await check_join(user_id, context):
        text = (
            "🔒 *Access Restricted*\n\n"
            "Join channels to use bot:\n\n"
            "🔐 CrazyTechOp\n"
            "🔐 CrazyTechOpChat\n\n"
            "_After joining click Try Again._"
        )

        await update.message.reply_text(
            text,
            reply_markup=join_buttons(),
            parse_mode="Markdown"
        )
        return

    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

    await update.message.reply_text("👋 Welcome! Send file 📁")


# ---------------- TRY AGAIN ---------------- #

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if await check_join(user_id, context):
        await query.edit_message_text("✅ Access Verified! Send file 📁")
    else:
        await query.answer("❌ Still not joined!", show_alert=True)


# ---------------- FILE HANDLER ---------------- #

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()

    if user_id in data["banned"]:
        return

    if not await check_join(user_id, context):
        await update.message.reply_text(
            "🔒 Join required!",
            reply_markup=join_buttons()
        )
        return

    data["total_files"] += 1
    save_data(data)

    await update.message.reply_text("✅ File received successfully!")


# ---------------- ADMIN COMMANDS ---------------- #

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    data = load_data()

    await update.message.reply_text(
        f"📊 Bot Stats\n\n"
        f"👥 Users: {len(data['users'])}\n"
        f"🚫 Banned: {len(data['banned'])}\n"
        f"📁 Files: {data['total_files']}"
    )


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban user_id")
        return

    user_id = int(context.args[0])
    data = load_data()

    if user_id not in data["banned"]:
        data["banned"].append(user_id)
        save_data(data)

    await update.message.reply_text(f"🚫 {user_id} banned.")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /unban user_id")
        return

    user_id = int(context.args[0])
    data = load_data()

    if user_id in data["banned"]:
        data["banned"].remove(user_id)
        save_data(data)

    await update.message.reply_text(f"✅ {user_id} unbanned.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast message")
        return

    message = " ".join(context.args)
    data = load_data()

    success = 0
    for user in data["users"]:
        try:
            await context.bot.send_message(user, message)
            success += 1
        except:
            pass

    await update.message.reply_text(f"📢 Broadcast sent to {success} users.")


# ---------------- APP ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("broadcast", broadcast))

app.run_polling()
