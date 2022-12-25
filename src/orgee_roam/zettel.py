from __future__ import annotations  # PEP 585

import datetime
import logging
import os.path
import re
import time
from dataclasses import dataclass, field

from orgee.parse_org import parse_org_file
from orgee.orgnode import OrgNode
from orgee.util import prop_by_key, first_prop_by_key, clean_text


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
    properties: list[tuple[str, str]] = field(default_factory=list)

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
            properties=rec["properties"],
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
            "properties": self.properties,
        }
        return rec

    @staticmethod
    def from_org_file(fn: str) -> list[Zettel]:
        root = parse_org_file(fn)
        zettels: list = []
        updated_ts = os.path.getmtime(fn)
        for node in root.recurse_nodes():
            if node.prop_by_key("ID"):
                zettel = Zettel.from_orgnode(
                    node=node, filename=fn, updated_ts=updated_ts
                )
                if zettel:
                    zettels.append(zettel)
        return zettels

    @staticmethod
    def root_from_org_file(fn: str) -> Zettel | None:
        root = parse_org_file(fn)
        return Zettel.from_orgnode(
            root, filename=fn, updated_ts=os.path.getmtime(fn)
        )

    @staticmethod
    def from_orgnode(
        node: OrgNode, filename: str, updated_ts: float | None = None
    ) -> Zettel | None:
        xc = node.prop_by_key("ROAM_EXCLUDE", parse=True)
        if xc and xc[0] is True:
            return None

        uuid = node.prop_by_key("ID")[0]
        if not updated_ts:
            updated_ts = time.time()
        zettel_hash = node.node_hash()
        return Zettel(
            uuid=uuid,
            title=node.title,
            filename=filename,
            updated_ts=updated_ts,
            lastchecked_ts=updated_ts,
            zettel_hash=zettel_hash,
            level=node.actual_level(),
            lineno=node.lineno,
            tags=node.tags,
            all_tags=node.all_tags(),
            aliases=set(node.prop_by_key("ROAM_ALIASES", parse=True)),
            olp=node.olp(),
            properties=node.properties,
        )

    def olp_str(self) -> str:
        return " → ".join(map(clean_text, self.olp))

    def orgnode(self, root: OrgNode | None = None) -> OrgNode:
        if not root:
            root = parse_org_file(self.filename)
        assert root
        if self.level == 0:
            return root
        else:
            node = root.find_olp(self.olp[1:])
            if not node:
                raise Exception(
                    f"Could not find node {self.olp} in {self.filename}"
                )
            return node

    def prop_by_key(self, key: str, parse=True, case_insensitive=True) -> list:
        return prop_by_key(
            key=key,
            props=self.properties,
            parse=parse,
            case_insensitive=case_insensitive,
        )

    def first_prop_by_key(
        self, key: str, parse=True, case_insensitive=True
    ) -> str | None:
        return first_prop_by_key(
            key=key,
            props=self.properties,
            parse=parse,
            case_insensitive=case_insensitive,
        )

    def creation_ts(self, self_correct=True, verbose=True) -> float:
        def correct(ts: float):
            node.properties.append(("CREATED_TS", str(int(ts))))
            if rm := node.root_meta:
                if not rm.first_other_meta_by_key("CREATED"):
                    dt = datetime.datetime.fromtimestamp(ts)
                    rm.other_meta.append(
                        (
                            "CREATED",
                            "%s %s"
                            % (
                                dt.strftime("%a %d %b %Y %H:%M:%S"),
                                dt.astimezone().tzinfo,
                            ),
                        )
                    )
            node.dump_root(self.filename)
            # Update zettel properties
            self.properties = node.properties
            if verbose:
                logging.info("Added CREATED_TS prop to %s", self.olp_str())

        # Try the CREATED_TS property
        if s := self.first_prop_by_key("CREATED_TS"):
            return float(s)
        # Try the created fileprop
        node = self.orgnode()
        if rm := node.root_meta:
            if s := rm.first_other_meta_by_key("created", parse=False):
                if m := re.match(r".+\((\d+)\)", s):
                    ts = float(m.groups()[0])
                    if self_correct:
                        correct(ts)
                    return ts
        logging.warning("Zettel [%s] has no CREATED_TS!", self.olp_str())
        return 0
