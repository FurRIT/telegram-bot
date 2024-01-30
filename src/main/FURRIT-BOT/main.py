import logging
import random
import re

import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, MessageHandler, filters
from db.users import add_current_members, get_members, add_pan_count, add_quote_db, get_quotes, add_fine, remove_fine, \
    get_member_by_user
from datetime import datetime, timedelta, time  # imported for /ban method

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

cooldown_dict = {}
frequency_dict = {
    "vore": 3
}
times_called_dict = {
    "vore": 0
}
users = {
    "vore": ["274315974", "222995514"]
}

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    user_id = user.id
    username = user.username

    try:
        await auto_awoo(update, context)
        await summons(update, context)
        add_current_members(username, user_id)
    except Exception as e:
        logging.error(e)


async def piss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    if replied_message:
        original_message_id = replied_message.message_id
        await update.message.reply_text(
            text="Pissed pants " + replied_message.from_user.username,
            reply_to_message_id=original_message_id)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="piss"
        )


async def summons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    v = re.findall(r'\b[vV]+[0oO]+[rR]+[eE3]+\b', message_text)
    p = re.findall(r'\b[pP]+[hH]+[Yy]+[sS]+[IiLl]+[cCkK]+[sS]\b', message_text)

    if v:
        summon_type = "vore"
        times_called_dict[summon_type] = times_called_dict[summon_type] + 1

        # Check if a cooldown is active for this type of summon
        if summon_type in cooldown_dict:
            current_time = datetime.now()
            cooldown_end_time = cooldown_dict[summon_type]

            if current_time < cooldown_end_time:
                return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"@{context.bot.get_user(users[summon_type][0])} will be summoned for {summon_type}."
        )

        # Set cooldown for 15 minutes
        cooldown_dict[summon_type] = datetime.now() + timedelta(minutes=15)

        return

    if p:
        summon_type = "physics"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"@MrHypercube will be summoned for {summon_type}."
        )
        return


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


'''
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message

    if replied_message:
        if replied_message.from_user == update.message.from_user:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You can't ban yourself.")
            return
        # TODO: or if replying user is not an admin then message : "not allowed to ban"
        # elif Telegram.ChatMember.status(bot.get_chat_member(chat_id, user_id)) != 'Administrator':
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Unauthorized to ban.")
            return
        else:
            #actual banning of the user
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id, # chat
                user_id=replied_message.from_user.id, # origional message
                until_date=(datetime.now() + timedelta(minutes = 5)), # need to decide how long to ban for
                revoke_messages=False) # need to decide if messages they send will be visible
            return
'''


# reads through all messages sent and looks for awoo to fine the person
# also currently houses the @admin function
async def auto_awoo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text0 = update.message.text
    logging.info(text0)
    t = re.findall(r"[@+A+a]+[w+W]+[o+0+O]+[o+0+O]+", text0)
    call = re.findall("@admin", text0)
    logging.info(t)  # idk wtf this does but it doesnt work without it
    members = get_members()
    if t:
        for x in members:
            if int(update.message.from_user.id) == int(x[0]):
                add_fine(x[0])
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Don't Awoo! - $350 fine!\n\n{}'s current fines ${}".format(
                        update.message.from_user.first_name,
                        x[2] + 350)
                )
    if call:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="test")
        # forwad message to admin chat
        # forward the message that had @admin
        # send a message saying the user that requested the @admin

        replied_message = update.message.reply_to_message

        context.bot.forward_message(
            chat_id=update.effective_message.chat_id,
            from_chat_id=update.effective_message.chat_id,
            message_id=replied_message.message_id, )


# removes a single fine from a user
# should allow the caller to specify the amt removed, also need to
#   change so that you call it using the @ of a user.
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
        if message[index] == '@':
            go = 1
        elif go == 1:
            if message[index] != " ":
                user += message[index]
            else:
                break
        index += 1
    members = get_members()
    for x in members:
        if str(user) == str(x[1]):  # if the user is in the chat
            remove_fine(350, x[0])
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="forgiving a $350 fine from {}\n\n{}'s current fines ${}".format(user, user, x[2] - 350))


# allows the caller to fine a user for a message
async def fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    if replied_message:
        original_message_id = replied_message.message_id
        user = replied_message.from_user.username

        members = get_members()
        for x in members:
            if int(update.message.from_user.id) == int(x[0]):
                add_fine(x[0])

        await update.message.reply_text(
            text="Fining " + user + " $350\n\n{}'s current fines ${}".format(update.message.from_user.first_name,
                                                                             x[2] + 350),
            reply_to_message_id=original_message_id)

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No user selected to fine"
        )


# used to grab a list of all members
# CADEN DO NOT DELETE
# IT IS USED BY MOST OF THE FUNCTIONS
async def get_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_members()[1][2]
    )


async def get_all_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_quotes()
    )


async def add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    # Need to create a base case for quotes that are too long
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

    # application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))

    pan_handler = CommandHandler('pan', pan)
    fine_handler = CommandHandler('fine', fines)
    remove_fine_handler = CommandHandler('unfine', Rfine)
    get_handler = CommandHandler('get', get_all_members)
    get_quote_handler = CommandHandler('get_quotes', get_all_quotes)
    add_quote_handler = CommandHandler('add_quote', add_quote)
    members_handler = MessageHandler(filters.CHAT, handle_messages)

    application.add_handler(pan_handler)
    application.add_handler(fine_handler)
    application.add_handler(remove_fine_handler)
    application.add_handler(get_handler)
    application.add_handler(get_quote_handler)
    application.add_handler(add_quote_handler)
    application.add_handler(members_handler)

    application.run_polling()
