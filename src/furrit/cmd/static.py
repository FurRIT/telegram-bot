"""
Static Message Commands.
"""

from typing import cast
import logging

import telegram
import telegram.ext

from furrit.types import BotData


async def cmd_welcome(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Show 'welcome' message.
    """
    effective_chat = update.effective_chat
    assert effective_chat is not None

    bot_data = cast(BotData, context.bot_data)
    msg = bot_data["msg_store"].get("welcome")

    if msg is None:
        logging.error("could not find message welcome")
        return

    await context.bot.send_message(
        chat_id=effective_chat.id,
        parse_mode="HTML",
        text=msg,
        disable_web_page_preview=True,
    )


async def cmd_links(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Show 'links' message.
    """
    effective_chat = update.effective_chat
    assert effective_chat is not None

    bot_data = cast(BotData, context.bot_data)
    msg = bot_data["msg_store"].get("links")

    if msg is None:
        logging.error("could not find message links")
        return

    await context.bot.send_message(
        chat_id=effective_chat.id,
        parse_mode="HTML",
        text=msg,
        disable_web_page_preview=True,
    )


async def cmd_chats(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Show 'links' message.
    """
    effective_chat = update.effective_chat
    assert effective_chat is not None

    bot_data = cast(BotData, context.bot_data)
    msg = bot_data["msg_store"].get("links")

    if msg is None:
        logging.error("could not find message links")
        return

    await context.bot.send_message(
        chat_id=effective_chat.id,
        parse_mode="HTML",
        text=msg,
        disable_web_page_preview=True,
    )


async def cmd_rules(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Show 'rules' message.
    """
    effective_chat = update.effective_chat
    assert effective_chat is not None

    bot_data = cast(BotData, context.bot_data)
    msg = bot_data["msg_store"].get("rules")

    if msg is None:
        logging.error("could not find message rules")
        return

    await context.bot.send_message(
        chat_id=effective_chat.id,
        parse_mode="HTML",
        text=msg,
        disable_web_page_preview=True,
    )


async def cmd_channels_sfw(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Show 'channels.sfw' message.
    """
    effective_chat = update.effective_chat
    assert effective_chat is not None

    bot_data = cast(BotData, context.bot_data)
    msg = bot_data["msg_store"].get("channels.sfw")

    if msg is None:
        logging.error("could not find message channels.sfw")
        return

    await context.bot.send_message(
        chat_id=effective_chat.id,
        parse_mode="HTML",
        text=msg,
        disable_web_page_preview=True,
    )


async def cmd_channels_nsfw(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Show 'channels.nsfw' message.
    """
    effective_chat = update.effective_chat
    assert effective_chat is not None

    bot_data = cast(BotData, context.bot_data)
    msg = bot_data["msg_store"].get("channels.nsfw")

    if msg is None:
        logging.error("could not find message channels.nsfw")
        return

    await context.bot.send_message(
        chat_id=effective_chat.id,
        parse_mode="HTML",
        text=msg,
        disable_web_page_preview=True,
    )


async def cmd_commands(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Show a derived message that summarizes commands.
    """
    effective_chat = update.effective_chat
    assert effective_chat is not None

    bot_data = cast(BotData, context.bot_data)

    await context.bot.send_message(
        chat_id=effective_chat.id, parse_mode="HTML", text=bot_data["cmds_msg"]
    )
