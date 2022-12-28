from __future__ import annotations  # PEP 585

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten, Zettel


class Zettels:
    def __init__(self, zk: ZettelKasten, zettels: list[Zettel] | None = None):
        self.zk = zk
        if zettels:
            # Make sure all the zettels belong to the zettelkasten
            assert {z.uuid for z in zettels} <= set(zk)
            self.zdic = {z.uuid: z for z in zettels}
        else:
            self.zdic = {}
