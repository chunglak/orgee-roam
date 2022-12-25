from __future__ import annotations  # PEP 585

import datetime
from typing import ValuesView

from orgee.orgnode import OrgNode

from .config import get_config
from .zettelkasten_cache import ZettelkastenCache
from .zettel import Zettel
from .create_zettel import create_zettel


class ZettelKasten:
    def __init__(
        self, config_file: str | None = None, update_cache: bool = True
    ):
        self.config, _ = get_config(fn=config_file)
        self.root = self.config["zettelkasten_root"]
        self.cache = ZettelkastenCache(
            zettelkasten_root=self.root,
            cache_fn=self.config["roam_cache"],
            update_cache=update_cache,
        )

    def zettels(self, update_cache: bool = True) -> ValuesView[Zettel]:
        self.update_cache(update_cache)
        return self.cache.zettels

    def update_cache(self, update_cache: bool = True):
        if update_cache:
            self.cache.update_cache()

    def create_zettel(
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
        update_cache: bool = True,
    ) -> Zettel:
        zettel = create_zettel(
            zk_root=self.root,
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
        )
        self.update_cache(update_cache)
        return zettel
