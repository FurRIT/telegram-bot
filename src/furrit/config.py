"""
Configuration and Conf. Validation.
"""

from typing import Sequence, Any
import os.path
import tomllib
import dataclasses


@dataclasses.dataclass(frozen=True)
class ConfigUser:
    """
    User in a Configuration.
    """

    tg_id: int
    name: str
    tg_username: str


@dataclasses.dataclass(frozen=True)
class SummonSection:
    """
    A `summon.*` section in the Configuration.
    """

    name: str
    keywords: frozenset[str]
    users: frozenset[ConfigUser]


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
    summons: Sequence[SummonSection]


def _load_user(thing: dict[str, Any]) -> tuple[ConfigUser, None] | tuple[None, str]:
    """
    Load `.summon.[name].users[i]`.
    """
    if not ("tg_id" in thing and isinstance(thing["tg_id"], int)):
        return (None, ".tg_id must exist and be of type int")

    if not ("name" in thing and isinstance(thing["name"], str)):
        return (None, ".name must exist and be of type str")

    if not ("tg_username" in thing and isinstance(thing["tg_username"], str)):
        return (None, ".tg_username must exist and be of type str")

    tg_id: int = thing["tg_id"]
    name: str = thing["name"]
    tg_username: str = thing["tg_username"]

    user = ConfigUser(tg_id, name, tg_username)
    return (user, None)


def _load_summon_section(
    name: str,
    body: Any,
) -> tuple[SummonSection, None] | tuple[None, str]:
    """
    Load `.summon.[name]` section.
    """

    if not isinstance(body, dict):
        return (None, "section must be dict")

    if not "keywords" in body:
        return (None, f".summon.{name}.keywords must exist")

    r_keywords = body["keywords"]
    if not isinstance(r_keywords, list):
        return (None, f".summon.{name}.keywords must be a list")

    for i, part in enumerate(r_keywords):
        if not isinstance(part, str):
            typ = type(part).__name__
            return (
                None,
                f".summon.{name}.keywords[{i}] must be a str; found {typ}",
            )

    keywords: frozenset[str] = frozenset(r_keywords)

    if "users" not in body:
        return (None, f".summon.{name}.users must exist")

    r_users = body["users"]
    if not isinstance(r_users, list):
        return (None, f".summon.{name}.users must be a list")

    de_users = []
    for i, r_user in enumerate(r_users):
        user, err = _load_user(r_user)
        if err is not None:
            return (None, f"error with .summon.{name}.users[{i}]; {err}")

        assert user is not None
        de_users.append(user)

    users: frozenset[ConfigUser] = frozenset(de_users)

    section = SummonSection(name, keywords, users)
    return (section, None)


def _load_summons(
    raw: dict[str, Any],
) -> tuple[Sequence[SummonSection], None] | tuple[None, str]:
    """
    Load `.summon` top-level mapping.
    """

    sections: list[SummonSection] = []

    if "summon" not in raw:
        return ([], None)

    r_summon = raw["summon"]
    if not isinstance(r_summon, dict):
        return (None, ".summon must be a dict")

    for name, body in r_summon.items():
        section, err = _load_summon_section(name, body)
        if err is not None:
            return (None, err)

        assert section is not None
        sections.append(section)

    return (sections, None)


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

    r_msgs_dir: str = raw["msgs_dir"]
    if not os.path.isabs(r_msgs_dir):
        conf_dir = os.path.dirname(path)
        msgs_dir = os.path.relpath(r_msgs_dir, conf_dir)
    else:
        msgs_dir = r_msgs_dir

    if not os.path.isdir(msgs_dir):
        return (None, f"error: .msgs_dir '{msgs_dir}' does not exist or is not a dir")

    r_admin_ids: list[int] = raw["admin_ids"]
    admin_ids = frozenset(r_admin_ids)

    cid: int = raw["cid"]
    admin_cid: int = raw["admin_cid"]
    bot_token: str = raw["bot_token"]

    summons, summons_err = _load_summons(raw)
    if summons_err is not None:
        return (None, summons_err)
    assert summons is not None

    config = Config(cid, admin_cid, bot_token, admin_ids, msgs_dir, summons)
    return (config, None)
