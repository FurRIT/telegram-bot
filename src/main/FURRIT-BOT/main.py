import logging
import random
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from db.users import add_current_members, get_members, add_fine, remove_fine, rebuild_tables, add_fines

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


#reads through all messages sent and looks for awoo to fine the person
# also currently houses the @admin function
async def auto_awoo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text0 = update.message.text
    logging.info(text0)
    t = re.findall(r"[@+A+a]+[w+W]+[o+0+O]+[o+0+O]+",text0)
    call = re.findall("@admin",text0)
    logging.info(t) #idk wtf this does but it doesnt work without it
    members = get_members()
    if t:
        for x in members:
            if int(update.message.from_user.id) == int(x[0]):
                add_fine(x[0])
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Don't Awoo! - $350 fine!\n\n{}'s current fines ${}".format(update.message.from_user.first_name,x[4] + 350)
                    #text="This is a test function, change it back later\n x[0] = {}\nx[1]={}\nx[2] = {} (fine value)".format(x[0],x[1],x[2])
                )
    if call: #if @admin was called
        #forwad message to admin chat
        #forward the message that had @admin
        #send a message saying the user that requested the @admin

        replied_message = update.message.reply_to_message
        #chat IDs
        #-1002082274403  second test server

        CID = -1002082274403 #the current chat id in use by the bot for a destination, change as needed
        if replied_message:
            await context.bot.forward_message(
                chat_id=CID,
                from_chat_id=replied_message.chat_id,
                message_id=replied_message.message_id, )
            await context.bot.send_message(
                chat_id=CID,

                text="Attention requested in '{}' by {}".format(update.message.chat.title,update.message.from_user.first_name))
            await context.bot.forward_message(
                chat_id=CID,
                from_chat_id=replied_message.chat_id,
                message_id=update.message.message_id, )


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
        if str(user) == str(x[1]): #if the user is in the chat
            remove_fine(350, x[0])
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="forgiving a $350 fine from {}\n\n{}'s current fines ${}".format(user,user,x[4] - 350))

async def add_users_fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = 0
    uid = '';
    fine = '';

    message = update.message.text
    print(message)
    add_cmd = message.split("\n")
    print(f"add_cmd: {add_cmd}")
    substrings = add_cmd[1].split(" ")
    uid = substrings[0]
    fine = substrings[1]

    print(f"uid: {uid}")
    print(f"fine: {fine}")

    if uid != '' and uid and fine != '' and fine:
        add_fines(uid, fine)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"attempted to add fines to user {uid} with amount {fine}")
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="inadequate parameters to fine a custom amount")




# allows the caller to fine a user for a message
async def fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    if replied_message:
        original_message_id = replied_message.message_id
        user = replied_message.from_user.username

        members = get_members()
        for x in members:
            if int(replied_message.from_user.id) == int(x[0]):
                add_fine(x[0])
                #await context.bot.send_message(chat_id=update.effective_chat.id,text="TEST\nx[0] = {}\nx[1]={}\nx[2] = {} (fine value)".format(x[0],x[1],x[2]))

                await update.message.reply_text(text="Fining " + user + " $350\n\n{}'s current fines ${}".format(replied_message.from_user.first_name,
                                                                               x[4] + 350), reply_to_message_id=original_message_id)

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No user selected to fine"
        )



#used to grab a list of all members
#CADEN DO NOT DELETE
#IT IS USED BY MOST OF THE FUNCTIONS
async def get_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_members()[1][2]
    )


if __name__ == '__main__':
    #rebuild_tables()
    application = ApplicationBuilder().token('6569990634:AAEJ2MLYy-ByCOjHbqzzfFyIbUvqi5zDUcU').build()

    # application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))


    pan_handler = CommandHandler('pan', pan)
    fine_handler = CommandHandler('fine', fines)
    remove_fine_handler = CommandHandler('unfine', Rfine)
    get_handler = CommandHandler('get', get_all_members)
    add_users = CommandHandler('add', add_users_fines)
    members_handler = MessageHandler(filters.CHAT, handle_messages)

    application.add_handler(pan_handler)
    application.add_handler(fine_handler)
    application.add_handler(remove_fine_handler)
    application.add_handler(get_handler)
    application.add_handler(add_users)
    application.add_handler(members_handler)


    application.run_polling()
