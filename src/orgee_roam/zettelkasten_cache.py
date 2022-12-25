from __future__ import annotations  # PEP 585

import json
import logging
import os, os.path
from collections.abc import MutableMapping
from typing import Iterator, ValuesView

from orgee.util import is_org_file

from orgee_roam.zettel import Zettel

VERBOSE_LIMIT = 100


class ZettelkastenCache(MutableMapping):
    def __init__(
        self, zettelkasten_root: str, cache_fn: str, update_cache: bool = True
    ):
        self.zettelkasten_root = zettelkasten_root
        self.cache_fn = cache_fn
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

    def is_json_outdated(self) -> bool:
        if os.path.isfile(self.cache_fn):
            return os.path.getmtime(self.cache_fn) < os.path.getmtime(
                self.zettelkasten_root
            )
        else:
            return True

    def update_cache(self, force=False) -> int:
        def org_files() -> Iterator[str]:
            for root, _, files in os.walk(self.zettelkasten_root):
                for fn in files:
                    if not is_org_file(fn):
                        continue
                    yield os.path.join(root, fn)

        def file_zettels() -> dict[str, list[Zettel]]:
            dic: dict = {}
            for zettel in self.zettels:
                dic.setdefault(zettel.filename, []).append(zettel)
            return dic

        if not force and not self.is_json_outdated():
            return 0
        all_files = set(org_files())
        existing_files = {zettel.filename for zettel in self.zettels}
        deleted_files = existing_files - all_files
        fndic = file_zettels()
        changes = 0

        if deleted_files:
            be_quiet = len(deleted_files) > VERBOSE_LIMIT
            # print(f"Be quiet deleted={be_quiet}")
            if be_quiet:
                logging.info(
                    "Deleting %d file%s",
                    len(deleted_files),
                    "s" if len(deleted_files) > 1 else "",
                )
            for fn in deleted_files:
                for zettel in fndic[fn]:
                    if not be_quiet:
                        logging.info(
                            "Removing «%s»", self.dic[zettel.uuid].olp_str()
                        )
                    del self.dic[zettel.uuid]
                    changes += 1
                del fndic[fn]

        fns = [
            fn
            for fn, zettels in fndic.items()
            if os.path.getmtime(fn)
            > max(zettel.lastchecked_ts for zettel in zettels)
        ]
        if fns:
            be_quiet = len(fns) > VERBOSE_LIMIT
            # print(f"Be quiet changed={be_quiet}")
            if be_quiet:
                logging.info(
                    "Updating %d file%s", len(fns), "s" if len(fns) > 1 else ""
                )
            for fn in fns:
                uts = os.path.getmtime(fn)
                zettels = fndic[fn]
                zettels2 = Zettel.from_org_file(fn)
                uuids = {zettel.uuid for zettel in zettels}
                uuids2 = {zettel.uuid for zettel in zettels2}
                for uuid in uuids - uuids2:
                    if not be_quiet:
                        logging.info("Removing %s", self.dic[uuid].olp_str())
                    del self.dic[uuid]
                    changes += 1
                for zettel in zettels2:
                    uuid = zettel.uuid
                    if zettel0 := self.dic.get(uuid):
                        if zettel.zettel_hash != zettel0.zettel_hash:
                            olp0, olp = zettel0.olp_str(), zettel.olp_str()
                            if olp != olp0:
                                if not be_quiet:
                                    logging.info(
                                        "Updated «%s» → «%s»", olp0, olp
                                    )
                            else:
                                if not be_quiet:
                                    logging.info("Updated «%s»", olp)
                        else:
                            zettel.updated_ts = zettel0.updated_ts
                    else:
                        if not be_quiet:
                            logging.info("Adding «%s»", zettel.olp_str())

                    zettel.lastchecked_ts = uts
                    self.dic[uuid] = zettel
                    changes += 1

        new_files = all_files - existing_files
        if new_files:
            be_quiet = len(new_files) > VERBOSE_LIMIT
            # print(f"Be quiet new={be_quiet}")
            if be_quiet:
                logging.info(
                    "Adding %d new file%s",
                    len(new_files),
                    "s" if len(new_files) > 1 else "",
                )
            for fn in new_files:
                zettels = Zettel.from_org_file(fn)
                for zettel in zettels:
                    uuid = zettel.uuid
                    if uuid in self.dic:
                        print(uuid)
                        print(zettel)
                        print(self.dic[uuid])
                        raise Exception("Duplicate ID!")
                    self.dic[uuid] = zettel
                    changes += 1
                    if not be_quiet:
                        logging.info("Adding «%s»", zettel.olp_str())

        if changes:
            logging.info(
                "%d node%s changed", changes, "s" if changes > 1 else ""
            )
            # Reset dics_by_prop memoization
            self._dics_by_prop = {}
        else:
            logging.info("No node changed")
        self.save_json()
        return changes

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
        self, key: str, check_unique=True, use_memoized=True, update_cache=True
    ) -> dict[str, Zettel]:
        """
        Return the zettelkasten indexed by a node property
        """
        if update_cache:
            self.update_cache()
        if use_memoized and (dic := self._dics_by_prop.get(key)):
            return dic
        # pairs = [
        #     (prop, zettel)
        #     for zettel in self.zettels
        #     if (prop := zettel.first_prop_by_key(key))
        # ]
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
