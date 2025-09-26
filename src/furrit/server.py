"""
HTTP Server.
"""

from typing import cast

import aiohttp
import aiohttp.web

from furrit.types import ApiBotData
from furrit.events import RawEvent, raw_event_to_msg_text
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

    if m_event_row is None:
        event_row = insert_event(raw_event["uid"])

        main_msg = await ctx.application.bot.send_message(
            chat_id=ctx.main_cid, text=msg_txt, parse_mode="HTML"
        )

        # XXX(mwp): not sure why this was needed; for some reason
        # python-telegram-bot throws an exception if these two requests are
        # made at the same time
        # await asyncio.sleep(0.20)

        events_msg = await ctx.application.bot.send_message(
            chat_id=ctx.events_cid, text=msg_txt, parse_mode="HTML"
        )

        insert_event_message(event_row.id, main_msg.id, ctx.main_cid)
        insert_event_message(event_row.id, events_msg.id, ctx.events_cid)

        return aiohttp.web.Response(status=200)

    event_messages = try_get_event_messages_by_event_id(m_event_row.id)
    for event_message in event_messages:
        # TODO: edit messages
        pass

    # TODO: update existing event
    return aiohttp.web.Response(status=201)
