import logging
import random
from telegram import Update, ChatMemberUpdated
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ChatMemberHandler

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

#removes a single fine from a user
# should allow the caller to specify the amt removed, also need to
#   change so that you call it using the @ of a user.
#chat_member_update: ChatMemberUpdated,
async def Rfine( update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    user_says = "".join(context.args)
    #target = chat_member_update.difference().get("status")
    if replied_message:
        original_message_id = replied_message.message_id
        await update.message.reply_text(
            text="forgiving a $350 fine from "+replied_message.from_user.username,
            reply_to_message_id=original_message_id)
    elif user_says != "":
        await context.bot.send_message(

            chat_id=update.effective_chat.id,
            text="Forgiving a $350 fine from "+user_says +
                 "\n You havent gotten this working yet\nIDK how to get the bot to check if a user is real"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No user selected"
        )


#allows the caller to fine a user for a message
async def fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    if replied_message:
        original_message_id = replied_message.message_id
        user = replied_message.from_user.username
        await update.message.reply_text(text="Fining "+user+" $350", reply_to_message_id=original_message_id)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No user selected to fine"
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You havent finished this yet"
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token('6368893309:AAFH_9TxDdRJfT7rReTWVkAjirFFdCpNSEM').build()

    #application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))

    start_handler = CommandHandler('start', start)
    pan_handler = CommandHandler('pan', pan)
    fine_handler = CommandHandler('fine', fines)
    remove_fine_handler = CommandHandler('unfine', Rfine)
    application.add_handler(start_handler)
    application.add_handler(pan_handler)
    application.add_handler(fine_handler)
    application.add_handler(remove_fine_handler)


    application.run_polling()
