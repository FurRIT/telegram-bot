"""
FurRIT Telegram Bot.
"""

from typing import cast
import io
import re
import sys
import random
import asyncio
import logging
import datetime
import textwrap
import argparse

from apscheduler.triggers.cron import CronTrigger  # type: ignore
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore

import aiohttp.web

from telegram import Update, User, ChatMemberUpdated, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    Application,
    filters,
    ChatMemberHandler,
    CallbackQueryHandler,
)
import telegram.helpers

from furrit.role import RoleDeriver
from furrit.config import load_config
from furrit.server import routes

from furrit.db.users import (
    add_update_tg_user,
    add_pan_count,
    incr_fine_awoo,
    AWOO_FINE_COST,
)
from furrit.db.quotes import random_quote
from furrit.types import BotData, ApiBotData
from furrit.button import handle_button
from furrit.summon import SummonTracker
from furrit.message import MessageStore, load_store_dir

from furrit.cmd.fine import cmd_fine, cmd_unfine, cmd_awoofines
from furrit.cmd.quote import cmd_addquote, cmd_getquote, cmd_quotestats
from furrit.cmd.static import (
    cmd_commands,
    cmd_links,
    cmd_chats,
    cmd_welcome,
    cmd_channels_sfw,
    cmd_channels_nsfw,
    cmd_rules,
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

    bot_data = cast(BotData, context.bot_data)
    admin_cid = bot_data["admin_cid"]

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


def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> tuple[bool, bool] | None:
    """
    Takes a ChatMemberUpdated instance and extracts whether the
    'old_chat_member' was a member of the chat and whether the 'new_chat_member'
    is a member of the chat. Returns None, if the status didn't change.
    """

    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get(
        "is_member", (None, None)
    )

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def greet_chat_members(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Greets new users in chats and announces when someone leaves"""
    chat_member = update.chat_member
    if chat_member is None:
        return

    effective_chat = update.effective_chat
    if effective_chat is None:
        return

    result = extract_status_change(chat_member)
    if result is None:
        return

    bot_data = cast(BotData, context.bot_data)
    msg = bot_data["msg_store"].get("welcome")
    if msg is None:
        logging.error("could not find message welcome")
        return

    was_member, is_member = result
    if not was_member and is_member:
        await context.bot.send_message(
            chat_id=effective_chat.id,
            parse_mode="HTML",
            text=msg,
        )


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

    bot_data = cast(BotData, context.bot_data)
    summon_tracker = bot_data["summon_tracker"]

    await summon_tracker.handle_update(update, context)


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


BAN_COMMAND_LENGTH = datetime.timedelta(minutes=5)


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
        until_date=(datetime.datetime.now() + BAN_COMMAND_LENGTH),
        revoke_messages=False,
    )


def _derive_bulletin_msg() -> str:
    """
    Derive the name of the current week's bulletin in the message store.
    """

    today = datetime.date.today()
    wkday = today.isoweekday()

    dy_off = wkday % 7
    dt_off = datetime.timedelta(dy_off)

    target = today - dt_off

    name = f"bulletin.{target.year}.{target.month:02}.{target.day:02}"
    return name


async def cmd_bulletin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bulletin command.
    """
    effective_chat = update.effective_chat
    assert effective_chat is not None

    msg_name = _derive_bulletin_msg()

    bot_data = cast(BotData, context.bot_data)
    msg = bot_data["msg_store"].get(msg_name)

    if msg is None:
        logging.warning("could not find bulletin message %s", msg_name)

        await effective_chat.send_message("Could not find a bulletin for this week.")
        return

    await effective_chat.send_message(text=msg, parse_mode="HTML")


async def daily_e(application: Application):
    """
    Send an 'e' message to the main chat.
    """
    bot_data = cast(BotData, application.bot_data)
    await application.bot.send_message(chat_id=bot_data["cid"], text="e")


async def daily_quote(application: Application):
    """
    Send a random daily quote.
    """
    bot_data = cast(BotData, application.bot_data)
    cid = bot_data["cid"]

    user_quote = random_quote(cid)
    if user_quote is None:
        return

    user, quote = user_quote

    date = datetime.datetime.now()
    date_fmted = date.strftime("%a %b %d %Y")

    header_msg = f"FurRIT Quote of the Day for _{date_fmted}_:"
    await application.bot.send_message(
        chat_id=cid, text=header_msg, parse_mode="MarkdownV2"
    )

    quote_date = datetime.datetime.fromisoformat(quote.quoter_msg_sent_at)
    quote_date_fmted = quote_date.strftime("%b %d %Y")

    response = f'"{quote.quote}"\n  — {user.tg_first_name}\n\n'
    response_esc = telegram.helpers.escape_markdown(response, version=2)
    response_esc += f"_{quote_date_fmted}_"

    await application.bot.send_message(
        chat_id=cid, text=response_esc, parse_mode="MarkdownV2"
    )


async def weekly_bulletin(application: Application):
    """
    Automatically send the weekly bulleting.
    """
    bot_data = cast(BotData, application.bot_data)

    msg_name = _derive_bulletin_msg()
    msg = bot_data["msg_store"].get(msg_name)
    if msg is None:
        logging.warning("could not find weekly bulletin message %s", msg_name)
        return

    cid = bot_data["cid"]
    await application.bot.send_message(chat_id=cid, text=msg, parse_mode="HTML")


COMMAND_HANDLERS = [
    ("commands", cmd_commands, "Get the list of commands."),
    ("links", cmd_links, "Get a list of FurRIT chats, channels, and sites."),
    ("chats", cmd_chats, "Get a list of chats, channels, and sites."),
    ("welcome", cmd_welcome, "Get welcome information for new Users."),
    ("bulletin", cmd_bulletin, "Get the weekly bulletin for this week."),
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


async def run(
    cid: int,
    admin_cid: int,
    events_cid: int,
    bot_token: str,
    admin_ids: frozenset[int],
    msg_store: MessageStore,
    summon_tracker: SummonTracker,
    api_host: str,
    api_port: int,
) -> None:
    """
    Run the Application.
    """

    cmds_msg_buf = io.StringIO()
    cmds_msg_buf.write("<strong>Commands</strong>\n")

    descriptors: list[tuple[str, str]] = []
    for command, _, description in COMMAND_HANDLERS:
        cmds_msg_buf.write(f"• <code>{command}</code> {description}\n")

        descriptor = (command, description)
        descriptors.append(descriptor)

    cmds_msg_buf.seek(0)
    cmds_msg = cmds_msg_buf.read()

    builder = ApplicationBuilder().token(bot_token)
    role_deriver = RoleDeriver(admin_ids)

    async def post_init(application: Application) -> None:
        application.bot_data["cid"] = cid
        application.bot_data["admin_cid"] = admin_cid
        application.bot_data["cmds_msg"] = cmds_msg
        application.bot_data["msg_store"] = msg_store
        application.bot_data["role_deriver"] = role_deriver
        application.bot_data["summon_tracker"] = summon_tracker

        await application.bot.set_my_commands(descriptors)

    builder.post_init(post_init)
    application = builder.build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        daily_e,
        CronTrigger(hour=9, minute=26),
        args=[application],
    )
    scheduler.add_job(
        daily_e,
        CronTrigger(hour=21, minute=26),
        args=[application],
    )
    scheduler.add_job(
        daily_quote,
        CronTrigger(hour=7, minute=0),
        args=[application],
    )
    scheduler.add_job(
        weekly_bulletin,
        CronTrigger(hour=9, minute=0, day_of_week=0),
        args=[application],
    )

    for command, callback, _ in COMMAND_HANDLERS:
        handler = CommandHandler(command, callback)
        application.add_handler(handler)

    members_handler = MessageHandler(filters.Chat(chat_id=cid), handle_message_generic)
    application.add_handler(members_handler)

    application.add_handler(
        ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER)
    )

    application.add_handler(CallbackQueryHandler(handle_button))

    web_app = aiohttp.web.Application()
    web_app.add_routes(routes)

    try:
        await application.initialize()
        await post_init(application)

        await application.start()

        assert application.updater is not None
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        scheduler.start()

        api_bd = ApiBotData(cid, events_cid, application)
        web_app["ctx"] = api_bd

        web_runner = aiohttp.web.AppRunner(web_app)

        await web_runner.setup()
        site = aiohttp.web.TCPSite(web_runner, api_host, api_port)
        await site.start()

        await asyncio.Future()
    finally:
        assert application.updater is not None
        await application.updater.stop()

        await application.stop()
        await application.shutdown()

        await web_runner.cleanup()


def main() -> None:
    """
    Load configurations & start listening.
    """
    parser = argparse.ArgumentParser(prog="furrit")
    parser.add_argument(
        "-c",
        "--config",
        default="config.toml",
        help="config file path (default %(default)s)",
    )
    args = parser.parse_args()

    m_config, m_err = load_config(args.config)
    if m_err is not None:
        err_msg = "\n".join(
            textwrap.wrap(f"error: {m_err}", subsequent_indent="       "),
        )
        print(err_msg, file=sys.stderr)

        sys.exit(1)

    assert m_config is not None
    config = m_config

    summon_tracker = SummonTracker.from_sections(config.chats.main, config.summons)
    msg_store = load_store_dir(config.msgs_dir)

    asyncio.run(
        run(
            config.chats.main,
            config.chats.admin,
            config.chats.events,
            config.bot_token,
            config.admin_ids,
            msg_store,
            summon_tracker,
            config.api.host,
            config.api.port,
        )
    )


if __name__ == "__main__":
    main()
