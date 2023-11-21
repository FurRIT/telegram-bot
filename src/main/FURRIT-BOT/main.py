import logging
import random
import re
import os
import sys
from pathlib import Path

import telegram
from telegram import Update, ChatMemberUpdated
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, MessageHandler, filters, \
    ChatMemberHandler
from db.users import add_current_members, get_members, rebuild_tables, add_fine, remove_fine


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
        await auto_awoo(update, context)
        add_current_members(username, user_id)
    except Exception as e:
        logging.error(e)


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


async def auto_awoo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text0 = update.message.text
    logging.info(text0)
    t = re.findall(r"[@+A+a]+[w+W]+[o+0+O]+[o+0+O]+",text0)
    logging.info(t)
    members = get_members()
    if t:
        for x in members:
            print(update.message.from_user.id)
            print(x[0])
            if int(update.message.from_user.id) == int(x[0]):
                add_fine(x[0])
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Don't Awoo! - $350 fine!\n\n{}'s current fines ${}".format(update.message.from_user.first_name,
                                                                                    x[2] + 350)
                )


# removes a single fine from a user
# should allow the caller to specify the amt removed, also need to
#   change so that you call it using the @ of a user.
# chat_member_update: ChatMemberUpdated,
async def Rfine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if a message was replied to
    replied_message = update.message.reply_to_message
    if replied_message:
        id = replied_message.from_user.id
        remove_fine(350, id)
        await update.message.reply_text(
            text="forgiving a $350 fine from " + replied_message.from_user.username,
            reply_to_message_id=replied_message.message_id)




    # if no message was replied to
    message = update.message.text
    user = ""
    index = 8
    go = 0
    print(message[8])
    while index < len(message):
        print(index)
        if message[index] == '@':
            print("found the @")
            go = 1
        elif go == 1:
            if message[index] != " ":
                user += message[index]
            else:
                break
        index += 1
    #update.message.chat.username
    chat = update.message.chat
    if user in chat.active_usernames:

        print("USER IS IN CHAT")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=chat.active_usernames)




    user_says = "".join(context.args)
    # target = chat_member_update.difference().get("status")
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    chat = await context.bot.get_chat(update.effective_chat.id)
    print(chat.username)
    name = '@' + admins[1].user.username
    members = get_members()
    if replied_message:
        for x in members:
            if int(update.message.from_user.id) == int(x[0]):
                x[2] -= 350
        original_message_id = replied_message.message_id
        await update.message.reply_text(
            text="forgiving a $350 fine from " + replied_message.from_user.username,
            reply_to_message_id=original_message_id)
    elif user_says == name:
        await context.bot.send_message(

            chat_id=update.effective_chat.id,
            text="Forgiving a $350 fine from " + user_says +
                 "\n You havent gotten this working yet\nIDK how to get the bot to check if a user is real"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No user selected"
        )

#TODO
# allows the caller to fine a user for a message
async def fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    if replied_message:
        original_message_id = replied_message.message_id
        user = replied_message.from_user.username
        await update.message.reply_text(text="Fining " + user + " $350", reply_to_message_id=original_message_id)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No user selected to fine"
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You havent finished this yet"
    )


async def get_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_members()[1][2]
    )


if __name__ == '__main__':
    application = ApplicationBuilder().token('6569990634:AAEJ2MLYy-ByCOjHbqzzfFyIbUvqi5zDUcU').build()

    # application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))

    pan_handler = CommandHandler('pan', pan)
    fine_handler = CommandHandler('fine', fines)
    remove_fine_handler = CommandHandler('unfine', Rfine)
    get_handler = CommandHandler('get', get_all_members)
    members_handler = MessageHandler(filters.CHAT, handle_messages)

    application.add_handler(pan_handler)
    application.add_handler(fine_handler)
    application.add_handler(remove_fine_handler)
    application.add_handler(get_handler)
    application.add_handler(members_handler)

    application.run_polling()
