"""
Button Callback Handling.
"""

from __future__ import annotations
from typing import Literal, TypedDict, TypeAlias
import enum
import json
import dataclasses


class RawEventCallbackData(TypedDict):
    """
    Raw Event Callback Data.
    """

    pk: Literal[0]
    ev: str
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

    ext_id: str
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
            "ev": self.ext_id,
            "rk": self.reaction_kind.value,
        }

    def to_json(self) -> str:
        """
        Construct into a RawEventCallbackData then serialize.
        """

        raw = self.to_raw()
        return json.dumps(raw)
