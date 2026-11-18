import html
import json
from datetime import date
from pathlib import Path
from urllib.parse import quote as _quote
import pandas as pd
import streamlit as st
from .config import ROOT, WATERMARK, STATUS_LABELS, COLORS, load_rules
from .database import list_zones, save_zones, save_analysis, save_review, get_reviews, list_datasets, latest_analyses, reviews_for_analyses
from .schemas import PARAMETERS, LANDCOVERS, LEGAL, QUALITIES, normalize_zone, values, ValidationError
from .geospatial import area_ha, center
from .services import analyse_zone
from .report_service import export_csv, export_geojson, export_markdown, export_html, safe_cell
from .prioritization import survey_sort
from .data_io import parse_upload
from .model_service import get_model_status, load_card
from .explain_service import explain_zone
from .training import read_card, approval_blockers, CANDIDATE_DIR

# Latar hero: ilustrasi kanopi & alur pasang buatan (SVG prosedural), bukan citra satelit.
_HERO_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1400 620' preserveAspectRatio='xMidYMid slice'>
<defs>
<filter id='c' x='0' y='0' width='100%' height='100%'><feTurbulence type='fractalNoise' baseFrequency='0.012 0.016' numOctaves='5' seed='11'/><feColorMatrix values='0.30 0 0 0 -0.02  0.85 0 0 0 0.02  0.28 0 0 0 0  0 0 0 0 1'/></filter>
<filter id='f' x='0' y='0' width='100%' height='100%'><feTurbulence type='turbulence' baseFrequency='0.11' numOctaves='3' seed='4'/><feColorMatrix values='0 0 0 0 0.02  0 0 0 0 0.10  0 0 0 0 0.04  1.1 0 0 0 -0.3'/></filter>
<filter id='b'><feGaussianBlur stdDeviation='3'/></filter>
<filter id='m'><feGaussianBlur stdDeviation='38'/></filter>
<filter id='w'><feTurbulence type='fractalNoise' baseFrequency='0.02' numOctaves='2' seed='3'/><feDisplacementMap in='SourceGraphic' scale='26'/></filter>
</defs>
<rect width='1400' height='620' fill='#0d3a1e'/>
<rect width='1400' height='620' filter='url(#c)'/>
<rect width='1400' height='620' filter='url(#f)'/>
<g filter='url(#w)'>
<path d='M-40 470 C 160 430 230 520 380 440 S 560 250 690 300 S 820 470 960 400 S 1180 180 1460 230' fill='none' stroke='#8a8a5c' stroke-width='40' stroke-linecap='round' filter='url(#b)' opacity='.75'/>
<path d='M-40 470 C 160 430 230 520 380 440 S 560 250 690 300 S 820 470 960 400 S 1180 180 1460 230' fill='none' stroke='#2f6f67' stroke-width='22' stroke-linecap='round'/>
<path d='M690 300 C 720 200 640 130 700 -20' fill='none' stroke='#2f6f67' stroke-width='9' stroke-linecap='round'/>
<path d='M380 440 C 350 520 420 560 400 660' fill='none' stroke='#2f6f67' stroke-width='7' stroke-linecap='round'/>
<path d='M960 400 C 1010 480 980 560 1040 660' fill='none' stroke='#2f6f67' stroke-width='8' stroke-linecap='round'/>
</g>
<ellipse cx='520' cy='150' rx='260' ry='70' fill='#fff' opacity='.20' filter='url(#m)'/>
<ellipse cx='1050' cy='470' rx='220' ry='60' fill='#fff' opacity='.12' filter='url(#m)'/>
</svg>"""
_HERO_PHOTO = ROOT / 'assets' / 'hero_mangrove.jpg'
def _hero_bg():
    # Foto latar bila tersedia; jatuh kembali ke ilustrasi SVG bila berkas tidak ada.
    if _HERO_PHOTO.exists():
        import base64
        return 'data:image/jpeg;base64,' + base64.b64encode(_HERO_PHOTO.read_bytes()).decode()
    return 'data:image/svg+xml,' + _quote(_HERO_SVG.replace('\n',''))
_HERO_BG = _hero_bg()

_CSS = r"""
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap');
    :root{--bg:#f4f9f3;--panel:#ffffff;--panel-2:#ecf6ec;--line:#d6e6d7;--g:#1c9a45;--g-hi:#2fbe4d;--g-deep:#0f6a30;--tx:#14301f;--tx-2:#4b6655;--tx-3:#7a917f;--amber:#e9b949;--shadow:0 1px 2px rgba(20,48,31,.05),0 6px 18px -12px rgba(20,48,31,.18);
      --ease:cubic-bezier(.2,.7,.2,1);--t-fast:150ms;--t:280ms;--cond:'Barlow Condensed','Arial Narrow','Roboto Condensed',Impact,sans-serif}
    html,body,[data-testid="stAppViewContainer"]{background:var(--bg)}
    [data-testid="stHeader"]{background:transparent}
    html,body,p,li,label,input,textarea,button,[data-testid="stMarkdownContainer"]{font-family:'Barlow','Segoe UI',system-ui,sans-serif}
    .block-container{padding:3.4rem 2.4rem 3rem;max-width:1500px;animation:mf-in var(--t) var(--ease) both}
    h1,h2,h3{font-family:var(--cond)!important;color:var(--tx)!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.5px!important}
    h1{font-size:3rem!important;line-height:1!important}h2{font-size:1.8rem!important;line-height:1.05!important}h3{font-size:1.3rem!important}
    [data-testid="stCaptionContainer"]{color:var(--tx-2)}
    /* Sidebar */
    [data-testid="stSidebar"]{background:var(--panel);border-right:1px solid var(--line)}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.75rem}
    [data-testid="stSidebarNav"] a{border-radius:0;border-left:3px solid transparent;transition:background var(--t-fast) var(--ease),border-color var(--t-fast) var(--ease),padding-left var(--t) var(--ease)}
    [data-testid="stSidebarNav"] a span:not([data-testid="stIconMaterial"]){font-family:var(--cond);text-transform:uppercase;letter-spacing:.8px;font-size:15px}
    [data-testid="stSidebarNav"] a:hover{background:var(--panel-2);border-left-color:var(--g-deep);padding-left:1.05rem}
    [data-testid="stSidebarNav"] a[aria-current="page"]{background:var(--panel-2);border-left-color:var(--g)}
    [data-testid="stNavSectionHeader"]{font-family:var(--cond);letter-spacing:1.6px;color:var(--tx-3)}
    .brand{background:var(--g);color:#04200e;padding:14px 16px 12px;display:flex;gap:12px;align-items:center}
    .brand-mark{width:30px;height:30px;border:2px solid #04200e;border-radius:50% 50% 50% 3px;position:relative;flex:none}
    .brand-mark::after{content:"";position:absolute;inset:6px;border-radius:50% 50% 50% 2px;background:#04200e}
    .brand-name{font-family:var(--cond);font-weight:700;font-size:23px;letter-spacing:1px;line-height:1}.brand-name span{font-weight:500;margin-left:3px}
    .brand-sub{font-family:var(--cond);font-size:11px;letter-spacing:1.2px;margin-top:4px;opacity:.8}
    .eyebrow{font-family:var(--cond);font-size:14px;letter-spacing:2px;font-weight:600;color:var(--g-deep);margin-bottom:6px;text-transform:uppercase}
    /* Hero */
    .hero{position:relative;display:grid;grid-template-columns:minmax(0,1fr) 380px;min-height:470px;margin:-.6rem -2.4rem 26px;background:#0d3a1e url("__HERO_BG__") 40% 55%/cover no-repeat;overflow:hidden}
    .hero-main{position:relative;display:flex;flex-direction:column;justify-content:space-between;padding:0 0 26px 2.4rem;background:linear-gradient(180deg,rgba(4,23,12,.0) 35%,rgba(4,23,12,.8)),linear-gradient(90deg,rgba(4,23,12,.25),transparent 40%)}
    .hero-brand{align-self:flex-start;background:var(--g);color:#04200e;padding:22px 26px 18px;font-family:var(--cond);font-weight:700;font-size:30px;letter-spacing:1.5px;line-height:1}
    .hero-brand small{display:block;font-size:13px;font-weight:600;letter-spacing:2px;margin-top:8px;opacity:.85}
    .hero-count{font-family:var(--cond);color:#fff;text-shadow:0 2px 14px rgba(0,0,0,.55)}
    .hero-count b{font-size:64px;font-weight:700;line-height:.9;display:block}
    .hero-count span{font-size:16px;letter-spacing:2.4px;text-transform:uppercase}
    .hero-count em{display:block;font-style:normal;font-family:'Barlow',sans-serif;font-size:11px;color:rgba(255,255,255,.6);margin-top:8px;letter-spacing:.3px}
    .hero-panel{background:linear-gradient(180deg,#0a4a22,#06331a);padding:44px 34px 34px;display:flex;flex-direction:column;justify-content:center;border-left:1px solid rgba(255,255,255,.08)}
    .hero-panel h1{color:#fff!important;font-size:3.5rem!important;line-height:.95!important;margin:0 0 12px;padding:0}
    .hero-panel .sub{font-family:var(--cond);font-size:19px;letter-spacing:2px;color:var(--g-hi);text-transform:uppercase;margin-bottom:16px}
    .hero-panel p{color:#cfe3d2;font-size:14.5px;line-height:1.6;margin:0 0 18px}
    .hero-panel ol{list-style:none;margin:0;padding:0;border-top:1px solid rgba(255,255,255,.14)}
    .hero-panel li{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.6px;font-size:15px;color:#fff;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.14);display:flex;gap:14px;transition:padding-left var(--t) var(--ease),color var(--t) var(--ease)}
    .hero-panel li:hover{padding-left:8px;color:var(--g-hi)}.hero-panel li i{font-style:normal;color:var(--g-hi)}
    /* Blocks */
    [data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--g);padding:16px 20px;border-radius:0;transition:transform var(--t) var(--ease),background var(--t) var(--ease),border-color var(--t) var(--ease)}
    [data-testid="stMetric"]:hover{transform:translateY(-3px);background:var(--panel-2);border-color:var(--g)}
    [data-testid="stMetricLabel"] *{font-family:var(--cond)!important;text-transform:uppercase;letter-spacing:1.4px;color:var(--tx-2);font-size:14px!important;white-space:normal!important;overflow:visible!important}
    [data-testid="stMetricValue"]{font-family:var(--cond);font-weight:700;font-size:2.5rem;line-height:1.05;color:var(--tx)}
    [data-testid="stMetricValue"] *{white-space:normal!important;overflow:visible!important}
    .status-badge{display:inline-block;font-family:var(--cond);font-size:14px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;border-radius:0;padding:4px 10px;margin-bottom:10px;color:#fff!important}
    .card{padding:22px 24px;border:1px solid var(--line);border-left:3px solid var(--g-deep);background:var(--panel);border-radius:0;height:100%;margin:8px 0 16px;transition:border-color var(--t) var(--ease),transform var(--t) var(--ease),background var(--t) var(--ease)}
    .card:hover{border-left-color:var(--g);transform:translateX(4px);background:var(--panel-2)}
    .card h3{margin-top:4px;padding-bottom:.3rem}.card p{color:var(--tx-2);font-size:14.5px;margin-bottom:0;line-height:1.6}
    .small-label{font-family:var(--cond);font-size:13px;letter-spacing:2px;color:var(--g-deep);text-transform:uppercase}
    .watermark{display:flex;align-items:center;gap:14px;font-size:13.5px;color:#6b4e0a;background:#fff7e0;border:1px solid #efd99e;padding:8px 10px;margin:0 0 22px}
    .watermark b{font-family:var(--cond);letter-spacing:1.8px;font-size:13px;background:var(--amber);color:#3a2a00;padding:3px 9px}
    .watermark span{letter-spacing:.2px}
    .stats{display:grid;grid-template-columns:240px minmax(0,1fr);background:var(--panel);border:1px solid var(--line);margin:0 0 22px}
    .stats-total{padding:22px 26px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:2px}
    .stats-total b{font-family:var(--cond);font-size:68px;line-height:.9;color:var(--tx);font-weight:700}
    .stats-total span{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.8px;font-size:15px;color:var(--g-deep);margin-top:6px}
    .stats-total small{color:var(--tx-3);font-size:12.5px}
    .stats-dist{padding:22px 28px;display:flex;flex-direction:column;justify-content:center;gap:14px}
    .stats-cap{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.8px;font-size:13px;color:var(--tx-3)}
    .stats-bar{display:flex;gap:3px;height:10px}
    .stats-bar i{display:block;transform-origin:left;animation:mf-grow .7s var(--ease) both}
    .stats-bar i:nth-child(2){animation-delay:.08s}.stats-bar i:nth-child(3){animation-delay:.16s}
    .stats-leg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
    .leg{display:flex;align-items:baseline;gap:12px;padding-top:2px}
    .leg b{font-family:var(--cond);font-size:38px;line-height:1;font-weight:700}
    .leg span{display:flex;align-items:center;gap:7px;color:var(--tx-2);font-size:13.5px;line-height:1.3}
    .leg em{width:8px;height:8px;flex:none;display:inline-block}
    [class*="st-key-mf_act_"]{background:var(--panel);border:1px solid var(--line);padding:22px 22px 18px;gap:.4rem;height:100%;position:relative;transition:border-color var(--t) var(--ease),background var(--t) var(--ease),transform var(--t) var(--ease)}
    [class*="st-key-mf_act_"]::before{content:"";position:absolute;left:-1px;top:-1px;height:3px;width:0;background:var(--g);transition:width .45s var(--ease)}
    [class*="st-key-mf_act_"]:hover{border-color:var(--g);background:var(--panel);transform:translateY(-3px);box-shadow:0 14px 30px -18px rgba(15,106,48,.45)}
    [class*="st-key-mf_act_"]:hover::before{width:calc(100% + 2px)}
    .act-n{font-family:var(--cond);font-size:13px;letter-spacing:2px;color:var(--g-deep)}
    .act-t{font-family:var(--cond);font-size:26px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--tx);line-height:1.05;margin-top:2px}
    .act-d{color:var(--tx-2);font-size:14px;line-height:1.55;margin:6px 0 8px;min-height:44px}
    [class*="st-key-mf_act_"] [data-testid="stPageLink"] a{min-height:40px;border-color:var(--line)}
    [data-testid="stColumn"]>[data-testid="stVerticalBlock"]>[data-testid="stLayoutWrapper"]:has(>[class*="st-key-mf_act_"]){flex:1;display:flex}
    [class*="st-key-mf_act_"]{flex:1}
    [class*="st-key-mf_act_"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]){margin-top:auto;width:100%}
    [class*="st-key-mf_act_"] [data-testid="stPageLink"],[class*="st-key-mf_act_"] [data-testid="stPageLink"] a{width:100%}
    [class*="st-key-mf_maptools"]{background:var(--panel);border:1px solid var(--line);padding:14px 18px 12px;box-shadow:var(--shadow);margin-bottom:6px}
    [class*="st-key-mf_mapframe"]{border:1px solid var(--line);box-shadow:var(--shadow);background:var(--panel);padding:4px}
    [class*="st-key-mf_mapframe"] iframe{display:block}
    .st-key-map_basemap [role="radiogroup"]{gap:0!important;flex-wrap:nowrap}
    .st-key-map_basemap [role="radiogroup"]>label{margin:0!important;padding:7px 12px;border:1px solid var(--line);background:var(--panel);cursor:pointer;transition:background var(--t-fast) var(--ease),border-color var(--t-fast) var(--ease)}
    .st-key-map_basemap [role="radiogroup"]>label+label{border-left:0}
    .st-key-map_basemap [role="radiogroup"]>label:hover{background:var(--panel-2)}
    .st-key-map_basemap [role="radiogroup"]>label:has(input:checked){background:var(--g);border-color:var(--g)}
    .st-key-map_basemap [role="radiogroup"]>label:has(input:checked) p{color:#fff}
    .st-key-map_basemap [role="radiogroup"]>label>div:first-child{display:none}
    .st-key-map_basemap [role="radiogroup"] p{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.2px;font-size:14px}
    .map-legend{display:flex;flex-wrap:wrap;align-items:center;gap:8px 22px;padding:12px 16px;background:var(--panel);border:1px solid var(--line);border-top:0;margin-top:-1rem}
    .ml-cap{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.6px;font-size:13px;color:var(--tx-3);margin-right:6px}
    .ml-item{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--tx-2)}
    .ml-item i{width:14px;height:14px;display:inline-block;opacity:.85}
    .ml-item b{font-family:var(--cond);font-size:18px;color:var(--tx)}
    .zcard{background:var(--panel);border:1px solid var(--line);border-top:4px solid var(--zc);padding:20px 22px 16px;box-shadow:var(--shadow);margin:6px 0 12px;animation:mf-in var(--t) var(--ease) both}
    .zc-id{font-family:var(--cond);letter-spacing:1.6px;font-size:13px;color:var(--tx-3);text-transform:uppercase}
    .zc-name{font-family:var(--cond);font-weight:700;font-size:28px;line-height:1.05;text-transform:uppercase;color:var(--tx);margin:4px 0 10px}
    .zc-pill{display:inline-block;background:var(--zc);color:#fff;font-family:var(--cond);text-transform:uppercase;letter-spacing:1.2px;font-size:13px;padding:3px 10px}
    .zc-grid{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin:16px 0 0}
    .zc-grid div{padding:12px 0}.zc-grid div+div{border-left:1px solid var(--line);padding-left:16px}
    .zc-grid span,.zc-rec span{display:block;font-family:var(--cond);text-transform:uppercase;letter-spacing:1.4px;font-size:12.5px;color:var(--tx-3)}
    .zc-grid b{font-family:var(--cond);font-size:30px;color:var(--tx);line-height:1.1}.zc-grid small{font-size:15px;color:var(--tx-3);font-weight:500}
    .zc-bar{height:4px;background:var(--panel-2);margin:0 0 14px}.zc-bar i{display:block;height:100%;background:var(--g);transform-origin:left;animation:mf-grow .7s var(--ease) both}
    .zc-rec b{display:block;color:var(--tx);font-size:15px;margin-top:3px}.zc-rec p{color:var(--tx-2);font-size:13.5px;line-height:1.55;margin:4px 0 0}
    .zc-foot{font-size:12px;color:var(--tx-3);margin-top:14px;padding-top:10px;border-top:1px dashed var(--line)}
    .sec-eyebrow{font-family:var(--cond);text-transform:uppercase;letter-spacing:2px;font-size:13px;color:var(--g-deep);margin:30px 0 2px}
    .sec-title{font-family:var(--cond);font-weight:700;text-transform:uppercase;font-size:30px;line-height:1.05;color:var(--tx);margin-bottom:18px}
    .qlist{list-style:none;margin:0;padding:0;position:relative}
    .qlist::before{content:"";position:absolute;left:31px;top:28px;bottom:40px;width:1px;background:linear-gradient(var(--g),var(--line))}
    .qlist li{display:grid;grid-template-columns:64px 1fr;gap:22px;padding:6px 0 26px;position:relative;cursor:default}
    .q-n{font-family:var(--cond);font-weight:700;font-size:44px;line-height:1;color:var(--bg);-webkit-text-stroke:1.5px var(--g);text-align:center;background:var(--bg);padding:6px 0;position:relative;z-index:1;transition:color var(--t) var(--ease),transform var(--t) var(--ease)}
    .q-body{border-bottom:1px solid var(--line);padding:6px 0 22px;transition:transform var(--t) var(--ease)}
    .qlist li:last-child .q-body{border-bottom:0}
    .q-t{font-family:var(--cond);font-weight:700;text-transform:uppercase;font-size:23px;letter-spacing:.4px;color:var(--tx);line-height:1.15}
    .q-body p{color:var(--tx-2);font-size:15px;line-height:1.6;margin:6px 0 10px;max-width:560px}
    .q-tag{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.4px;font-size:12.5px;color:var(--g-deep);display:inline-flex;align-items:center;gap:8px}
    .q-tag::before{content:"";width:18px;height:1px;background:var(--g);transition:width var(--t) var(--ease)}
    .qlist li:hover .q-n{color:var(--g);transform:scale(1.06)}
    .qlist li:hover .q-body{transform:translateX(6px)}
    .qlist li:hover .q-tag::before{width:34px}
    .sys{margin:0 0 16px;border-top:2px solid var(--tx)}
    .sys>div{display:grid;grid-template-columns:110px 1fr;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}
    .sys dt{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.4px;font-size:13px;color:var(--tx-3)}
    .sys dd{margin:0;color:var(--tx);font-size:15px;font-weight:500;display:flex;align-items:center;gap:9px}
    .sys code{font-family:'IBM Plex Mono',Consolas,monospace!important;font-size:12.5px;background:transparent;color:#8a6a12;padding:0;border-bottom:1px dashed #d7b65a;border-radius:0}
    .sys code.ok{color:var(--g-deep);border-color:var(--g)}
    .live{width:8px;height:8px;border-radius:50%;background:var(--g);box-shadow:0 0 0 0 rgba(28,154,69,.5);animation:mf-pulse 2.4s var(--ease) infinite;flex:none}
    .sys-note{color:var(--tx-2);font-size:14.5px;line-height:1.6;margin:0 0 14px}
    .sys-quote{font-family:'Barlow',sans-serif;font-style:italic;color:var(--tx);font-size:15px;line-height:1.55;padding-left:14px;border-left:3px solid var(--g);margin:0 0 26px}
    .zl-cap{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.6px;font-size:13px;color:var(--tx-3);display:flex;justify-content:space-between;border-bottom:2px solid var(--tx);padding-bottom:6px}
    .zl-cap b{color:var(--tx);font-size:15px}
    .zlist{list-style:none;margin:0;padding:0}
    .zlist li{display:grid;grid-template-columns:10px 1fr auto;gap:12px;align-items:center;padding:12px 4px;border-bottom:1px solid var(--line);transition:background var(--t-fast) var(--ease),padding var(--t) var(--ease)}
    .zlist li:hover{background:var(--panel);padding-left:10px}
    .zlist i{width:10px;height:10px;border-radius:50%;display:block}
    .zl-n{color:var(--tx);font-weight:500;font-size:15px}
    .zl-s{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.1px;font-size:13px;font-weight:600;text-align:right}
    @keyframes mf-pulse{0%{box-shadow:0 0 0 0 rgba(28,154,69,.45)}70%{box-shadow:0 0 0 8px rgba(28,154,69,0)}100%{box-shadow:0 0 0 0 rgba(28,154,69,0)}}
    @keyframes mf-grow{from{transform:scaleX(0)}to{transform:none}}
    @media(max-width:900px){.stats{grid-template-columns:1fr}.stats-total{border-right:0;border-bottom:1px solid var(--line)}.stats-leg{grid-template-columns:1fr;gap:8px}}
    .notice{color:var(--tx-2);font-size:14px;border-top:1px solid var(--line);padding-top:18px;margin-top:20px}
    /* Buttons: fill slides in from the left */
    [data-testid="stButton"] button,[data-testid="stDownloadButton"] button,[data-testid="stFormSubmitButton"] button,[data-testid="stPageLink"] a,[data-testid="stLinkButton"] a{
      border-radius:0;border:1px solid var(--g);color:var(--tx);min-height:46px;
      background:linear-gradient(var(--g),var(--g)) no-repeat left center/0% 100%,transparent;
      transition:background-size var(--t) var(--ease),color var(--t) var(--ease),border-color var(--t) var(--ease),transform var(--t-fast) var(--ease),box-shadow var(--t) var(--ease)}
    [data-testid="stButton"] button p,[data-testid="stDownloadButton"] button p,[data-testid="stFormSubmitButton"] button p,[data-testid="stPageLink"] a p,[data-testid="stLinkButton"] a p{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.6px;font-weight:600;font-size:15.5px}
    [data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover,[data-testid="stFormSubmitButton"] button:hover,[data-testid="stPageLink"] a:hover,[data-testid="stLinkButton"] a:hover{
      background-size:100% 100%,auto;color:#fff;border-color:var(--g);box-shadow:0 8px 22px -12px rgba(28,154,69,.7)}
    [data-testid="stPageLink"] a:hover p,[data-testid="stPageLink"] a:hover span{color:#fff!important}
    [data-testid="stButton"] button:active,[data-testid="stDownloadButton"] button:active,[data-testid="stFormSubmitButton"] button:active,[data-testid="stPageLink"] a:active{transform:scale(.975);box-shadow:none;transition-duration:80ms}
    button[kind="primary"],button[kind="primaryFormSubmit"]{background:linear-gradient(var(--g-hi),var(--g-hi)) no-repeat left center/0% 100%,var(--g)!important;color:#fff!important}
    button[kind="primary"]:hover,button[kind="primaryFormSubmit"]:hover{background-size:100% 100%,auto!important}
    button:disabled{opacity:.45;border-color:var(--line)!important}
    button:focus-visible,a:focus-visible{outline:2px solid var(--g-hi)!important;outline-offset:2px}
    [data-testid="stPageLink"] a{padding:.6rem 1rem}
    [data-testid="stPageLink"] a [data-testid="stIconMaterial"]{color:var(--g);transition:transform var(--t) var(--ease),color var(--t) var(--ease)}
    [data-testid="stPageLink"] a:hover [data-testid="stIconMaterial"]{transform:translateX(4px)}
    /* Form controls */
    [data-baseweb="tab"]{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.2px;transition:color var(--t-fast) var(--ease)}
    [data-baseweb="tab"] p{font-family:var(--cond);font-size:16px}
    [data-baseweb="tab-highlight"]{background:var(--g)!important;transition:all var(--t) var(--ease)!important}
    [data-baseweb="radio"] div,[data-baseweb="checkbox"] div{transition:all var(--t-fast) var(--ease)}
    [data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"],[data-baseweb="base-input"]{border-radius:0!important;transition:border-color var(--t-fast) var(--ease),box-shadow var(--t-fast) var(--ease)}
    [data-testid="stWidgetLabel"] p{font-family:var(--cond);text-transform:uppercase;letter-spacing:1.2px;font-size:13.5px;color:var(--tx-2)}
    [data-testid="stExpander"] details{border-radius:0;border-color:var(--line);background:var(--panel)}
    [data-testid="stExpander"] summary{transition:background var(--t-fast) var(--ease)}[data-testid="stExpander"] summary:hover{background:var(--panel-2)}
    [data-testid="stDataFrame"],[data-testid="stAlert"],[data-testid="stCode"] pre,iframe{border-radius:0!important}
    [data-testid="stDataFrame"]{border:1px solid var(--line)}
    hr{border-color:var(--line)!important}
    [data-testid="stMetric"],.card,.stats,[class*="st-key-mf_act_"],[data-testid="stExpander"] details{box-shadow:var(--shadow)}
    [data-testid="stSidebar"]{box-shadow:1px 0 0 var(--line)}
    @keyframes mf-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
    @media(max-width:900px){.hero{grid-template-columns:1fr;min-height:0}.hero-main{min-height:300px;padding-left:1.2rem}.hero-panel{padding:28px 22px}.hero-panel h1{font-size:2.6rem!important}
      .block-container{padding:3.2rem 1.2rem 2rem}.hero{margin:-.6rem -1.2rem 22px}h1{font-size:2.3rem!important}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
""".replace('__HERO_BG__', _HERO_BG)

def apply_style():
    st.markdown('<style>'+_CSS+'</style>',unsafe_allow_html=True)

def show_table(frame, **kwargs):
    # Protect the built-in dataframe CSV download as well as our export buttons.
    st.dataframe(frame.map(safe_cell), **kwargs)


def scope():
    return {'Demo': 'demo', 'Analis lokal': 'local', 'Skenario Demak A–C': 'scenario'}.get(st.session_state.get('workspace_mode','Demo'), 'demo')

def workspace_zones():
    if scope() == 'scenario':
        from .scenario_service import load_scenario_zones
        try:
            return load_scenario_zones()
        except (ValidationError, ValueError) as exc:
            st.error(f'Skenario belum dapat dimuat: {exc}')
            return []
    return list_zones(scope())

def header(eyebrow,title,description, research=False):
    st.markdown(f'<div class="eyebrow">{html.escape(eyebrow)}</div>',unsafe_allow_html=True)
    st.title(title)
    st.caption(description)
    if research:
        st.caption('RISET · Sumber historis baca-saja; simulasi input terpisah dari data survei.')
    elif scope() in ('demo', 'scenario'): watermark()

def watermark():
    if scope() == 'scenario':
        st.warning('SKENARIO HIPOTETIS · 19 November 2026 · Koordinat dan nilai bersumber dari data historis, '
                   'diasumsikan mewakili kondisi skenario. Bukan survei terbaru. Tanggal survei asli belum terverifikasi. Baca-saja.')
        return
    st.markdown(f'<div class="watermark"><b>DEMO</b><span>{WATERMARK} · Seluruh nilai dan batas zona bersifat sintetis</span></div>',unsafe_allow_html=True)

def local_demo_watermark(zones):
    """Di ruang kerja lokal, tampilkan watermark bila ada zona bertanda sintetis."""
    if scope()=='local' and any(z['is_demo'] for z in zones): watermark()

def badge(status):
    color=COLORS.get(status,'#89928e')
    st.markdown(f'<span class="status-badge" style="background:{color}">● {STATUS_LABELS.get(status,status)}</span>',unsafe_allow_html=True)

def choose_zone(zones,key):
    by_id={z['zone_id']:z for z in zones}
    ids=list(by_id)
    current=st.session_state.get('selected_zone')
    if current not in ids: current=ids[0]
    st.session_state[key]=current
    def remember():
        st.session_state['selected_zone']=st.session_state[key]
    selected=st.selectbox('Pilih zona',ids,index=None,format_func=lambda v:by_id[v]['zone_name'],key=key,on_change=remember)
    if selected is None:
        selected=current
    st.session_state['selected_zone']=selected
    return by_id[selected]

def empty_state():
    st.info('Belum ada zona dalam ruang kerja ini. Tambahkan titik atau impor CSV/GeoJSON pada Data & model.')
    st.page_link('pages/5_Data_Model.py',label='Buka Data & model',icon=':material/add_location_alt:')
    if scope() == 'local':
        def use_scenario():
            st.session_state['workspace_mode'] = 'Skenario Demak A–C'
        st.button('Tampilkan skenario Demak A–C', on_click=use_scenario)

def results_for(zones):
    """Hasil analisis untuk banyak zona: 2 query SQL total, bukan 2 per zona."""
    stored=latest_analyses([z['zone_id'] for z in zones])
    checksum=load_rules()['checksum']
    fresh={}
    for z in zones:
        s=stored.get(z['zone_id'])
        if s and s['result']['feature_snapshot']==z and s['result']['screening']['rules_checksum']==checksum:
            fresh[z['zone_id']]=s
    reviews=reviews_for_analyses([s['id'] for s in fresh.values()]) if fresh else {}
    out=[]
    for z in zones:
        s=fresh.get(z['zone_id'])
        if s:
            r=s['result'];r['reviews']=reviews.get(s['id'],[])
            out.append((r,s['id']))
        else: out.append((analyse_zone(z),None))
    return out

def result_for(zone):
    return results_for([zone])[0]

def exports(results,key):
    st.caption('Ekspor menyertakan mode, kualitas, versi aturan, waktu analisis, geometri, serta sumber setiap observasi.')
    a,b,c,d=st.columns(4)
    a.download_button('CSV',export_csv(results),'mangrove_fit_hasil.csv','text/csv',key=key+'csv',width='stretch')
    b.download_button('GeoJSON',export_geojson(results),'mangrove_fit_hasil.geojson','application/geo+json',key=key+'geo',width='stretch')
    c.download_button('Laporan HTML',export_html(results),'mangrove_fit_laporan.html','text/html',key=key+'html',width='stretch')
    d.download_button('Markdown',export_markdown(results),'mangrove_fit_laporan.md','text/markdown',key=key+'md',width='stretch')

def observation_rows(zone):
    rows=[]
    for k,m in PARAMETERS.items():
        o=zone['observations'][k]
        scenario = zone['provenance'].get('scenario')
        value = o['value']
        # Numeric values stay numeric (negative numbers need no CSV formula escaping).
        display = round(value, 4) if isinstance(value, (int, float)) else value
        rows.append({'Parameter':m['label'],'Nilai':display,'Satuan':m['unit'],
                     'Sumber': ('Dataset historis · ' + zone['provenance']['source_row_id']) if scenario and value is not None else (o['source'] or 'Belum tersedia'),
                     ('Tanggal skenario' if scenario else 'Tanggal'):o['date'] or '—',
                     'Kualitas': 'Data historis · skenario' if scenario and value is not None else o['quality_flag'],
                     'Metode pengolahan':o.get('method') or '—','Datum':o.get('datum') or '—'})
    return rows

def stats_strip(total,results):
    """Satu panel ringkas: total zona + distribusi status penyaringan."""
    counts=[(st_,sum(r['screening']['status']==st_ for r in results)) for st_ in ('ELIGIBLE','NEEDS_REVIEW','EXCLUDED')]
    done=sum(c for _,c in counts)
    bar=''.join(f'<i style="flex:{c};background:{COLORS[k]}" title="{html.escape(STATUS_LABELS[k])}: {c}"></i>' for k,c in counts if c) or '<i style="flex:1;background:var(--line)"></i>'
    legend=''.join(f'<div class="leg"><b style="color:{COLORS[k]}">{c}</b><span><em style="background:{COLORS[k]}"></em>{html.escape(STATUS_LABELS[k])}</span></div>' for k,c in counts)
    st.markdown(f'<div class="stats"><div class="stats-total"><b>{total}</b><span>Lokasi tersedia</span><small>{done} sudah disaring</small></div>'
                f'<div class="stats-dist"><div class="stats-cap">Hasil penyaringan awal</div><div class="stats-bar">{bar}</div><div class="stats-leg">{legend}</div></div></div>',unsafe_allow_html=True)

QUESTIONS = [
    ('01','Apakah habitatnya sesuai?','Saring nonhabitat, batas legal, dan kekurangan data inti.','Screening habitat & legal'),
    ('02','Apa yang perlu diperiksa?','Telusuri hidrologi, gelombang, regenerasi, dan pasokan propagul.','Faktor pembatas'),
    ('03','Langkah awal apa yang masuk akal?','Lindungi, kaji regenerasi, tinjau hidrologi, atau lakukan survei tambahan.','Rekomendasi tindakan'),
]

def home_questions():
    items=''.join(f'<li><span class="q-n">{n}</span><div class="q-body"><div class="q-t">{html.escape(t)}</div><p>{html.escape(d)}</p><span class="q-tag">{html.escape(tag)}</span></div></li>' for n,t,d,tag in QUESTIONS)
    return f'<div class="sec-eyebrow">Kerangka kajian</div><div class="sec-title">Tiga pertanyaan sebelum menanam</div><ol class="qlist">{items}</ol>'

def home_status(zones,results):
    ms=get_model_status()
    ready=ms['status']=='MODEL_READY'
    mode={'demo': 'Demo · baca-saja', 'local': 'Analis lokal · SQLite', 'scenario': 'Skenario Demak A–C · baca-saja'}[scope()]
    note=('Model XGBoost tervalidasi aktif; skor dan SHAP tampil di halaman Analisis setelah screening.' if ready
          else 'XGBoost dan SHAP belum aktif karena belum ada model yang disetujui. Hasil berasal dari aturan yang dapat diperiksa.')
    from .research_service import available_models
    if available_models() and not ready:
        note='Model operasional belum disetujui. Eksperimen XGBoost, SHAP, dan demonstrasi prediksi tersedia melalui menu XGBoost & SHAP · Riset.'
    rows=''.join(f'<li><i style="background:{COLORS[r["screening"]["status"]]}"></i><span class="zl-n">{html.escape(z["zone_name"])}</span>'
                 f'<span class="zl-s" style="color:{COLORS[r["screening"]["status"]]}">{html.escape(STATUS_LABELS[r["screening"]["status"]])}</span></li>' for z,r in zip(zones,results))
    zl=f'<div class="zl-cap">Ringkasan zona <b>{len(zones)}</b></div><ul class="zlist">{rows}</ul>' if zones else ''
    return (f'<div class="sec-eyebrow">Sistem</div><div class="sec-title">Status saat ini</div>'
            f'<dl class="sys"><div><dt>Ruang kerja</dt><dd><span class="live"></span>{mode}</dd></div>'
            f'<div><dt>Metode</dt><dd>Aturan screening terbuka</dd></div>'
            f'<div><dt>Model</dt><dd><code class="{"ok" if ready else ""}">{html.escape(ms["status"])}</code></dd></div></dl>'
            f'<p class="sys-note">{note}</p>'
            f'<p class="sys-quote">Hijau berarti bisa dikaji lebih lanjut, bukan siap ditanam atau pasti berhasil.</p>{zl}')

def home():
    zones=workspace_zones()
    note={'demo': 'zona sintetis (demo)', 'scenario': 'titik skenario historis Demak', 'local': 'zona di ruang kerja lokal'}[scope()]
    st.markdown(f'''<div class="hero"><div class="hero-main"><div class="hero-brand">MANGROVE-FIT<small>PESISIR DEMAK · JAWA TENGAH</small></div><div class="hero-count"><b>{len(zones)}</b><span>{note}</span><em>Foto latar dekoratif, bukan dokumentasi lokasi studi di Demak.</em></div></div><div class="hero-panel"><h1>Kaji dulu,<br>baru menanam</h1><div class="sub">Penyaringan berbasis aturan</div><p>Mulai dari kondisi pesisir, telusuri faktor pembatas, dan susun prioritas survei sebelum menentukan intervensi.</p><ol><li><i>01</i>Peta kawasan</li><li><i>02</i>Penyaringan habitat</li><li><i>03</i>Kajian tindakan</li></ol></div></div>''',unsafe_allow_html=True)
    if scope() in ('demo', 'scenario'): watermark()
    local_demo_watermark(zones)
    results=[r for r,_ in results_for(zones)]
    stats_strip(len(zones),results)
    actions=[('pages/2_Peta.py','01','Peta kawasan','Lihat batas zona dan hasil penyaringan di atas peta.',':material/map:'),
             ('pages/3_Analisis.py','02','Analisis lokasi','Periksa parameter, aturan yang terpicu, dan rekomendasi.',':material/eco:'),
             ('pages/5_Data_Model.py','03','Impor dataset','Unggah CSV atau GeoJSON ke ruang kerja lokal.',':material/upload_file:')]
    for col,(page,n,title,desc,icon) in zip(st.columns(3,gap='medium'),actions):
        with col, st.container(key=f'mf_act_{n}'):
            st.markdown(f'<div class="act-n">{n}</div><div class="act-t">{title}</div><p class="act-d">{desc}</p>',unsafe_allow_html=True)
            st.page_link(page,label='Buka',icon=icon,width='stretch')
    left,right=st.columns([1.55,1],gap='large')
    with left:
        st.markdown(home_questions(),unsafe_allow_html=True)
    with right:
        st.markdown(home_status(zones,results),unsafe_allow_html=True)
        if not zones: empty_state()
    st.markdown('<div class="notice">Kesesuaian habitat ≠ keberhasilan rehabilitasi. Setiap tindakan tetap memerlukan verifikasi lapangan dan peninjauan ahli.</div>',unsafe_allow_html=True)

def offline_map(zones,results,selected_id=None):
    from shapely.geometry import shape
    bounds=[shape(z['geometry']).bounds for z in zones]
    xmin=min(b[0] for b in bounds); xmax=max(b[2] for b in bounds)
    ymin=min(b[1] for b in bounds); ymax=max(b[3] for b in bounds)
    dx=max(xmax-xmin,.002);dy=max(ymax-ymin,.002)
    xmin-=dx*.12;ymin-=dy*.12;dx*=1.24;dy*=1.24
    def xy(x,y): return (45+720*(x-xmin)/dx,450-390*(y-ymin)/dy)
    paths=[]
    for z,r in zip(zones,results):
        g=shape(z['geometry']);col=COLORS[r['screening']['status']]
        if g.geom_type=='Point':
            x,y=xy(g.x,g.y)
            sel=z['zone_id']==selected_id
            paths.append(f'<rect x="{x-27}" y="{y-27}" width="54" height="54" fill="{col}" fill-opacity=".85" stroke="{"#14301f" if sel else "#ffffff"}" stroke-width="{4 if sel else 2}"/>')
        else:
            polys=list(g.geoms) if g.geom_type=='MultiPolygon' else [g]
            for p in polys:
                d=' '.join('M '+' L '.join(f'{xy(x,y)[0]},{xy(x,y)[1]}' for x,y in ring.coords)+' Z' for ring in [p.exterior,*p.interiors])
                sel=z['zone_id']==selected_id
                paths.append(f'<path d="{d}" fill="{col}" fill-opacity="{.5 if sel else .25}" stroke="{col}" stroke-width="{5 if sel else 2.5}" fill-rule="evenodd"/>')
        lat,lon=center(z['geometry']);x,y=xy(lon,lat)
        label=z['zone_id'].removeprefix('SKENARIO-') if z['provenance'].get('scenario') else z['zone_id']
        paths.append(f'<text x="{x}" y="{y+5}" font-size="{20 if len(label)<=3 else 12}" font-weight="bold" text-anchor="middle" fill="#193a30">{html.escape(label)}</text>')
    grid=''.join(f'<path d="M {x} 35 V 470" stroke="#d4ded5"/>' for x in range(45,800,80))+''.join(f'<path d="M 35 {y} H 785" stroke="#d4ded5"/>' for y in range(50,480,60))
    st.markdown(f'<svg viewBox="0 0 820 510" role="img" aria-label="Peta skematis koordinat zona" style="width:100%;background:#eaf1ec">{grid}{"".join(paths)}<text x="38" y="28" font-size="12" fill="#567260">SKEMA KOORDINAT · TANPA BASEMAP · EPSG:4326</text><text x="38" y="497" font-size="11" fill="#567260">Bukan peta jarak/luas · Pilih zona melalui panel di samping</text></svg>',unsafe_allow_html=True)
    st.caption(f'Rentang zona: {min(b[0] for b in bounds):.5f}–{max(b[2] for b in bounds):.5f} BT; {min(b[1] for b in bounds):.5f}–{max(b[3] for b in bounds):.5f} lintang.')

BASEMAPS = {
    'Satelit': dict(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Citra © Esri, Maxar, Earthstar Geographics, GIS User Community'),
    'Terang': dict(tiles='cartodbpositron', attr=None),
    'OSM': dict(tiles='OpenStreetMap', attr=None),
}

def map_legend(pairs):
    items=''.join(f'<div class="ml-item"><i style="background:{COLORS[k]}"></i><span>{html.escape(STATUS_LABELS[k])}</span><b>{sum(r["screening"]["status"]==k for _,r in pairs)}</b></div>' for k in STATUS_LABELS)
    st.markdown(f'<div class="map-legend"><div class="ml-cap">Hasil penyaringan awal</div>{items}</div>',unsafe_allow_html=True)

def zone_card(zone,result):
    status=result['screening']['status']; col=COLORS[status]
    ar=area_ha(zone['geometry']); comp=result['completeness']
    lat,lon=center(zone['geometry'])
    area_txt=f'{ar:,.2f}<small> ha</small>' if ar is not None else '—<small> titik</small>'
    st.markdown(f"""<div class="zcard" style="--zc:{col}">
      <div class="zc-id">{html.escape(zone['zone_id'])} · {html.escape(zone['geometry']['type'])}</div>
      <div class="zc-name">{html.escape(zone['zone_name'])}</div>
      <span class="zc-pill">{html.escape(STATUS_LABELS[status])}</span>
      <div class="zc-grid"><div><span>Luas geometri</span><b>{area_txt}</b></div><div><span>Data inti</span><b>{comp['available']}<small>/{comp['total']}</small></b></div></div>
      <div class="zc-bar"><i style="width:{comp['percent']}%"></i></div>
      <div class="zc-rec"><span>Langkah awal</span><b>{html.escape(result['recommendation']['action'])}</b><p>{html.escape(result['recommendation']['focus'])}</p></div>
      <div class="zc-foot">{lat:.5f}, {lon:.5f} · EPSG:4326</div></div>""",unsafe_allow_html=True)

def fit_view(bounds,width_px=720,height_px=540,max_zoom=14):
    """Pusat & zoom Web Mercator yang memuat semua bounds. Dihitung di Python agar stabil saat peta dirender ulang."""
    import math
    x0=min(b[0] for b in bounds);y0=min(b[1] for b in bounds);x1=max(b[2] for b in bounds);y1=max(b[3] for b in bounds)
    merc=lambda lat:math.log(math.tan(math.pi/4+math.radians(lat)/2))
    dx=max(x1-x0,1e-4)*1.08; dy=max(merc(y1)-merc(y0),1e-6)*1.08
    zx=math.log2(width_px*360/(256*dx)); zy=math.log2(height_px*2*math.pi/(256*dy))
    return ((y0+y1)/2,(x0+x1)/2),int(max(2,min(max_zoom,math.floor(min(zx,zy)))))

def map_page():
    header('EKSPLORASI / 01','Peta kawasan','Jelajahi zona kandidat dan periksa dasar klasifikasinya.')
    zones=workspace_zones()
    local_demo_watermark(zones)
    if not zones: empty_state();return
    with st.container(key='mf_maptools'):
        a,b,c,d=st.columns([1.4,1,1.1,.9],vertical_alignment='bottom')
        search=a.text_input('Cari zona',placeholder='Nama atau ID zona')
        status=b.selectbox('Status screening',['Semua']+list(STATUS_LABELS),format_func=lambda x:STATUS_LABELS.get(x,x))
        basemap=c.radio('Latar peta',list(BASEMAPS),horizontal=True,key='map_basemap')
        offline=d.toggle('Skematis offline',help='Gunakan jika internet, basemap, atau komponen peta gagal dimuat.')
    pairs=[(z,r) for z,(r,_) in zip(zones,results_for(zones))]
    pairs=[(z,r) for z,r in pairs if search.lower() in (z['zone_name']+' '+z['zone_id']).lower() and (status=='Semua' or r['screening']['status']==status)]
    if not pairs: st.info('Tidak ada zona yang sesuai filter.');return
    zs,rs=zip(*pairs)
    selected_id=st.session_state.get('selected_zone')
    if selected_id not in {z['zone_id'] for z in zs}: selected_id=zs[0]['zone_id']
    left,right=st.columns([2.3,1],gap='large')
    with left:
        if offline: offline_map(zs,rs,selected_id)
        else:
            import folium
            from streamlit_folium import st_folium
            from shapely.geometry import shape,Point
            bm=BASEMAPS[basemap]
            map_center,map_zoom=fit_view([shape(z['geometry']).bounds for z in zs])
            m=folium.Map(location=map_center,zoom_start=map_zoom,tiles=bm['tiles'],attr=bm['attr'],control_scale=True,scrollWheelZoom=False)
            for z,r in pairs:
                col=COLORS[r['screening']['status']]; sel=z['zone_id']==selected_id
                # Folium embeds popup HTML in a JavaScript template literal.
                popup_name=html.escape(z['zone_name']).replace('`','&#96;').replace('$','&#36;')
                popup=folium.Popup(f'<strong>{popup_name}</strong><br>{html.escape(z["zone_id"])}<br>{STATUS_LABELS[r["screening"]["status"]]}',max_width=250)
                tip=f'{html.escape(z["zone_id"])} · {popup_name}'
                if z['geometry']['type']=='Point':
                    label=z['zone_id'].removeprefix('SKENARIO-') if z['provenance'].get('scenario') else z['zone_id']
                    marker_html=(f'<div style="width:56px;height:56px;box-sizing:border-box;background:{col}dd;'
                                 f'border:{4 if sel else 2}px solid {"#14301f" if sel else "#ffffff"};'
                                 'box-shadow:0 2px 8px #0008;display:flex;align-items:center;justify-content:center;'
                                 f'color:#14301f;font-weight:800;font-size:{22 if len(label)<=3 else 11}px;'
                                 f'font-family:Arial,sans-serif">{html.escape(label)}</div>')
                    folium.Marker(location=center(z['geometry']), icon=folium.DivIcon(html=marker_html,icon_size=(56,56),icon_anchor=(28,28)),
                                  popup=popup,tooltip=tip,z_index_offset=1000 if sel else 0).add_to(m)
                else:
                    style={'fillColor':col,'color':'#ffffff' if sel else col,'weight':4 if sel else 2,'fillOpacity':.45 if sel else .25,'dashArray':None}
                    folium.GeoJson({'type':'Feature','properties':{'zone_id':z['zone_id']},'geometry':z['geometry']},style_function=lambda f,style=style:style,highlight_function=lambda f:{'weight':4,'fillOpacity':.55},tooltip=tip,popup=popup).add_to(m)
            with st.container(key='mf_mapframe'):
                response=st_folium(m,height=540,use_container_width=True,center=map_center,zoom=map_zoom,key='coast_map_'+scope(),returned_objects=['last_object_clicked','last_clicked'])
            click=response.get('last_object_clicked')
            signature=json.dumps(click,sort_keys=True)
            if click and st.session_state.get('map_last_click_'+scope())!=signature:
                st.session_state['map_last_click_'+scope()]=signature
                p=Point(click['lng'],click['lat'])
                hit=next((z for z in zs if shape(z['geometry']).covers(p)),None)
                if not hit:
                    points=[z for z in zs if z['geometry']['type']=='Point']
                    if points: hit=min(points,key=lambda z:shape(z['geometry']).distance(p))
                if hit and hit['zone_id']!=selected_id:
                    st.session_state['selected_zone']=hit['zone_id']
                    st.rerun()
            note='Citra satelit hanya latar visual; batas zona demo fiktif dan tidak diturunkan dari citra ini.' if basemap=='Satelit' else 'Basemap © OpenStreetMap contributors.'
            c=response.get('last_clicked')
            st.caption((f"Klik terakhir: {c['lat']:.5f}, {c['lng']:.5f} · " if c else '')+note+' Jika peta kosong, aktifkan Skematis offline.')
        map_legend(pairs)
        if any(z['geometry']['type']=='Point' for z in zs):
            st.caption('Kotak berlabel menandai titik pengamatan; ukurannya hanya untuk tampilan, bukan batas atau luas lahan. Kotak terpilih memiliki garis tepi lebih tebal.')
    with right:
        zone=choose_zone(list(zs),'map_zone_'+scope())
        result=next(r for z,r in pairs if z['zone_id']==zone['zone_id'])
        zone_card(zone,result)
        st.page_link('pages/3_Analisis.py',label='Analisis zona ini',icon=':material/arrow_forward:',width='stretch')
        st.caption('Klik kotak titik atau poligon untuk memilih zona. Luas hanya dihitung untuk geometri poligon sumber.')

MODEL_STATUS_TEXT = {
    'NO_MODEL_AVAILABLE': 'Belum ada model XGBoost yang disetujui. Penilaian memakai aturan screening.',
    'MODEL_INVALID': 'Artefak model ditolak oleh gerbang validasi.',
    'SCREENING_EXCLUDED': 'Zona dikecualikan oleh screening, sehingga model tidak dijalankan.',
    'MISSING_REQUIRED_FEATURES': 'Fitur wajib model belum lengkap. Nilai kosong tidak diimputasi.',
    'OUT_OF_DOMAIN': 'Nilai zona berada di luar rentang data latih; prediksi tidak diberikan.',
    'EXPLANATION_INVALID': 'Penjelasan gagal uji konsistensi dan ditahan.',
}

def _plabel(k): return PARAMETERS.get(k,{}).get('label',k)

def model_unavailable(ex):
    text=MODEL_STATUS_TEXT.get(ex['status'],'')
    if ex['status']!='NO_MODEL_AVAILABLE' and ex.get('message'): text+=' '+ex['message']
    st.info(f"{ex['status']} — {text}")
    if ex.get('missing'): st.write('Belum terisi: '+', '.join(_plabel(k) for k in ex['missing']))
    if ex.get('outside'): st.write('Di luar domain: '+', '.join(_plabel(k) for k in ex['outside']))
    if ex['status']=='NO_MODEL_AVAILABLE':
        st.page_link('pages/7_Riset.py', label='Coba XGBoost & SHAP dalam mode riset', icon=':material/science:')
        st.caption('Model diaktifkan lewat scripts/train_model.py lalu scripts/approve_model.py oleh peninjau ahli. Lihat tab Status model di halaman Data & model.')

def model_tab(ex):
    if ex['status']!='OK': model_unavailable(ex);return
    card,_=load_card()
    a,b,c=st.columns(3)
    a.metric('Skor model',f"{ex['score']:.2f}")
    b.metric('Versi',card['version'])
    test=card.get('metrics',{}).get('test',{})
    c.metric('Balanced accuracy uji',test.get('balanced_accuracy','—'))
    st.caption(f"Probabilitas kelas positif untuk target «{card['target']}». Bukan persen keberhasilan tanam. Disetujui oleh {card['approved_by']}.")
    m=card.get('metrics',{})
    if m:
        rows=[]
        for name,label in (('validation','Validasi'),('test','Uji (blok independen)')):
            if name in m:
                base=m.get('baseline_prevalence',{}).get(name,{})
                rows.append({'Bagian':label,'n':m[name]['n'],'Balanced acc.':m[name]['balanced_accuracy'],'F1':m[name]['f1'],'PR-AUC':m[name]['pr_auc'],'Brier':m[name]['brier'],'Baseline BA':base.get('balanced_accuracy')})
        st.markdown('**Kinerja pada data yang tidak dipakai melatih**')
        show_table(pd.DataFrame(rows),hide_index=True,width='stretch')
    st.markdown('**Input zona terhadap domain data latih**')
    show_table(pd.DataFrame([{'Parameter':_plabel(k),'Nilai zona':v,'Min latih':card['domain'].get(k,[None,None])[0],'Maks latih':card['domain'].get(k,[None,None])[1]} for k,v in ex['inputs'].items()]),hide_index=True,width='stretch')

def shap_tab(ex):
    if ex['status']!='OK':
        model_unavailable(ex)
        st.caption('Alasan screening ada pada tab Screening dan bukan nilai SHAP.')
        return
    import altair as alt
    df=pd.DataFrame([{'Parameter':f"{_plabel(k)} = {ex['inputs'][k]}",'SHAP':round(v,4),'Arah':'menaikkan skor' if v>=0 else 'menurunkan skor'} for k,v in ex['factors']])
    chart=alt.Chart(df).mark_bar().encode(
        x=alt.X('SHAP:Q',title='Kontribusi (log-odds)'),
        y=alt.Y('Parameter:N',sort=None,title=None),
        color=alt.Color('Arah:N',scale=alt.Scale(domain=['menaikkan skor','menurunkan skor'],range=['#1c9a45','#c55a4f']),legend=alt.Legend(orient='bottom',title=None)),
        tooltip=['Parameter','SHAP','Arah']).properties(height=max(140,42*len(df)))
    st.altair_chart(chart,use_container_width=True)
    st.caption(f"Nilai dasar {ex['bias']:+.3f} + jumlah kontribusi = margin {ex['margin']:+.3f} (log-odds) → skor {ex['score']:.2f}. "
               'Kontribusi menjelaskan perilaku model, bukan hubungan sebab-akibat di lapangan.')
    chk=ex.get('shap_check') or {}
    if chk.get('available') and chk.get('ok'): st.caption(f"✓ Dicek ulang dengan shap {chk.get('shap_version')} TreeExplainer (selisih maks {chk['max_abs_diff']:.1e}).")
    elif chk: st.caption(chk.get('message',''))

def model_status_panel():
    st.page_link('pages/7_Riset.py', label='Buka eksperimen XGBoost, SHAP & prediksi riset', icon=':material/science:')
    st.subheader('Model aktif')
    status=get_model_status()
    card,_=load_card()
    if card:
        a,b,c=st.columns(3)
        a.metric('Versi',card['version']); b.metric('Target',card['target']); c.metric('Disetujui oleh',card['approved_by'])
        st.caption('Fitur: '+', '.join(_plabel(f) for f in card['features']))
    else:
        st.code(status['status'],language=None)
        st.write(status['message'])
    cand=read_card(CANDIDATE_DIR)
    st.subheader('Kandidat terakhir')
    if cand:
        st.write(f"**{cand.get('version')}** · status `{cand.get('status')}` · data `{cand.get('training',{}).get('data_file')}`")
        if cand.get('synthetic'): st.warning('Kandidat ini dilatih dari data sintetis; hanya untuk uji kode dan tidak dapat disetujui.')
        m=cand.get('metrics',{})
        ds=(cand.get('training') or {}).get('dataset_manifest') or {}
        if ds: st.caption(f"Dataset {ds.get('dataset_id')} · {ds.get('rows')} titik · {ds.get('blocks')} blok · target {cand.get('target')} · fitur: "+', '.join(_plabel(f) for f in cand.get('features',[])))
        rows=[]
        for key,label in (('test','Uji (blok independen)'),('cv_leave_one_block_out','Validasi silang antar-blok')):
            if key in m:
                base=m['baseline_prevalence']['test']['balanced_accuracy'] if key=='test' else 0.5
                rows.append({'Evaluasi':label,'n':m[key]['n'],'Balanced acc.':m[key]['balanced_accuracy'],'Baseline BA':base,'PR-AUC':m[key]['pr_auc'],
                             'Baseline PR-AUC':m[key].get('baseline_pr_auc',m[key].get('prevalence'))})
        if rows: show_table(pd.DataFrame(rows),hide_index=True,width='stretch')
        blockers=approval_blockers(cand,CANDIDATE_DIR)
        if blockers: st.warning('Belum layak disetujui:\n\n'+'\n'.join('- '+b for b in blockers))
        elif not cand.get('synthetic'): st.success('Lolos pemeriksaan otomatis. Menunggu keputusan peninjau ahli (scripts/approve_model.py).')
    else: st.caption('Belum ada kandidat di models/candidate.')
    st.subheader('Cara melatih & mengaktifkan')
    st.markdown('1. Siapkan CSV berlabel nyata: kolom target 0/1, kolom blok spasial, dan kolom parameter numerik.\n'
                '2. Latih kandidat (status PENDING_REVIEW, belum aktif):')
    st.code('python scripts/import_sea_site.py "<path>/sea-site_dataset_withNAs.csv"\n'
            'python scripts/train_model.py data/training/D01_sea_site_seedling.csv --target seedling_presence '
            '--features inundation_duration_h_day soil_ph redox_mv bed_slope --block-col blok --manifest data/manifests/D01.json',language='bash')
    st.markdown('3. Peninjau ahli memeriksa metrik di `models/candidate/model_card.json`, lalu menyetujui:')
    st.code('python scripts/approve_model.py --reviewer "Nama Peninjau" --note "catatan"',language='bash')
    st.caption('Gerbang menolak model sintetis, checksum tidak cocok, atau kinerja uji tidak melampaui baseline. Tidak ada unggahan pickle/joblib.')

def analysis_page():
    header('KAJIAN / 02','Analisis lokasi','Lihat kelengkapan data, alasan screening, dan opsi pemeriksaan berikutnya.')
    zones=workspace_zones()
    local_demo_watermark(zones)
    if not zones: empty_state();return
    zone=choose_zone(zones,'analysis_zone_'+scope())
    r,aid=result_for(zone)
    if scope()=='local' and zone['is_demo']: watermark()
    a,b,c=st.columns([1.4,1,1])
    with a: badge(r['screening']['status']);st.caption(r['screening']['status'])
    b.metric('Kelengkapan parameter inti',f"{r['completeness']['percent']}%")
    ex=explain_zone(zone,r['screening'])
    research_result, research_error = None, None
    if zone['provenance'].get('scenario'):
        from .research_service import predict_scenario_reference, ResearchError
        try:
            research_result = predict_scenario_reference(zone)
        except (ResearchError, ValidationError) as error:
            research_error = str(error)
        c.metric('Skor XGBoost riset · semai alami', f"{research_result['probability']:.3f}" if research_result else 'Tidak tersedia')
        st.caption('RESEARCH_ONLY · Skor baris historis sumber, bukan peluang keberhasilan tanam atau pengukuran kondisi terbaru. Model operasional tetap belum aktif.')
    else:
        c.metric('Skor model XGBoost',f"{ex['score']:.2f}" if ex['status']=='OK' else 'Tidak tersedia',help=None if ex['status']=='OK' else ex['status'])
    if aid: st.caption(f"Analisis tersimpan #{aid} · {r['analysis_timestamp']} UTC · {r['screening']['rules_version']}")
    elif scope() == 'local': st.caption('Pratinjau aturan dari data saat ini. Simpan analisis untuk membuat snapshot dan catatan verifikasi.')
    else: st.caption('Pratinjau baca-saja. Screening dan skor riset merupakan dua hasil yang berbeda.')
    tabs=st.tabs(['Data input','Screening','Model XGBoost','Penjelasan SHAP','Rekomendasi & verifikasi'])
    with tabs[0]:
        st.write(f"**Tutupan:** {zone['landcover_type']} · **Status legal:** {zone['legal_status']}")
        if zone['provenance'].get('scenario'):
            rows = pd.DataFrame(observation_rows(zone))
            available = rows['Kualitas'].ne('missing')
            st.caption(f"{int(available.sum())} dari {len(rows)} parameter tersedia pada baris sumber. Nilai kosong tidak diisi dengan tebakan.")
            show_table(rows[available],hide_index=True,width='stretch')
            with st.expander(f"Parameter belum tersedia ({int((~available).sum())})"):
                show_table(rows[~available],hide_index=True,width='stretch')
            st.caption(zone['provenance'].get('unit_note') or '')
        else:
            show_table(pd.DataFrame(observation_rows(zone)),hide_index=True,width='stretch',height=490)
        st.caption('Kelengkapan menghitung ketersediaan 7 parameter inti; bukan keyakinan model atau mutu ekologis.')
        with st.expander('Provenance dataset & geometri'):
            st.json({'provenance':zone['provenance'],'geometry':zone['geometry']})
        if scope()=='local': st.page_link('pages/5_Data_Model.py',label='Edit data zona',icon=':material/edit:')
    with tabs[1]:
        st.subheader(STATUS_LABELS[r['screening']['status']])
        for reason in r['screening']['reasons']: st.write('• '+reason)
        for warning in r['warnings']: st.warning(warning)
        st.caption(f"Aturan {r['screening']['rules_version']} · Konsep awal yang memerlukan telaah ahli.")
    with tabs[2]:
        if research_result:
            st.info(research_result['watermark'])
            st.write(research_result['note'])
            st.write(f"ID model: `{research_result['model']}` · observasi `{research_result['historical_id']}`")
            st.write(f"Skor kelas 1 (semai ditemukan): **{research_result['probability']:.3f}** · ambang final {research_result['threshold']:.2f}")
            with st.expander('Fitur lengkap yang benar-benar digunakan model'):
                st.json(research_result['inputs'])
            st.download_button('Unduh skor & SHAP riset titik ini', json.dumps(research_result, indent=2, ensure_ascii=False, allow_nan=False),
                               f"RISET_{zone['zone_id']}.json", 'application/json')
        elif research_error: st.error(research_error)
        else: model_tab(ex)
    with tabs[3]:
        if research_result:
            st.caption('SHAP lokal untuk baris historis pada model final. Kontribusi bukan sebab-akibat; ini bukan validasi baru.')
            local_shap = pd.DataFrame(list(research_result['contributions'].items()), columns=['Fitur sumber', 'Kontribusi log-odds'])
            st.bar_chart(local_shap.set_index('Fitur sumber'), horizontal=True)
            st.caption(f"Aditivitas lulus: bias {research_result['bias']:.4f} + kontribusi = margin {research_result['margin']:.4f}.")
        elif research_error: st.error(research_error)
        else: shap_tab(ex)
    with tabs[4]:
        st.subheader(r['recommendation']['action'])
        st.write(r['recommendation']['focus'])
        for i,s in enumerate(r['recommendation']['next_steps'],1): st.write(f'{i}. {s}')
        st.info('Hasil ini merupakan arahan pemeriksaan awal. Peninjauan ahli dan izin setempat tetap diperlukan.')
        if scope()!='local': st.caption('Skenario dan Demo bersifat baca-saja. Gunakan Analis lokal untuk menyimpan survei dan catatan.')
        else:
            if st.button('Simpan analisis saat ini',type='primary'):
                save_analysis(r);st.success('Snapshot analisis tersimpan.');st.rerun()
            if aid:
                with st.form('review_form'):
                    reviewer=st.text_input('Nama verifikator / ahli')
                    decision=st.selectbox('Hasil tinjauan',['Perlu survei tambahan','Tunda intervensi','Diteruskan untuk kajian ahli'])
                    notes=st.text_area('Catatan verifikasi',placeholder='Temuan lapangan, referensi dokumen izin, koreksi, dan tindak lanjut.')
                    if st.form_submit_button('Simpan catatan'):
                        try: save_review(aid,reviewer,notes,decision);st.success('Catatan tersimpan.');st.rerun()
                        except ValueError as e: st.error(str(e))
                st.caption('Catatan tidak mengganti status screening secara otomatis. Perbaiki input bila ada temuan baru, lalu simpan analisis ulang.')
            reviews=get_reviews(zone['zone_id'])
            if reviews: show_table(pd.DataFrame(reviews),hide_index=True,width='stretch')
    st.divider()
    st.subheader('Unduh hasil kajian')
    exports([r],'analysis_')

def comparison_page():
    header('PRIORITAS / 03','Bandingkan zona','Susun urutan survei dengan alasan yang dapat ditelusuri.')
    zones=workspace_zones()
    local_demo_watermark(zones)
    if not zones: empty_state();return
    ids=[z['zone_id'] for z in zones]
    selected=st.multiselect('Pilih 2–5 zona',ids,default=ids[:min(3,len(ids))],max_selections=5,format_func=lambda v:next(z['zone_name'] for z in zones if z['zone_id']==v))
    if not selected: st.info('Pilih zona untuk dibandingkan.');return
    a,b=st.columns(2)
    filt=a.selectbox('Filter status',['Semua']+list(STATUS_LABELS),format_func=lambda x:STATUS_LABELS.get(x,x))
    ordering=b.selectbox('Urutkan berdasarkan',['Urutan survei','Kelengkapan data terendah','Nama zona'])
    results=[r for r,_ in results_for([z for z in zones if z['zone_id'] in selected])]
    results=[r for r in results if filt=='Semua' or r['screening']['status']==filt]
    if ordering=='Urutan survei': results=survey_sort(results)
    elif ordering=='Kelengkapan data terendah': results=sorted(results,key=lambda r:r['completeness']['percent'])
    else: results=sorted(results,key=lambda r:r['feature_snapshot']['zone_name'])
    if not results: st.info('Tidak ada zona sesuai filter.');return
    st.info('Urutan survei: perlu verifikasi → bisa dikaji lanjut → dikecualikan; dalam kelompok, data paling tidak lengkap diperiksa lebih dahulu. Ini bukan skor prioritas program atau keberhasilan tanam.')
    rows=[]
    if scope() == 'scenario':
        from .research_service import predict_scenario_reference, ResearchError
        research_outputs = []
        cards = st.columns(len(results))
        for i, r in enumerate(results):
            z = r['feature_snapshot']
            available = sum(o['value'] is not None for o in z['observations'].values())
            score = None
            try:
                prediction = predict_scenario_reference(z)
                score = prediction['probability']
                research_outputs.append(prediction)
            except (ResearchError, ValidationError) as error:
                cards[i].warning(str(error))
            with cards[i]:
                st.subheader(z['zone_name'].split(' · ')[0])
                st.metric('Skor riset · semai alami', f'{score:.3f}' if score is not None else 'Tidak tersedia')
                st.caption(f"{available}/{len(PARAMETERS)} parameter tersedia · sumber {z['provenance']['source_row_id']}")
            rows.append({'Titik': z['zone_name'].split(' · ')[0],
                         'Screening': STATUS_LABELS[r['screening']['status']],
                         'Parameter tersedia': f'{available}/{len(PARAMETERS)}',
                         'Data inti lengkap (%)': r['completeness']['percent'],
                         'Skor riset semai': round(score, 3) if score is not None else None,
                         'Kualitas': 'Data historis · skenario'})
        show_table(pd.DataFrame(rows),hide_index=True,width='stretch')
        st.caption('RESEARCH_ONLY · Skor 0–1 menjelaskan keberadaan semai pada baris historis, bukan kelas kesesuaian habitat atau peluang keberhasilan tanam. '
                   'Balanced accuracy validasi model 48,8%; skor tidak dipakai menentukan urutan survei.')
        with st.expander('Alasan screening dan tindak lanjut per titik'):
            for r in results:
                z = r['feature_snapshot']
                st.markdown(f"**{z['zone_name']}**")
                st.write(r['recommendation']['action'])
                for reason in r['screening']['reasons']:
                    st.write('• ' + reason)
                st.caption('Luas kawasan belum ditentukan karena geometri berupa titik. Degradasi/abrasi belum dinilai tanpa data perubahan garis pantai.')
        if research_outputs:
            st.download_button('Unduh perbandingan skor riset', json.dumps(
                {'watermark': 'RISET HISTORIS / SKENARIO — BUKAN VALIDASI LAPANGAN TERBARU',
                 'results': research_outputs}, ensure_ascii=False, indent=2, allow_nan=False),
                'RISET_perbandingan_Demak.json', 'application/json')
    else:
        for i,r in enumerate(results,1):
            z=r['feature_snapshot'];v=values(z)
            rows.append({'Urutan survei':i,'ID':z['zone_id'],'Nama':z['zone_name'],'Luas (ha)':area_ha(z['geometry']),'Screening':STATUS_LABELS[r['screening']['status']],'Kelengkapan (%)':r['completeness']['percent'],'Kelas habitat ML':'Tidak tersedia','Sinyal degradasi':'Abrasi terindikasi' if v.get('shoreline_change_m_y') is not None and v['shoreline_change_m_y']<0 else 'Belum dinilai','Kualitas':r['data_quality'],'Tindakan awal':r['recommendation']['action'],'Alasan':' | '.join(r['screening']['reasons'])})
        show_table(pd.DataFrame(rows),hide_index=True,width='stretch')
    st.subheader('Bandingkan parameter')
    nums=[k for k,m in PARAMETERS.items() if 'range' in m and any(values(r['feature_snapshot']).get(k) is not None for r in results)]
    if not nums:
        st.info('Belum ada parameter numerik untuk dibandingkan.')
        exports(results,'comparison_')
        return
    param=st.selectbox('Parameter grafik',nums,format_func=lambda k:f"{PARAMETERS[k]['label']} ({PARAMETERS[k]['unit']})", key='comparison_parameter_'+scope())
    chart=pd.DataFrame([{'Zona':r['feature_snapshot']['zone_id'],'Nilai':values(r['feature_snapshot']).get(param)} for r in results]).set_index('Zona')
    if chart['Nilai'].notna().any():
        st.bar_chart(chart.dropna(),color='#278267',height=250)
        if chart['Nilai'].isna().any(): st.caption('Zona tanpa nilai tidak digambar; kosong bukan nol.')
    else: st.info('Belum ada nilai untuk parameter ini.')
    st.caption('Lihat sumber, tanggal, dan kualitas setiap nilai pada Analisis lokasi → Data input.')
    exports(results,'comparison_')

def zone_form():
    zones=list_zones('local')
    selected=st.selectbox('Tambah atau edit',['__new__']+[z['zone_id'] for z in zones],format_func=lambda x:'＋ Buat zona baru' if x=='__new__' else next(z['zone_name'] for z in zones if z['zone_id']==x),key='edit_choice')
    existing=next((z for z in zones if z['zone_id']==selected),None)
    with st.form('zone_form_'+selected):
        a,b=st.columns(2)
        zid=a.text_input('ID zona',value=existing['zone_id'] if existing else '',disabled=bool(existing),placeholder='ZONA-001')
        name=b.text_input('Nama zona',value=existing['zone_name'] if existing else '',placeholder='Nama lokasi survei')
        land=a.selectbox('Jenis tutupan',LANDCOVERS,index=LANDCOVERS.index(existing['landcover_type']) if existing else len(LANDCOVERS)-1)
        legal=b.selectbox('Status legal',LEGAL,index=LEGAL.index(existing['legal_status']) if existing else 1)
        st.caption('Terverifikasi berarti Anda memiliki bukti status lahan/izin. Catat referensinya di bawah; pilihan ini bukan verifikasi otomatis aplikasi.')
        legal_ref=st.text_input('Referensi status lahan / izin',value=existing.get('provenance',{}).get('legal_reference','') if existing else '')
        geom=json.dumps(existing['geometry'],ensure_ascii=False) if existing else '{"type":"Point","coordinates":[112.5,-6.9]}'
        geometry=st.text_area('Geometri GeoJSON (EPSG:4326)',value=geom,height=100,help='Point: [bujur, lintang]. Polygon: ring tertutup. Koordinat contoh perlu diganti dengan hasil survei.')
        st.markdown('**Observasi per parameter**')
        st.caption('Isi nilai beserta sumber, tanggal YYYY-MM-DD, kualitas, dan metode per baris. Biarkan nilai kosong bila belum diukur. Satuan sudah ditetapkan; jangan diganti.')
        rows=[]
        for k,m in PARAMETERS.items():
            o=existing['observations'][k] if existing else {}
            rows.append({'parameter':k,'value':'' if o.get('value') is None else str(o['value']),'unit':m['unit'],'source':o.get('source') or '', 'date':o.get('date') or '', 'quality_flag':o.get('quality_flag') if o.get('quality_flag') not in (None,'missing') else 'measured','method':o.get('method') or '', 'datum':o.get('datum') or ''})
        edited=st.data_editor(pd.DataFrame(rows),hide_index=True,width='stretch',height=500,disabled=['parameter','unit'],column_config={'quality_flag':st.column_config.SelectboxColumn('Kualitas',options=QUALITIES,required=True),'value':st.column_config.TextColumn('Nilai'),'source':st.column_config.TextColumn('Sumber'),'date':st.column_config.TextColumn('Tanggal'),'method':st.column_config.TextColumn('Metode'),'datum':st.column_config.TextColumn('Datum elevasi')},key='observations_'+selected)
        submitted=st.form_submit_button('Simpan zona',type='primary')
    if submitted:
        try:
            observations={r['parameter']:{k:(None if pd.isna(v) else v) for k,v in r.items() if k!='parameter'} for r in edited.to_dict('records')}
            provenance=dict(existing['provenance']) if existing else {}
            provenance['legal_reference']=legal_ref
            p={'zone_id':zid,'zone_name':name,'landcover_type':land,'legal_status':legal,'observations':observations,'provenance':provenance}
            # Jangan mencuci penanda data sintetis saat diedit.
            if existing and existing['is_demo']: p['quality_flag']='demo'
            z=normalize_zone(p,json.loads(geometry))
            save_zones([z],replace=bool(existing))
            st.session_state['selected_zone']=z['zone_id']
            st.success('Zona tersimpan. Buka Analisis lokasi untuk melihat hasil terbaru.')
        except (ValueError,TypeError,KeyError) as e: st.error(str(e))
    with st.expander('Kategori yang diperbolehkan untuk nilai teks'):
        for k,m in PARAMETERS.items():
            if 'choices' in m: st.write(f"**{k}:** {', '.join(m['choices'])}")

def data_page():
    header('PENGELOLAAN / 04','Data & model','Kelola zona, jejak sumber observasi, dan kesiapan model.')
    tabs=st.tabs(['Impor & template','Tambah / edit zona','Dataset tersimpan','Status model'])
    with tabs[0]:
        st.subheader('Mulai dari data yang dapat ditelusuri')
        st.write('CSV untuk titik sampel; GeoJSON untuk polygon atau titik. Semua koordinat mengikuti EPSG:4326 [longitude, latitude].')
        a,b,c=st.columns(3)
        a.download_button('Template CSV kosong',(ROOT/'data/demo/template_kosong.csv').read_bytes(),'template_kosong.csv','text/csv')
        b.download_button('Contoh CSV sintetis',(ROOT/'data/demo/titik_simulasi.csv').read_bytes(),'titik_simulasi.csv','text/csv')
        c.download_button('Contoh GeoJSON sintetis',(ROOT/'data/demo/zona_simulasi.geojson').read_bytes(),'zona_simulasi.geojson','application/geo+json')
        st.caption('Contoh GeoJSON memakai ID demo yang dicadangkan. Ubah ID sebelum diimpor ke Analis lokal; penanda data demo tetap dipertahankan.')
        if scope()!='local':
            st.info('Pilih Analis lokal pada sidebar untuk mengimpor atau mengedit. Dataset demo bersifat baca-saja.')
        else:
            uploaded=st.file_uploader('Unggah CSV / GeoJSON',type=['csv','geojson','json'],help='Maksimum sesuai konfigurasi, default 10 MB dan 1.000 zona.')
            if uploaded:
                try:
                    zones,meta=parse_upload(uploaded.getvalue(),uploaded.name)
                    st.success(f'Validasi lolos: {len(zones)} zona. Data belum disimpan sampai tombol impor ditekan.')
                    show_table(pd.DataFrame([{'ID':z['zone_id'],'Nama':z['zone_name'],'Geometri':z['geometry']['type'],'Data sintetis':z['is_demo']} for z in zones]),hide_index=True,width='stretch')
                    replace=st.checkbox('Perbarui zona lokal dengan ID yang sama',help='Riwayat analisis sebelumnya tetap tersimpan.')
                    if st.button('Impor dan simpan',type='primary'):
                        try: save_zones(zones,replace=replace,dataset=meta);st.success('Dataset tersimpan. Pilih Analisis lokasi untuk melanjutkan.')
                        except ValueError as e: st.error(str(e))
                except (ValidationError,TypeError,KeyError) as e: st.error(f'VALIDATION_ERROR — {e}')
    with tabs[1]:
        if scope()!='local': st.info('Pilih Analis lokal untuk menambah atau mengedit zona.')
        else: zone_form()
    with tabs[2]:
        zs=workspace_zones()
        if zs:
            show_table(pd.DataFrame([{'ID':z['zone_id'],'Nama':z['zone_name'],'Geometri':z['geometry']['type'],'Legal':z['legal_status'],'Sumber sintetis':z['is_demo']} for z in zs]),hide_index=True,width='stretch')
            if st.button('Cadangkan seluruh zona sebagai GeoJSON'):
                rs=[r for r,_ in results_for(zs)]
                st.download_button('Unduh cadangan',export_geojson(rs),'mangrove_fit_cadangan.geojson','application/geo+json')
        else: empty_state()
        datasets=list_datasets()
        if datasets and scope()=='local': show_table(pd.DataFrame(datasets),hide_index=True,width='stretch')
        st.caption('Cadangan penuh termasuk riwayat analisis dan tinjauan: tutup aplikasi, lalu salin berkas data/app.db. Ekspor GeoJSON menyimpan data zona dan tinjauan analisis yang dipilih.')
    with tabs[3]:
        model_status_panel()

def methodology_page():
    header('REFERENSI / 05','Metodologi & batasan','Pahami apa yang disimpulkan aplikasi, dari mana asalnya, dan apa yang belum diketahui.')
    a,b,c=st.columns(3)
    for col,title,text in [(a,'01 · Screening','Validasi data, geometri, habitat, legal, dan ketersediaan parameter inti.'),(b,'02 · Kajian tindakan','Aturan terbuka memberi arah pemeriksaan; peninjauan ahli tetap diperlukan.'),(c,'03 · Model bersyarat','XGBoost dan SHAP belum terhubung. Tidak ada probabilitas atau akurasi yang dibuat-buat.')]:
        with col: st.markdown(f'<div class="card"><h3>{title}</h3><p>{text}</p></div>',unsafe_allow_html=True)
    st.subheader('Tiga hal yang berbeda')
    show_table(pd.DataFrame([{'Hasil':'Kesesuaian habitat','Makna':'Kondisi yang mendukung habitat mangrove','Status MVP':'Prediksi model belum tersedia'},{'Hasil':'Urgensi intervensi','Makna':'Ancaman/degradasi yang perlu diteliti','Status MVP':'Hanya sinyal dari observasi; tidak ada skor komposit'},{'Hasil':'Kesiapan tindakan','Makna':'Kecukupan data, izin, dan tinjauan ahli','Status MVP':'Penyaringan awal; bukan izin tanam'}]),hide_index=True,width='stretch')
    st.subheader('Aturan yang dapat diperiksa')
    st.code((ROOT/'config/rules.yaml').read_text(),language='yaml')
    st.write('Aturan ini merupakan konsep awal. Tidak ada ambang salinitas, elevasi, atau genangan universal yang diangkat menjadi klaim ilmiah. Perubahan rules.yaml mengubah checksum dan membatalkan penggunaan snapshot lama sebagai hasil terkini.')
    with st.expander('Parameter, satuan, dan sumber data',expanded=True):
        show_table(pd.DataFrame([{'Field':k,'Parameter':m['label'],'Satuan':m['unit']} for k,m in PARAMETERS.items()]),hide_index=True,width='stretch')
        st.write('Salinitas, hidroperiode, substrat, dan regenerasi perlu sumber lapangan/sekunder terverifikasi. NDVI dan NDMI bukan pengukuran langsung salinitas atau keberhasilan penanaman. Elevasi tanpa datum tidak ditafsirkan terhadap pasang surut.')
    st.subheader('Keterbatasan yang perlu diketahui')
    st.markdown('- Semua zona bawaan adalah sintetis. Koordinat dan luasan tidak menunjukkan lokasi rehabilitasi nyata.\n- Status legal dan sumber diisi pengguna; aplikasi tidak memverifikasinya secara independen.\n- Tidak ada login multiuser atau sinkronisasi; ruang kerja ini untuk laptop lokal.\n- Basemap memerlukan internet. Data, formulir, screening, dan peta skematis tetap dapat digunakan offline setelah dependensi terpasang.\n- Tinjauan ahli berupa catatan, tidak mengizinkan aktivitas secara otomatis.\n- SHAP, bila diintegrasikan kelak, menjelaskan model dan bukan hubungan sebab-akibat.')
    st.subheader('Rujukan teknis')
    st.markdown('[Streamlit](https://docs.streamlit.io/) · [SQLite / Python](https://docs.python.org/3/library/sqlite3.html) · [GeoJSON RFC 7946](https://www.rfc-editor.org/rfc/rfc7946) · [Folium](https://python-visualization.github.io/folium/latest/)')
    st.caption('Rujukan ilmiah pada dokumen spesifikasi disertakan dalam docs/spesifikasi_sumber.md untuk telaah ahli. Aplikasi tidak mengunduh atau mengklaim sudah memakai dataset tersebut.')
