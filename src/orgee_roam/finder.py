from __future__ import annotations

# import os.path

# from orgtools.util import clean_text
from .zettel import Zettel
from .create_zettel import create_zettel
from .zettel_org_heading import make_zettel_org_heading


class ZettelFinder:
    def __init__(self, zettels: list[Zettel]):
        self.zettels = zettels

    def filter(self, filter_func) -> ZettelFinder:
        return ZettelFinder(zettels=list(filter(filter_func, self.zettels)))

    def make_finder_file(self, fn: str, title: str, add_info_func=None):
        root_zettel = create_zettel(
            title=f"{title} ({len(self.zettels)})",
            properties=[("ROAM_EXCLUDE", "t")],
            body=[""],
            filename=fn,
            overwrite=True,
        )
        root = root_zettel.orgnode()
        for zettel in self.zettels:
            root.add_child(
                make_zettel_org_heading(
                    zettel,
                    use_id=True,
                    add_info_func=add_info_func,
                )
            )
        root.dump_root(root_zettel.filename)

    # def make_links_file(self, fn: str, title: str = None):
    #     root_zettel = create_zettel(
    #         title=title if title else f"Zettel Links ({len(self.zettels)} zettels)",
    #         body=[""],
    #         filename=fn,
    #         overwrite=True,
    #         root=os.path.expanduser("~/.emacs.d"),
    #     )
    #     body: list = []
    #     for zettel in self.zettels:
    #         body.append("")
    #         h = f"{zettel.olp_str()} #zz"
    #         if zettel.tags:
    #             h += " " + " ".join(f"#{tag}" for tag in sorted(zettel.tags))
    #         body.append(h)
    #         names = [zettel.title]
    #         if zettel.aliases:
    #             names.extend(zettel.aliases)
    #         url = f"id:{zettel.uuid}"
    #         for name in names:
    #             body.append(f"[[{url}][{clean_text(name)}]]")
    #     root = root_zettel.orgnode()
    #     root.body = body
    #     root.dump_root(root_zettel.filename)
