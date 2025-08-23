"""
FurRIT Telegram Bot.
"""

import re
import os
import random
import logging
from datetime import datetime, timedelta  # imported for /ban method

import dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update, Bot, User
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from db.users import (
    add_update_tg_user,
    get_members,
    add_pan_count,
    add_quote_db,
    get_quotes,
    incr_fine_awoo,
    remove_fine,
    add_fines,
    AWOO_FINE_COST,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

AT_ADMIN_RE = re.compile(r"@admin")


async def search_handle_at_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """
    Search for and handle '@admin' in message text.

    Returns whether or not @admin matched.
    """
    message = update.message
    assert message is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    if message.text is None:
        return False

    at_admin_match = AT_ADMIN_RE.search(message.text)
    if at_admin_match is None:
        return False

    admin_cid = context.bot_data["ADMIN_CID"]

    # TODO: sent some sort of message indicating that @admin must be a reply; or
    # handle the case where it is not a reply; still returns True to indicate an
    # @admin match
    if message.reply_to_message is None:
        return True
    reply_to = message.reply_to_message

    assert message.from_user is not None

    await context.bot.send_message(
        chat_id=effective_chat.id, text="Contacting the admin team"
    )
    await context.bot.forward_message(
        chat_id=admin_cid,
        from_chat_id=reply_to.chat_id,
        message_id=reply_to.message_id,
    )
    await context.bot.send_message(
        chat_id=admin_cid,
        text="Attention requested in '{}' by {}".format(
            reply_to.chat.title, message.from_user.first_name
        ),
    )
    await context.bot.forward_message(
        chat_id=admin_cid,
        from_chat_id=reply_to.chat_id,
        message_id=message.message_id,
    )
    return True


AWOO_RE = re.compile(r"[@Aa]+[rwW]+[o0O]+([\s\.\?!,:;\-—\*]+|$)")


async def search_handle_awoo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """
    Search for and handle 'awoo' in message text.

    Returns whether or not awoo matched.
    """
    message = update.message
    assert message is not None

    text = message.text
    if text is None:
        return False

    awoo_matches = AWOO_RE.findall(text)
    if len(awoo_matches) == 0:
        return False

    from_user = message.from_user
    assert from_user is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    c_fines = incr_fine_awoo(from_user.id)
    assert c_fines is not None

    await context.bot.send_message(
        chat_id=effective_chat.id,
        text=f"""Don't Awoo! - ${AWOO_FINE_COST} fine!

{from_user.first_name}'s current fines ${c_fines}""",
    )

    return True


VORE_RE = re.compile(r"[Vv]+[Oo0]+[Rr]+[Ee3]+[SszZ]*")
VORE_STICKER_PACK_NAME = "FJZGIF"


async def search_handle_vore(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """
    Search for and handle 'vore' in message text.

    Returns whether or not vore matched.
    """
    message = update.message
    assert message is not None

    if message.text is None:
        return False

    vore_matches = VORE_RE.findall(message.text)
    if len(vore_matches) == 0:
        return False

    sticker_set = await context.bot.get_sticker_set(name=VORE_STICKER_PACK_NAME)
    stickers_in_set = sticker_set.stickers
    sticker_ids = [sticker.file_id for sticker in stickers_in_set]
    random_sticker_id = random.choice(sticker_ids)

    await message.reply_sticker(
        sticker=random_sticker_id, reply_to_message_id=message.message_id
    )
    return True


async def handle_message_generic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    If a new user speaks in chat, they are added to the database.
    Waits for 'awoo' to be sent in the chat.
    :param update:
    :param context:
    :return:
    """
    message = update.message
    if message is None:
        return

    # XXX(mwp): bookkeep new users joining or sending messages in chat
    users: list[User | None] = [message.from_user]
    if message.new_chat_members is not None:
        users.extend(message.new_chat_members)

    for user in users:
        if user is not None:
            add_update_tg_user(user)

    at_admined = await search_handle_at_admin(update, context)
    if (
        message is not None
        and message.text is not None
        and message.text.startswith("/")
    ):
        return

    # NOTE: avoid checking for 'awoo' and 'vore' variants if the '@admin' check
    # is triggered; 'fun' stuff shouldn't trigger during admin summons
    if not at_admined:
        await search_handle_awoo(update, context)
        await search_handle_vore(update, context)


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
    replied_message = update.message

    if replied_message:
        if replied_message.from_user == update.message.from_user:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="You can't pan yourself."
            )
            return
        if replied_message.from_user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="You can't pan the bot."
            )
            return
        else:
            original_message_id = replied_message.message_id
            sticker_pack_name = "FURRIT_PAN"
            sticker_set = await context.bot.get_sticker_set(name=sticker_pack_name)
            stickers_in_set = sticker_set.stickers
            sticker_ids = [sticker.file_id for sticker in stickers_in_set]
            random_sticker_id = random.choice(sticker_ids)
            add_pan_count(replied_message.from_user.id)
            await update.message.reply_sticker(
                sticker=random_sticker_id, reply_to_message_id=original_message_id
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You need to reply to a message to pan.",
        )


async def print_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding to this list:
    # Make a new line and type: links += "\n the links + any other info abt it"
    links = "**Links:**"
    links += """Greater Rochester Area Resources
 • Rochester Furs (https://t.me/RochesterFurs) — Group for all local area furries
 • Rochester Furs Events Channel (https://t.me/RochesterFurryEvents)"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=links)


async def print_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding to this list:
    # Make a new line and type: chan += "\n the channel + any other info abt it"
    chan = "**Furrit Channels:**"
    chan += """FurRIT-Exclusive Resources
 • FurRIT Telegram Folder (https://t.me/addlist/gy2K43K2_tBjOWFh) — All FurRIT Chats and Channels
 • ROOVille (https://t.me/+5-hPmg8gUd40MWNh) — NSFW art-sharing chat (admin approval required)
 • FurRIT After Dark (https://t.me/+u5NuEZcx3npmZDI5) — NSFW adult chat (admin approval required)
 • FurRIT Discord (https://discord.gg/kS4rryY)
 
 
 __Use /channels_sfw and /channels_nsfw to get a list of outside channels and chats run by FurRIT members.__"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=chan)


async def print_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding to this list:
    # Make a new line and type: rule += "\n the rule + any other info abt it"
    rules = " **Furrit Rules:** "
    rules += """
• FurRIT is for people who identify as members of the Furry Fandom
• Group Chat is 18+
• This community is a safe place for everyone of all genders, sexualities, races, etc.
• Messaging that solicits or elicits sexual arousal should not be shared (keep that in NSFW chats)
  > Forbidden content includes: moderate-heavy flirting, irl NSFW stories/content, porn, and kinks
  > Permitted content includes: suggestive furry memes (no genitals), jokes, and non-sexual adult topics (e.g. swearing, alcohol, violence)
Don't be horny in Main
Reply to any message with @admin {optional note} to flag it for attention.


 **Membership Policy** (must satisfy at least one of the following):
• Current RIT Students
• Alumni
• Staff
• Faculty
• Accepted to RIT
• Significant Other/Spouse of Member"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rules)


async def sfw_print_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding a chat to this list:
    # Make a new line and type: chat += "\n the chat + any other info abt it"
    chat = """SFW Affiliated Chats and Channels
Run by FurRIT members rather than the Admin Team. Subject to their own rules.

Azu (http://t.me/azu_shorttail)
 • Infurmation Technology — Get help with code and complain about technology
Vanawolf (http://t.me/vanawolf)
 • I Vana See Cuteness (https://t.me/VanaCute) — Only the cutest, most adorable SFW content
 • I Vana Appreciate (https://t.me/VanaAppreciate) — Creative, skillfull, thought provoking, mind expanding, calming, good
Xoren (http://t.me/MrHyperCube)
 • Xoren's Stream Studio (https://t.me/XorenMoonbeam) — Announcements from your local streaming Physics Folf!"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=chat)


async def nsfw_print_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding a chat to this list:
    # Make a new line and type: chat += "\n the chat + any other info abt it"
    chat = """"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=chat)


async def print_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formating of manually adding a command to this list:
    # Make a new line and type: command += "\n the command + any other info abt it"
    commands = "The list of user commands for the Bot:"
    commands += "\n /chats : lists all Furrit chats\n/commands : lists the commands for this bot"
    commands += "\n /rules : Lists all the current rules of furrit\n/channels : lists furrit channels"
    commands += "\n /links : Lists links to furrit channels, chats, sites, etc"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=commands)


async def autoAwoo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # count = telegram.Bot.get_chat_member_count(update.effective_chat.id)
    # count = telegram.Bot.getChatMemberCount(context.bot,update.effective_chat.id)
    count = await context.bot.get_chat_member_count(update.effective_chat.id)
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    text = "There are {} members in this chat.\n The admins of this chat are \n{}\n{}".format(
        count, admins[0].user.username, admins[1].user.username
    )
    text1 = admins[0].user.username + admins[1].user.username
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


#     print(admins) #remove /TODO


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
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="You can't ban yourself."
            )
            return
            # TODO: or if replying user is not an admin then message : "not allowed to ban"
            # elif Telegram.ChatMember.status(bot.get_chat_member(chat_id, user_id)) != 'Administrator':
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="Unauthorized to ban."
            )
            return
        else:
            # actual banning of the user
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,  # chat
                user_id=replied_message.from_user.id,  # origional message
                until_date=(
                    datetime.now() + timedelta(minutes=5)
                ),  # need to decide how long to ban for
                revoke_messages=False,
            )  # need to decide if messages they send will be visible
            return


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
            reply_to_message_id=replied_message.message_id,
        )
        return

    # idk if this actually works yet, so imma just skip it with a return
    return
    # if no message was replied to
    message = update.message.text
    user = ""
    index = 8
    go = 0
    print(message[8])
    while index < len(message):
        if message[index] == "@":
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
                text="forgiving a $350 fine from {}\n\n{}'s current fines ${}".format(
                    user, user, x[4] - 350
                ),
            )


async def add_users_fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    The code to manually add fines to a User
    Author: Torin
    """
    count = 0
    uid = ""
    fine = ""

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
                add_fines(uid, fine)
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
                incr_fine_awoo(x[0])
                # await context.bot.send_message(chat_id=update.effective_chat.id,text="TEST\nx[0] = {}\nx[1]={}\nx[2] = {} (fine value)".format(x[0],x[1],x[2]))
                await update.message.reply_text(
                    text="Fining "
                    + user
                    + " $350\n\n{}'s current fines ${}".format(
                        replied_message.from_user.first_name, x[4] + 350
                    ),
                    reply_to_message_id=original_message_id,
                )

    #         await update.message.reply_text(
    #             text="Fining " + user + " $350\n\n{}'s current fines ${}".format(update.message.from_user.first_name,
    #                                                                              x[2] + 350),
    #             reply_to_message_id=original_message_id)

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="No user selected to fine"
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
        chat_id=update.effective_chat.id, text=get_members()[1][2]
    )


async def get_all_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    A test command (will not be deployed) that gets the list of all the quotes in the database.
    author: Caden
    :param update:
    :param context:
    :return:
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_quotes())


async def add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a message to the quotes database.
    Cannot quote yourself or the bot.
    author: Caden
    Modified by: Torin
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
                    chat_id=update.effective_chat.id, text="You can't quote yourself."
                )
                return

            if replied_message.from_user.id == context.bot.id:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text="You can't quote the bot."
                )
                return

            else:
                quote_user_id = replied_message.from_user.id
                quote_contents = replied_message.text
                sender_user_id = update.message.from_user.id
                value = add_quote_db(sender_user_id, quote_user_id, quote_contents)
                if value == 1:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id, text="Quote added."
                    )
                if value == 0:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="You can't quote this twice!",
                    )
    except Exception as e:
        logging.info(e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Failed. {e}"
        )


async def daily_e(bot: Bot):
    await bot.send_message(chat_id=CID, text="e")


async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Chat ID: `{chat_id}`", parse_mode="Markdown")


async def barn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied_message = update.message.reply_to_message

    if replied_message:
        original_message_id = replied_message.message_id
        sticker_pack_name = "furrit_barn"
        sticker_set = await context.bot.get_sticker_set(name=sticker_pack_name)
        stickers_in_set = sticker_set.stickers
        sticker_ids = [sticker.file_id for sticker in stickers_in_set]
        random_sticker_id = random.choice(sticker_ids)
        await update.message.reply_sticker(
            sticker=random_sticker_id, reply_to_message_id=original_message_id
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You need to reply to a message to pan.",
        )


COMMAND_HANDLERS = [
    ("pan", pan),
    ("fine", fines),
    ("unfine", Rfine),
    ("barn", barn_command),
    ("get", get_all_members),
    ("add", add_users_fines),
    ("get_quotes", get_all_quotes),
    ("quote", add_quote),
    ("awoo", autoAwoo),
    ("commands", print_commands),
    ("channels_sfw", sfw_print_chats),
    ("channels_nsfw", nsfw_print_chats),
    ("rules", print_rules),
    ("chats", print_c),
    ("links", print_links),
    ("getc", get_chat_id),
]


def main() -> None:
    """
    Load configurations & start listening.
    """
    dotenv.load_dotenv()

    raw_cid = os.environ["CID"]
    cid = int(raw_cid)

    raw_admin_cid = os.environ["ADMIN_CID"]
    admin_cid = int(raw_admin_cid)

    bot_token = os.environ["BOT_TOKEN"]
    application = ApplicationBuilder().token(bot_token).build()

    # NOTE: store the data into the bot datastore for access in handlers
    application.bot_data["ADMIN_CID"] = admin_cid

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        daily_e,
        CronTrigger(hour=6, minute=21),  # Set desired time here (e.g., 9:00 AM)
        args=[application.bot],  # Pass bot context
    )
    scheduler.add_job(
        daily_e,
        CronTrigger(hour=9, minute=21),  # Set desired time here (e.g., 9:00 AM)
        args=[application.bot],  # Pass bot context
    )
    scheduler.add_job(
        daily_e,
        CronTrigger(hour=18, minute=21),  # Set desired time here (e.g., 9:00 AM)
        args=[application.bot],  # Pass bot context
    )
    scheduler.add_job(
        daily_e,
        CronTrigger(hour=21, minute=21),  # Set desired time here (e.g., 9:00 AM)
        args=[application.bot],  # Pass bot context
    )

    for command, callback in COMMAND_HANDLERS:
        handler = CommandHandler(command, callback)
        application.add_handler(handler)

    members_handler = MessageHandler(filters.Chat(chat_id=cid), handle_message_generic)
    application.add_handler(members_handler)

    application.run_polling()
    scheduler.start()


if __name__ == "__main__":
    main()
