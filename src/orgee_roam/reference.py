from __future__ import annotations  # PEP 585

import re

from .zettel import Zettel
from .zettelkasten import Zettelkasten


def references_dict(zk: Zettelkasten) -> dict[str, list[Zettel]]:
    dic: dict = {}
    for zettel in zk.zettels:
        s = zettel.orgnode().dumps()
        uuids = re.findall(r"\[\[id:(.+?)\]\[.+?\]\]", s)
        if uuids:
            for uuid in uuids:
                dic.setdefault(uuid, []).append(zettel)
    return dic


def references_dict2(zk: Zettelkasten) -> dict[str, list[Zettel]]:
    dic: dict = {}
    for zettel in zk.zettels:
        s = zettel.orgnode().dumps()
        uuids = re.findall(r"\[\[id:(.+?)\]\[.+?\]\]", s)
        if uuids:
            for uuid in uuids:
                dic.setdefault(uuid, []).append(zettel)
    return dic
