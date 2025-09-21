"""
HTTP Server.
"""

import aiohttp
import aiohttp.web

routes = aiohttp.web.RouteTableDef()


@routes.get("/ping")
async def ping(request: aiohttp.web.Request):
    return aiohttp.web.Response(text="pong")
