from __future__ import annotations  # PEP 585

import re

from orgee import OrgNode


def parse_logs(
    root: OrgNode, logs_subtree_name: str = "Log"
) -> list[dict] | None:
    if node := root.find_child_by_title(logs_subtree_name):
        return parse_node_logs(node=node)
    return None


def parse_node_logs(node: OrgNode) -> list[dict]:
    return list(map(parse_log, node.children))


def parse_log(node: OrgNode) -> dict:
    # TODO: parse node children
    t = node.title.strip()
    dic = {}
    if m := re.match(r"\[(.+?)\]\s*(.+)", t):
        date, title = m.groups()
        dic["date"] = date
        dic["title"] = title
    dic["body"] = "\n".join(node.body)
    dic["tags"] = node.tags
    return dic
