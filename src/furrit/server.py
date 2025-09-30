"""
HTTP Server.
"""

from typing import cast
import logging

import aiohttp
import aiohttp.web

import telegram

from furrit.types import ApiBotData
from furrit.events import RawEvent, raw_event_to_msg_text
from furrit.button import EventCallbackData, EventReactionKind
from furrit.db.events import (
    try_get_event_by_ext_id,
    insert_event,
    insert_event_message,
    try_get_event_messages_by_event_id,
)

routes = aiohttp.web.RouteTableDef()


@routes.get("/ping")
async def ping(request: aiohttp.web.Request):
    ctx = cast(ApiBotData, request.app["ctx"])

    await ctx.application.bot.send_message(ctx.main_cid, "hello http api!")
    return aiohttp.web.Response(text="pong")


@routes.post("/event")
async def post_event(request: aiohttp.web.Request):
    """Handle POST /event"""
    ctx = cast(ApiBotData, request.app["ctx"])
    raw_event = cast(RawEvent, await request.json())

    m_event_row = try_get_event_by_ext_id(raw_event["uid"])
    msg_txt = raw_event_to_msg_text(raw_event)

    is_new_event: bool = m_event_row is None
    if m_event_row is None:
        m_event_row = insert_event(raw_event["uid"])

    keyboard = [
        [
            telegram.InlineKeyboardButton(
                "Yes",
                callback_data=EventCallbackData(
                    m_event_row.id, EventReactionKind.YES
                ).to_json(),
            ),
            telegram.InlineKeyboardButton(
                "Maybe",
                callback_data=EventCallbackData(
                    m_event_row.id, EventReactionKind.MAYBE
                ).to_json(),
            ),
            telegram.InlineKeyboardButton(
                "No",
                callback_data=EventCallbackData(
                    m_event_row.id, EventReactionKind.NO
                ).to_json(),
            ),
        ]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    if is_new_event:
        main_msg = await ctx.application.bot.send_message(
            chat_id=ctx.main_cid,
            text=msg_txt,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

        # XXX(mwp): not sure why this was needed; for some reason
        # python-telegram-bot throws an exception if these two requests are
        # made at the same time
        # await asyncio.sleep(0.20)

        events_msg = await ctx.application.bot.send_message(
            chat_id=ctx.events_cid,
            text=msg_txt,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

        insert_event_message(m_event_row.id, main_msg.id, ctx.main_cid)
        insert_event_message(m_event_row.id, events_msg.id, ctx.events_cid)

        return aiohttp.web.Response(status=200)

    event_messages = try_get_event_messages_by_event_id(m_event_row.id)
    for event_message in event_messages:
        await ctx.application.bot.edit_message_text(
            msg_txt,
            chat_id=event_message.tg_chat_id,
            message_id=event_message.tg_msg_id,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    return aiohttp.web.Response(status=201)
