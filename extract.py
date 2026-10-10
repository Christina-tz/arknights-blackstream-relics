# -*- coding: utf-8 -*-
"""从 blackstream.json 提取藏品数据，生成结构化中间 JSON 与 CSV"""
import json
import csv
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\29921\AppData\Local\Temp\blackstream.json"

d = json.load(open(SRC, encoding="utf-8"))
classifier_items = d["classifier"]["items"]
pools = d["pools"]["pools"]
prts_items = d["prts"]["topics"]["沉沦者的黑流树海"]["items"]

# ---- 稀有度映射 ----
RARITY_META = {
    "SUPER_RARE": {"label": "超稀有", "short": "金", "price": 16, "order": 3},
    "RARE": {"label": "稀有", "short": "蓝", "price": 12, "order": 2},
    "NORMAL": {"label": "普通", "short": "白", "price": 8, "order": 1},
}

# ---- 节点 ID -> 中文名 ----
NODE_ID_NAME = {
    "BATTLE_NORMAL": "作战",
    "BATTLE_ELITE": "紧急作战",
    "BATTLE_BOSS": "险路恶敌",
    "BATTLE_SAVAGE": "“居民”据点",
    "BATTLE_SHOP": "诡意行商",
    "SCRAP_SHOP": "秘境行商",
    "SACRIFICE": "失与得",
    "DUEL": "狭路相逢",
    "EVACUATE": "险路小径",
    "FINAL": "险路尽头",
    "WANDERING_RESIDENT": "流窜的“居民”",
}

# ---- 每个池：显示名 + 获取节点 + 是否“输入（牺牲）”池 ----
def pool_meta(p):
    name = p.get("name", "")
    pid = p.get("id", "")
    nodes = []
    is_input = "输入" in pid and ("失与得" in pid)
    nb = p.get("nodeBindings") or []
    if nb:
        nodes = [b.get("nodeName", "") for b in nb]
    else:
        sr = p.get("sourceReferences") or []
        if sr:
            s = sr[0]
            st = s.get("sourceType")
            if st == "node":
                for nid in s.get("sourceIds", []):
                    if nid in NODE_ID_NAME:
                        nodes.append(NODE_ID_NAME[nid])
                if not nodes:
                    nodes = [name]
            elif st == "choiceScene":
                # 用池名（去掉括号后缀）作为事件名
                nodes = [name.split("（")[0]]
            elif st == "choice":
                nodes = ["得偿所愿"]
            elif st == "relicEffect":
                nodes = ["额外掉落"]
            elif st == "stage":
                nodes = [name]
            elif st == "researchWorkbook":
                nodes = ["隐藏"]
            else:
                nodes = [name]
    # 池显示名：歧义名补充上下文
    display = name
    return {"id": pid, "display": display, "nodes": nodes, "is_input": is_input, "order": p.get("order", 0)}

pool_meta_map = {p["id"]: pool_meta(p) for p in pools}

# 藏品 -> 池成员
item_pools = {}
for p in pools:
    for cid in p.get("collectibles", []):
        item_pools.setdefault(cid, []).append(p["id"])

# 诡意行商池成员
guiyi_pool = next((p for p in pools if p["id"] == "rogue_6:诡意行商"), None)
guiyi_set = set(guiyi_pool["collectibles"]) if guiyi_pool else set()

# PRTS 编号映射（sourceIconId -> numberLabel, category）
prts_by_icon = {}
for pi in prts_items:
    prts_by_icon[pi.get("sourceIconId")] = pi

def base_item_id(cid):
    # 变体 _a/_b/_c 还原为基础 id
    for suf in ("_a", "_b", "_c"):
        if cid.endswith(suf):
            return cid[:-len(suf)]
    return cid

# 构建输出行
rows = []
collectibles = [it for it in classifier_items if it.get("dataType") == "藏品"]
# 排序：先稀有度(金>蓝>白)，再编号
def sort_key(c):
    r = RARITY_META.get(c.get("rarity"), {"order": 0})["order"]
    return (-r, c.get("itemId", ""))

for c in sorted(collectibles, key=sort_key):
    cid = c["itemId"]
    rarity = c.get("rarity")
    rmeta = RARITY_META.get(rarity, {})
    # PRTS 信息
    base_id = base_item_id(cid)
    pi = prts_by_icon.get(base_id)
    no = ""
    category = ""
    if pi:
        no = pi.get("numberLabel", "")
        category = pi.get("category", "")
    variant = ""
    if cid != base_id:
        variant = cid[len(base_id):].lstrip("_").upper()
    # 售价
    if cid in guiyi_set and rarity in RARITY_META:
        price = f"{rmeta['price']} 源石锭"
        price_sort = rmeta["price"]
    else:
        price = "不可购买"
        price_sort = 0
    # 失与得
    can_sac = bool(c.get("canSacrifice"))
    # 池
    pool_ids = item_pools.get(cid, [])
    pool_displays = []
    obtain_nodes = set()
    for pid in pool_ids:
        pm = pool_meta_map.get(pid)
        if not pm:
            continue
        pool_displays.append(pm["display"])
        if not pm["is_input"]:
            for n in pm["nodes"]:
                obtain_nodes.add(n)
    # 失与得可交换但没在“输出”池时，节点补充说明由 canSacrifice 体现
    rows.append({
        "no": no,
        "name": c.get("name", ""),
        "variant": variant,
        "rarity": rarity or "",
        "rarity_label": rmeta.get("label", ""),
        "rarity_short": rmeta.get("short", ""),
        "price": price,
        "price_sort": price_sort,
        "can_sacrifice": "可交换" if can_sac else "不可交换",
        "can_sacrifice_bool": can_sac,
        "category": category,
        "pools": "、".join(pool_displays),
        "pool_count": len(pool_displays),
        "nodes": "、".join(sorted(obtain_nodes)),
        "itemId": cid,
    })

# 输出中间 JSON
out_json = os.path.join(BASE, "collectibles_data.json")
json.dump(rows, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 输出 CSV
out_csv = os.path.join(BASE, "collectibles_data.csv")
with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["编号", "名称", "稀有度", "诡意行商售价", "失与得", "分类", "藏品池", "可获取节点"])
    for r in rows:
        w.writerow([r["no"], r["name"] + (f"-{r['variant']}" if r["variant"] else ""),
                    r["rarity_label"], r["price"], r["can_sacrifice"], r["category"],
                    r["pools"], r["nodes"]])

print("rows:", len(rows))
from collections import Counter
print("rarity:", dict(Counter(r["rarity"] for r in rows)))
print("price dist:", dict(Counter(r["price"] for r in rows)))
print("sac:", dict(Counter(r["can_sacrifice"] for r in rows)))
print("category dist:", dict(Counter(r["category"] for r in rows)))
print("with no:", sum(1 for r in rows if r["no"]))
print("with pools:", sum(1 for r in rows if r["pool_count"] > 0))
print("with nodes:", sum(1 for r in rows if r["nodes"]))
print("wrote:", out_json, out_csv)
