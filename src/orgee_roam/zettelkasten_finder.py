from __future__ import annotations  # PEP 585

import datetime

from .zettel import Zettel
from .zettel_list import ZettelList


class ZettelFinder:
    def __init__(self, zl: ZettelList | None = None) -> None:
        self.zl = zl if zl else ZettelList()
        self.zk = self.zl.zk

    def make_finder_files(self):
        def add_info_func(z: Zettel) -> str:
            uts = z.updated_ts
            cts = z.creation_ts()
            return "(%s | /%s/)" % (
                datetime.datetime.fromtimestamp(uts).strftime(
                    "%a %d %b %Y, %H:%M"
                )
                if uts
                else "–",
                datetime.datetime.fromtimestamp(cts).strftime("%d %b %y")
                if cts
                else "–",
            )

        zettels = sorted(
            self.zk.zettels(update_cache=False),
            key=lambda z: z.updated_ts,
            reverse=True,
        )
        self.zl.make_list(
            zettels=zettels,
            title="Nodes by updated timestamp",
            add_info_func=add_info_func,
            filename="zettel-finder-new.org",
            overwrite=True,
            exclude_from_roam=True,
        )
        zettels = restrict_zettels(zettels)
        self.zl.make_list(
            zettels=zettels,
            title="Restricted nodes by updated timestamp",
            add_info_func=add_info_func,
            filename="zettel-finder-restricted-new.org",
            overwrite=True,
            exclude_from_roam=True,
        )
        # zf.make_links_file(fn="zettel-finder-restricted.org")

    def make_finder_by_creation_ts(self):
        def add_info_func(z: Zettel) -> str:
            ts = z.creation_ts()
            if ts:
                return datetime.datetime.fromtimestamp(ts).strftime(
                    "(%a %d %b %Y, %H:%M)"
                )
            else:
                return ""

        zettels = sorted(
            self.zk.zettels(update_cache=False),
            key=lambda z: z.creation_ts(),
            reverse=True,
        )
        self.zl.make_list(
            zettels=zettels,
            title="Nodes by creation timestamp",
            add_info_func=add_info_func,
            filename="zettel-finder-by-ts-new.org",
            overwrite=True,
            exclude_from_roam=True,
        )
        zettels = restrict_zettels(zettels)
        self.zl.make_list(
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
