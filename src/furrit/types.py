"""
Shared type definitions.
"""

from typing import TypedDict
import dataclasses

import furrit.role
import furrit.message
import furrit.summon

import telegram.ext


class BotData(TypedDict):
    """
    Type description of custom bot data.
    """

    cid: int
    admin_cid: int
    cmds_msg: str
    bridge_host: str
    bridge_port: int
    msg_store: furrit.message.MessageStore
    role_deriver: furrit.role.RoleDeriver
    summon_tracker: furrit.summon.SummonTracker


@dataclasses.dataclass(frozen=True)
class ApiBotData:
    """
    Typed bot data passed to HTTP(S) handlers.
    """

    main_cid: int
    events_cid: int
    application: telegram.ext.Application
