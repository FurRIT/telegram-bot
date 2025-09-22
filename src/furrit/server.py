"""
HTTP Server.
"""

from typing import cast
import aiohttp
import aiohttp.web

from furrit.types import ApiBotData

routes = aiohttp.web.RouteTableDef()


@routes.get("/ping")
async def ping(request: aiohttp.web.Request):
    ctx = cast(ApiBotData, request.app["ctx"])

    await ctx.application.bot.send_message(ctx.main_cid, "hello http api!")
    return aiohttp.web.Response(text="pong")
