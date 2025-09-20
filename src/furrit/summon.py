"""
Summon-Handling Utilities.
"""

from __future__ import annotations
from typing import NamedTuple, TypeAlias, Iterable, Literal, MutableSequence, cast
import re
import enum
import random
import logging
import datetime
import dataclasses

import telegram
import telegram.ext
import telegram.error

from furrit.config import ConfigUser, SummonSection


@enum.unique
class TriggerKind(enum.Enum):
    """
    Summon State Kind.
    """

    START = 0
    COUNTING = 1
    COOLDOWN = 2


class TriggerStart(NamedTuple):
    """
    Summon State Start.
    """

    kind: Literal[TriggerKind.START]


class TriggerCounting(NamedTuple):
    """
    Summon State Counting.
    """

    kind: Literal[TriggerKind.COUNTING]
    msg_count: int
    first: datetime.datetime
    last: datetime.datetime


class TriggerCooldown(NamedTuple):
    """
    Summon State Cooldown.
    """

    kind: Literal[TriggerKind.COOLDOWN]
    triggered: datetime.datetime


Trigger: TypeAlias = TriggerStart | TriggerCounting | TriggerCooldown


@dataclasses.dataclass(frozen=True)
class SummonInfo:
    """
    Static information for Summoning.
    """

    pattern: re.Pattern[str]
    users: frozenset[ConfigUser]
    keyword: str
    threshold: int
    within: int
    cooldown: int


DEFAULT_THRESHOLD = 3
DEFAULT_WITHIN = 3600000
#DEFAULT_COOLDOWN = 900000
DEFAULT_COOLDOWN = 30


CANNOT_INITIATE_CONVERSATION_ERR_MSG = (
    "Forbidden: bot can't initiate conversation with a user"
)


@dataclasses.dataclass
class SummonTracker:
    """
    Tracks and issues summons.
    """

    cid: int
    infos: list[SummonInfo]
    states: MutableSequence[Trigger]

    @staticmethod
    def from_sections(cid: int, sections: Iterable[SummonSection]) -> SummonTracker:
        """
        Create a SummonTracker from Config sections.
        """
        infos = []
        states: MutableSequence[Trigger] = []

        for section in sections:
            regex = "|".join(map(re.escape, section.keywords))
            regex = f"({regex})"

            pattern = re.compile(regex, flags=re.IGNORECASE)

            threshold = (
                section.threshold
                if section.threshold is not None
                else DEFAULT_THRESHOLD
            )
            within = section.within if section.within is not None else DEFAULT_WITHIN
            cooldown = (
                section.cooldown if section.cooldown is not None else DEFAULT_COOLDOWN
            )

            state = TriggerStart(TriggerKind.START)
            info = SummonInfo(
                pattern,
                section.users,
                next(iter(section.keywords)),
                threshold,
                within,
                cooldown,
            )

            infos.append(info)
            states.append(state)

        return SummonTracker(cid, infos, states)

    async def handle_update(
        self, update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle a Message's Text.
        """

        message = update.message
        if message is None:
            return

        text = message.text
        if text is None:
            return

        effective_chat = update.effective_chat
        if effective_chat is None or effective_chat.id != self.cid:
            return

        for i, (info, state) in enumerate(zip(self.infos, self.states)):
            match = info.pattern.search(text)
            if match is None:
                continue

            now = datetime.datetime.now(datetime.timezone.utc)
            kind = state.kind
            n_state: Trigger | None = None

            if kind == TriggerKind.START:
                n_state = TriggerCounting(
                    TriggerKind.COUNTING, 1, message.date, message.date
                )
            if kind == TriggerKind.COUNTING:
                counting = cast(TriggerCounting, state)
                from_start_ms = int(
                    (message.date - counting.first) / datetime.timedelta(milliseconds=1)
                )

                # CASE: trigger happens but window has elapsed; go back to
                # start; count the message
                if from_start_ms > info.within:
                    n_state = TriggerCounting(
                        TriggerKind.COUNTING, 1, message.date, message.date
                    )
                # CASE: have not exceeded window - increment count
                else:
                    n_state = TriggerCounting(
                        TriggerKind.COUNTING,
                        counting.msg_count + 1,
                        counting.first,
                        message.date,
                    )
            if kind == TriggerKind.COOLDOWN:
                cooldown = cast(TriggerCooldown, state)
                over = cooldown.triggered + datetime.timedelta(
                    milliseconds=info.cooldown
                )

                # CASE: we have been cooling down and that time is now elapsed;
                # count the message towards a trigger
                if now > over:
                    n_state = TriggerCounting(
                        TriggerKind.COUNTING, 1, message.date, message.date
                    )

            # CASE: we've been counting and hit the threshold
            if (
                n_state is not None
                and n_state.kind == TriggerKind.COUNTING
                and n_state.msg_count >= info.threshold
            ):
                user = random.choice(list(iter(info.users)))

                await context.bot.send_message(
                    chat_id=effective_chat.id,
                    text=f"{user.name} will be summoned for {info.keyword}.",
                )

                try:
                    await context.bot.forward_message(
                        user.tg_id, effective_chat.id, message.id
                    )
                except telegram.error.Forbidden as error:
                    if error.message == CANNOT_INITIATE_CONVERSATION_ERR_MSG:
                        logging.error(
                            "could not initiate conversation with user %s", user
                        )
                    else:
                        raise error

                n_state = TriggerCooldown(TriggerKind.COOLDOWN, message.date)

            if n_state is None:
                continue
            self.states[i] = n_state
