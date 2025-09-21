"""
Shared type definitions.
"""

from typing import TypedDict

import furrit.role
import furrit.message
import furrit.summon


class BotData(TypedDict):
    """
    Type description of custom bot data.
    """

    cid: int
    admin_cid: int
    cmds_msg: str
    msg_store: furrit.message.MessageStore
    role_deriver: furrit.role.RoleDeriver
    summon_tracker: furrit.summon.SummonTracker
