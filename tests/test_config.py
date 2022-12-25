from __future__ import annotations  # PEP 585

import os.path
import tempfile

from orgee_roam.config import DEFAULT_DICT, get_config, update_defaults


def test_default_config():
    d = get_config()
    for k, v in d.items():
        assert v == DEFAULT_DICT[k]


def test_change_val():
    nd = {"roam_cache": "foo"}
    d = update_defaults(nd)
    for k, v in nd.items():
        assert d[k] == v


def test_update_from_file():
    with tempfile.TemporaryDirectory() as tdir:
        fn = os.path.join(tdir, "config.ini")
        with open(fn, "w", encoding="utf8") as fh:
            fh.write(
                """
            [DEFAULT]
            foo = bar
            path1 = /tmp/mypath
            """
            )
        d = get_config(fn)
        assert d["foo"] == "bar"
        assert d["path1"] == "/tmp/mypath"
