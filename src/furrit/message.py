"""
Static Message Utilities.
"""

import os
import os.path
import dataclasses


@dataclasses.dataclass(frozen=True)
class MessageStore:
    """
    In-Memory Store of Messages.
    """

    mapping: dict[str, str]

    def get(self, prefix: str) -> str | None:
        """
        Get a message corresponding to a message.
        """
        if prefix not in self.mapping:
            return None

        return self.mapping[prefix]


def load_store_dir(path: str) -> MessageStore:
    """
    Load a MessageStore from a directory.
    """

    messages = {}

    for node in os.listdir(path):
        node_path = os.path.join(path, node)
        if not os.path.isfile(node_path):
            continue

        prefix, postfix = os.path.splitext(node)
        if postfix != ".html":
            continue

        with open(node_path, "r", encoding="utf-8") as file:
            txt = file.read()

        messages[prefix] = txt

    return MessageStore(messages)
