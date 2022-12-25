from __future__ import annotations

import datetime

from .zettelkasten import Zettelkasten
from .finder import ZettelFinder
from .zettel import Zettel


def make_finder_files():
    # def add_info_func(z: Zettel) -> str:
    #     ts = z.updated_ts
    #     if ts:
    #         return datetime.datetime.fromtimestamp(ts).strftime(
    #             "(%a %d %b %Y, %H:%M:%S)"
    #         )
    #     else:
    #         return ""
    def add_info_func(z: Zettel) -> str:
        uts = z.updated_ts
        cts = z.creation_ts()
        return "(%s | /%s/)" % (
            datetime.datetime.fromtimestamp(uts).strftime("%a %d %b %Y, %H:%M")
            if uts
            else "–",
            datetime.datetime.fromtimestamp(cts).strftime("%d %b %y") if cts else "–",
        )

    zk = Zettelkasten(auto_update=True)
    zettels = sorted(zk.zettels, key=lambda z: z.updated_ts, reverse=True)
    zf = ZettelFinder(zettels=zettels)
    zf.make_finder_file(
        fn="zettel-finder.org",
        title="Nodes by updated timestamp",
        add_info_func=add_info_func,
    )
    # zf.make_links_file(fn="zettel-finder.org")
    zettels = restrict_zettels(zettels)
    zf = ZettelFinder(zettels=zettels)
    zf.make_finder_file(
        fn="zettel-finder-restricted.org",
        title="Restricted nodes by updated timestamp",
        add_info_func=add_info_func,
    )
    # zf.make_links_file(fn="zettel-finder-restricted.org")


def make_finder_by_creation_ts():
    def add_info_func(z: Zettel) -> str:
        ts = z.creation_ts()
        if ts:
            return datetime.datetime.fromtimestamp(ts).strftime("(%a %d %b %Y, %H:%M)")
        else:
            return ""

    zk = Zettelkasten(auto_update=True)
    zettels = sorted(zk.zettels, key=lambda z: z.creation_ts(), reverse=True)
    zf = ZettelFinder(zettels=zettels)
    zf.make_finder_file(
        fn="zettel-finder-by-ts.org",
        title="Nodes by creation timestamp",
        add_info_func=add_info_func,
    )
    zettels = restrict_zettels(zettels)
    zf = ZettelFinder(zettels=zettels)
    zf.make_finder_file(
        fn="zettel-finder-by-ts-restricted.org",
        title="Restricted nodes by creation timestamp",
        add_info_func=add_info_func,
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
