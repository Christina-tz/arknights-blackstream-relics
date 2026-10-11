# -*- coding: utf-8 -*-
"""生成单文件自包含版：筛选器 + 一览表 合二为一，数据与图标全部内嵌"""
import json, base64, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\29921\AppData\Local\Temp\blackstream.json"
SEAL_PNG = r"C:\Users\29921\AppData\Local\Temp\seal_silver.png"

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
    "BATTLE_NORMAL": "作战", "BATTLE_ELITE": "紧急作战", "BATTLE_BOSS": "险路恶敌",
    "BATTLE_SAVAGE": "“居民”据点", "BATTLE_SHOP": "诡意行商", "SCRAP_SHOP": "秘境行商",
    "SACRIFICE": "失与得", "DUEL": "狭路相逢", "EVACUATE": "险路小径",
    "FINAL": "险路尽头", "WANDERING_RESIDENT": "流窜的“居民”",
}

def pool_meta(p):
    pid = p.get("id", ""); name = p.get("name", "")
    nodes = []; is_input = "失与得" in pid and "输入" in pid
    nb = p.get("nodeBindings") or []
    if nb:
        nodes = [b.get("nodeName", "") for b in nb]
    else:
        sr = p.get("sourceReferences") or []
        if sr:
            s = sr[0]; st = s.get("sourceType")
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
    return {"name": name, "nodes": nodes, "is_input": is_input}

item_pools = {}
for p in pools:
    for cid in p.get("collectibles", []):
        item_pools.setdefault(cid, []).append(p["id"])

pool_meta_map = {p["id"]: pool_meta(p) for p in pools}

def pset(pid):
    p = next((x for x in pools if x["id"] == pid), None)
    return set(p.get("collectibles", [])) if p else set()

def coll(s):
    by = {it["itemId"]: it for it in classifier_items}
    return {x for x in s if by.get(x, {}).get("dataType") == "藏品"}

guiyi_set = coll(pset("rogue_6:诡意行商"))
huxian_set = coll(pset("rogue_6:不期而遇：湖中仙女") | pset("rogue_6:不期而遇：湖中仙女（紧急）") | pset("rogue_6:不期而遇：湖中仙女（直接收藏品）"))
xianlu_set = coll(pset("rogue_6:pool_boss"))

prts_by_icon = {pi.get("sourceIconId"): pi for pi in prts_items}

def base_id(cid):
    for suf in ("_a", "_b", "_c"):
        if cid.endswith(suf):
            return cid[: -len(suf)]
    return cid

rows = []
for it in classifier_items:
    if it.get("dataType") != "藏品":
        continue
    cid = it["itemId"]; rarity = it.get("rarity"); rm = RARITY_META.get(rarity, {})
    pi = prts_by_icon.get(base_id(cid))
    no = pi.get("numberLabel", "") if pi else ""
    no_num = int(pi.get("number")) if pi else None
    category = pi.get("category", "") if pi else ""
    price = rm.get("price") if rarity in RARITY_META else None
    pools_list = []; nodes_list = []
    for pid in item_pools.get(cid, []):
        pm = pool_meta_map.get(pid)
        if not pm:
            continue
        pools_list.append(pm["name"])
        if not pm["is_input"]:
            for n in pm["nodes"]:
                if n and n not in nodes_list:
                    nodes_list.append(n)
    rows.append({
        "no": no, "no_num": no_num, "name": it.get("name", ""),
        "rarity": rarity or "", "rarity_label": rm.get("label", ""),
        "rarity_short": rm.get("short", ""), "rarity_order": rm.get("order", 0),
        "price": price, "in_guiyi": cid in guiyi_set,
        "can_sacrifice": bool(it.get("canSacrifice")),
        "category": category, "pools": pools_list, "nodes": nodes_list,
        "g": cid in guiyi_set, "h": cid in huxian_set, "x": cid in xianlu_set,
    })

rows.sort(key=lambda r: (-r["rarity_order"], r["no_num"] if r["no_num"] is not None else 99999, r["name"]))
data_json = json.dumps(rows, ensure_ascii=False)

# 图标 base64
icon_b64 = ""
if os.path.exists(SEAL_PNG):
    icon_b64 = base64.b64encode(open(SEAL_PNG, "rb").read()).decode("ascii")

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>沉沦者的黑流树海 · 藏品工具</title>
<link rel="icon" type="image/png" href="data:image/png;base64,__ICON__">
<style>
  :root{--bg:#0f1420;--card:#1a2130;--card2:#222c40;--line:#2e3a52;--txt:#e8edf6;--sub:#9aa7bd;--acc:#35d0a5;--acc2:#4da3ff;--warn:#ffb454;--gold:#e8b23a;--blue:#4da3ff;--white:#c9cdd3;--good:#7ecf8b}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    background:radial-gradient(1200px 600px at 20% -10%,#1b2740 0%,transparent 60%),radial-gradient(900px 500px at 100% 0%,#122a2a 0%,transparent 55%),var(--bg);
    color:var(--txt);min-height:100vh;padding:28px 16px 60px}
  .wrap{max-width:1000px;margin:0 auto}
  header{display:flex;align-items:center;gap:14px}
  .logo{width:48px;height:48px;border-radius:10px;background:var(--card);border:1px solid var(--line);padding:5px;flex-shrink:0}
  h1{font-size:22px;font-weight:700;letter-spacing:.5px}
  .sub{color:var(--sub);font-size:13px;margin-top:4px}
  .tabs{margin-top:20px;display:flex;gap:8px;flex-wrap:wrap}
  .tab{background:var(--card);border:1px solid var(--line);color:var(--sub);border-radius:999px;padding:9px 20px;font-size:14px;cursor:pointer;transition:.15s}
  .tab:hover{color:var(--txt)}
  .tab.active{background:var(--acc);border-color:var(--acc);color:#06130e;font-weight:700}
  section{margin-top:16px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px}
  .searchbar input{width:100%;background:var(--card2);border:1px solid var(--line);border-radius:12px;color:var(--txt);font-size:15px;padding:13px 16px;outline:none;transition:.15s}
  .searchbar input:focus{border-color:var(--acc);box-shadow:0 0 0 3px rgba(53,208,165,.12)}
  .searchbar input::placeholder{color:#5b6677}
  .filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
  .filter{position:relative;display:block;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;cursor:pointer;transition:.15s;user-select:none}
  .filter:hover{border-color:#3b4a68}
  .filter.active{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc),0 8px 24px rgba(53,208,165,.12)}
  .filter input{position:absolute;opacity:0;pointer-events:none}
  .fhead{display:flex;align-items:center;gap:12px}
  .ficon{width:40px;height:40px;border-radius:12px;background:var(--card2);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
  .ftitle{flex:1}
  .fname{font-size:15px;font-weight:700}
  .fdesc{font-size:11px;color:var(--sub);margin-top:2px}
  .fcount{font-size:13px;font-weight:700;color:var(--sub);white-space:nowrap}
  .filter.active .fcount{color:var(--acc)}
  .switch{width:42px;height:23px;border-radius:999px;background:var(--card2);border:1px solid var(--line);position:relative;transition:.15s;flex-shrink:0}
  .switch::after{content:"";position:absolute;top:2px;left:2px;width:17px;height:17px;border-radius:50%;background:var(--sub);transition:.18s}
  .filter.active .switch{background:var(--acc);border-color:var(--acc)}
  .filter.active .switch::after{left:21px;background:#06130e}
  .toolbar{margin-top:14px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
  .toolbar .sel{font-size:14px;color:var(--sub)}
  .toolbar .sel b{color:var(--acc);font-size:16px}
  .toolbar .spacer{flex:1}
  .fgroups{display:flex;flex-wrap:wrap;gap:8px}
  .fgroup{display:flex;gap:4px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:4px}
  .fbtn{padding:5px 12px;border-radius:6px;border:none;background:transparent;color:var(--sub);cursor:pointer;font-size:13px;white-space:nowrap}
  .fbtn:hover{color:var(--txt)}
  .fbtn.active{background:var(--acc);color:#06130e;font-weight:600}
  .btn{background:var(--card2);border:1px solid var(--line);color:var(--sub);border-radius:999px;padding:6px 16px;font-size:13px;cursor:pointer;transition:.15s}
  .btn:hover{color:var(--txt);border-color:var(--acc)}
  .tablewrap{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;overflow-x:auto}
  table{border-collapse:collapse;width:100%;font-size:13px;min-width:760px}
  th,td{padding:10px 13px;text-align:left;border-bottom:1px solid #232931;vertical-align:top}
  th{color:var(--sub);font-weight:600;font-size:12px;background:var(--card2);position:sticky;top:0;z-index:2;white-space:nowrap}
  tbody tr:hover{background:var(--card2)}
  td.num{color:var(--sub);font-size:12px;font-variant-numeric:tabular-nums;white-space:nowrap}
  td.name{font-weight:600;min-width:130px}
  .badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;white-space:nowrap}
  .badge.gold{background:rgba(232,178,58,.16);color:var(--gold)}
  .badge.blue{background:rgba(79,143,216,.16);color:var(--blue)}
  .badge.white{background:rgba(201,205,211,.14);color:var(--white)}
  .price-buy{color:var(--gold);font-weight:600;white-space:nowrap}
  .price-no{color:var(--sub);white-space:nowrap}
  .sac-yes{color:var(--good);font-weight:600}
  .sac-no{color:var(--sub)}
  .src{display:inline-flex;gap:4px;flex-wrap:wrap}
  .src span{display:inline-block;padding:1px 8px;border-radius:6px;font-size:11px;border:1px solid var(--line);color:var(--sub)}
  .src span.g{background:rgba(53,208,165,.12);border-color:rgba(53,208,165,.35);color:var(--acc)}
  .src span.h{background:rgba(77,163,255,.12);border-color:rgba(77,163,255,.35);color:var(--blue)}
  .src span.x{background:rgba(255,180,84,.12);border-color:rgba(255,180,84,.35);color:var(--warn)}
  .tags{display:flex;flex-wrap:wrap;gap:4px}
  .tag{display:inline-block;padding:1px 8px;border-radius:6px;font-size:11px;background:var(--card2);border:1px solid var(--line);color:var(--sub);white-space:nowrap}
  .tag.node{background:rgba(79,143,216,.10);border-color:rgba(79,143,216,.30);color:#8db8e8}
  .tag.pool{background:rgba(232,178,58,.08);border-color:rgba(232,178,58,.22);color:#d9b25f}
  .tag.empty{color:#565d66;border-style:dashed}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
  .stat{background:var(--card2);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
  .stat .v{font-size:20px;font-weight:600}
  .stat .k{font-size:12px;color:var(--sub);margin-top:2px}
  .legend{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-top:14px;font-size:13px;color:var(--sub);line-height:1.8}
  .legend b{color:var(--txt)}
  .chip{display:inline-block;padding:1px 8px;border-radius:10px;margin:0 3px;font-size:12px;color:#0e1116;font-weight:600}
  .empty{margin-top:16px;background:var(--card);border:1px dashed var(--line);border-radius:16px;padding:36px 20px;text-align:center;color:var(--sub);font-size:14px}
  .note{color:var(--sub);font-size:12px;margin-top:18px;line-height:1.8}
  .note a{color:var(--acc)}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <img class="logo" src="data:image/png;base64,__ICON__" alt="博士银印">
    <div>
      <h1>沉沦者的黑流树海 · 藏品工具</h1>
      <div class="sub">《明日方舟》集成战略第六主题 · 收藏品数据工具（单文件离线版）</div>
    </div>
  </header>

  <nav class="tabs">
    <button class="tab active" data-view="filter">🎯 获取筛选器</button>
    <button class="tab" data-view="table">📋 收藏品一览表</button>
  </nav>

  <section id="view-filter">
    <div class="searchbar"><input id="f-search" type="text" placeholder="🔍 按物品名称搜索（支持编号，如「女妖之吻」「No.013」）" autocomplete="off"></div>
    <div class="filters" id="filters"></div>
    <div class="toolbar">
      <span class="sel">命中 <b id="f-count">0</b> 件藏品</span>
      <span class="spacer"></span>
      <button class="btn" id="f-all">全选</button>
      <button class="btn" id="f-clear">清空</button>
    </div>
    <div class="tablewrap" style="margin-top:14px">
      <table><thead><tr><th>编号</th><th>名称</th><th>稀有度</th><th>诡意行商售价</th><th>失与得</th><th>命中来源</th></tr></thead><tbody id="f-tbody"></tbody></table>
    </div>
  </section>

  <section id="view-table" style="display:none">
    <div class="cards" id="stats"></div>
    <div class="legend">
      <b>稀有度（低→高）</b>：<span class="chip" style="background:#c9cdd3">N</span> 普通 → <span class="chip" style="background:#4da3ff">R</span> 稀有 → <span class="chip" style="background:#e8b23a">SR</span> 超稀有。
      <b>售价规则</b>：诡意行商按稀有度 N=8 / R=12 / SR=16 源石锭；「不可购买」= 不在诡意行商常规库存。
    </div>
    <div class="toolbar">
      <div class="searchbar" style="flex:1;min-width:220px"><input id="t-search" type="text" placeholder="搜索编号或名称…" autocomplete="off"></div>
      <div class="fgroups">
        <div class="fgroup" id="t-rarity"></div>
        <div class="fgroup" id="t-sac"></div>
        <div class="fgroup" id="t-price"></div>
      </div>
      <span class="sel" id="t-count"></span>
    </div>
    <div class="tablewrap" style="margin-top:14px">
      <table><thead><tr>
        <th data-sort="no">编号</th><th data-sort="name">名称</th><th data-sort="rarity">稀有度</th><th data-sort="price">诡意行商售价</th><th data-sort="sac">失与得</th><th data-sort="category">分类</th><th>藏品池</th><th>可获取节点</th>
      </tr></thead><tbody id="t-tbody"></tbody></table>
    </div>
  </section>

  <div class="note">
    数据来源：路标档案馆藏品池（归档于 2026-08-24）。本文件为单文件离线版，数据与图标已全部内嵌，可随意移动位置、离线打开。项目仓库：<a href="https://github.com/Christina-tz/arknights-blackstream-relics" target="_blank">GitHub · arknights-blackstream-relics</a>
  </div>
</div>

<script>
const DATA = __DATA__;
const R = {SUPER_RARE:{label:"SR",cls:"gold"},RARE:{label:"R",cls:"blue"},NORMAL:{label:"N",cls:"white"}};
const RF = {SUPER_RARE:{label:"超稀有",cls:"gold"},RARE:{label:"稀有",cls:"blue"},NORMAL:{label:"普通",cls:"white"}};
const $ = id => document.getElementById(id);

// ---------- 标签切换 ----------
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
  t.classList.add('active');
  $('view-filter').style.display = t.dataset.view === 'filter' ? 'block' : 'none';
  $('view-table').style.display = t.dataset.view === 'table' ? 'block' : 'none';
}));

// ---------- 筛选器视图 ----------
const SRCS = [
  {key:'g', icon:'🏪', name:'诡意行商', desc:'BATTLE_SHOP · 商品库存'},
  {key:'h', icon:'🧚', name:'湖中仙女', desc:'不期而遇 · 普通/紧急/直接'},
  {key:'x', icon:'⚔️', name:'险路恶敌', desc:'三层 BATTLE_BOSS · 收藏品二选一'},
];
const fstate = {g:false,h:false,x:false,q:""};

function buildFCards(){
  $('filters').innerHTML = SRCS.map(s=>{
    const n = DATA.filter(r=>r[s.key]).length;
    return `<label class="filter ${fstate[s.key]?'active':''}" data-key="${s.key}">
      <input type="checkbox" ${fstate[s.key]?'checked':''}>
      <div class="fhead"><div class="ficon">${s.icon}</div>
      <div class="ftitle"><div class="fname">${s.name}</div><div class="fdesc">${s.desc}</div></div>
      <div class="fcount">${n} 件</div><div class="switch"></div></div>
    </label>`;
  }).join("");
}
function fFiltered(){
  const keys = SRCS.filter(s=>fstate[s.key]).map(s=>s.key);
  let r = keys.length ? DATA.filter(x=>keys.every(k=>x[k])) : DATA;
  const q = fstate.q.trim().toLowerCase();
  if(q) r = r.filter(x => x.name.toLowerCase().includes(q) || (x.no||"").toLowerCase().includes(q));
  return r;
}
function srcTags(r){
  const t=[]; if(r.g)t.push('<span class="g">诡意行商</span>'); if(r.h)t.push('<span class="h">湖中仙女</span>'); if(r.x)t.push('<span class="x">险路恶敌</span>');
  return t.length?`<div class="src">${t.join('')}</div>`:'<span style="color:var(--sub)">—</span>';
}
function renderFilter(){
  const rows = fFiltered(); $('f-count').textContent = rows.length;
  $('f-tbody').innerHTML = rows.map(r=>{
    const rm = R[r.rarity]||{label:r.rarity_label||"—",cls:"white"};
    const pr = r.price==null?`<span class="price-no">不可购买</span>`:`<span class="price-buy">${r.price} 源石锭</span>`;
    const sac = r.can_sacrifice?'<span class="sac-yes">可交换</span>':'<span class="sac-no">不可交换</span>';
    return `<tr><td class="num">${r.no||"—"}</td><td class="name">${r.name}</td><td><span class="badge ${rm.cls}">${rm.label}</span></td><td>${pr}</td><td>${sac}</td><td>${srcTags(r)}</td></tr>`;
  }).join("");
}
$('filters').addEventListener('click', e=>{
  const f = e.target.closest('.filter'); if(!f) return;
  const k = f.dataset.key; fstate[k] = !fstate[k]; buildFCards(); renderFilter();
});
$('f-search').addEventListener('input', e=>{ fstate.q = e.target.value; renderFilter(); });
$('f-all').onclick = ()=>{ SRCS.forEach(s=>fstate[s.key]=true); buildFCards(); renderFilter(); };
$('f-clear').onclick = ()=>{ SRCS.forEach(s=>fstate[s.key]=false); buildFCards(); renderFilter(); };

// ---------- 一览表视图 ----------
const tstate = {q:"",rarity:"全部",sac:"全部",price:"全部",sort:"rarity",asc:false};

function priceText(r){ return r.price==null?"不可购买":r.price+" 源石锭"; }
function renderStats(){
  const rar={},sac={};
  DATA.forEach(r=>{ rar[r.rarity_label]=(rar[r.rarity_label]||0)+1; sac[r.can_sacrifice?"可交换":"不可交换"]=(sac[r.can_sacrifice?"可交换":"不可交换"]||0)+1; });
  const cards=[
    {k:"收藏品总数",v:DATA.length+" 件"},
    {k:"超稀有(SR)",v:(rar["超稀有"]||0)+" 件",c:"var(--gold)"},
    {k:"稀有(R)",v:(rar["稀有"]||0)+" 件",c:"var(--blue)"},
    {k:"普通(N)",v:(rar["普通"]||0)+" 件",c:"var(--white)"},
    {k:"失与得·可交换",v:(sac["可交换"]||0)+" 件",c:"var(--good)"},
    {k:"不可交换",v:(sac["不可交换"]||0)+" 件"},
    {k:"诡意行商可购",v:DATA.filter(r=>r.in_guiyi).length+" 件",c:"var(--acc)"},
  ];
  $('stats').innerHTML = cards.map(c=>`<div class="stat"><div class="v" style="${c.c?'color:'+c.c:''}">${c.v}</div><div class="k">${c.k}</div></div>`).join("");
}
function buildTFilters(){
  const ro=["全部","超稀有","稀有","普通"];
  $('t-rarity').innerHTML = ro.map(o=>`<button class="fbtn ${tstate.rarity===o?'active':''}" data-rarity="${o}">${o}</button>`).join("");
  const so=["全部","可交换","不可交换"];
  $('t-sac').innerHTML = so.map(o=>`<button class="fbtn ${tstate.sac===o?'active':''}" data-sac="${o}">失与得·${o}</button>`).join("");
  const po=["全部","8 源石锭","12 源石锭","16 源石锭","不可购买"];
  $('t-price').innerHTML = po.map(o=>`<button class="fbtn ${tstate.price===o?'active':''}" data-price="${o}">售价·${o}</button>`).join("");
}
function tFiltered(){
  let r = DATA.filter(x=>{
    if(tstate.q){ const q=tstate.q.toLowerCase(); if(!(x.name.toLowerCase().includes(q)||x.no.toLowerCase().includes(q))) return false; }
    if(tstate.rarity!=="全部" && x.rarity_label!==tstate.rarity) return false;
    if(tstate.sac!=="全部" && (x.can_sacrifice?"可交换":"不可交换")!==tstate.sac) return false;
    if(tstate.price!=="全部" && priceText(x)!==tstate.price) return false;
    return true;
  });
  const k=tstate.sort;
  r.sort((a,b)=>{
    let va,vb;
    if(k==="no"){va=a.no_num??99999;vb=b.no_num??99999;}
    else if(k==="name"){return tstate.asc?a.name.localeCompare(b.name,"zh"):b.name.localeCompare(a.name,"zh");}
    else if(k==="rarity"){va=a.rarity_order;vb=b.rarity_order;}
    else if(k==="price"){va=a.price??0;vb=b.price??0;}
    else if(k==="sac"){va=a.can_sacrifice?1:0;vb=b.can_sacrifice?1:0;}
    else if(k==="category"){return tstate.asc?a.category.localeCompare(b.category,"zh"):b.category.localeCompare(a.category,"zh");}
    return tstate.asc?va-vb:vb-va;
  });
  return r;
}
function ttags(arr,cls){
  if(!arr||!arr.length) return '<span class="tag empty">—</span>';
  return `<div class="tags">${arr.map(x=>`<span class="tag ${cls}">${x}</span>`).join('')}</div>`;
}
function renderTable(){
  const rows=tFiltered(); $('t-count').textContent=`共 ${rows.length} / ${DATA.length} 件`;
  $('t-tbody').innerHTML=rows.map(r=>{
    const rm=RF[r.rarity]||{label:r.rarity_label||"—",cls:"white"};
    const pr=r.price==null?`<span class="price-no">不可购买</span>`:`<span class="price-buy">${r.price}</span> <span style="color:var(--sub);font-size:12px">源石锭</span>`;
    const sac=r.can_sacrifice?'<span class="sac-yes">可交换</span>':'<span class="sac-no">不可交换</span>';
    return `<tr><td class="num">${r.no||"—"}</td><td class="name">${r.name}</td><td><span class="badge ${rm.cls}">${rm.label}</span></td><td>${pr}</td><td>${sac}</td><td>${r.category||"—"}</td><td>${ttags(r.pools,"pool")}</td><td>${ttags(r.nodes,"node")}</td></tr>`;
  }).join("");
}
$('t-search').addEventListener('input', e=>{ tstate.q=e.target.value; renderTable(); });
document.querySelectorAll('.fgroup').forEach(g=>g.addEventListener('click', e=>{
  const b=e.target.closest('button'); if(!b) return;
  if(b.dataset.rarity!==undefined){tstate.rarity=b.dataset.rarity;buildTFilters();}
  if(b.dataset.sac!==undefined){tstate.sac=b.dataset.sac;buildTFilters();}
  if(b.dataset.price!==undefined){tstate.price=b.dataset.price;buildTFilters();}
  renderTable();
}));
document.querySelectorAll('thead th[data-sort]').forEach(th=>th.addEventListener('click', ()=>{
  const k=th.dataset.sort; if(tstate.sort===k)tstate.asc=!tstate.asc; else{tstate.sort=k;tstate.asc=false;}
  renderTable();
}));

// ---------- 初始化 ----------
buildFCards(); renderFilter();
renderStats(); buildTFilters(); renderTable();
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", data_json).replace("__ICON__", icon_b64)
out = os.path.join(BASE, "沉沦者的黑流树海_藏品工具.html")
open(out, "w", encoding="utf-8").write(html)
print("OK:", out, len(html), "bytes;", len(rows), "rows; icon_b64", len(icon_b64))
