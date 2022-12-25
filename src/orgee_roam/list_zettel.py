from __future__ import annotations  # PEP 585

import logging

from .zettelkasten import Zettelkasten
from .zettel import Zettel
from .create_zettel import create_zettel
from .zettel_org_heading import make_zettel_org_heading


def make_list_zettel(
    zettels: list[Zettel],
    title: str,
    fn: str,
    zk: Zettelkasten | None = None,
    overwrite=True,
):
    if not zk:
        zk = Zettelkasten()
    root_zettel = create_zettel(
        title=f"{title} ({len(zettels)} zettels)",
        properties=[("ROAM_EXCLUDE", "t")],
        body=[""],
        filename=fn,
        overwrite=overwrite,
    )
    root = root_zettel.orgnode()
    for zettel in zettels:
        node = make_zettel_org_heading(zettel)
        root.add_child(node)
    root.dump(root_zettel.filename)
    logging.info("Saved %d links to %s", len(zettels), root_zettel.filename)
