"""
Fine Commands.
"""

from typing import cast
import telegram
import telegram.ext

from furrit.db.users import (
    get_user_fines,
    add_update_tg_user,
    do_forgive_fine,
    do_fine_user,
    try_get_user_by_tg_id,
    try_get_user_by_tg_username,
)

from furrit.role import Role
from furrit.types import BotData
from furrit.parse import parse_optional_username

MANUAL_FINE_COST = 350


async def cmd_fine(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
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

    from_user = message.from_user
    assert from_user is not None

    bot_data = cast(BotData, context.bot_data)
    role = bot_data["role_deriver"].derive(from_user)

    if role != Role.ADMINISTRATOR:
        await context.bot.send_message(
            chat_id=effective_chat.id,
            text="You must be an administrator to fine",
        )
        return

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


MANUAL_UNFINE_COST = 350


async def cmd_unfine(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
    """
    Removes a single fine from a user. Can specify amount removed.
    author: Torin
    """
    message = update.message
    assert message is not None

    from_user = message.from_user
    assert from_user is not None

    effective_chat = update.effective_chat
    assert effective_chat is not None

    bot_data = cast(BotData, context.bot_data)
    role = bot_data["role_deriver"].derive(from_user)

    if role != Role.ADMINISTRATOR:
        await context.bot.send_message(
            chat_id=effective_chat.id,
            text="You must be an administrator to unfine",
        )
        return

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


async def cmd_awoofines(
    update: telegram.Update, _context: telegram.ext.ContextTypes.DEFAULT_TYPE
):
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

    m_username, _ = parse_optional_username(text)

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
