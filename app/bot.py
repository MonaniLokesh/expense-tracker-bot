import logging
import io
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
    user_id = update.message.from_user.id
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    response = ""

    try:

        if update.message.photo:
            print(f"--- PHOTO RECEIVED from {user_id} ---")
            file_id = update.message.photo[-1].file_id
            new_file = await context.bot.get_file(file_id)
    
            image_buffer = io.BytesIO()
            await new_file.download_to_memory(image_buffer)
            image_bytes = image_buffer.getvalue()
            
            response = await run_agent(user_id, image_data=image_bytes)

        elif update.message.text:
            user_message = update.message.text
            print(f"--- TEXT RECEIVED from {user_id}: {user_message} ---")
            response = await run_agent(user_id, message_text=user_message)

        await update.message.reply_text(str(response))

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Something went wrong processing your request.")

print("Building Bot Application...")
app = (
    ApplicationBuilder()
    .token(TELEGRAM_BOT_TOKEN)
    .read_timeout(30)
    .write_timeout(30)
    .connect_timeout(30)
    .build()
)
app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    print("Running locally...")
    app.run_polling()