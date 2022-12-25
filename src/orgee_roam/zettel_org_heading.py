from orgee.orgnode import OrgNode
from orgee.util import clean_text, escape_url

from .zettel import Zettel


def make_zettel_org_heading(
    zettel: Zettel, use_id: bool = True, add_info_func=None, add_file_url=False
) -> OrgNode:
    node = OrgNode()
    if use_id:
        url = f"id:{zettel.uuid}"
    else:
        url = escape_url("file:%s::%d" % (zettel.filename, zettel.lineno))
    title = "[[%s][%s]]" % (url, clean_text(zettel.title))
    if aliases := zettel.aliases:
        # title += " | %s" % " | ".join(aliases)
        title += " | %s" % " | ".join(
            f"[[{url}][{alias}]]" for alias in aliases
        )
    if len(zettel.olp) > 1:
        title = " > ".join(map(clean_text, zettel.olp[:-1])) + " > " + title
    if add_info_func:
        s = add_info_func(zettel)
        if s:
            title += " " + s
    if add_file_url:
        furl = escape_url("file:%s::%d" % (zettel.filename, zettel.lineno))
        title = f"([[{furl}][🔗]]) " + title
    node.title = title
    node.tags = zettel.all_tags
    return node
