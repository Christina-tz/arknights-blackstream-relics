# -*- coding: utf-8 -*-
"""生成收藏品一览表：交互式 HTML + Excel"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\29921\AppData\Local\Temp\blackstream.json"

d = json.load(open(SRC, encoding="utf-8"))
classifier_items = d["classifier"]["items"]
pools = d["pools"]["pools"]
prts_items = d["prts"]["topics"]["沉沦者的黑流树海"]["items"]

RARITY_META = {
    "SUPER_RARE": {"label": "超稀有", "short": "金", "price": 16, "order": 3},
    "RARE": {"label": "稀有", "short": "蓝", "price": 12, "order": 2},
    "NORMAL": {"label": "普通", "short": "白", "price": 8, "order": 1},
}

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

def pool_meta(p):
    name = p.get("name", "")
    pid = p.get("id", "")
    nodes = []
    is_input = "失与得" in pid and "输入" in pid
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
    return {"id": pid, "name": name, "nodes": nodes, "is_input": is_input}

pool_meta_map = {p["id"]: pool_meta(p) for p in pools}

item_pools = {}
for p in pools:
    for cid in p.get("collectibles", []):
        item_pools.setdefault(cid, []).append(p["id"])

guiyi_set = set(next(p for p in pools if p["id"] == "rogue_6:诡意行商")["collectibles"])

prts_by_icon = {pi.get("sourceIconId"): pi for pi in prts_items}

def base_item_id(cid):
    for suf in ("_a", "_b", "_c"):
        if cid.endswith(suf):
            return cid[: -len(suf)]
    return cid

rows = []
collectibles = [it for it in classifier_items if it.get("dataType") == "藏品"]

for c in collectibles:
    cid = c["itemId"]
    rarity = c.get("rarity")
    rmeta = RARITY_META.get(rarity, {})
    pi = prts_by_icon.get(base_item_id(cid))
    no = pi.get("numberLabel", "") if pi else ""
    category = pi.get("category", "") if pi else ""
    name = c.get("name", "")

    in_guiyi = cid in guiyi_set
    if rarity in RARITY_META:
        price = rmeta["price"]
    else:
        price = None
    can_sac = bool(c.get("canSacrifice"))

    pool_displays = []
    obtain_nodes = []
    for pid in item_pools.get(cid, []):
        pm = pool_meta_map.get(pid)
        if not pm:
            continue
        pool_displays.append(pm["name"])
        if not pm["is_input"]:
            for n in pm["nodes"]:
                if n and n not in obtain_nodes:
                    obtain_nodes.append(n)

    rows.append({
        "no": no,
        "no_num": int(pi.get("number")) if pi else None,
        "name": name,
        "rarity": rarity or "",
        "rarity_label": rmeta.get("label", ""),
        "rarity_short": rmeta.get("short", ""),
        "rarity_order": rmeta.get("order", 0),
        "price": price,
        "in_guiyi": in_guiyi,
        "can_sacrifice": can_sac,
        "category": category,
        "pools": pool_displays,
        "nodes": obtain_nodes,
    })

# 默认排序：稀有度降序，再编号升序
rows.sort(key=lambda r: (-r["rarity_order"], r["no_num"] if r["no_num"] is not None else 9999, r["name"]))

json.dump(rows, open(os.path.join(BASE, "collectibles_data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ============ 生成 HTML ============
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

data_json = json.dumps(rows, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>沉沦者的黑流树海 · 收藏品一览表</title>
<style>
:root{
  --bg:#0e1116; --panel:#171b22; --panel2:#1c212a; --border:#2a3038;
  --text:#e8eaed; --muted:#9aa3ad; --accent:#e3b341;
  --gold:#e8b23a; --blue:#4f8fd8; --white:#c9cdd3;
  --good:#7ecf8b; --bad:#6f7680;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,"PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  font-size:14px;line-height:1.5}
.wrap{max-width:1500px;margin:0 auto;padding:24px 20px 60px}
h1{font-size:22px;margin:0 0 4px;display:flex;align-items:center;gap:10px}
h1 .sub{font-size:13px;color:var(--muted);font-weight:400}
.intro{color:var(--muted);font-size:13px;margin:6px 0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.card .k{font-size:12px;color:var(--muted)}
.card .v{font-size:20px;font-weight:600;margin-top:2px}
.card .v small{font-size:12px;color:var(--muted);font-weight:400}
.legend{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin:14px 0;font-size:13px;color:var(--muted)}
.legend b{color:var(--text)}
.legend .chip{display:inline-block;padding:1px 8px;border-radius:10px;margin:0 4px;font-size:12px;color:#0e1116;font-weight:600}
.toolbar{position:sticky;top:0;background:var(--bg);padding:12px 0;z-index:10;display:flex;flex-wrap:wrap;gap:10px;align-items:center;border-bottom:1px solid var(--border);margin-bottom:8px}
#search{flex:1;min-width:220px;padding:9px 14px;border-radius:8px;border:1px solid var(--border);background:var(--panel2);color:var(--text);font-size:14px;outline:none}
#search:focus{border-color:var(--accent)}
.fgroups{display:flex;flex-wrap:wrap;gap:8px}
.fgroup{display:flex;gap:4px;background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:4px}
.fbtn{padding:5px 12px;border-radius:6px;border:none;background:transparent;color:var(--muted);cursor:pointer;font-size:13px;white-space:nowrap}
.fbtn:hover{color:var(--text)}
.fbtn.active{background:var(--accent);color:#0e1116;font-weight:600}
.count{color:var(--muted);font-size:13px;white-space:nowrap}
.table-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;min-width:1000px}
thead th{position:sticky;top:0;background:var(--panel2);color:var(--muted);font-weight:600;font-size:12px;
  text-align:left;padding:10px 12px;border-bottom:1px solid var(--border);white-space:nowrap;cursor:pointer;user-select:none;z-index:2}
thead th:hover{color:var(--text)}
tbody td{padding:9px 12px;border-bottom:1px solid #232931;vertical-align:top}
tbody tr:hover{background:var(--panel2)}
td.no{color:var(--muted);font-size:12px;white-space:nowrap;font-variant-numeric:tabular-nums}
td.name{font-weight:600;min-width:140px}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;white-space:nowrap}
.badge.gold{background:rgba(232,178,58,.16);color:var(--gold)}
.badge.blue{background:rgba(79,143,216,.16);color:var(--blue)}
.badge.white{background:rgba(201,205,211,.14);color:var(--white)}
td.price{white-space:nowrap;font-variant-numeric:tabular-nums}
.price-buy{color:var(--gold);font-weight:600}
.price-no{color:var(--muted)}
td.sac{white-space:nowrap}
.sac-yes{color:var(--good);font-weight:600}
.sac-no{color:var(--bad)}
.tags{display:flex;flex-wrap:wrap;gap:4px}
.tag{display:inline-block;padding:1px 8px;border-radius:6px;font-size:11px;background:var(--panel2);border:1px solid var(--border);color:var(--muted);white-space:nowrap}
.tag.node{background:rgba(79,143,216,.10);border-color:rgba(79,143,216,.30);color:#8db8e8}
.tag.pool{background:rgba(232,178,58,.08);border-color:rgba(232,178,58,.22);color:#d9b25f}
.tag.empty{color:#565d66;border-style:dashed}
.foot{color:var(--muted);font-size:12px;margin-top:18px;line-height:1.8}
.foot a{color:var(--accent)}
</style>
</head>
<body>
<div class="wrap">
  <h1>沉沦者的黑流树海 · 收藏品一览表 <span class="sub">ROGUE 6 / 藏品池</span></h1>
  <div class="intro">数据来源：<a href="https://www.lubiao.wiki/pools/rogue_6" style="color:var(--accent)">路标档案馆 · 藏品池</a>（归档 JSON，共 285 件藏品，含 α/β/γ 结构变体）。</div>

  <div class="cards" id="cards"></div>

  <div class="legend">
    <b>稀有度与售价规则</b>：<span class="chip" style="background:#e8b23a">超稀有·金</span> 诡意行商售价 <b>16 源石锭</b>；
    <span class="chip" style="background:#4f8fd8">稀有·蓝</span> 售价 <b>12 源石锭</b>；
    <span class="chip" style="background:#c9cdd3">普通·白</span> 售价 <b>8 源石锭</b>。
    售价为 PRTS「行商售价」基准（不受负面效果影响）；<b>「不可购买」</b>表示该藏品不在诡意行商常规库存中（多为事件 / 结局 / 解锁专属）。
  </div>

  <div class="toolbar">
    <input id="search" type="text" placeholder="搜索编号或名称…">
    <div class="fgroups">
      <div class="fgroup" id="f-rarity"></div>
      <div class="fgroup" id="f-sac"></div>
      <div class="fgroup" id="f-price"></div>
    </div>
    <span class="count" id="count"></span>
  </div>

  <div class="table-wrap">
    <table id="tbl">
      <thead>
        <tr>
          <th data-sort="no">编号</th>
          <th data-sort="name">名称</th>
          <th data-sort="rarity">稀有度</th>
          <th data-sort="price">诡意行商售价</th>
          <th data-sort="sac">失与得</th>
          <th data-sort="category">分类</th>
          <th>位于的藏品池</th>
          <th>可获取节点</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>

  <div class="foot">
    <b>说明</b>：①「失与得」= 该藏品能否在【失与得】节点投入交换（可交换 / 不可交换）。②「位于的藏品池」列出该藏品所归属的全部藏品池名称（含失与得的 N/R/SR 输入、输出池）。③「可获取节点」= 能从哪些节点 / 事件获得该藏品（作战、紧急作战、险路恶敌、“居民”据点、诡意行商、秘境行商、狭路相逢、失与得输出、不期而遇事件、得偿所愿、命运所指等）。④ α/β/γ 为同一藏品在不同「结构」等级下的变体，各自独立计数与掉落。<br>
    数据归档于 2026-08-24（PRTS 同步），页面版本：本体（2026.07.17 16:00 至今）。
  </div>
</div>

<script>
const DATA = __DATA__;
const R = {SUPER_RARE:{label:"超稀有",short:"金",cls:"gold"},RARE:{label:"稀有",short:"蓝",cls:"blue"},NORMAL:{label:"普通",short:"白",cls:"white"}};

const state = {q:"", rarity:"全部", sac:"全部", price:"全部", sort:"rarity", asc:false};

function priceText(r){
  if(r.price==null) return "不可购买";
  return r.price + " 源石锭";
}

function renderStats(){
  const n = DATA.length;
  const rar = {}, sac = {}, price = {};
  DATA.forEach(r=>{
    rar[r.rarity_label] = (rar[r.rarity_label]||0)+1;
    sac[r.can_sacrifice?"可交换":"不可交换"] = (sac[r.can_sacrifice?"可交换":"不可交换"]||0)+1;
    const p = r.price==null?"不可购买":r.price+"源石锭";
    price[p] = (price[p]||0)+1;
  });
  const cards = [
    {k:"收藏品总数", v:n+" 件"},
    {k:"超稀有(金)", v:(rar["超稀有"]||0)+" 件", c:"var(--gold)"},
    {k:"稀有(蓝)", v:(rar["稀有"]||0)+" 件", c:"var(--blue)"},
    {k:"普通(白)", v:(rar["普通"]||0)+" 件", c:"var(--white)"},
    {k:"失与得·可交换", v:(sac["可交换"]||0)+" 件", c:"var(--good)"},
    {k:"不可交换", v:(sac["不可交换"]||0)+" 件", c:"var(--bad)"},
    {k:"可在诡意行商购买", v:DATA.filter(r=>r.in_guiyi).length+" 件", c:"var(--accent)"},
  ];
  document.getElementById("cards").innerHTML = cards.map(c=>
    `<div class="card"><div class="k">${c.k}</div><div class="v" style="${c.c?'color:'+c.c:''}">${c.v}</div></div>`
  ).join("");
}

function buildFilters(){
  const rarityOpts = ["全部","超稀有","稀有","普通"];
  document.getElementById("f-rarity").innerHTML = rarityOpts.map(o=>
    `<button class="fbtn ${state.rarity===o?'active':''}" data-rarity="${o}">${o}</button>`).join("");
  const sacOpts = ["全部","可交换","不可交换"];
  document.getElementById("f-sac").innerHTML = sacOpts.map(o=>
    `<button class="fbtn ${state.sac===o?'active':''}" data-sac="${o}">失与得·${o}</button>`).join("");
  const priceOpts = ["全部","8 源石锭","12 源石锭","16 源石锭","不可购买"];
  document.getElementById("f-price").innerHTML = priceOpts.map(o=>
    `<button class="fbtn ${state.price===o?'active':''}" data-price="${o}">售价·${o}</button>`).join("");
}

function filtered(){
  let rows = DATA.filter(r=>{
    if(state.q){
      const q = state.q.toLowerCase();
      if(!(r.name.toLowerCase().includes(q) || r.no.toLowerCase().includes(q))) return false;
    }
    if(state.rarity!=="全部" && r.rarity_label!==state.rarity) return false;
    if(state.sac!=="全部" && (r.can_sacrifice?"可交换":"不可交换")!==state.sac) return false;
    if(state.price!=="全部" && priceText(r)!==state.price) return false;
    return true;
  });
  const key = state.sort;
  rows.sort((a,b)=>{
    let va,vb;
    if(key==="no"){ va=a.no_num??99999; vb=b.no_num??99999; }
    else if(key==="name"){ va=a.name; vb=b.name; return state.asc?va.localeCompare(vb,"zh"):vb.localeCompare(va,"zh"); }
    else if(key==="rarity"){ va=a.rarity_order; vb=b.rarity_order; }
    else if(key==="price"){ va=a.price??0; vb=b.price??0; }
    else if(key==="sac"){ va=a.can_sacrifice?1:0; vb=b.can_sacrifice?1:0; }
    else if(key==="category"){ va=a.category; vb=b.category; return state.asc?va.localeCompare(vb,"zh"):vb.localeCompare(va,"zh"); }
    return state.asc?va-vb:vb-va;
  });
  return rows;
}

function tags(arr, cls){
  if(!arr || arr.length===0) return `<span class="tag empty">—</span>`;
  return `<div class="tags">` + arr.map(x=>`<span class="tag ${cls}">${x}</span>`).join("") + `</div>`;
}

function render(){
  const rows = filtered();
  const tb = document.getElementById("tbody");
  tb.innerHTML = rows.map(r=>{
    const rm = R[r.rarity] || {label:r.rarity_label||"—",cls:"white",short:""};
    const pr = r.price==null
      ? `<span class="price-no">不可购买</span>`
      : `<span class="price-buy">${r.price}</span> <span style="color:var(--muted);font-size:12px">源石锭</span>`;
    const sac = r.can_sacrifice
      ? `<span class="sac-yes">可交换</span>`
      : `<span class="sac-no">不可交换</span>`;
    return `<tr>
      <td class="no">${r.no||"—"}</td>
      <td class="name">${r.name}</td>
      <td><span class="badge ${rm.cls}">${rm.label}${rm.short?"·"+rm.short:""}</span></td>
      <td class="price">${pr}</td>
      <td class="sac">${sac}</td>
      <td>${r.category||"—"}</td>
      <td>${tags(r.pools,"pool")}</td>
      <td>${tags(r.nodes,"node")}</td>
    </tr>`;
  }).join("");
  document.getElementById("count").textContent = `共 ${rows.length} / ${DATA.length} 件`;
}

// 事件
document.getElementById("search").addEventListener("input", e=>{state.q=e.target.value; render();});
document.querySelectorAll(".fgroup").forEach(g=>{
  g.addEventListener("click", e=>{
    const b = e.target.closest("button"); if(!b) return;
    if(b.dataset.rarity!==undefined){ state.rarity=b.dataset.rarity; buildFilters(); }
    if(b.dataset.sac!==undefined){ state.sac=b.dataset.sac; buildFilters(); }
    if(b.dataset.price!==undefined){ state.price=b.dataset.price; buildFilters(); }
    render();
  });
});
document.querySelectorAll("thead th[data-sort]").forEach(th=>{
  th.addEventListener("click", ()=>{
    const k = th.dataset.sort;
    if(state.sort===k) state.asc=!state.asc; else {state.sort=k; state.asc=false;}
    render();
  });
});

renderStats();
buildFilters();
render();
</script>
</body>
</html>
"""

html = html.replace("__DATA__", data_json)
out_html = os.path.join(BASE, "沉沦者的黑流树海_收藏品一览表.html")
open(out_html, "w", encoding="utf-8").write(html)
print("HTML:", out_html, len(html), "bytes")

# ============ 生成 Excel ============
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "收藏品一览表"

headers = ["编号", "名称", "稀有度", "诡意行商售价(源石锭)", "失与得", "分类", "位于的藏品池", "可获取节点"]

hfill = PatternFill("solid", fgColor="1F2937")
hfont = Font(bold=True, color="FFFFFF", size=11)
thin = Side(style="thin", color="D1D5DB")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

rar_fill = {
    "超稀有": PatternFill("solid", fgColor="FDE68A"),
    "稀有": PatternFill("solid", fgColor="BFDBFE"),
    "普通": PatternFill("solid", fgColor="E5E7EB"),
}
rar_font = {
    "超稀有": Font(color="92400E", bold=True, size=11),
    "稀有": Font(color="1E40AF", bold=True, size=11),
    "普通": Font(color="374151", size=11),
}

for c, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=c, value=h)
    cell.fill = hfill
    cell.font = hfont
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = border

for i, r in enumerate(rows, 2):
    price_v = r["price"] if r["price"] is not None else "不可购买"
    sac_v = "可交换" if r["can_sacrifice"] else "不可交换"
    vals = [r["no"] or "—", r["name"], r["rarity_label"], price_v, sac_v,
            r["category"] or "—", "、".join(r["pools"]) if r["pools"] else "—",
            "、".join(r["nodes"]) if r["nodes"] else "—"]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(row=i, column=c, value=v)
        cell.border = border
        cell.alignment = Alignment(vertical="center", wrap_text=(c in (7, 8)))
        if c == 3 and r["rarity_label"] in rar_fill:
            cell.fill = rar_fill[r["rarity_label"]]
            cell.font = rar_font[r["rarity_label"]]
            cell.alignment = Alignment(horizontal="center", vertical="center")

widths = [8, 22, 10, 20, 10, 12, 46, 40]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:H{len(rows)+1}"

out_xlsx = os.path.join(BASE, "沉沦者的黑流树海_收藏品一览表.xlsx")
wb.save(out_xlsx)
print("XLSX:", out_xlsx, len(rows), "rows")
