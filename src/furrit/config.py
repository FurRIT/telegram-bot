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

    name       The Section Name.
    keywords   Keywords that should cause a summon.
    users      The user pool to summon from.
    threshold  Number of messages a keyword appears in before a summon.
    within     Time span within which the threshold must be met (in ms).
    cooldown   Time span after a summon where a new summon cannot occur (in ms).
    """

    name: str
    keywords: frozenset[str]
    users: frozenset[ConfigUser]
    threshold: int | None
    within: int | None
    cooldown: int | None


@dataclasses.dataclass(frozen=True)
class ApiSection:
    """
    A `api` section in the Configuration.
    """

    host: str
    port: int


@dataclasses.dataclass(frozen=True)
class ChatsSection:
    """
    A `chats` section in the configuration.
    """

    main: int
    admin: int
    events: int


@dataclasses.dataclass(frozen=True)
class Config:
    """
    Root Configuration.
    """

    bot_token: str
    admin_ids: frozenset[int]
    msgs_dir: str
    api: ApiSection
    chats: ChatsSection
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

    if len(r_keywords) == 0:
        return (None, f".summon.{name}.keywords must have at least one element")

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

    if "threshold" in body:
        if not isinstance(body["threshold"], int):
            return (None, f".summon.{name}.threshold must be a int")
        threshold = body["threshold"]
    else:
        threshold = None

    if "within" in body:
        if not isinstance(body["within"], int):
            return (None, f".summon.{name}.within must be a int")
        within = body["within"]
    else:
        within = None

    if "cooldown" in body:
        if not isinstance(body["cooldown"], int):
            return (None, f".summon.{name}.cooldown must be a int")
        cooldown = body["cooldown"]
    else:
        cooldown = None

    section = SummonSection(name, keywords, users, threshold, within, cooldown)
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


def _load_chats(raw: dict[str, Any]) -> tuple[ChatsSection, None] | tuple[None, str]:
    """
    Load `.chats` top-level mapping.
    """

    if not ("main" in raw and isinstance(raw["main"], int)):
        return (None, ".chats.main must exist and be of type int")

    if not ("admin" in raw and isinstance(raw["admin"], int)):
        return (None, ".chats.admin must exist and be of type int")

    if not ("events" in raw and isinstance(raw["events"], int)):
        return (None, ".chats.events must exist and be of type int")

    main: int = raw["main"]
    admin: int = raw["admin"]
    events: int = raw["events"]

    return (ChatsSection(main, admin, events), None)


def _load_api(raw: dict[str, Any]) -> tuple[ApiSection, None] | tuple[None, str]:
    """
    Load `.api` top-level mapping.
    """

    if not ("host" in raw and isinstance(raw["host"], str)):
        return (None, ".api.host must exist and be of type str")

    if not ("port" in raw and isinstance(raw["port"], int)):
        return (None, ".api.port must exist and be of type int")

    host: str = raw["host"]
    port: int = raw["port"]

    return (ApiSection(host, port), None)


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
        return (None, f".msgs_dir '{msgs_dir}' does not exist or is not a dir")

    r_admin_ids: list[int] = raw["admin_ids"]
    admin_ids = frozenset(r_admin_ids)

    bot_token: str = raw["bot_token"]

    summons, summons_err = _load_summons(raw)
    if summons_err is not None:
        return (None, summons_err)
    assert summons is not None

    if not ("api" in raw and isinstance(raw["api"], dict)):
        return (None, ".api does not exist or is not a mapping")

    r_api = raw["api"]
    api, api_err = _load_api(r_api)
    if api_err is not None:
        return (None, api_err)
    assert api is not None

    if not ("chats" in raw and isinstance(raw["chats"], dict)):
        return (None, ".chats does not exist or is not a mapping")

    r_chats = raw["chats"]
    chats, chats_err = _load_chats(r_chats)
    if chats_err is not None:
        return (None, chats_err)
    assert chats is not None

    config = Config(bot_token, admin_ids, msgs_dir, api, chats, summons)
    return (config, None)
