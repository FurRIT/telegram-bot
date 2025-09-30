"""
Button Callback Handling.
"""

from __future__ import annotations
from typing import Literal, TypedDict, TypeAlias, cast
import enum
import json
import logging
import dataclasses

import aiohttp
import aiohttp.client

import telegram
import telegram.ext


from furrit.types import BotData
from furrit.db.users import try_get_user_by_tg_id
from furrit.db.events import try_get_event_by_id


class RawEventCallbackData(TypedDict):
    """
    Raw Event Callback Data.
    """

    pk: Literal[0]
    ev: int
    rk: Literal[0] | Literal[1] | Literal[2]


@enum.unique
class EventReactionKind(enum.Enum):
    """
    Reaction Button Metadata.
    """

    YES = 0
    MAYBE = 1
    NO = 2


RawCallbackData: TypeAlias = RawEventCallbackData


@dataclasses.dataclass(frozen=True)
class EventCallbackData:
    """
    Re-Interpreted RawEventCallbackData.

    ext_id:        `.ev` from source
    reaction_kind: `.rk` from source
    """

    eid: int
    reaction_kind: EventReactionKind

    @staticmethod
    def from_raw(raw: RawEventCallbackData) -> EventCallbackData:
        """
        Construct from raw EventCallbackData.
        """

        ext_id = raw["ev"]
        reaction_kind = EventReactionKind(raw["rk"])

        return EventCallbackData(ext_id, reaction_kind)

    def to_raw(self) -> RawEventCallbackData:
        """
        Construct into RawEventCallbackData.
        """

        return {
            "pk": 0,
            "ev": self.eid,
            "rk": self.reaction_kind.value,
        }

    def to_json(self) -> str:
        """
        Construct into a RawEventCallbackData then serialize.
        """

        raw = self.to_raw()
        return json.dumps(raw)


class RawRsvpRequest(TypedDict):
    """
    Raw RSVP Request -> Bridge.
    """

    telegram_id: int
    telegram_username: str
    telegram_name: str
    status: Literal[0] | Literal[1] | Literal[2]


async def handle_button(
    update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle all button presses.

    Interpret callback query data and make the appropriate changes.
    """

    query = update.callback_query
    assert query is not None

    await query.answer()

    user = update.effective_user
    if user is None:
        return None

    bot_data = cast(BotData, context.bot_data)

    data = query.data
    if data is None:
        return None

    de = json.loads(data)

    if not ("pk" in de and isinstance(de["pk"], int)):
        return None

    pk = de["pk"]

    # XXX(mwp): right now there's only one payload kind; in the future this
    # could be expanded; for now pk=0 is an event payload
    if pk != 0:
        return None

    raw = cast(RawEventCallbackData, de)
    event = EventCallbackData.from_raw(raw)

    user_row = try_get_user_by_tg_id(user.id)
    if user_row is None:
        return None

    event_row = try_get_event_by_id(event.eid)
    if event_row is None:
        return None

    url = (
        "http://"
        + bot_data["bridge_host"]
        + ":"
        + str(bot_data["bridge_port"])
        + f"/event/{event_row.ext_id}/rsvp"
    )
    body: RawRsvpRequest = {
        "telegram_id": user_row.tg_id,
        "telegram_name": user_row.tg_first_name,
        "telegram_username": (
            user_row.tg_username if user_row.tg_username is not None else ""
        ),
        "status": event.reaction_kind.value,
    }

    ok = False
    session = aiohttp.ClientSession()

    async with session.post(url, json=body) as response:
        ok = response.ok
    await session.close()

    if not ok:
        logging.error(
            "received error from bridge rsvp event id=%s status_code=%d",
            event_row.ext_id,
            response.status,
        )
