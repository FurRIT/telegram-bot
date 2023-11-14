import logging
import random
import os
import sys
from pathlib import Path

import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, MessageHandler, filters
from db.users import add_current_members, get_members, rebuild_tables, add_pan_count, add_quote_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    user_id = user.id
    username = user.username

    try:
        add_current_members(username, user_id)
    except Exception as e:
        logging.error(e)


async def pan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message

    if replied_message:
        if replied_message.from_user == update.message.from_user:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You can't pan yourself."
            )
            return
        if replied_message.from_user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You can't pan the bot."
            )
            return
        else:
            original_message_id = replied_message.message_id
            sticker_pack_name = 'FURRIT_PAN'
            sticker_set = await context.bot.get_sticker_set(name=sticker_pack_name)
            stickers_in_set = sticker_set.stickers
            sticker_ids = [sticker.file_id for sticker in stickers_in_set]
            random_sticker_id = random.choice(sticker_ids)
            add_pan_count(replied_message.from_user.id)
            await update.message.reply_sticker(sticker=random_sticker_id, reply_to_message_id=original_message_id)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You need to reply to a message to pan."
        )


async def get_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_members()
    )


async def add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    logging.info(replied_message)

    try:
        if replied_message:
            if replied_message.from_user == update.message.from_user:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You can't quote yourself."
                )
                return

            if replied_message.from_user.id == context.bot.id:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You can't quote the bot."
                )
                return

            else:
                quote_user_id = replied_message.from_user.id
                quote_contents = replied_message.text
                logging.info(quote_contents)
                sender_user_id = update.message.from_user.id
                value = add_quote_db(sender_user_id, quote_user_id, quote_contents)
                if value == 1:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Quote added."
                    )
                if value == 0:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="You can't quote this twice!"
                    )
    except Exception as e:
        logging.info(e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Failed. {e}"
        )


if __name__ == '__main__':
    application = ApplicationBuilder().token('6569990634:AAEJ2MLYy-ByCOjHbqzzfFyIbUvqi5zDUcU').build()
    pan_handler = CommandHandler('pan', pan)
    get_handler = CommandHandler('get', get_all_members)
    add_quote_handler = CommandHandler('add_quote', add_quote)
    members_handler = MessageHandler(filters.CHAT, handle_messages)

    application.add_handler(pan_handler)
    application.add_handler(get_handler)
    application.add_handler(add_quote_handler)
    application.add_handler(members_handler)

    application.run_polling()
