import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!"
    )


async def pan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message

    if replied_message:
        original_message_id = replied_message.message_id
        await update.message.reply_text(text="Panned", reply_to_message_id=original_message_id)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You can't pan yourself!"
        )


if __name__ == '__main__':
    application = ApplicationBuilder().token('6368893309:AAFH_9TxDdRJfT7rReTWVkAjirFFdCpNSEM').build()

    start_handler = CommandHandler('start', start)
    pan_handler = CommandHandler('pan', pan)
    application.add_handler(start_handler)
    application.add_handler(pan_handler)


    application.run_polling()
