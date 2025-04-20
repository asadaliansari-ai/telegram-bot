import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
import time

# --- CONFIGURATION ---
TOKEN = "8135535856:AAGbnoF4OTeO3ueGm2rf5IUO-ECKdooKQMg"  # Your bot token
OWNER_USERNAME = "7545004970"  # Your Telegram Username (fixed now)
OWNER_ID = 7545004970  # Your Telegram User ID (for future use)
PREMIUM_USERS = {}  # Dictionary of premium users {user_id: expiration_time}
PREMIUM_DURATION = 86400  # Default duration: 1 day (in seconds)
USER_WARNINGS = {}  # Dictionary of user warnings {user_id: warnings_count}

# --- BANNED HINDI WORDS (excluding 'kutte', 'kamine') ---
BANNED_WORDS = [
    "madarchod", "bhosdike", "bhenchod", "lund", "gandu", "chutiya", "chut", "bhosdi",
    "randi", "gaand", "laundiya", "mc", "bc", "chodu", "chutmar", "gaandfat",
    "suar", "haraami", "najaayaz", "jhant", "chod", "behen ke laude", "jhant", "lauda"
]

# --- LOGGER SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- MESSAGE HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message = update.message.text.lower()
    user_id = update.message.from_user.id

    # Check if the user is premium or not
    is_premium = user_id in PREMIUM_USERS and PREMIUM_USERS[user_id] > time.time()

    # Delay logic: if not premium, wait 60 seconds
    if not is_premium:
        time.sleep(60)  # Wait for 1 minute if the user is not premium

    # Check for banned words in the message
    if any(word in message for word in BANNED_WORDS):
        # Update the warning count
        if user_id not in USER_WARNINGS:
            USER_WARNINGS[user_id] = 0

        USER_WARNINGS[user_id] += 1
        warnings = USER_WARNINGS[user_id]

        if warnings <= 4:
            # If less than 4 warnings, issue a warning
            try:
                await update.message.delete()
                await update.message.reply_text(f"🚨 Warning {warnings}/4: Gali mat do bhai, sudhar jao!")
            except Exception as e:
                print(f"Error while deleting message: {e}")
        elif warnings == 5:
            # If 5th warning, mute for 20 minutes
            await update.message.delete()
            await update.message.reply_text("🚫 You have been muted for 20 minutes for using abusive language.")
            await update.message.chat.mute_member(user_id, duration=1200)  # 20 minutes
        elif warnings > 5:
            # After muting, ban the user for 1 day
            await update.message.delete()
            await update.message.reply_text("🚫 You have been banned for 1 day for repeatedly using abusive language.")
            await update.message.chat.ban_member(user_id, until_date=time.time() + 86400)  # 1 day ban

# --- OWNER CONTROLS (Premium management by Username) ---
async def set_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user is the owner based on username
    if update.message.from_user.username == OWNER_USERNAME:
        if len(context.args) == 2:
            username = context.args[0]
            premium_duration = int(context.args[1])

            # Get the user by their username
            user = await update.message.chat.get_member(username)

            if user:
                # Add user to premium list
                user_id = user.user.id
                expiration_time = time.time() + premium_duration  # Set expiration based on duration
                PREMIUM_USERS[user_id] = expiration_time
                await update.message.reply_text(f"User {username} added as premium for {premium_duration} seconds.")
            else:
                await update.message.reply_text("User not found by username.")
        else:
            await update.message.reply_text("Please provide a username and premium duration in seconds.")
    else:
        await update.message.reply_text("You are not authorized to set premium users.")

# --- MAIN RUNNER ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Add commands for the owner to manage premium users
    app.add_handler(CommandHandler("setpremium", set_premium))

    # Add message handler for all messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_polling()
