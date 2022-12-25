from __future__ import annotations  # PEP 585

import logging

from .zettelkasten import Zettelkasten


def rename_tag(
    zk: Zettelkasten, old_tag: str, new_tag: str, dry_run=True
) -> int:
    i = 0
    for zettel in zk.zettels:
        if old_tag in zettel.tags:
            if not dry_run:
                node = zettel.orgnode()
                node.tags.remove(old_tag)
                if new_tag:
                    node.tags.add(new_tag)
                node.dump_root(zettel.filename)
            logging.info(
                "Renamed «%s» to «%s» in %s", old_tag, new_tag, zettel.olp_str()
            )
            i += 1
    logging.info(
        "Renamed «%s» to «%s» in %d zettel%s",
        old_tag,
        new_tag,
        i,
        "s" if i > 1 else "",
    )
    return i
