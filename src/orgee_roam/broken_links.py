from __future__ import annotations  # PEP 585

import multiprocessing
import re

from .zettel import Zettel
from .zettelkasten import Zettelkasten


def find_broken_links(
    zk: Zettelkasten, nth=4
) -> list[tuple[Zettel, list[tuple[str, str]]]]:
    with multiprocessing.Pool(nth) as pool:
        rs = pool.map(func, zk.zettels)
    rez = []
    for r in rs:
        if not r:
            continue
        z, tus = r
        tus = [tu for tu in tus if tu[0] not in zk]
        if tus:
            rez.append((z, tus))
    return rez


def func(z: Zettel) -> tuple[Zettel, list[tuple[str, str]]] | None:
    recs = re.findall(r"\[\[id:(.+?)\]\[(.+?)\]\]", z.orgnode().dumps())
    # recs = [(uuid, title) for uuid, title in recs if uuid not in zk]
    return (z, recs) if recs else None


