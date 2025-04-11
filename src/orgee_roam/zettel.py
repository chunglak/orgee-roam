from __future__ import annotations  # PEP 585

import datetime
import os.path
import time
from dataclasses import dataclass, field

from orgee import OrgNode, remove_org_markup, OrgProperties
from orgee.util import clean_text

NOT_RESTRICTED_TAGS = {
    "album",
    "article",
    "auto",
    "band",
    "book",
    "character",
    "country",
    "movie",
    "painting",
    "paper",
    "person",
    "single",
    "song",
    "stock",
    "video",
    "webclip",
    "youtube",
}


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
            tags=set(rec["tags"]),
            all_tags=set(rec["all_tags"]),
            aliases=set(rec["aliases"]),
            olp=rec["olp"],
            properties=OrgProperties.from_rec(rec=rec["properties"]),
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
            "properties": self.properties.to_rec(),
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
                    # pylint: disable=broad-exception-raised
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
        return 0

    @property
    def url(self) -> str:
        return f"id:{self.uuid}"

    def org_link(self, title: str | None = None) -> str:
        return f"[[{self.url}][{title if title else self.title}]]"

    def org_heading(
        self,
        heading: str | None = None,
        title: str | None = None,
        add_all_tags: bool = True,
        add_tags: bool = True,
        add_aliases: bool = False,
        add_olp: bool = False,
        todo: str | None = None,
    ) -> OrgNode:
        heading = heading if heading else self.org_link(title=title)
        if add_aliases and (aliases := self.aliases):
            heading += " | %s" % " | ".join(
                f"[[{self.url}][{alias}]]" for alias in aliases
            )
        if add_olp and len(self.olp) > 1:
            heading = (
                " > ".join(map(clean_text, self.olp[:-1])) + " > " + heading
            )
        node = OrgNode(title=heading)
        if add_all_tags:
            node.tags = self.all_tags.copy()
        elif add_tags:
            node.tags = self.tags.copy()
        if todo:
            node.todo = todo
        return node

    def is_restricted(self) -> bool:
        return not NOT_RESTRICTED_TAGS & self.all_tags

    def is_excluded(self) -> bool:
        return bool(self.properties.first_property_by_key("ROAM_EXCLUDE"))
