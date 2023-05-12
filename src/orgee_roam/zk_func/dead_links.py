from __future__ import annotations  # PEP 585

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten, Zettel


def check_dead_links(
    zk: ZettelKasten,
) -> list[tuple[Zettel, list[tuple[str, str]]]]:
    def check(zettel: Zettel) -> list[tuple[str, str]]:
        node = zettel.orgnode
        if not node.is_root():
            return []
        if "auto" in node.tags:
            return []
        s = node.dumps()
        m = re.findall(r"\[\[id:(.+?)\]\[(.+?)\]\]", s)
        if m:
            return [(zid, title) for zid, title in m if zid not in zk]
        else:
            return []

    rez: list = []
    for zettel in zk.zettels:
        if ls := check(zettel):
            rez.append((zettel, ls))
    return rez
