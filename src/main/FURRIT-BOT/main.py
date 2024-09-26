import logging
import random
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, MessageHandler, filters
from db.users import add_current_members, get_members, add_pan_count, add_quote_db, get_quotes, add_fine, remove_fine, rebuild_tables, add_fines
from datetime import datetime, timedelta  # imported for /ban method


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    If a new user speaks in chat, they are added to the database.
    Waits for 'awoo' to be sent in the chat.
    :param update:
    :param context:
    :return:
    """
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
    """
    Pan awaits a trigger for its command.  It checks the replied message.
    If a user replies to themself, they are not allowed to pan themself.
    If a user replies to the bot, they are not allowed to pan the bot.
    If there is no replied message, the bot warns the user that there must be a replied message.

    If the replied message check is successful, then it grabs the FURRIT_PAN sticker pack and
    sends a random sticker from that set in reply to the message replied to by the user.

    author: Caden
    :param update:
    :param context:
    :return:
    """
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



async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ban is currently unfinished, as far as I'm aware.
    Times out a user for 5 minutes.
    author: Theta
    :param update:
    :param context:
    :return:
    """
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
            # actual banning of the user
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,  # chat
                user_id=replied_message.from_user.id,  # origional message
                until_date=(datetime.now() + timedelta(minutes=5)),  # need to decide how long to ban for
                revoke_messages=False)  # need to decide if messages they send will be visible
            return


# reads through all messages sent and looks for awoo to fine the person
# also currently houses the @admin function
async def auto_awoo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    A service that goes through a message sent and looks for 'awoo'.
    Also apparently houses the @admin function (needs to be taken out and made into its own service)
    author: Torin
    :param update:
    :param context:
    :return:
    """
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

#                         update.message.from_user.first_name, x[4] + 350)
                    # text="This is a test function, change it back later\n x[0] = {}\nx[1]={}\nx[2] = {} (fine value)".format(x[0],x[1],x[2])
                        update.message.from_user.first_name,x[2] + 350)
                )
    if call:# if @admin was called
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="test")

        # forwad message to admin chat
        # forward the message that had @admin
        # send a message saying the user that requested the @admin

        replied_message = update.message.reply_to_message
        # chat IDs
        # -1002082274403  second test server

        CID = -1002082274403  # the current chat id in use by the bot for a destination, change as needed
        if replied_message:
            await context.bot.forward_message(
                chat_id=CID,
                from_chat_id=replied_message.chat_id,
                message_id=replied_message.message_id, )
            await context.bot.send_message(
                chat_id=CID,
                text="Attention requested in '{}' by {}".format(update.message.chat.title, update.message.from_user.first_name))
            await context.bot.forward_message(
                chat_id=CID,
                from_chat_id=replied_message.chat_id,
                message_id=update.message.message_id, )

#         context.bot.forward_message(
#             chat_id=update.effective_message.chat_id,
#             from_chat_id=update.effective_message.chat_id,
#             message_id=replied_message.message_id, )



async def Rfine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Removes a single fine from a user.  Can specify amount removed.
    author: Torin
    :param update:
    :param context:
    :return:
    """
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
                text="forgiving a $350 fine from {}\n\n{}'s current fines ${}".format(user, user, x[4] - 350))


async def add_users_fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = 0
    uid = '';
    fine = '';

    message = update.message.text
    message = message.split("\n")
    f = 0
    for command in message:
        if f == 0:
            f = 1
            continue
        input = command.split(" ")
        first = 1
        for num in input:
            if first == 1:
                uid = num
                first = 2
                continue
            if first == 2:
                fine = num
                first = 1
                add_fines(uid,fine)
                continue


    # if uid != '' and uid and fine != '' and fine:
    #     # add_fines(uid, fine)
    #     await context.bot.send_message(
    #         chat_id=update.effective_chat.id,
    #         text=f"attempted to add fines to user {uid} with amount {fine}")
    # else:
    #     await context.bot.send_message(
    #         chat_id=update.effective_chat.id,
    #         text="inadequate parameters to fine a custom amount")



async def fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to fine a user by replying to their message.
    author: Torin
    :param update:
    :param context:
    :return:
    """
    replied_message = update.message.reply_to_message
    if replied_message:
        original_message_id = replied_message.message_id
        user = replied_message.from_user.username

        members = get_members()
        for x in members:
            if int(replied_message.from_user.id) == int(x[0]):
                add_fine(x[0])
                # await context.bot.send_message(chat_id=update.effective_chat.id,text="TEST\nx[0] = {}\nx[1]={}\nx[2] = {} (fine value)".format(x[0],x[1],x[2]))
                await update.message.reply_text(text="Fining " + user + " $350\n\n{}'s current fines ${}".format(
                    replied_message.from_user.first_name,
                    x[4] + 350), reply_to_message_id=original_message_id)

#         await update.message.reply_text(
#             text="Fining " + user + " $350\n\n{}'s current fines ${}".format(update.message.from_user.first_name,
#                                                                              x[2] + 350),
#             reply_to_message_id=original_message_id)


    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No user selected to fine"
        )


# used to grab a list of all members
# CADEN DO NOT DELETE
# IT IS USED BY MOST OF THE FUNCTIONS
async def get_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    A test command (will not be deployed) that gets the list of the members in the database.
    author: Caden
    :param update:
    :param context:
    :return:
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_members()[1][2]
    )


async def get_all_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    A test command (will not be deployed) that gets the list of all the quotes in the database.
    author: Caden
    :param update:
    :param context:
    :return:
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_quotes()
    )


async def add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a message to the quotes database.
    Cannot quote yourself or the bot.
    author: Caden
    :param update:
    :param context:
    :return:
    """
    replied_message = update.message.reply_to_message
    # TODO: Need to create a base case for quotes that are too long
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
    # rebuild_tables()
    
    #I removed the token, its in our dms caden
    application = ApplicationBuilder().token('Token goes here').build()

    # application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))

    pan_handler = CommandHandler('pan', pan)
    fine_handler = CommandHandler('fine', fines)
    remove_fine_handler = CommandHandler('unfine', Rfine)
    get_handler = CommandHandler('get', get_all_members)
    add_users = CommandHandler('add', add_users_fines)
    get_quote_handler = CommandHandler('get_quotes', get_all_quotes)
    add_quote_handler = CommandHandler('add_quote', add_quote)
    members_handler = MessageHandler(filters.CHAT, handle_messages)

    application.add_handler(pan_handler)
    application.add_handler(fine_handler)
    application.add_handler(remove_fine_handler)
    application.add_handler(get_handler)
    application.add_handler(add_users)
    application.add_handler(get_quote_handler)
    application.add_handler(add_quote_handler)
    application.add_handler(members_handler)

    application.run_polling()
