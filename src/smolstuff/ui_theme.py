"""Shared dark presentation tokens; no business state or authority lives here."""

STYLE = """
:root{color-scheme:dark;--bg:#101115;--surface:#1b1d24;--raised:#22252e;--ink:#f5f3fb;--muted:#b1b3c3;--line:#363945;--accent:#c4b5fd;--mint:#a8e8ce;--wait:#3b3046;--progress:#233843;--done:#243c33;--idle:#2b2d37}

*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:15px;line-height:1.6}
a{color:var(--accent);text-underline-offset:4px}
button,input,select{font:inherit}
button,a,input,select,summary{-webkit-tap-highlight-color:transparent}
button,a,summary{touch-action:manipulation}
a,button,input,select,summary{outline-offset:5px}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--mint)}
.skip{position:fixed;top:-80px;left:16px;z-index:5;background:var(--mint);color:#15231e;padding:12px;border-radius:12px}
.skip:focus{top:12px}

.app-layout{max-width:1440px;margin:auto;display:grid;grid-template-columns:228px minmax(0,1fr);min-height:100vh}
.rail{padding:34px 24px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:40px}
.brand{display:flex;gap:10px;align-items:center;color:var(--ink);font-size:23px;font-weight:750;letter-spacing:-1px;text-decoration:none}
.brand-mark{width:38px;height:38px;flex-shrink:0;background:var(--accent);border-radius:13px;color:#211b36;display:grid;place-items:center;transform:rotate(-7deg);font-size:24px;font-weight:800}
.rail-label,.kicker{font-size:11px;text-transform:uppercase;letter-spacing:1.8px;font-weight:700;color:var(--muted)}
.rail nav{display:grid;gap:7px}
.rail nav a{display:flex;align-items:center;gap:12px;padding:12px;border:1px solid transparent;border-radius:12px;color:var(--muted);text-decoration:none;font-size:13px;font-weight:550}
.rail nav a:hover{color:var(--ink);background:var(--raised)}
.rail nav a[aria-current=page]{color:var(--accent);background:#292438;border-color:#4b4163}
.nav-icon{font-size:17px;width:20px;text-align:center}
.rail-note{margin-top:auto;background:var(--surface);border:1px solid var(--line);padding:15px;border-radius:16px;font-size:12px;color:var(--muted)}
.rail-note strong{color:var(--mint);display:block;margin-bottom:5px}

main{min-width:0;padding:30px 42px 56px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:32px;padding-bottom:20px;border-bottom:1px solid var(--line)}
.workspace{font-size:13px;color:var(--muted)}
.workspace strong{color:var(--ink);font-weight:550}
.demo-tag{border:1px solid #4a425f;color:#d9ccff;background:#292438;border-radius:99px;padding:5px 12px;font-size:11px;font-weight:600}
.home{font-size:13px}
.hero{position:relative;padding:27px 30px 30px;border:1px solid #48405a;border-radius:24px;margin-bottom:26px;background:radial-gradient(ellipse at 100% 0%,#353047 0%,transparent 65%),#1c1b25;overflow:hidden}
.hero .kicker{color:#d0c1f7}
.hero h1{max-width:570px;font-size:36px;line-height:1.2;font-weight:650;letter-spacing:-1.3px;margin:12px 0}
.hero .lede{max-width:580px;margin-bottom:0}
.hero-spark{position:absolute;right:26px;top:26px;color:var(--accent);font-size:30px}
.counts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:22px 0 30px}
.counts span,.counts a.count-link{display:flex;flex-direction:column-reverse;padding:16px 18px;border:1px solid var(--line);border-radius:16px;background:var(--surface);font-size:11px;color:var(--muted);text-decoration:none}
.counts a.count-link{border-color:#6a5a88;background:linear-gradient(180deg,#262235 0%,var(--surface) 70%);cursor:pointer}
.counts a.count-link:hover,.counts a.count-link:focus-visible{border-color:var(--accent);color:var(--ink);outline:none}
.counts strong{font-size:28px;color:var(--ink);font-weight:600;line-height:1.25;margin-top:5px;font-variant-numeric:tabular-nums}
.attention-card{border-color:#6a5a88;margin:0 0 22px}
#attention-filter-note{margin:0 0 12px}

h1{font-size:30px;line-height:1.25;letter-spacing:-1px;font-weight:650;margin:0 0 12px}
h2{font-size:12px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin:28px 0 14px;font-weight:650}
h3{font-size:18px;letter-spacing:-.4px;line-height:1.35;margin:15px 0 8px;font-weight:600}
.lede,.note,.tagline{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
article,.card{min-width:0;border:1px solid var(--line);background:var(--surface);border-radius:20px;padding:24px;margin-top:18px;box-shadow:0 8px 30px #00000014}
.grid article{margin:0;display:flex;flex-direction:column;transition:border-color .16s,transform .16s}
.grid article:hover{border-color:#6f618d;transform:translateY(-2px)}
article p,.card p{margin:8px 0}
.grid article>p:not(.status){color:var(--muted);font-size:13px}
.card-top{display:flex;align-items:center;justify-content:space-between;gap:10px}
.card-icon{display:grid;place-items:center;width:40px;height:40px;border:1px solid #56486d;border-radius:13px;background:#30283e;color:#dfccff;font-size:20px}
.status{display:inline-flex;align-items:center;font-size:11px;font-weight:650;line-height:1.4;padding:6px 10px;border:1px solid var(--line);border-radius:99px;background:var(--idle);color:var(--ink);width:fit-content}
.status.decision,.status.waiting{background:var(--wait);color:#e8c8fa;border-color:#6a4b7a}
.status.progress,.status.executing,.status.reconciling{background:var(--progress);color:#b5e1f2;border-color:#426778}
.status.done,.status.completed{background:var(--done);color:var(--mint);border-color:#427562}
.card-actions{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin-top:auto;padding-top:22px}
.open{font-size:13px;text-decoration:none;color:var(--ink);border:1px solid var(--line);padding:9px 14px;border-radius:10px}
.open:hover{background:var(--raised)}
form{display:inline}
button{font-size:13px;font-weight:650;border-radius:11px;padding:11px 16px;min-height:44px;cursor:pointer;margin:5px 6px 5px 0;border:1px solid var(--line);color:var(--ink);background:var(--raised)}
button.primary{background:var(--accent);border-color:var(--accent);color:#20192f}
button.primary:hover{background:#d4c8ff}
button.secondary{background:transparent;color:var(--ink)}
button.secondary:hover{background:var(--raised)}
label{display:block;color:var(--muted);font-size:13px;margin:16px 0}
input,select{display:block;width:100%;max-width:320px;background:#14151c;color:var(--ink);border:1px solid #747988;border-radius:10px;padding:11px 13px;margin-top:7px;min-height:44px}
input[type=checkbox]{display:inline;width:20px;min-height:20px;vertical-align:middle;accent-color:var(--accent);margin:0 8px}
input[type=hidden]{display:none}
details{margin-top:22px;padding-top:18px;border-top:1px solid var(--line)}
summary{cursor:pointer;min-height:44px;color:var(--accent);font-weight:600;font-size:13px}
details p,details li{font-size:13px;color:var(--muted)}
pre{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere;background:#14151c;border:1px solid var(--line);padding:16px;border-radius:12px}
dl{display:grid;grid-template-columns:minmax(120px,1fr) 2fr;gap:8px}
dt{color:var(--muted)}
dd{margin:0}
.decision{font-size:22px;font-weight:650;letter-spacing:-.4px;margin:10px 0 6px;color:var(--ink)}
.consequence{font-size:14px;color:var(--muted);margin:0 0 4px;max-width:42rem}
.sim-banner{margin:0 0 18px;padding:12px 16px;border:1px solid #56486d;border-radius:14px;background:#252033;color:#d7ccec;font-size:13px;line-height:1.45}
.sim-banner strong{color:var(--ink);font-weight:650}
.decision-hero{margin-bottom:18px}
.decision-card{margin-top:0}
.launch-primary{border-color:#6a5a88;background:linear-gradient(180deg,#262235 0%,var(--surface) 70%)}
h2.launch-title{font-size:20px;letter-spacing:-.4px;text-transform:none;color:var(--ink);margin:10px 0 8px;font-weight:650}
.card-next{margin:4px 0 0;font-size:12px}
.decision-actions{padding-top:14px;gap:8px}
.decision-actions form{display:inline}
.decision-actions button{margin:0 8px 8px 0}
.why-details{margin-top:18px;padding-top:16px}
.built-with{font-size:12px;color:var(--muted)}
.empty{font-size:13px;color:var(--muted);padding:14px 18px;border:1px dashed var(--line);border-radius:12px;margin:0}
.activity{list-style:none;padding:0;display:grid;gap:10px}
.activity li{padding:16px 20px;border:1px solid var(--line);border-radius:14px;background:var(--surface);font-size:13px;color:var(--muted);overflow-wrap:anywhere}
.activity strong{color:var(--ink)}
ul,ol{padding-left:24px}
li{margin:8px 0;overflow-wrap:anywhere}
.footer-note{margin-top:40px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:11px}
.alert{border-left:3px solid #efbbbc}
.alert p{color:#f4cdd0}
.stock-table{width:100%;border-collapse:collapse;margin:12px 0 4px;font-variant-numeric:tabular-nums}
.stock-table th,.stock-table td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:left;font-size:13px}
.stock-table th{color:var(--muted);font-weight:650;font-size:11px;text-transform:uppercase;letter-spacing:.6px}
.stock-table td.num,.stock-table th.num{text-align:right}
.stock-table tbody tr:last-child td{border-bottom:0}
.stock-table .total-row td{color:var(--ink);font-weight:600;border-top:1px solid var(--line)}
.catalog-meta{display:flex;flex-wrap:wrap;gap:8px 14px;margin:8px 0 0;font-size:12px;color:var(--muted)}
.catalog-meta strong{color:var(--ink);font-weight:550}
.catalog-toolbar{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:14px;margin:18px 0 12px}
.catalog-toolbar label{margin:0;flex:1 1 220px}
.catalog-toolbar input[type=search]{max-width:100%;margin-top:6px}
.catalog-wrap{border:1px solid var(--line);border-radius:16px;background:var(--surface);overflow:auto;max-height:min(70vh,720px)}
.catalog-table{width:100%;border-collapse:separate;border-spacing:0;font-variant-numeric:tabular-nums;min-width:1040px}
.catalog-table td.date{font-variant-numeric:tabular-nums;white-space:nowrap;font-size:12px;color:var(--muted)}
.catalog-table th,.catalog-table td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;font-size:13px;vertical-align:top}
.catalog-table thead th{position:sticky;top:0;z-index:2;background:#22252e;color:var(--muted);font-weight:650;font-size:11px;text-transform:uppercase;letter-spacing:.5px}
.catalog-table th.col-product,.catalog-table td.col-product{position:sticky;left:0;z-index:1;background:var(--surface);min-width:180px;max-width:240px;box-shadow:1px 0 0 var(--line)}
.catalog-table thead th.col-product{z-index:3;background:#22252e}
.catalog-table td.num,.catalog-table th.num{text-align:right;white-space:nowrap}
.catalog-table td.sku{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;color:var(--muted);white-space:nowrap}
.catalog-table tbody tr:hover td{background:#22252e}
.catalog-table tbody tr:hover td.col-product{background:#22252e}
.catalog-table tbody tr.is-hidden{display:none}
.catalog-table tbody tr.catalog-focus{outline:2px solid var(--accent);outline-offset:-2px;background:rgba(167,139,250,.08)}
.catalog-table .product-name{font-weight:600;color:var(--ink);display:block;margin-bottom:2px;line-height:1.3}
.catalog-table .product-meta{display:block;font-size:11px;color:var(--muted);margin:0 0 4px;line-height:1.35;font-weight:450}
.catalog-table .col-category{font-size:11px;color:var(--muted);white-space:nowrap;max-width:6.5rem;padding-left:8px;padding-right:8px}
.catalog-table .col-itemid{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:11px;color:var(--muted);white-space:nowrap;max-width:8.5rem}
.catalog-table .issue-cell{display:flex;flex-direction:column;align-items:flex-start;gap:4px;min-width:6.5rem}
.catalog-table .issue-cell .row-status{margin:0}
.catalog-table .issue-cell .row-open{font-size:11px;line-height:1.3;white-space:normal}
.catalog-table .sort-btn{appearance:none;-webkit-appearance:none;background:transparent;border:0;color:inherit;font:inherit;font-weight:650;font-size:inherit;text-transform:inherit;letter-spacing:inherit;padding:0;margin:0;cursor:pointer;display:inline-flex;align-items:center;gap:4px;min-height:auto}
.catalog-table .sort-btn:hover,.catalog-table .sort-btn:focus-visible{color:var(--ink)}
.catalog-table .sort-btn[data-dir="asc"]::after{content:" ▲";font-size:9px;color:var(--accent,#b5e1f2)}
.catalog-table .sort-btn[data-dir="desc"]::after{content:" ▼";font-size:9px;color:var(--accent,#b5e1f2)}
.catalog-table .muted-zero{color:var(--muted);font-weight:400}
.catalog-table details{margin:0;padding:0;border:0}
.catalog-table summary{min-height:auto;padding:2px 0;font-size:12px;font-weight:550}
.catalog-table .unavail-cell{min-width:4.5rem}
.catalog-table .unavail-split{margin:0}
.catalog-table .unavail-split>summary{list-style:none;cursor:pointer;text-align:right;padding:0;font-variant-numeric:tabular-nums;font-weight:650}
.catalog-table .unavail-split>summary::-webkit-details-marker{display:none}
.catalog-table .unavail-split>summary::after{content:" ▾";font-size:10px;color:var(--muted);font-weight:400}
.catalog-table .unavail-split[open]>summary::after{content:" ▴"}
.catalog-table .unavail-parts{display:grid;gap:4px;margin:6px 0 0;padding:6px 8px;border:1px solid var(--line);border-radius:10px;background:#1c1f27;text-align:left;font-size:11px}
.catalog-table .unavail-parts div{display:flex;justify-content:space-between;gap:10px;margin:0}
.catalog-table .unavail-parts dt{margin:0;color:var(--muted);font-weight:650}
.catalog-table .unavail-parts dd{margin:0;color:var(--ink);font-variant-numeric:tabular-nums}
.catalog-table .product-detail{margin-top:8px;padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:#1c1f27}
.catalog-table .product-prices,.catalog-table .product-attrs{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px 14px;margin:0 0 10px;font-size:12px}
.catalog-table .product-prices div,.catalog-table .product-attrs div{margin:0}
.catalog-table .product-prices dt,.catalog-table .product-attrs dt{color:var(--muted);font-weight:650;font-size:10px;text-transform:uppercase;letter-spacing:.5px;margin:0 0 2px}
.catalog-table .product-prices dd,.catalog-table .product-attrs dd{margin:0;color:var(--ink);font-weight:550}
.catalog-table .product-desc{margin:0 0 8px;font-size:12px;color:var(--muted)}
.catalog-table .row-status{margin:0;cursor:help;display:inline-block;padding:3px 8px;font-size:11px;line-height:1.25;white-space:normal;max-width:7.5rem;text-align:center}
.catalog-table .row-open{font-size:12px;white-space:nowrap}
.catalog-empty{padding:18px;color:var(--muted);font-size:13px;display:none}
.catalog-empty.is-visible{display:block}
.catalog-mobile-hint{display:none}
.inbound-hot{color:#b5e1f2;font-weight:650}
.hold-hot{color:#f0c4a8;font-weight:650}

@media(max-width:1050px){.app-layout{grid-template-columns:190px minmax(0,1fr)}
.rail{padding:28px 16px}
main{padding:26px}
.hero h1{font-size:30px}
.counts span{padding:14px 12px}
}
@media(max-width:760px){.app-layout{display:block}
.rail{padding:18px 20px;gap:16px;border-right:0;border-bottom:1px solid var(--line)}
.rail nav{display:flex;flex-wrap:wrap;gap:4px}
.rail nav a{padding:8px;font-size:11px;min-height:44px;gap:5px}
.rail-label,.rail-note{display:none}
.brand{font-size:21px}
.brand-mark{height:32px;width:32px}
.top{margin-bottom:22px}
.grid{grid-template-columns:1fr}
main{padding:22px 20px 40px}
.hero{padding:22px}
.hero h1{font-size:29px;padding-right:15px}
.hero-spark{font-size:22px;right:18px;top:18px}
.counts{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.counts span{padding:12px 16px}
h1{font-size:26px}
article,.card{padding:20px}
.top{flex-wrap:wrap}
button{max-width:100%;white-space:normal}
dl{grid-template-columns:1fr}
.open{min-height:44px}
.stock-table{display:block;overflow-x:auto}
.catalog-wrap{overflow-x:visible}
.catalog-mobile-hint{display:block;margin:0 0 10px}
.catalog-table{min-width:0;width:100%}
.catalog-table .col-more{display:none}
.catalog-table th.col-product,.catalog-table td.col-product{position:static;box-shadow:none;min-width:0;max-width:none;width:42%}
.catalog-table th.col-key,.catalog-table td.col-key{padding:8px 6px}
.catalog-table .product-name{font-size:13px}
.catalog-table .product-meta{font-size:10px;margin-bottom:2px}
}

@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
}

"""
