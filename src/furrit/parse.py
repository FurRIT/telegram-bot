"""
Parsing Utilities.
"""

import re

PARSE_OPTIONAL_USERNAME_RE = re.compile(r"^@([_\-a-zA-Z0-9]*)(.*)")


def parse_optional_username(text: str) -> tuple[str | None, str]:
    """
    Parse the text of a Telegram Message, assuming that if the first word is
    prefixed with @[a-zA-Z0-9] it is username argument.

    Returns (username, extra_text)
    """

    space_after_cmd_idx = text.find(" ")
    if space_after_cmd_idx == -1:
        return (None, "")

    txt_after_cmd = text[(space_after_cmd_idx + 1) :]

    username_match = PARSE_OPTIONAL_USERNAME_RE.match(txt_after_cmd)
    if username_match is None:
        return (None, txt_after_cmd)

    username = username_match[1]
    query = username_match[2]

    return (username, query)
