import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from app.config import TELEGRAM_BOT_TOKEN
from app.agent_runner import run_agent

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    print(f"User {user_id} says: {user_message}")

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    except Exception:
        pass

    try:
        response = await run_agent(user_id, user_message)
        await update.message.reply_text(str(response))
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Something went wrong.")

if __name__ == "__main__":
    print("Bot is starting...")
    
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .read_timeout(30) 
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()