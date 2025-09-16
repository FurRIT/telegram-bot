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
    Application,
    filters,
)
import telegram.helpers

from furrit.db.users import (
    get_user_fines,
    add_update_tg_user,
    add_pan_count,
    incr_fine_awoo,
    do_forgive_fine,
    do_fine_user,
    try_do_add_quote,
    try_get_user_by_tg_id,
    try_get_user_by_tg_username,
    AWOO_FINE_COST,
)
from furrit.db.quotes import (
    search_quotes,
    random_quote,
    derive_quote_stats,
    derive_user_quote_stats,
)
from furrit.messages import (
    LINKS_MESSAGE,
    CHATS_MESSAGE,
    RULES_MESSAGE,
    CHANNELS_SFW_MESSAGE,
    CHANNELS_NSFW_MESSAGE,
    COMMANDS_MESSAGE,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def _random_sticker_pack_sticker(
    name: str, context: ContextTypes.DEFAULT_TYPE
) -> str:
    """Get a random sticker from a sticker pack."""
    stickers = await context.bot.get_sticker_set(name=name)
    file_ids = [sticker.file_id for sticker in stickers.stickers]

    return random.choice(file_ids)


PARSE_OPTIONAL_USERNAME_RE = re.compile(r"^@([_\-a-zA-Z0-9]*)(.*)")


def _parse_optional_username(text: str) -> tuple[str | None, str]:
    """
    Parse the text of a Telegram Message, assuming that if the first word is
    prefixed with @[a-zA-Z0-9] it is username argument.

    Returns (username, extra_text)
    """

    space_after_cmd_idx = text.find(" ")
    if space_after_cmd_idx == -1:
        return (None, "")

    txt_after_cmd = text[(space_after_cmd_idx + 1) :]

    username_match = PARSE_OPTIONAL_USERNAME_RE.match(txt_after_cmd)
    if username_match is None:
        return (None, txt_after_cmd)

    username = username_match[1]
    query = username_match[2]

    return (username, query)


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

    await context.bot.send_message(
        chat_id=effective_chat.id, text="Contacting the admin team"
    )

    if message.reply_to_message is None:
        message_to_forward = message
    else:
        message_to_forward = message.reply_to_message

    await context.bot.forward_message(
        chat_id=admin_cid,
        from_chat_id=message_to_forward.chat_id,
        message_id=message_to_forward.message_id,
    )

    assert message.from_user is not None
    await context.bot.send_message(
        chat_id=admin_cid,
        text=f"Attention requested in '{message_to_forward.chat.title}' by {message.from_user.first_name}",
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

    sticker = await _random_sticker_pack_sticker(VORE_STICKER_PACK_NAME, context)
    await message.reply_sticker(sticker=sticker, reply_to_message_id=message.message_id)
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


PAN_STICKER_PACK_NAME = "FURRIT_PAN"


async def cmd_pan(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    message = update.message
    assert message is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    reply_to_message = message.reply_to_message
    if reply_to_message is None:
        await context.bot.send_message(
            chat_id=effective_chat.id,
            text="You need to reply to a message to pan.",
        )
        return

    if message.from_user == reply_to_message.from_user:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="You can't pan yourself."
        )
        return

    user_to_pan = reply_to_message.from_user
    assert user_to_pan is not None

    if user_to_pan.id == context.bot.id:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="You can't pan the bot."
        )
        return

    sticker = await _random_sticker_pack_sticker(PAN_STICKER_PACK_NAME, context)
    add_pan_count(user_to_pan.id)

    await message.reply_sticker(
        sticker=sticker, reply_to_message_id=reply_to_message.id
    )


BARN_STICKER_PACK_NAME = "furrit_barn"


async def cmd_barn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """\\barn command"""
    message = update.message
    assert message is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    reply_to_message = message.reply_to_message
    if reply_to_message is None:
        await context.bot.send_message(
            chat_id=effective_chat.id,
            text="You need to reply to a message to barn.",
        )
        return

    if message.from_user == reply_to_message.from_user:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="You can't barn yourself."
        )
        return

    user_to_pan = reply_to_message.from_user
    assert user_to_pan is not None

    if user_to_pan.id == context.bot.id:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="You can't barn the bot."
        )
        return

    sticker = await _random_sticker_pack_sticker(BARN_STICKER_PACK_NAME, context)
    await message.reply_sticker(
        sticker=sticker, reply_to_message_id=reply_to_message.id
    )


async def cmd_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_chat = update.effective_chat
    assert effective_chat is not None

    await context.bot.send_message(
        chat_id=effective_chat.id, parse_mode="MarkdownV2", text=LINKS_MESSAGE
    )


async def cmd_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_chat = update.effective_chat
    assert effective_chat is not None

    await context.bot.send_message(
        chat_id=effective_chat.id, parse_mode="MarkdownV2", text=CHATS_MESSAGE
    )


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_chat = update.effective_chat
    assert effective_chat is not None

    await context.bot.send_message(
        chat_id=effective_chat.id, parse_mode="MarkdownV2", text=RULES_MESSAGE
    )


async def cmd_channels_sfw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_chat = update.effective_chat
    assert effective_chat is not None

    await context.bot.send_message(
        chat_id=effective_chat.id, parse_mode="MarkdownV2", text=CHANNELS_SFW_MESSAGE
    )


async def cmd_channels_nsfw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_chat = update.effective_chat
    assert effective_chat is not None

    await context.bot.send_message(
        chat_id=effective_chat.id, parse_mode="MarkdownV2", text=CHANNELS_NSFW_MESSAGE
    )


async def cmd_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_chat = update.effective_chat
    assert effective_chat is not None

    await context.bot.send_message(
        chat_id=effective_chat.id, parse_mode="MarkdownV2", text=COMMANDS_MESSAGE
    )


BAN_COMMAND_LENGTH = timedelta(minutes=5)


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ban is currently unfinished, as far as I'm aware.
    Times out a user for 5 minutes.
    author: Theta
    :param update:
    :param context:
    :return:
    """
    message = update.message
    assert message is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    reply_to_message = message.reply_to_message
    if reply_to_message is None:
        return

    if reply_to_message.from_user == message.from_user:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="You can't ban yourself."
        )
        return

    # TODO: or if replying user is not an admin then message : "not allowed to ban"
    # elif Telegram.ChatMember.status(bot.get_chat_member(chat_id, user_id)) != 'Administrator':
    # await context.bot.send_message(
    #     chat_id=update.effective_chat.id, text="Unauthorized to ban."
    # )
    # return

    user_to_ban = reply_to_message.from_user
    assert user_to_ban is not None

    await context.bot.ban_chat_member(
        chat_id=effective_chat.id,
        user_id=user_to_ban.id,
        until_date=(datetime.now() + BAN_COMMAND_LENGTH),
        revoke_messages=False,
    )


MANUAL_UNFINE_COST = 350


async def cmd_unfine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Removes a single fine from a user. Can specify amount removed.
    author: Torin
    """
    message = update.message
    assert message is not None

    reply_to_message = message.reply_to_message
    if reply_to_message is None:
        to_reply_to = message.message_id
        user_to_unfine = message.from_user
    else:
        to_reply_to = reply_to_message.message_id
        user_to_unfine = reply_to_message.from_user

    assert user_to_unfine is not None

    # XXX(mwp): make sure the user we're about to unfine is registered
    add_update_tg_user(user_to_unfine)

    ok, cfines_or_msg = do_forgive_fine(user_to_unfine.id, MANUAL_UNFINE_COST)
    if not ok:
        await message.reply_text(
            text=f"Cannot forgive ${MANUAL_UNFINE_COST} without becoming negative!"
        )
        return

    assert isinstance(cfines_or_msg, int)
    await message.reply_text(
        text=f"""Forgiving ${MANUAL_UNFINE_COST} from {user_to_unfine.first_name}.

{user_to_unfine.first_name}'s current fines ${cfines_or_msg}""",
        reply_to_message_id=to_reply_to,
    )


MANUAL_FINE_COST = 350


async def cmd_fine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to fine a user by replying to their message.
    author: Torin
    :param update:
    :param context:
    :return:
    """
    message = update.message
    assert message is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    reply_to_message = message.reply_to_message
    if reply_to_message is None:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="No user selected to fine"
        )
        return

    user_to_fine = reply_to_message.from_user
    assert user_to_fine is not None

    # XXX(mwp): make sure the user we're about to fine is registered
    add_update_tg_user(user_to_fine)

    c_fines = do_fine_user(user_to_fine.id, MANUAL_FINE_COST)
    assert c_fines is not None

    await message.reply_text(
        text=f"""Fining {user_to_fine.full_name} ${MANUAL_FINE_COST}!

{user_to_fine.full_name}'s current fines ${c_fines}""",
        reply_to_message_id=reply_to_message.message_id,
    )


async def cmd_addquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a message to the quotes database.
    Cannot quote yourself or the bot.
    author: Caden
    Modified by: Torin
    :param update:
    :param context:
    :return:
    """
    message = update.message
    assert message is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    reply_to_message = message.reply_to_message
    assert reply_to_message is not None

    if reply_to_message is None:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="You must reply to a message to quote."
        )
        return

    if reply_to_message.text is None:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="Quoted message must have text."
        )
        return

    assert message.from_user is not None
    assert reply_to_message.from_user is not None

    if reply_to_message.from_user == message.from_user:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="You can't quote yourself."
        )
        return

    if reply_to_message.from_user.id == context.bot.id:
        await context.bot.send_message(
            chat_id=effective_chat.id, text="You can't quote the bot."
        )
        return

    # XXX(mwp): make sure both users are present in the database
    add_update_tg_user(message.from_user)
    add_update_tg_user(reply_to_message.from_user)

    # XXX(mwp): try to add a quote, handling when it isn't possible
    res = try_do_add_quote(reply_to_message, message)

    ok, err_msg = res
    if not ok:
        assert err_msg is not None
        await context.bot.send_message(chat_id=effective_chat.id, text=err_msg)


async def cmd_getquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Get quote command.
    """
    message = update.message
    assert message is not None

    text = message.text
    assert text is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    m_username, remaining = _parse_optional_username(text)

    if m_username is None:
        user_quote = random_quote(effective_chat.id)
        if user_quote is None:
            await message.reply_text(text="Could not find a random Quote!")
            return
    else:
        stripped = remaining.strip()
        user_quote = search_quotes(stripped, effective_chat.id, username=m_username)
        if user_quote is None:
            await message.reply_text(
                text="Could not find a Quote that matched that criteria!"
            )
            return

    user, quote = user_quote

    date = datetime.fromisoformat(quote.quoter_msg_sent_at)
    date_fmted = date.strftime("%b %d %Y")

    response = f'"{quote.quote}"\n  — {user.tg_first_name}\n\n'
    response_esc = telegram.helpers.escape_markdown(response, version=2)
    response_esc += f"_{date_fmted}_"

    await effective_chat.send_message(response_esc, parse_mode="MarkdownV2")


async def cmd_quotestats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Quote statistics command.
    """
    message = update.message
    assert message is not None

    text = message.text
    assert text is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    m_username, _ = _parse_optional_username(text)

    if m_username is None:
        qs = derive_quote_stats()

        prelude = f"*Overall*\n{qs.quote_count} total quotes\n\n*Total Times Quoted*"

        total_times = ""
        for user, count in qs.top_adders:
            total_times += f"• {count}: {user.tg_first_name}\n"

        total_quotes = ""
        for user, count in qs.top_adders:
            total_quotes += f"• {count}: {user.tg_first_name}\n"

        total_times_esc = telegram.helpers.escape_markdown(total_times, version=2)
        total_quotes_esc = telegram.helpers.escape_markdown(total_quotes, version=2)

        reply = f"{prelude}{total_times_esc}\n*Total Quotes Added*\n{total_quotes_esc}"
        await effective_chat.send_message(text=reply, parse_mode="MarkdownV2")
    else:
        m_triple = derive_user_quote_stats(m_username)

        if m_triple is None:
            await effective_chat.send_message(
                "Could not find Quotes that involve that user."
            )
            return
        user, times_quoted, times_added = m_triple

        reply = f"*Overall for {user.tg_first_name}*\n\n*Total Times Quoted*\n{times_quoted}\n*Total Quotes Added*\n{times_added}"
        await effective_chat.send_message(text=reply, parse_mode="MarkdownV2")


async def cmd_awoofines(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Awoo Fines Command.
    """
    message = update.message
    assert message is not None

    text = message.text
    assert text is not None

    from_user = message.from_user
    assert from_user is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    m_username, _ = _parse_optional_username(text)

    # XXX(mwp): ensure that the Telegram User is in the database
    add_update_tg_user(from_user)

    if m_username is None:
        user = try_get_user_by_tg_id(from_user.id)
        assert user is not None
    else:
        user = try_get_user_by_tg_username(m_username)
        if user is None:
            await effective_chat.send_message(
                "Could not find a user with that username."
            )
            return

    fines = get_user_fines(user.id)
    if fines == 0:
        reply = f"{user.tg_first_name} doesn't have any fines!"
    else:
        reply = f"{user.tg_first_name}'s current fines total ${fines}."

    reply_esc = telegram.helpers.escape_markdown(reply, version=2)
    await effective_chat.send_message(text=reply_esc, parse_mode="MarkdownV2")


async def daily_e(bot: Bot):
    await bot.send_message(chat_id=CID, text="e")


COMMAND_HANDLERS = [
    ("commands", cmd_commands, "Get the list of commands."),
    ("links", cmd_links, "Get a list of FurRIT chats, channels, and sites."),
    ("chats", cmd_chats, "Get a list of chats, channels, and sites."),
    (
        "channels_sfw",
        cmd_channels_sfw,
        "Get a list of SFW FurRIT-affiliated channels and chats.",
    ),
    (
        "channels_nsfw",
        cmd_channels_nsfw,
        "Get a list of NSFW FurRIT-affiliated channels and chats.",
    ),
    ("rules", cmd_rules, "Get a list of chat rules and membership policies."),
    (
        "addquote",
        cmd_addquote,
        "Use as a reply to a text message to add it to the database of FurRIT quotes.",
    ),
    (
        "getquote",
        cmd_getquote,
        "[@USER] [SEARCH QUERY] to get a random quote; includes options to search by user and/or text content.",
    ),
    (
        "quotestats",
        cmd_quotestats,
        "[@USER] to get the total number of quotes added and authored; if a user is specified, stats are only shown for that user.",
    ),
    (
        "awoofines",
        cmd_awoofines,
        "[@USER] for your current total awoo fines owed; if a username is specified, fines for that user are shown instead.",
    ),
    ("pan", cmd_pan, "Use as a reply to pan a User."),
    ("barn", cmd_barn, "Use as a reply to barn a User."),
    ("fine", cmd_fine, "Use as a reply to manually fine a User."),
    ("unfine", cmd_unfine, "User as a reply to remove a fine from a User."),
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

    descriptors: list[tuple[str, str]] = []
    for command, _, description in COMMAND_HANDLERS:
        descriptor = (command, description)
        descriptors.append(descriptor)

    builder = ApplicationBuilder().token(bot_token)

    async def post_init(application: Application) -> None:
        application.bot_data["ADMIN_CID"] = admin_cid
        await application.bot.set_my_commands(descriptors)

    builder.post_init(post_init)
    application = builder.build()

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

    for command, callback, _ in COMMAND_HANDLERS:
        handler = CommandHandler(command, callback)
        application.add_handler(handler)

    members_handler = MessageHandler(filters.Chat(chat_id=cid), handle_message_generic)
    application.add_handler(members_handler)

    application.run_polling()
    scheduler.start()


if __name__ == "__main__":
    main()
