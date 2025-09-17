"""
Configuration and Conf. Validation.
"""

import os.path
import tomllib
import dataclasses


@dataclasses.dataclass(frozen=True)
class Config:
    """
    Root Configuration.
    """

    cid: int
    admin_cid: int
    bot_token: str


def load_config(path: str) -> tuple[Config, None] | tuple[None, str]:
    """
    Load a Config from a configuration file.

    Both loads and validates a configuration for semantic errors.
    """

    if not os.path.isfile(path):
        return (None, "config file path does not exist or is not a file")

    with open(path, "rb") as file:
        try:
            raw = tomllib.load(file)
        except tomllib.TOMLDecodeError:
            return (None, "error occured during toml decoding")

    if not "cid" in raw and isinstance(raw["cid"], int):
        return (None, ".cid must exist and be of type int")

    if not "admin_cid" in raw and isinstance(raw["admin_cid"], int):
        return (None, ".admin_cid must exist and be of type int")

    if not "bot_token" in raw and isinstance(raw["bot_token"], str):
        return (None, ".bot_token must exist and be of type str")

    cid: int = raw["cid"]
    admin_cid: int = raw["admin_cid"]
    bot_token: str = raw["bot_token"]

    config = Config(cid, admin_cid, bot_token)
    return (config, None)
