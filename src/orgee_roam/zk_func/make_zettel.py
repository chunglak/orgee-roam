from __future__ import annotations  # PEP 585

import datetime
import logging
import os.path
import time
import uuid
from typing import TYPE_CHECKING

from slugify import slugify  # type:ignore

from orgee.orgnode import OrgNode
from orgee.util import dump_property
from kombini.safe_filename import safe_filename_no_diacritic

from ..zettel import Zettel

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten


def make_zettel(
    zk: ZettelKasten,
    title: str,
    aliases: set[str] | None = None,
    tags: set[str] | None = None,
    properties: list[tuple[str, str]] | None = None,
    body: list[str] | None = None,
    children: list[OrgNode] | None = None,
    parent: Zettel | None = None,
    file_properties: list[str] | None = None,
    file_other_meta: list[tuple[str, str]] | None = None,
    dt: datetime.datetime | None = None,
    filename: str | None = None,
    zid: str | None = None,
    overwrite: bool = False,
    save_cache: bool = True,
) -> Zettel:
    if not dt:
        dt = datetime.datetime.now()
    if not zid:
        zid = str(uuid.uuid4())

    node = OrgNode(title=title, is_root=not bool(parent))
    if properties:
        node.properties = properties
    node.replace_prop("ID", zid)
    node.replace_prop("CREATED_TS", str(int(dt.timestamp())))
    # node.properties.append(("ID", zid))
    # node.properties.append(("CREATED_TS", str(int(dt.timestamp()))))
    if aliases:
        node.replace_prop("ROAM_ALIASES", dump_property(list(aliases)))
    if tags:
        node.tags = tags
    if body:
        node.body = body
    if children:
        for child in children:
            node.add_child(child)

    if parent:
        if filename:
            raise Exception("Child node cannot set the parent filename")
        filename = parent.filename
        parent_node = parent.orgnode()
        parent_node.add_child(node)
        parent_node.dump_root(filename)
        logging.info("Added node %s to node %s", title, parent.olp_str())
    else:
        rm = node.root_meta
        assert rm
        rm.other_meta.append(
            (
                "CREATED",
                "%s %s"
                % (dt.strftime("%a %d %b %Y %H:%M"), dt.astimezone().tzinfo),
            )
        )
        if file_properties:
            rm.properties = file_properties
        if file_other_meta:
            rm.other_meta.extend(file_other_meta)
        if not filename:
            filename = mk_fn(s=title, dt=dt, root=zk.root)
        else:
            filename = os.path.join(zk.root, filename)
        if os.path.isfile(filename) and not overwrite:
            raise Exception(f"There is already a file named {filename}!")
        node.dump_root(filename)
        logging.info("Created file %s for node %s", filename, title)

    ts = time.time()
    zettel = Zettel(
        uuid=zid,
        title=title,
        filename=filename,
        updated_ts=ts,
        lastchecked_ts=ts,
        zettel_hash=node.node_hash(),
        level=node.actual_level(),
        lineno=1,
        tags=node.tags,
        aliases=aliases if aliases else set(),
        olp=node.olp(),
        properties=node.properties,
    )
    zk[zid] = zettel
    if save_cache:
        zk.save_json()
    return zettel


def mk_fn(s: str, dt: datetime.datetime, root: str) -> str:
    slug = slugify(s, max_length=50)
    s0 = f"{dt.strftime('%Y%m%d%H%M%S')}-{slug}"
    fn = safe_filename_no_diacritic(f"{s0}.org")
    i = 0
    # Make sure the file doesn't exist
    while True:
        ffn = os.path.join(root, fn)
        if not os.path.isfile(ffn):
            return ffn
        i += 1
        fn = safe_filename_no_diacritic(f"{s0}-{i}.org")
