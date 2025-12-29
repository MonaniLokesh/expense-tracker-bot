from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from app.expense_parser import parse_expense
from app.queries import insert_expense, get_total, date_range
from app.config import TELEGRAM_BOT_TOKEN


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.message.from_user.id

    try:
        if any(x in text for x in ["spent", "paid", "bought"]):
            expense = parse_expense(text)
            insert_expense(user_id, expense)

            await update.message.reply_text(
                f"✅ Recorded ₹{expense['amount']} for {expense['category']}"
            )

        elif any(x in text for x in ["yesterday", "last week", "last month"]):
            for period in ["yesterday", "last week", "last month"]:
                if period in text:
                    start, end = date_range(period)
                    total = get_total(user_id, start, end)

                    await update.message.reply_text(
                        f"💰 Total expense for {period}: ₹{total}"
                    )
                    break
        else:
            await update.message.reply_text(
                "Try:\n• I spent 300 for coffee\n• Total expense last week"
            )

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("❌ Failed to record expense")



if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
