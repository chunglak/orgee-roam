from __future__ import annotations  # PEP 585

import logging
from typing import TYPE_CHECKING

from orgee import OrgNode, OrgProperties
from orgee.util import escape_url, clean_text

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten, Zettel


def make_list_zettel(
    zk: ZettelKasten,
    zettels: list[Zettel],
    title: str,
    add_info_func=None,
    filename: str | None = None,
    zid: str | None = None,
    overwrite=False,
    exclude_from_roam: bool = False,
    use_id: bool = True,
    add_file_url: bool = False,
    add_aliases: bool = True,
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
        overwrite=overwrite,
        save_cache=save_cache,
    )
    root = root_zettel.orgnode
    for zettel in zettels:
        node = make_zettel_org_heading(
            zettel,
            use_id=use_id,
            add_info_func=add_info_func,
            add_file_url=add_file_url,
            add_aliases=add_aliases,
        )
        root.add_child(node)
    root.dump(root_zettel.filename)
    logging.info("Saved %d links to %s", len(zettels), root_zettel.filename)
    return root_zettel


def make_zettel_org_heading(
    zettel: Zettel,
    use_id=True,
    add_info_func=None,
    add_file_url=False,
    add_aliases: bool = True,
) -> OrgNode:
    node = OrgNode()
    if use_id:
        url = f"id:{zettel.uuid}"
    else:
        url = escape_url("file:%s::%d" % (zettel.filename, zettel.lineno))
    title = "[[%s][%s]]" % (url, clean_text(zettel.title))
    if add_aliases and (aliases := zettel.aliases):
        # title += " | %s" % " | ".join(aliases)
        title += " | %s" % " | ".join(
            f"[[{url}][{alias}]]" for alias in aliases
        )
    if len(zettel.olp) > 1:
        title = " > ".join(map(clean_text, zettel.olp[:-1])) + " > " + title
    if add_info_func:
        s = add_info_func(zettel)
        if s:
            title += " " + s
    if add_file_url:
        furl = escape_url("file:%s::%d" % (zettel.filename, zettel.lineno))
        title = f"([[{furl}][🔗]]) " + title
    node.title = title
    node.tags = zettel.all_tags
    return node
