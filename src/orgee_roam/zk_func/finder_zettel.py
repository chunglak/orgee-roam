from __future__ import annotations  # PEP 585

import datetime
from typing import TYPE_CHECKING

from orgee.orgnode import OrgNode

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten, Zettel


def make_finder_files(zk: ZettelKasten):
    def heading(z: Zettel) -> OrgNode:
        s = z.org_link()
        uts = z.updated_ts
        cts = z.creation_ts()
        s += " (%s | /%s/)" % (
            datetime.datetime.fromtimestamp(uts).strftime("%a %d %b %Y, %H:%M")
            if uts
            else "–",
            datetime.datetime.fromtimestamp(cts).strftime("%d %b %y")
            if cts
            else "–",
        )
        return z.org_heading(heading=s, add_olp=True)

    zettels = sorted(
        zk.zettels,
        key=lambda z: z.updated_ts,
        reverse=True,
    )
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


def make_finder_files_by_creation_ts(zk: ZettelKasten):
    def heading(z: Zettel) -> OrgNode:
        s = z.org_link()
        ts = z.creation_ts()
        if ts:
            s += " " + datetime.datetime.fromtimestamp(ts).strftime(
                "(%a %d %b %Y, %H:%M)"
            )
        return z.org_heading(heading=s, add_olp=True)

    zettels = sorted(
        zk.zettels,
        key=lambda z: z.creation_ts(),
        reverse=True,
    )
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
