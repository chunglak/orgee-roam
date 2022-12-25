from __future__ import annotations  # PEP 585

import os.path
import configparser
from typing import Mapping

OPE = os.path.expanduser

CONFIG_FILE_LOCATIONS = [
    OPE("~/.orgee-roam.ini"),
    OPE("~/.config/orgee-roam.ini"),
]
DEFAULT_DICT: dict = {
    "roam_cache": "~/.orgee-roam-cache.json",
    "zettelkasten_root": "~/orgee_zettelkasten",
}
PATH_KEYS = ["roam_cache", "zettelkasten_root"]


def get_config(fn: str | None = None) -> tuple[dict[str, str], str | None]:
    locations = [fn] if fn else CONFIG_FILE_LOCATIONS
    for loc in locations:
        if dic := parse_file(loc):
            return (dic, loc)
    return (update_defaults(), None)


def parse_file(fn: str) -> dict[str, str] | None:
    if not os.path.isfile(fn):
        return None
    config = configparser.ConfigParser()
    config.read(fn)
    return update_defaults(config.defaults())


def update_defaults(dic: Mapping[str, str] | None = None) -> dict[str, str]:
    rez = DEFAULT_DICT.copy()
    if dic:
        rez.update(dic)
    for k in PATH_KEYS:
        rez[k] = OPE(rez[k])
    return rez
