from __future__ import annotations  # PEP 585

import datetime
import os.path
import time
from dataclasses import dataclass, field

from orgee import OrgNode, remove_org_markup, OrgProperties


@dataclass
class Zettel:
    uuid: str
    title: str
    filename: str
    updated_ts: float
    lastchecked_ts: float
    # Hash of the underlying OrgNode
    zettel_hash: str
    level: int
    lineno: int
    tags: set[str] = field(default_factory=set)
    all_tags: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)
    olp: list[str] = field(default_factory=list)
    properties: OrgProperties = field(default_factory=OrgProperties)
    _orgnode: OrgNode | None = None

    @staticmethod
    def from_rec(rec: dict) -> Zettel:
        return Zettel(
            uuid=rec["uuid"],
            title=rec["title"],
            filename=rec["filename"],
            updated_ts=rec["updated_ts"],
            lastchecked_ts=rec["lastchecked_ts"],
            zettel_hash=rec["zettel_hash"],
            level=rec["level"],
            lineno=rec["lineno"],
            tags=rec["tags"],
            all_tags=set(rec["all_tags"]),
            aliases=set(rec["aliases"]),
            olp=rec["olp"],
            properties=OrgProperties.from_raw(tus=rec["properties"]),
        )

    def to_rec(self) -> dict:
        rec = {
            "uuid": self.uuid,
            "title": self.title,
            "filename": self.filename,
            "updated_ts": self.updated_ts,
            "updated_dt": datetime.datetime.fromtimestamp(
                self.updated_ts
            ).isoformat(),
            "lastchecked_ts": self.lastchecked_ts,
            "zettel_hash": self.zettel_hash,
            "level": self.level,
            "lineno": self.lineno,
            "tags": list(self.tags),
            "all_tags": list(self.all_tags),
            "aliases": list(self.aliases),
            "olp": self.olp,
            "properties": self.properties.dump(),
        }
        return rec

    @staticmethod
    def from_org_file(fn: str) -> list[Zettel]:
        root = OrgNode.from_file(fn)
        zettels: list = []
        updated_ts = os.path.getmtime(fn)
        for node in root.recurse_nodes():
            if node.properties.first_property_by_key("ID"):
                zettel = Zettel.from_orgnode(
                    node=node, filename=fn, updated_ts=updated_ts
                )
                if zettel:
                    zettels.append(zettel)
        return zettels

    @staticmethod
    def from_orgnode(
        node: OrgNode, filename: str, updated_ts: float | None = None
    ) -> Zettel | None:
        uuid = node.properties.first_property_by_key("ID")
        if not updated_ts:
            updated_ts = time.time()
        zettel_hash = node.node_hash()
        zettel = Zettel(
            uuid=uuid,  # type:ignore
            title=node.title,
            filename=filename,
            updated_ts=updated_ts,
            lastchecked_ts=updated_ts,
            zettel_hash=zettel_hash,
            level=node.actual_level(),
            lineno=node.lineno,
            tags=node.tags,
            all_tags=node.all_tags(),
            aliases=set(
                node.properties.property_by_key("ROAM_ALIASES")  # type:ignore
            ),
            olp=node.olp(),
            properties=node.properties,
        )
        zettel.orgnode = node
        return zettel

    def __str__(self) -> str:
        return " → ".join(map(remove_org_markup, self.olp))

    @property
    def orgnode(self) -> OrgNode:
        if self._orgnode is None:
            # That's the case when zettel is built from rec
            # Normally the node is used to create the zettel and kept
            root = OrgNode.from_file(self.filename)
            assert root
            if self.level == 0:
                self._orgnode = root
            else:
                node = root.find_olp(self.olp[1:])
                if not node:
                    raise Exception(
                        f"Could not find node {self.olp} in {self.filename}"
                    )
                self._orgnode = node
        return self._orgnode

    @orgnode.setter
    def orgnode(self, node: OrgNode):
        self._orgnode = node

    def save(self):
        node = self.orgnode
        # Update node from zettel
        node.title = self.title
        node.tags = self.tags
        node.properties = self.properties
        node.properties.replace_property("ID", self.uuid)
        if self.aliases:
            node.properties.replace_property("ROAM_ALIASES", self.aliases)
        # Save file the node belongs to
        node.dump_root(self.filename)

    def creation_ts(self) -> float:
        if s := self.properties.first_property_by_key("CREATED_TS"):
            return float(s)
        else:
            return 0
