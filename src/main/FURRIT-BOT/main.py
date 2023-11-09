import logging
import random

import telegram
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

async def print_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding to this list:
    # Make a new line and type: links += "\n the links + any other info abt it"
    links = "Links:"
    links += "\n There are none"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=links
    )

async def print_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding to this list:
    # Make a new line and type: chan += "\n the channel + any other info abt it"
    chan = "Furrit Channels:"
    chan += "\n There are none"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=chan
    )

async def print_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding to this list:
    # Make a new line and type: rule += "\n the rule + any other info abt it"
    rules = "Furrit Rules:"
    rules += "\n There are none, go wild"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=rules
    )

async def print_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #Formating of manually adding a chat to this list:
    #Make a new line and type: chat += "\n the chat + any other info abt it"
    chat = "IDK, there arent any others"
    chat += "\n find some"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=chat
    )
async def print_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding a command to this list:
    # Make a new line and type: command += "\n the command + any other info abt it"
    commands = "The list of user commands for the Bot:"
    commands += "\n /chats : lists all Furrit chats\n/commands : lists the commands for this bot"
    commands += "\n /rules : Lists all the current rules of furrit\n/channels : lists furrit channels"
    commands += "\n /links : Lists links to furrit channels, chats, sites, etc"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=commands
    )
async def autoAwoo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #count = telegram.Bot.get_chat_member_count(update.effective_chat.id)
    #count = telegram.Bot.getChatMemberCount(context.bot,update.effective_chat.id)
    count = await context.bot.get_chat_member_count(update.effective_chat.id)
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    text = "There are {} members in this chat.\n The admins of this chat are \n{}\n{}".format(count,admins[0].user.username,admins[1].user.username)
    text1 = admins[0].user.username + admins[1].user.username
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text
    )
    print(admins) #remove /TODO

#removes a single fine from a user
# should allow the caller to specify the amt removed, also need to
#   change so that you call it using the @ of a user.
#chat_member_update: ChatMemberUpdated,
async def Rfine( update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message
    user_says = "".join(context.args)
    #target = chat_member_update.difference().get("status")
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    chat = await context.bot.get_chat(update.effective_chat.id)
    print(chat.username)
    name = '@' + admins[1].user.username
    if replied_message:
        original_message_id = replied_message.message_id
        await update.message.reply_text(
            text="forgiving a $350 fine from "+replied_message.from_user.username,
            reply_to_message_id=original_message_id)
    elif user_says == name:
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
    application.add_handler(CommandHandler("awoo",autoAwoo))

    application.add_handler(CommandHandler("commands", print_commands))
    application.add_handler(CommandHandler("chats", print_chats))
    application.add_handler(CommandHandler("rules", print_rules))
    application.add_handler(CommandHandler("channels", print_c))
    application.add_handler(CommandHandler("links", print_links))

    application.run_polling()
