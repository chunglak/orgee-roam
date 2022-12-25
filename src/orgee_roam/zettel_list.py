from __future__ import annotations  # PEP 585

import logging

from orgee.orgnode import OrgNode
from orgee.util import clean_text, escape_url

from .zettelkasten import ZettelKasten
from .zettel import Zettel


class ZettelList:
    def __init__(self, zk: ZettelKasten | None = None) -> None:
        self.zk = zk if zk else ZettelKasten()

    def make_list(
        self,
        zettels: list[Zettel],
        title: str,
        add_info_func=None,
        filename: str | None = None,
        zid: str | None = None,
        overwrite=False,
        exclude_from_roam: bool = False,
        update_cache: bool = True,
    ):
        if exclude_from_roam:
            properties = [("ROAM_EXCLUDE", "t")]
            update_cache = False
        else:
            properties = None
        root_zettel = self.zk.create_zettel(
            title=f"{title} ({len(zettels)} zettels)",
            properties=properties,
            body=[""],
            filename=filename,
            zid=zid,
            overwrite=overwrite,
            update_cache=False,
        )
        root = root_zettel.orgnode()
        for zettel in zettels:
            node = make_zettel_org_heading(zettel, add_info_func=add_info_func)
            root.add_child(node)
        root.dump(root_zettel.filename)
        self.zk.update_cache(update_cache)
        logging.info("Saved %d links to %s", len(zettels), root_zettel.filename)


def make_zettel_org_heading(
    zettel: Zettel, use_id=True, add_info_func=None, add_file_url=False
) -> OrgNode:
    node = OrgNode()
    if use_id:
        url = f"id:{zettel.uuid}"
    else:
        url = escape_url("file:%s::%d" % (zettel.filename, zettel.lineno))
    title = "[[%s][%s]]" % (url, clean_text(zettel.title))
    if aliases := zettel.aliases:
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
