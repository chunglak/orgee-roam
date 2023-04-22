from __future__ import annotations  # PEP 585

import logging
from typing import TYPE_CHECKING

from orgee import OrgNode, OrgProperties

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten, Zettel


def make_list_zettel(
    zk: ZettelKasten,
    zettels: list[Zettel],
    title: str,
    tags: set[str] | None = None,
    headings_dic: dict[str, OrgNode] | None = None,
    filename: str | None = None,
    zid: str | None = None,
    overwrite=False,
    exclude_from_roam: bool = False,
    add_tags: bool = True,
    add_aliases: bool = True,
    add_olp: bool = True,
    todo: str | None = None,
    save_cache: bool = True,
) -> Zettel:
    if exclude_from_roam:
        properties = OrgProperties.from_raw([("ROAM_EXCLUDE", "t")])
    else:
        properties = None
    root_zettel = zk.make_zettel(
        title=f"{title} ({len(zettels)} zettels)",
        properties=properties,
        body=[""],
        filename=filename,
        zid=zid,
        tags=tags,
        overwrite=overwrite,
        save_cache=save_cache,
    )
    root = root_zettel.orgnode
    for zettel in zettels:
        if headings_dic and (n := headings_dic.get(zettel.uuid)):
            node = n
        else:
            node = zettel.org_heading(
                add_tags=add_tags,
                add_aliases=add_aliases,
                add_olp=add_olp,
                todo=todo,
            )
        root.add_child(node)
    root.dump(root_zettel.filename)
    logging.info("Saved %d links to %s", len(zettels), root_zettel.filename)
    return root_zettel
