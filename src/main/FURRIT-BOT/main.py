import logging
import random
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
        sticker_pack_name = 'FURRIT_PAN'
        sticker_set = await context.bot.get_sticker_set(name=sticker_pack_name)
        stickers_in_set = sticker_set.stickers
        sticker_ids = [sticker.file_id for sticker in stickers_in_set]

        random_sticker_id = random.choice(sticker_ids)

        await update.message.reply_sticker(sticker=random_sticker_id, reply_to_message_id=original_message_id)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You need to reply to a message to pan."
        )

#indexing
async def Rfine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Removing $350 from\nYou lucky bastard"
    )


#why wwont it work????
async def fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="AWOOOOOOOOOO\nfining a user"
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token('6368893309:AAFH_9TxDdRJfT7rReTWVkAjirFFdCpNSEM').build()

    start_handler = CommandHandler('start', start)
    pan_handler = CommandHandler('pan', pan)
    fine_handler = CommandHandler('fine', fines)
    remove_fine_handler = CommandHandler('un fine', Rfine)
    application.add_handler(start_handler)
    application.add_handler(pan_handler)
    application.add_handler(fine_handler)
    application.add_handler(remove_fine_handler)


    application.run_polling()
