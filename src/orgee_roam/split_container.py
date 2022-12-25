from __future__ import annotations

import datetime
import logging

from orgee.orgnode import OrgNode

from .create_zettel import create_zettel
from .zettel import Zettel
from .zettelkasten import Zettelkasten


def split_zettel_container(zid: str, zk: Zettelkasten) -> list[Zettel]:
    def parse_child(node: OrgNode) -> Zettel | None:
        if "ignore" in node.tags:
            return None
        zid = node.first_prop_by_key("ID")
        if not zid:
            logging.error("Node %s has no ID!", node.olp_str())
        assert zid
        cts = node.first_prop_by_key("CREATED_TS")
        assert cts
        dt = datetime.datetime.fromtimestamp(float(cts))
        aliases = set(node.prop_by_key("ROAM_ALIASES", parse=True))
        if tags := node.all_tags():
            file_other_meta = [("FILETAGS", " ".join(tags))]
        else:
            file_other_meta = []
        zettel = create_zettel(
            title=node.title,
            aliases=aliases,
            properties=node.properties,
            body=node.body,
            children=node.children,
            file_other_meta=file_other_meta,
            dt=dt,
            zid=zid,
        )
        return zettel

    zettel = zk[zid]
    root = zettel.orgnode()
    zs = list(filter(None, map(parse_child, root.children)))
    root.children = []
    root.dump_root(zettel.filename)
    logging.info(
        "Split container into %d zettel%s", len(zs), "s" if len(zs) > 1 else ""
    )
    return zs
