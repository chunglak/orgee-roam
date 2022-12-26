from __future__ import annotations  # PEP 585

import datetime

from ..zettel import Zettel
from ..zettelkasten import ZettelKasten

from .list_zettel import make_list_zettel


def make_finder_files(zk: ZettelKasten):
    def add_info_func(z: Zettel) -> str:
        uts = z.updated_ts
        cts = z.creation_ts()
        return "(%s | /%s/)" % (
            datetime.datetime.fromtimestamp(uts).strftime("%a %d %b %Y, %H:%M")
            if uts
            else "–",
            datetime.datetime.fromtimestamp(cts).strftime("%d %b %y")
            if cts
            else "–",
        )

    zettels = sorted(
        zk.zettels,
        key=lambda z: z.updated_ts,
        reverse=True,
    )
    make_list_zettel(
        zk=zk,
        zettels=zettels,
        title="Nodes by updated timestamp",
        add_info_func=add_info_func,
        filename="zettel-finder-new.org",
        overwrite=True,
        exclude_from_roam=True,
    )
    zettels = restrict_zettels(zettels)
    make_list_zettel(
        zk=zk,
        zettels=zettels,
        title="Restricted nodes by updated timestamp",
        add_info_func=add_info_func,
        filename="zettel-finder-restricted-new.org",
        overwrite=True,
        exclude_from_roam=True,
    )
    # zf.make_links_file(fn="zettel-finder-restricted.org")


def make_finder_files_by_creation_ts(zk: ZettelKasten):
    def add_info_func(z: Zettel) -> str:
        ts = z.creation_ts()
        if ts:
            return datetime.datetime.fromtimestamp(ts).strftime(
                "(%a %d %b %Y, %H:%M)"
            )
        else:
            return ""

    zettels = sorted(
        zk.zettels,
        key=lambda z: z.creation_ts(),
        reverse=True,
    )
    make_list_zettel(
        zk=zk,
        zettels=zettels,
        title="Nodes by creation timestamp",
        add_info_func=add_info_func,
        filename="zettel-finder-by-ts-new.org",
        overwrite=True,
        exclude_from_roam=True,
    )
    zettels = restrict_zettels(zettels)
    make_list_zettel(
        zk=zk,
        zettels=zettels,
        title="Restricted nodes by creation timestamp",
        add_info_func=add_info_func,
        filename="zettel-finder-by-ts-restricted-new.org",
        overwrite=True,
        exclude_from_roam=True,
    )


def restrict_zettels(zettels: list[Zettel]) -> list[Zettel]:
    exclude_tags = {
        "album",
        "article",
        "band",
        "book",
        "character",
        "country",
        "movie",
        "painting",
        "paper",
        "person",
        "song",
        "stock",
        "video",
        "webclip",
        "youtube",
    }
    return [z for z in zettels if not exclude_tags & z.all_tags]
