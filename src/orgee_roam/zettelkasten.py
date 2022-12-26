from __future__ import annotations  # PEP 585

import datetime
import json
import os, os.path
from collections.abc import MutableMapping
from typing import ValuesView

from orgee.orgnode import OrgNode

from .const import ZK_CACHE, ZK_ROOT
from .zettel import Zettel
from .zk_func.update_cache import update_cache
from .zk_func.make_zettel import make_zettel
from .zk_func.list_zettel import make_list_zettel
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
            props = zettel.prop_by_key(key)
            for prop in props:
                pairs.append((prop, zettel))

        dic = dict(pairs)
        if len(dic) == len(pairs) or not check_unique:
            self._dics_by_prop[key] = dic
            return dic
        else:
            d: dict = {}
            for ca, z in pairs:
                d.setdefault(ca, []).append(z)
            for ca, zs in d.items():
                if len(zs) > 1:
                    print(f"{ca}: {', '.join(z.olp_str() for z in zs)}")
            raise Exception("Some props are in multiple zettels!")

    def is_json_outdated(self) -> bool:
        if os.path.isfile(self.cache_fn):
            return os.path.getmtime(self.cache_fn) < os.path.getmtime(self.root)
        else:
            return True

    def update_cache(self) -> int:
        return update_cache(zk=self)

    def make_zettel(
        self,
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
        add_info_func=None,
        filename: str | None = None,
        zid: str | None = None,
        overwrite=False,
        exclude_from_roam: bool = False,
        use_id: bool = True,
        add_file_url: bool = False,
        save_cache: bool = True,
    ) -> Zettel:
        return make_list_zettel(
            zk=self,
            zettels=zettels,
            title=title,
            add_info_func=add_info_func,
            filename=filename,
            zid=zid,
            overwrite=overwrite,
            exclude_from_roam=exclude_from_roam,
            use_id=use_id,
            add_file_url=add_file_url,
            save_cache=save_cache,
        )

    def make_finder_files(self):
        make_finder_files(zk=self)

    def make_finder_files_by_creation_ts(self):
        make_finder_files_by_creation_ts(zk=self)
