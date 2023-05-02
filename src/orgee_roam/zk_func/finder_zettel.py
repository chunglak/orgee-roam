from __future__ import annotations  # PEP 585

import datetime
from typing import TYPE_CHECKING

from orgee.orgnode import OrgNode

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten, Zettel


def make_finder_files(zk: ZettelKasten, exclude_auto: bool = True):
    def heading(z: Zettel) -> OrgNode:
        node = z.org_heading(add_olp=True, add_aliases=True)
        uts = z.updated_ts
        cts = z.creation_ts()
        ts1 = (
            datetime.datetime.fromtimestamp(uts).strftime(
                # "%a %d %b %Y, %H:%M"
                "%Y-%m-%d %H:%M"
            )
            if uts
            else "–"
        )
        ts2 = (
            datetime.datetime.fromtimestamp(cts).strftime("%d %b %y")
            if cts
            else "–"
        )
        node.title = f"={ts1}= {node.title} /{ts2}/"
        return node

    zettels = sorted(
        zk.zettels,
        key=lambda z: z.updated_ts,
        reverse=True,
    )
    if exclude_auto:
        zettels = [z for z in zettels if "auto" not in z.tags]
    zk.make_list_zettel(
        zettels=zettels,
        title="Nodes by updated timestamp",
        tags={"auto"},
        headings_dic={z.uuid: heading(z) for z in zettels},
        filename="zettel-finder.org",
        overwrite=True,
        exclude_from_roam=True,
    )
    zettels = restrict_zettels(zettels)
    zk.make_list_zettel(
        zettels=zettels,
        title="Restricted nodes by updated timestamp",
        tags={"auto"},
        headings_dic={z.uuid: heading(z) for z in zettels},
        filename="zettel-finder-restricted.org",
        overwrite=True,
        exclude_from_roam=True,
    )


def make_finder_files_by_creation_ts(
    zk: ZettelKasten, exclude_auto: bool = True
):
    def heading(z: Zettel) -> OrgNode:
        node = z.org_heading(add_olp=True, add_aliases=True)
        ts = z.creation_ts()
        if ts:
            tss = datetime.datetime.fromtimestamp(ts).strftime(
                "%a %d %b %Y, %H:%M"
            )
            node.title = f"={tss}= {node.title}"
        return node

    zettels = sorted(
        zk.zettels,
        key=lambda z: z.creation_ts(),
        reverse=True,
    )
    if exclude_auto:
        zettels = [z for z in zettels if "auto" not in z.tags]
    zk.make_list_zettel(
        zettels=zettels,
        title="Nodes by creation timestamp",
        tags={"auto"},
        headings_dic={z.uuid: heading(z) for z in zettels},
        filename="zettel-finder-by-ts.org",
        overwrite=True,
        exclude_from_roam=True,
    )
    zettels = restrict_zettels(zettels)
    zk.make_list_zettel(
        zettels=zettels,
        title="Restricted nodes by creation timestamp",
        tags={"auto"},
        headings_dic={z.uuid: heading(z) for z in zettels},
        filename="zettel-finder-by-ts-restricted.org",
        overwrite=True,
        exclude_from_roam=True,
    )


def restrict_zettels(zettels: list[Zettel]) -> list[Zettel]:
    return [z for z in zettels if z.is_restricted()]
