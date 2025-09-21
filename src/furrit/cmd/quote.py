"""
Quote Commands.
"""

import datetime

import telegram
import telegram.ext

from furrit.db.users import (
    try_do_add_quote,
    add_update_tg_user,
)
from furrit.db.quotes import (
    search_quotes,
    random_quote,
    derive_quote_stats,
    derive_user_quote_stats,
)
from furrit.parse import parse_optional_username


async def cmd_addquote(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
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
    if ok:
        await context.bot.send_message(
            chat_id=effective_chat.id,
            reply_to_message_id=message.id,
            text="Successfully added quote.",
        )
        return

    assert err_msg is not None
    await context.bot.send_message(chat_id=effective_chat.id, text=err_msg)


async def cmd_getquote(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Get quote command.
    """
    message = update.message
    assert message is not None

    text = message.text
    assert text is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    m_username, remaining = parse_optional_username(text)

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

    date = datetime.datetime.fromisoformat(quote.quoter_msg_sent_at)
    date_fmted = date.strftime("%b %d %Y")

    response = f'"{quote.quote}"\n  — {user.tg_first_name}\n\n'
    response_esc = telegram.helpers.escape_markdown(response, version=2)
    response_esc += f"_{date_fmted}_"

    await effective_chat.send_message(response_esc, parse_mode="MarkdownV2")


async def cmd_quotestats(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Quote statistics command.
    """
    message = update.message
    assert message is not None

    text = message.text
    assert text is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    m_username, _ = parse_optional_username(text)

    if m_username is None:
        qs = derive_quote_stats()

        prelude = f"*Overall*\n{qs.quote_count} total quotes\n\n*Total Times Quoted*\n"

        total_times = ""
        for user, count in qs.top_quoted:
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
