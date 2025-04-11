import os.path
import tomllib
from pathlib import Path

from xdg_base_dirs import xdg_config_home

CONFIG_ROOT = xdg_config_home() / "orgee-roam"
CONFIG_FILE = CONFIG_ROOT / "config.toml"

OPE = os.path.expanduser
DEFAULTS: dict = {
    "paths": {
        "cache": OPE("~/.zk-cache.json"),
        "root": OPE("~/zettelkasten"),
    },
}


class Config:
    _instance = None
    _settings: dict = {}

    def __new__(cls, config_file: Path | str | None = None):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            if not config_file:
                config_file = CONFIG_FILE
            if isinstance(config_file, str):
                config_file = Path(config_file)
            cls._instance._load_config(config_file)
        return cls._instance

    def _load_config(self, config_file: Path):
        if config_file.is_file():
            with open(config_file, "rb") as f:
                self._settings = tomllib.load(f)
        else:
            self._settings = DEFAULTS

    def get(self, section, key):
        section = section.lower()
        key = key.lower()
        if section in self._settings and key in self._settings[section]:
            return self._settings[section][key]
        return None
