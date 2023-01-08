from __future__ import annotations  # PEP 585

import logging
import re
from typing import TYPE_CHECKING

from orgee.parse_org import parse_org_document

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten, Zettel


def normalize_zettel_links(zettel: Zettel, zk: ZettelKasten):
    def find_id(link: str) -> tuple[str, str]:
        m = re.match(r"\[\[id:(.+?)\]\[(.+?)\]\]", link)
        return m.groups()  # type:ignore

    node = zettel.orgnode
    if not node.is_root():
        raise Exception("Normalization of links only supported for root nodes!")
    zas = node.dumps()
    links = re.findall(r"\[\[id:.+?\]\[.+?\]\]", zas)
    dic = {find_id(link): link for link in links}
    n = 0
    for tu, link in dic.items():
        zid, otitle = tu
        z = zk[zid]
        if otitle != z.title:
            new_link = f"[[id:{zid}][{z.title}]]"
            zas = zas.replace(link, new_link)
            print(f"{link} → {new_link}")
            n += 1
    if n:
        zettel.orgnode = parse_org_document(zas)
        zettel.save()
        logging.info(
            "Normalized %d link%s in %s", n, "s" if n > 1 else "", zettel.title
        )
