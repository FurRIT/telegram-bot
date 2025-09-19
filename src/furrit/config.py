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
    admin_ids: frozenset[int]
    msgs_dir: str


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

    if not ("cid" in raw and isinstance(raw["cid"], int)):
        return (None, ".cid must exist and be of type int")

    if not ("admin_cid" in raw and isinstance(raw["admin_cid"], int)):
        return (None, ".admin_cid must exist and be of type int")

    if not ("bot_token" in raw and isinstance(raw["bot_token"], str)):
        return (None, ".bot_token must exist and be of type str")

    if not ("admin_ids" in raw and isinstance(raw["admin_ids"], list)):
        return (None, ".admin_ids must exist and be of type list")

    for i, item in enumerate(raw["admin_ids"]):
        if not isinstance(item, int):
            return (None, f".admin_ids[{i}] must be of type int")

    if not ("msgs_dir" in raw and isinstance(raw["msgs_dir"], str)):
        return (None, ".msgs_dir must exist and be of type str")

    r_admin_ids: list[int] = raw["admin_ids"]
    admin_ids = frozenset(r_admin_ids)

    cid: int = raw["cid"]
    admin_cid: int = raw["admin_cid"]
    bot_token: str = raw["bot_token"]
    msgs_dir: str = raw["msgs_dir"]

    config = Config(cid, admin_cid, bot_token, admin_ids, msgs_dir)
    return (config, None)
