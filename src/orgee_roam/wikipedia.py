from __future__ import annotations  # PEP 585

import datetime
import logging
import random
import re
from urllib.parse import unquote

import wikipediaapi  # type:ignore

from orgee.orgnode import OrgNode

from .zettelkasten import Zettelkasten
from .zettel import Zettel

STALE_ND = 180
PROB_UPDATE = 0.1


def update_wikipedia_org_subtrees(
    zettel: Zettel,
    wps: dict | None = None,
    force: bool = False,
    stale_nd: int = STALE_ND,
    prob_update: float = PROB_UPDATE,
) -> bool:
    name = zettel.olp_str()
    if not wps:
        wps = wikiprops(zettel)
    if not wps:
        logging.warning("No wikipedia property in %s", name)
        return False
    node = zettel.orgnode()
    changed = False
    filename = zettel.filename

    # Update page for each lang
    for lang, tu in wps.items():
        title, update_prop_p = tu
        pk = wikipedia_prop_key(lang)

        # Automatically find page from other languages
        if not title:
            for lang2, tu2 in wps.items():
                if title2 := tu2[0]:
                    wi = wikipediaapi.Wikipedia(lang2)
                    page = wi.page(title2)
                    if not (rec := page.langlinks.get(lang)):
                        logging.error(
                            "No page in %s for %s(%s)", lang, title2, lang2
                        )
                        continue
                    title = rec.title
                    update_prop(node=node, pk=pk, pv=title)
                    node.dump_root(filename)
                    changed = True
                    logging.info("Updated wiki title for %s to %s", lang, title)
                    break
            if not title:
                logging.error(
                    "Could not find link in %s from another language for «%s»",
                    lang,
                    zettel.olp_str(),
                )
                continue

        if update_prop_p:
            update_prop(node=node, pk=pk, pv=title)
            logging.info("Updated wiki title for %s to %s", lang, title)
            node.dump_root(filename)
            changed = True

        url = wiki_url(title=title, lang=lang)
        wnode = node.find_child_by_title(url=url)
        # Don't update existing subtree unless forced
        if wnode:
            if not force:
                ret_node = wnode.find_child_by_title(
                    title="Retrieved", startswith=True
                )
                if ret_node:
                    s = ret_node.title
                    m = re.match(r"Retrieved\s*\[(\d{4}-\d{2}-\d{2}).*\]", s)
                    if not m:
                        raise Exception(f"Could not parse {s} at {name}")
                    dt = datetime.datetime.strptime(
                        m.groups()[0], "%Y-%m-%d"
                    ).date()
                    if (datetime.date.today() - dt).days < stale_nd:
                        continue
                    elif random.random() > prob_update:
                        continue

        nwnode, actual_title = mk_wnode(lang=lang, title=title)
        nwnode.level = node.actual_level() + 1
        if not wnode and actual_title != title:
            title = actual_title
            update_prop(node=node, pk=pk, pv=title)
            node.dump_root(filename)
            changed = True
            url = wiki_url(title=title, lang=lang)
            wnode = node.find_child_by_title(url=url)
        if not wnode:
            node.add_child(nwnode)
        else:
            if subtrees_equal_p(nwnode, wnode):
                continue
            idx = node.find_child_by_title_index
            node.add_child(node=nwnode, position=idx, replace=True)
        node.tags.add("wikipedia")
        node.dump_root(filename)
        logging.info("Updated subtree for %s(%s) in node %s", title, lang, name)
        changed = True

    return changed


def update_prop(node: OrgNode, pk: str, pv: str):
    node.properties = [(k, v) for k, v in node.properties if k != pk]
    node.properties.append((pk, pv))
    logging.info("Updating property %s to %s", pk, pv)


def subtrees_equal_p(node1: OrgNode, node2: OrgNode) -> bool:
    b1 = ("\n".join(node1.body)).strip()
    b2 = ("\n".join(node2.body)).strip()
    return b1 == b2


def mk_wnode(lang: str, title: str) -> tuple[OrgNode, str]:
    wi = wikipediaapi.Wikipedia(lang)
    page = wi.page(title)
    n = OrgNode()
    try:
        url = unquote(page.fullurl)
    except:
        print(page)
        raise
    n.title = "[[%s][Wikipedia(%s): %s]]" % (url, lang, page.title)
    n.tags.add("auto")
    n.body.append(page.summary)
    dt = datetime.date.today().strftime("%Y-%m-%d %a")
    n.add_child(OrgNode(title=f"Retrieved [{dt}]"))
    m = re.match(r"https://.+/wiki/(.+)", url)
    assert m
    return n, m.groups()[0]


def wikiprops(zettel: Zettel) -> dict[str, tuple[str, bool]]:
    def match(v):
        if m := re.match(r"https://.+/wiki/(.+)", v):
            return unquote(m.groups()[0]).strip()
        else:
            return None

    dic = {}
    for k, v in zettel.properties:
        if k.startswith("WIKIPEDIA_PAGE"):
            if k.startswith("WIKIPEDIA_PAGE_"):
                lang = k[-2:].lower()
            elif k == "WIKIPEDIA_PAGE":
                lang = "en"
            else:
                raise Exception(f"Unexpected property {k}")

            v = v.strip('"')
            if title := match(v):
                dic[lang] = (title, True)
            else:
                dic[lang] = (v, False)
    return dic  # type:ignore


def wikinodes(zk: Zettelkasten) -> list[tuple[Zettel, dict]]:
    return [
        (zettel, wps) for zettel in zk.zettels if (wps := wikiprops(zettel))
    ]


def wikipedia_prop_key(lang: str | None = None) -> str:
    if not lang or lang == "en":
        k = "WIKIPEDIA_PAGE"
    else:
        k = f"WIKIPEDIA_PAGE_{lang.upper()}"
    return k


def wiki_url(title: str, lang: str | None = None):
    if not lang:
        lang = "en"
    return f"https://{lang}.wikipedia.org/wiki/{title}"
