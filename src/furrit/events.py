"""
Event Handling Utilities.
"""

from typing import TypedDict, TypeAlias, Literal, cast
import io
import zoneinfo
import datetime


class RawOrganizer(TypedDict):
    """
    An Organizer defined in the Bridge client schema.
    """

    uid: str
    furname: str | None
    username: str | None


RawAttendeeStatus: TypeAlias = (
    Literal["ACCEPTED"] | Literal["TENTATIVE"] | Literal["DECLINED"]
)


class RawAttendee(TypedDict):
    """
    An Attendee defined in the Bridge client schema.
    """

    aid: str
    uid: str
    furname: str | None
    username: str | None
    status: RawAttendeeStatus


class RawEvent(TypedDict):
    """
    An Event as defined in the Bridge client schema.
    """

    uid: str
    status: Literal["TENTATIVE"] | Literal["CONFIRMED"] | Literal["CANCELED"]
    allday: bool
    organizer: RawOrganizer
    attendees: list[RawAttendee]
    summary: str | None
    location: str | None
    description: str | None
    dtstart: str
    dtend: str


def _to_date_string(date: datetime.datetime) -> str:
    """
    Replaces the behavior of Date.toDateString.
    """
    return date.strftime("%a %b %d %Y")


def _to_date_time_string(date: datetime.datetime) -> str:
    """
    Simple Date Time Format.
    """
    return date.strftime("%a %b %d %Y %I:%M %p")


def _format_date_range(raw_event: RawEvent) -> str:
    """
    Format a date range in a RawEvent for `raw_event_to_msg_text`.

    If `allday` - format components w/out time component; otherwise format with
    date and time.
    """

    buf = io.StringIO()
    allday = raw_event["allday"]

    def _field_to_local_datetime(field: str) -> datetime.datetime:
        string = cast(dict[str, str], raw_event)[field]
        converted = datetime.datetime.fromisoformat(string)

        return converted.astimezone(zoneinfo.ZoneInfo("America/New_York"))

    datetime_fmter = _to_date_string if allday else _to_date_time_string

    dtstart = _field_to_local_datetime("dtstart")
    dtend = _field_to_local_datetime("dtend")

    components = [dtstart, dtend]

    fmted = " - ".join(map(datetime_fmter, components))
    buf.write(fmted)

    buf.seek(0)
    txt = buf.read()
    buf.close()

    return txt


_MAP_EMOJI = "🗺"
_CALENDAR_EMOJI = "📆"

_STATUS_TO_SECTION_HEADER: dict[RawAttendeeStatus, str] = {
    "ACCEPTED": "<i>Yes Attending:</i>",
    "TENTATIVE": "<i>Maybe:</i>",
    "DECLINED": "<i>No:</i>",
}
_STATUS_ORDER: list[RawAttendeeStatus] = ["ACCEPTED", "TENTATIVE", "DECLINED"]


def raw_event_to_msg_text(raw_event: RawEvent) -> str:
    """
    Turn a RawEvent into the body of the message.
    """

    buf = io.StringIO()
    buf.write(f"<b>{raw_event['summary']}</b>\n\n")

    date_range = _format_date_range(raw_event)
    buf.write("<b>")
    buf.write(_CALENDAR_EMOJI)
    buf.write(" ")
    buf.write(date_range)
    buf.write("</b>")
    buf.write("\n\n")

    buf.write("<b>")
    buf.write(_MAP_EMOJI)
    buf.write(" ")

    location = raw_event["location"] if raw_event["location"] is not None else "Unknown"
    buf.write(location)

    buf.write("</b>")
    buf.write("\n\n")

    description = (
        raw_event["description"] + "\n\n"
        if raw_event["description"] is not None
        else ""
    )
    buf.write(description)

    status_to_attendee_idxs = {}
    for i, attendee in enumerate(raw_event["attendees"]):
        status = attendee["status"]
        if status not in status_to_attendee_idxs:
            status_to_attendee_idxs[status] = [i]
        else:
            status_to_attendee_idxs[status].append(i)

    for a_status in _STATUS_ORDER:
        header = _STATUS_TO_SECTION_HEADER[a_status]

        buf.write(header)
        buf.write("\n")

        if a_status not in status_to_attendee_idxs:
            continue

        attendee_idxs = status_to_attendee_idxs[a_status]

        for idx in attendee_idxs:
            attendee = raw_event["attendees"][idx]
            furname = attendee["furname"]

            if furname is None:
                continue

            buf.write(" • ")
            buf.write(furname)
            buf.write("\n")

    buf.seek(0)
    txt = buf.read()
    buf.close()

    return txt
