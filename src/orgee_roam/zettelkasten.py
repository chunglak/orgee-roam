from __future__ import annotations  # PEP 585

import datetime
import json
import os, os.path  # pylint: disable=multiple-imports
from collections.abc import MutableMapping
from typing import ValuesView

from orgee import OrgNode, OrgProperties

from .const import ZK_CACHE, ZK_ROOT
from .zettel import Zettel
from .zk_func.update_cache import update_cache
from .zk_func.make_zettel import make_zettel
from .zk_func.list_zettel import make_list_zettel
from .zk_func.dead_links import check_dead_links
from .zk_func.finder_zettel import (
    make_finder_files,
    make_finder_files_by_creation_ts,
)

VERBOSE_LIMIT = 100


class ZettelKasten(MutableMapping):
    def __init__(
        self,
        cache_fn: str | None = None,
        root: str | None = None,
        update_cache: bool = True,  # pylint: disable=redefined-outer-name
    ):
        self.root = root if root else ZK_ROOT
        self.cache_fn = cache_fn if cache_fn else ZK_CACHE
        self.dic = self.load_json()
        self._dics_by_prop: dict[str, dict[str, Zettel]] = {}
        if update_cache:
            self.update_cache()

    def __getitem__(self, k: str) -> Zettel:
        return self.dic[k]

    def __setitem__(self, k: str, v: Zettel) -> None:
        self.dic[k] = v

    def __delitem__(self, k: str) -> None:
        del self.dic[k]

    def __iter__(self):
        return iter(self.dic)

    def __len__(self) -> int:
        return len(self.dic)

    @property
    def zettels(self) -> ValuesView[Zettel]:
        return self.dic.values()

    def save_json(self):
        recs = [
            zettel.to_rec()
            for zettel in sorted(
                self.zettels, key=lambda n: n.updated_ts, reverse=True
            )
        ]
        with open(self.cache_fn, "w", encoding="utf-8") as fh:
            json.dump(recs, fh, indent=2, ensure_ascii=False)

    def load_json(self) -> dict[str, Zettel]:
        if os.path.isfile(self.cache_fn):
            with open(self.cache_fn, "r", encoding="utf-8") as fh:
                recs = json.load(fh)
                zettels = map(Zettel.from_rec, recs)
                return {zettel.uuid: zettel for zettel in zettels}
        else:
            return {}

    def dict_by_prop(
        self, key: str, check_unique=True, use_memoized=True
    ) -> dict[str, Zettel]:
        """
        Return the zettelkasten indexed by a node property
        """
        if use_memoized and (dic := self._dics_by_prop.get(key)):
            return dic
        # Allow a zettel to have multiple props
        pairs = []
        for zettel in self.zettels:
            props = zettel.properties.property_by_key(key)
            for prop in props:
                pairs.append((str(prop), zettel))

        dic = dict(pairs)
        if len(dic) == len(pairs) or not check_unique:
            self._dics_by_prop[key] = dic
            return dic
        d: dict = {}
        for ca, z in pairs:
            d.setdefault(ca, []).append(z)
        for ca, zs in d.items():
            if len(zs) > 1:
                print(f"{ca}: {', '.join(str(z) for z in zs)}")
        # pylint: disable=broad-exception-raised
        raise Exception("Some props are in multiple zettels!")

    def is_json_outdated(self) -> bool:
        if os.path.isfile(self.cache_fn):
            return os.path.getmtime(self.cache_fn) < os.path.getmtime(self.root)
        return True

    def update_cache(self) -> int:
        return update_cache(zk=self)

    def make_zettel(
        self,
        title: str,
        aliases: set[str] | None = None,
        tags: set[str] | None = None,
        properties: OrgProperties | None = None,
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
        return make_zettel(
            zk=self,
            title=title,
            aliases=aliases,
            tags=tags,
            properties=properties,
            body=body,
            children=children,
            parent=parent,
            file_properties=file_properties,
            file_other_meta=file_other_meta,
            dt=dt,
            filename=filename,
            zid=zid,
            overwrite=overwrite,
            save_cache=save_cache,
        )

    def make_list_zettel(
        self,
        zettels: list[Zettel],
        title: str,
        tags: set[str] | None = None,
        headings_dic: dict[str, OrgNode] | None = None,
        filename: str | None = None,
        zid: str | None = None,
        overwrite=False,
        exclude_from_roam: bool = False,
        add_auto_tag: bool = True,
        add_tags: bool = True,
        add_aliases: bool = True,
        add_olp: bool = True,
        todo: str | None = None,
        save_cache: bool = True,
    ) -> Zettel:
        return make_list_zettel(
            zk=self,
            zettels=zettels,
            title=title,
            tags=tags,
            headings_dic=headings_dic,
            filename=filename,
            zid=zid,
            overwrite=overwrite,
            exclude_from_roam=exclude_from_roam,
            add_auto_tag=add_auto_tag,
            add_tags=add_tags,
            add_aliases=add_aliases,
            add_olp=add_olp,
            todo=todo,
            save_cache=save_cache,
        )

    def make_finder_files(self):
        make_finder_files(zk=self)

    def make_finder_files_by_creation_ts(self):
        make_finder_files_by_creation_ts(zk=self)

    def check_dead_links(self):
        return check_dead_links(self)
