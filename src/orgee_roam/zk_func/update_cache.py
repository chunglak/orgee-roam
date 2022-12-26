from __future__ import annotations  # PEP 585

import logging
import os
from typing import TYPE_CHECKING, Iterator

from orgee.util import is_org_file

from ..zettel import Zettel

if TYPE_CHECKING:
    from orgee_roam import ZettelKasten

VERBOSE_LIMIT = 100


def update_cache(zk: ZettelKasten) -> int:
    def org_files() -> Iterator[str]:
        for root, _, files in os.walk(zk.root):
            for fn in files:
                if not is_org_file(fn):
                    continue
                yield os.path.join(root, fn)

    def file_zettels() -> dict[str, list[Zettel]]:
        dic: dict = {}
        for zettel in zk.zettels:
            dic.setdefault(zettel.filename, []).append(zettel)
        return dic

    if not zk.is_json_outdated():
        return 0
    all_files = set(org_files())
    existing_files = {zettel.filename for zettel in zk.zettels}
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
                    logging.info("Removing «%s»", zk.dic[zettel.uuid].olp_str())
                del zk.dic[zettel.uuid]
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
                    logging.info("Removing %s", zk.dic[uuid].olp_str())
                del zk.dic[uuid]
                changes += 1
            for zettel in zettels2:
                uuid = zettel.uuid
                if zettel0 := zk.dic.get(uuid):
                    if zettel.zettel_hash != zettel0.zettel_hash:
                        olp0, olp = zettel0.olp_str(), zettel.olp_str()
                        if olp != olp0:
                            if not be_quiet:
                                logging.info("Updated «%s» → «%s»", olp0, olp)
                        else:
                            if not be_quiet:
                                logging.info("Updated «%s»", olp)
                    else:
                        zettel.updated_ts = zettel0.updated_ts
                else:
                    if not be_quiet:
                        logging.info("Adding «%s»", zettel.olp_str())

                zettel.lastchecked_ts = uts
                zk.dic[uuid] = zettel
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
                if uuid in zk.dic:
                    print(uuid)
                    print(zettel)
                    print(zk.dic[uuid])
                    raise Exception("Duplicate ID!")
                zk.dic[uuid] = zettel
                changes += 1
                if not be_quiet:
                    logging.info("Adding «%s»", zettel.olp_str())

    if changes:
        logging.info("%d node%s changed", changes, "s" if changes > 1 else "")
        # Reset dics_by_prop memoization
        zk._dics_by_prop = {}  # pylint: disable=protected-access
    else:
        logging.info("No node changed")
    zk.save_json()
    return changes
