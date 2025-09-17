"""
Role Definitions.

Role definitions and guard utilities.
"""

import enum
import dataclasses

import telegram


@enum.unique
class Role(enum.Enum):
    """
    Roles ordered by presedence.
    """

    UNKNOWN = 0
    MEMBER = 1
    ADMINISTRATOR = 2


@dataclasses.dataclass(frozen=True)
class RoleDeriver:
    """
    Derives the Role of a User.

    Derives a User's Role using the context provided during construction.
    """

    admin_ids: set[int]

    def derive(self, user: telegram.User) -> Role:
        """
        Derive a User's Role.
        """

        if user.id in self.admin_ids:
            return Role.ADMINISTRATOR

        return Role.UNKNOWN
