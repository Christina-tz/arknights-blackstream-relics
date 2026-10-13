# -*- coding: utf-8 -*-
"""生成「藏品获取筛选器」：诡意行商 / 湖中仙女 / 险路恶敌 三来源交叉筛选"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\29921\AppData\Local\Temp\blackstream.json"

d = json.load(open(SRC, encoding="utf-8"))
classifier_items = d["classifier"]["items"]
pools = d["pools"]["pools"]
prts_items = d["prts"]["topics"]["沉沦者的黑流树海"]["items"]

by_itemid = {it["itemId"]: it for it in classifier_items}

def pset(pid):
    p = next((x for x in pools if x["id"] == pid), None)
    return set(p.get("collectibles", [])) if p else set()

def coll(s):
    return {x for x in s if by_itemid.get(x, {}).get("dataType") == "藏品"}

GUIYI = coll(pset("rogue_6:诡意行商"))
HUXIAN = coll(pset("rogue_6:不期而遇：湖中仙女")
              | pset("rogue_6:不期而遇：湖中仙女（紧急）")
              | pset("rogue_6:不期而遇：湖中仙女（直接收藏品）"))
XIANLU = coll(pset("rogue_6:pool_boss"))

RARITY_META = {
    "SUPER_RARE": {"label": "超稀有", "short": "金", "price": 16, "order": 3},
    "RARE": {"label": "稀有", "short": "蓝", "price": 12, "order": 2},
    "NORMAL": {"label": "普通", "short": "白", "price": 8, "order": 1},
}

prts_by_icon = {pi.get("sourceIconId"): pi for pi in prts_items}

def base_id(cid):
    for suf in ("_a", "_b", "_c"):
        if cid.endswith(suf):
            return cid[: -len(suf)]
    return cid

# 去重：α/β/γ 只保留 γ；襁褓生灵冗余条目只保留基础项
import re
from collections import defaultdict
def _logical_base(cid):
    for suf in ("_a", "_b", "_c"):
        if cid.endswith(suf):
            return cid[: -len(suf)]
    m = re.match(r"^(rogue_6_legacy_\d+)_[12]$", cid)
    if m:
        return m.group(1)
    m = re.match(r"^(rogue_6_legacy_0)[5-9]$", cid)
    if m:
        return m.group(1) + "4"
    return cid

_colls = [it for it in classifier_items if it.get("dataType") == "藏品"]
_by_base = defaultdict(list)
for _c in _colls:
    _by_base[_logical_base(_c["itemId"])].append(_c["itemId"])
_keep_ids = set()
for _bid, _ids in _by_base.items():
    _gamma = [i for i in _ids if i.endswith("_c")]
    if _gamma:
        _keep_ids.add(_gamma[0])
    else:
        _base = [i for i in _ids if i == _bid]
        _keep_ids.add(_base[0] if _base else sorted(_ids)[0])

rows = []
for it in classifier_items:
    if it.get("dataType") != "藏品":
        continue
    cid = it["itemId"]
    if cid not in _keep_ids:
        continue
    rarity = it.get("rarity")
    rm = RARITY_META.get(rarity, {})
    pi = prts_by_icon.get(base_id(cid))
    no = pi.get("numberLabel", "") if pi else ""
    no_num = int(pi.get("number")) if pi else None
    rows.append({
        "no": no, "no_num": no_num, "name": it.get("name", ""),
        "rarity": rarity or "", "rarity_label": rm.get("label", ""),
        "rarity_short": rm.get("short", ""), "rarity_order": rm.get("order", 0),
        "price": rm.get("price"), "in_guiyi": cid in GUIYI,
        "can_sacrifice": bool(it.get("canSacrifice")),
        "g": cid in GUIYI, "h": cid in HUXIAN, "x": cid in XIANLU,
    })

rows.sort(key=lambda r: (-r["rarity_order"], r["no_num"] if r["no_num"] is not None else 99999, r["name"]))
data_json = json.dumps(rows, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>藏品获取筛选器 · 沉沦者的黑流树海</title>
<style>
  :root{
    --bg:#0f1420; --card:#1a2130; --card2:#222c40; --line:#2e3a52;
    --txt:#e8edf6; --sub:#9aa7bd; --acc:#35d0a5; --acc2:#4da3ff; --warn:#ffb454; --bad:#ff6b6b;
    --gold:#e8b23a; --blue:#4da3ff; --white:#c9cdd3;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    background:radial-gradient(1200px 600px at 20% -10%, #1b2740 0%, transparent 60%),
               radial-gradient(900px 500px at 100% 0%, #122a2a 0%, transparent 55%),
               var(--bg);
    color:var(--txt); min-height:100vh; padding:32px 16px;
  }
  .wrap{max-width:1000px;margin:0 auto}
  h1{font-size:24px;font-weight:700;letter-spacing:.5px}
  .sub{color:var(--sub);font-size:13px;margin-top:6px}
  .rule{margin-top:18px;background:var(--card);border:1px solid var(--line);border-radius:14px;
    padding:14px 16px;font-size:13px;line-height:1.7;color:var(--sub)}
  .rule b{color:var(--txt)}
  .rule .hl{color:var(--acc)}

  /* 筛选开关 */
  .filters{margin-top:18px;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
  .filter{
    position:relative;display:block;background:var(--card);border:1px solid var(--line);
    border-radius:16px;padding:18px;cursor:pointer;transition:.15s;user-select:none;
  }
  .filter:hover{border-color:#3b4a68}
  .filter.active{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc), 0 8px 24px rgba(53,208,165,.12)}
  .filter input{position:absolute;opacity:0;pointer-events:none}
  .fhead{display:flex;align-items:center;gap:12px}
  .ficon{width:42px;height:42px;border-radius:12px;background:var(--card2);display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0}
  .ftitle{flex:1}
  .fname{font-size:16px;font-weight:700}
  .fdesc{font-size:12px;color:var(--sub);margin-top:2px}
  .fcount{font-size:13px;font-weight:700;color:var(--sub);white-space:nowrap}
  .filter.active .fcount{color:var(--acc)}
  .switch{width:44px;height:24px;border-radius:999px;background:var(--card2);border:1px solid var(--line);
    position:relative;transition:.15s;flex-shrink:0}
  .switch::after{content:"";position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;
    background:var(--sub);transition:.18s}
  .filter.active .switch{background:var(--acc);border-color:var(--acc)}
  .filter.active .switch::after{left:22px;background:#06130e}

  /* 工具条 */
  .toolbar{margin-top:20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
  .toolbar .sel{font-size:14px;color:var(--sub)}
  .toolbar .sel b{color:var(--acc);font-size:16px}
  .toolbar .spacer{flex:1}
  .btn{background:var(--card2);border:1px solid var(--line);color:var(--sub);border-radius:999px;
    padding:6px 16px;font-size:13px;cursor:pointer;transition:.15s}
  .btn:hover{color:var(--txt);border-color:var(--acc)}

  /* 结果表 */
  .result{margin-top:16px;display:none}
  .tablewrap{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{padding:11px 14px;text-align:left;border-bottom:1px solid var(--line)}
  th{color:var(--sub);font-weight:600;font-size:12px;background:var(--card2);position:sticky;top:0}
  tr:last-child td{border-bottom:none}
  tbody tr:hover{background:var(--card2)}
  td.num{color:var(--sub);font-size:12px;font-variant-numeric:tabular-nums;white-space:nowrap}
  td.name{font-weight:600}
  .badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;white-space:nowrap}
  .badge.gold{background:rgba(232,178,58,.16);color:var(--gold)}
  .badge.blue{background:rgba(79,143,216,.16);color:var(--blue)}
  .badge.white{background:rgba(201,205,211,.14);color:var(--white)}
  .price-buy{color:var(--gold);font-weight:600;white-space:nowrap}
  .price-no{color:var(--sub);white-space:nowrap}
  .sac-yes{color:var(--acc);font-weight:600}
  .sac-no{color:var(--sub)}
  .src{display:inline-flex;gap:4px;flex-wrap:wrap}
  .src span{display:inline-block;padding:1px 8px;border-radius:6px;font-size:11px;border:1px solid var(--line);color:var(--sub)}
  .src span.g{background:rgba(53,208,165,.12);border-color:rgba(53,208,165,.35);color:var(--acc)}
  .src span.h{background:rgba(77,163,255,.12);border-color:rgba(77,163,255,.35);color:var(--blue)}
  .src span.x{background:rgba(255,180,84,.12);border-color:rgba(255,180,84,.35);color:var(--warn)}
  .empty{margin-top:16px;background:var(--card);border:1px dashed var(--line);border-radius:16px;
    padding:40px 20px;text-align:center;color:var(--sub);font-size:14px}
  .note{color:var(--sub);font-size:12px;margin-top:16px;line-height:1.8}
</style>
</head>
<body>
<div class="wrap">
  <h1>🎯 藏品获取筛选器</h1>
  <div class="sub">沉沦者的黑流树海 · 按「获取来源」交叉筛选收藏品（可多选取交集）</div>

  <div class="rule">
    <b>筛选逻辑：</b>勾选一个来源 = 显示该来源可获取的全部藏品；<b>同时勾选多个 = 取交集</b>
    （即「同时可在这些来源获得」的藏品）。<span class="hl">湖中仙女</span>已合并「普通」「紧急」「直接收藏品」三个子池。
  </div>

  <div class="filters" id="filters"></div>

  <div class="toolbar">
    <span class="sel">命中 <b id="count">0</b> 件藏品</span>
    <span class="spacer"></span>
    <button class="btn" id="all">全选</button>
    <button class="btn" id="clear">清空</button>
  </div>

  <div class="result" id="result">
    <div class="tablewrap">
      <table>
        <thead><tr>
          <th>编号</th><th>名称</th><th>稀有度</th><th>诡意行商售价</th><th>失与得</th><th>命中来源</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>

  <div class="empty" id="empty">未启用任何来源筛选，当前显示全部 285 件藏品。</div>

  <div class="note">
    说明：①「诡意行商」来源 = 诡意行商节点商品库存（192 件藏品）。②「湖中仙女」来源 = 不期而遇·湖中仙女事件（普通 / 紧急 / 直接收藏品，共 15 件）。③「险路恶敌」来源 = 三层险路恶敌收藏品二选一（33 件）。④「命中来源」列出该藏品实际所属的三个来源。数据归档自路标档案馆藏品池（2026-08-24）。
  </div>
</div>

<script>
const DATA = __DATA__;

const SRCS = [
  {key:'g', icon:'🏪', name:'诡意行商', desc:'BATTLE_SHOP · 商品库存', color:'var(--acc)'},
  {key:'h', icon:'🧚', name:'湖中仙女', desc:'不期而遇 · 普通/紧急/直接', color:'var(--blue)'},
  {key:'x', icon:'⚔️', name:'险路恶敌', desc:'三层 BATTLE_BOSS · 收藏品二选一', color:'var(--warn)'},
];

const state = { g:false, h:false, x:false };
const $ = id => document.getElementById(id);
const R = {SUPER_RARE:{label:"超稀有",short:"金",cls:"gold"},RARE:{label:"稀有",short:"蓝",cls:"blue"},NORMAL:{label:"普通",short:"白",cls:"white"}};

function buildFilters(){
  $('filters').innerHTML = SRCS.map(s=>{
    const n = DATA.filter(r=>r[s.key]).length;
    return `<label class="filter ${state[s.key]?'active':''}" data-key="${s.key}">
      <input type="checkbox" ${state[s.key]?'checked':''}>
      <div class="fhead">
        <div class="ficon">${s.icon}</div>
        <div class="ftitle">
          <div class="fname">${s.name}</div>
          <div class="fdesc">${s.desc}</div>
        </div>
        <div class="fcount">${n} 件</div>
        <div class="switch"></div>
      </div>
    </label>`;
  }).join("");
}

function activeKeys(){
  return SRCS.filter(s=>state[s.key]).map(s=>s.key);
}

function filtered(){
  const keys = activeKeys();
  if(keys.length === 0) return DATA;
  return DATA.filter(r => keys.every(k => r[k]));
}

function srcTags(r){
  const tags = [];
  if(r.g) tags.push('<span class="g">诡意行商</span>');
  if(r.h) tags.push('<span class="h">湖中仙女</span>');
  if(r.x) tags.push('<span class="x">险路恶敌</span>');
  return tags.length ? `<div class="src">${tags.join('')}</div>` : '<span style="color:var(--sub)">—</span>';
}

function render(){
  const rows = filtered();
  $('count').textContent = rows.length;
  const tb = $('tbody');
  if(rows.length){
    $('result').style.display = 'block';
    $('empty').style.display = 'none';
    tb.innerHTML = rows.map(r=>{
      const rm = R[r.rarity] || {label:r.rarity_label||"—",cls:"white",short:""};
      const pr = r.price==null ? `<span class="price-no">不可购买</span>` : `<span class="price-buy">${r.price} 源石锭</span>`;
      const sac = r.can_sacrifice ? `<span class="sac-yes">可交换</span>` : `<span class="sac-no">不可交换</span>`;
      return `<tr>
        <td class="num">${r.no||"—"}</td>
        <td class="name">${r.name}</td>
        <td><span class="badge ${rm.cls}">${rm.label}${rm.short?"·"+rm.short:""}</span></td>
        <td>${pr}</td>
        <td>${sac}</td>
        <td>${srcTags(r)}</td>
      </tr>`;
    }).join("");
  } else {
    $('result').style.display = 'none';
    $('empty').style.display = 'block';
    $('empty').textContent = '没有藏品同时命中当前所选来源（交集为空）。';
  }
}

$('filters').addEventListener('click', e=>{
  const f = e.target.closest('.filter');
  if(!f) return;
  const k = f.dataset.key;
  state[k] = !state[k];
  buildFilters();
  render();
});
$('all').onclick = ()=>{ SRCS.forEach(s=>state[s.key]=true); buildFilters(); render(); };
$('clear').onclick = ()=>{ SRCS.forEach(s=>state[s.key]=false); buildFilters(); render(); };

buildFilters();
render();
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", data_json)
out = os.path.join(BASE, "藏品获取筛选器_诡意行商_湖中仙女_险路恶敌.html")
open(out, "w", encoding="utf-8").write(html)
print("OK:", out, len(html), "bytes;", len(rows), "rows")
print("诡意", len(GUIYI), "湖仙", len(HUXIAN), "险路", len(XIANLU),
      "三交", len(GUIYI & HUXIAN & XIANLU))
