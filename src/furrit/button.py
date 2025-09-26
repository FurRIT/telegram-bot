"""
Button Callback Handling.
"""

from __future__ import annotations
from typing import Literal, TypedDict, TypeAlias, cast
import enum
import json
import dataclasses

import telegram
import telegram.ext


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

    # TODO: actually perform a request to the bridge to rsvp for us
    print(event)

