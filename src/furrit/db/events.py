"""
Event Database Handling.
"""

from typing import NamedTuple, Sequence

from furrit.db.utils import connect


class EventRow(NamedTuple):
    """
    Row in the `EVENTS` table.
    """

    id: int
    ext_id: str


class EventMessageRow(NamedTuple):
    """
    Row in the `EVENT_MESSAGES` table.
    """

    event_id: int
    tg_msg_id: int
    tg_chat_id: int


def try_get_event_by_ext_id(ext_id: str) -> EventRow | None:
    """
    Try to get an Event row by `event.ext_id`.
    """

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT id, ext_id FROM EVENTS WHERE ext_id = ? LIMIT 1",
        (ext_id,),
    )
    row: tuple[int, str] | None = cur.fetchone()

    if row is None:
        return None

    cur.close()
    con.close()

    return EventRow(*row)


def insert_event(ext_id: str) -> EventRow:
    """
    Insert a new row into EVENTS.
    """

    con = connect()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO EVENTS (ext_id) VALUES (?)",
        (ext_id,),
    )

    cur.close()
    con.close()

    event_row = try_get_event_by_ext_id(ext_id)
    assert event_row is not None

    return event_row


def try_get_event_messages_by_event_id(event_id: int) -> Sequence[EventMessageRow]:
    """
    Get EventMessageRow(s) by `event_message.event_id` -> `event.id`.
    """

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT event_id, tg_msg_id FROM EVENT_MESSAGES WHERE event_id = ?", (event_id,)
    )
    rows: list[tuple[int, int, int]] = cur.fetchall()

    cur.close()
    con.close()

    objs = list(map(lambda row: EventMessageRow(*row), rows))
    return objs


def insert_event_message(event_id: int, tg_msg_id: int, tg_chat_id: int) -> None:
    """
    Insert a new row into EVENT_MESSAGES.
    """

    con = connect()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO EVENT_MESSAGES (event_id, tg_msg_id, tg_chat_id) VALUES (?, ?, ?)",
        (
            event_id,
            tg_msg_id,
            tg_chat_id,
        ),
    )

    cur.close()
    con.close()
