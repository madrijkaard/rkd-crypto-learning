import os
import json
import pandas as pd

class ClusterVisualizer:

    def __init__(self, output_file: str = "cluster_report.html"):
        self.output_file = output_file

    def generate(
        self,
        clustered_df: pd.DataFrame,
        best_k: int,
        best_silhouette: float,
        silhouette_vals: dict,
        inertia_vals: dict,
    ) -> str:

        df = clustered_df.reset_index()

        assets = []
        for _, row in df.iterrows():
            assets.append({
                "symbol": str(row["symbol"]).replace("/USDT", ""),
                "vol": float(row["vol_abs"]),
                "corr": float(row["correlation_btc"]),
                "cluster": int(row["cluster"]),
                "dist": float(row["distance_to_centroid"]),
            })

        cluster_counts = df["cluster"].value_counts().to_dict()

        assets_json = json.dumps(assets)
        silhouette_json = json.dumps({str(k): round(v, 4) for k, v in silhouette_vals.items()})
        inertia_json = json.dumps({str(k): round(v, 4) for k, v in inertia_vals.items()})

        c0_count = cluster_counts.get(0, 0)
        c1_count = cluster_counts.get(1, 0)
        total = len(df)

        html = self._build_html(
            assets_json=assets_json,
            silhouette_json=silhouette_json,
            inertia_json=inertia_json,
            best_k=best_k,
            best_silhouette=best_silhouette,
            c0_count=c0_count,
            c1_count=c1_count,
            total=total,
        )

        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Relatório HTML salvo em: {self.output_file}")
        return self.output_file

    def _build_html(
        self,
        assets_json: str,
        silhouette_json: str,
        inertia_json: str,
        best_k: int,
        best_silhouette: float,
        c0_count: int,
        c1_count: int,
        total: int,
    ) -> str:

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Crypto Cluster Report</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #06080f;
    --panel: #0d1220;
    --border: #1a2340;
    --c0: #00e5ff;
    --c1: #ff4d6d;
    --c0dim: rgba(0,229,255,0.12);
    --c1dim: rgba(255,77,109,0.12);
    --text: #c8d8f0;
    --muted: #4a5a7a;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
  }}
  body::before {{
    content:'';
    position:fixed; inset:0;
    background-image:
      linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events:none;
  }}

  header {{
    padding: 2rem 3rem 1rem;
    border-bottom: 1px solid var(--border);
    display:flex; align-items:flex-end; justify-content:space-between;
    flex-wrap:wrap; gap:1rem;
  }}
  .logo {{ font-size:1.6rem; font-weight:800; letter-spacing:-0.03em; }}
  .logo span {{ color:var(--c0); }}
  .subtitle {{ font-family:'Space Mono',monospace; font-size:0.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.15em; margin-top:0.25rem; }}
  .legend {{ display:flex; gap:1.5rem; font-family:'Space Mono',monospace; font-size:0.75rem; }}
  .legend-item {{ display:flex; align-items:center; gap:0.5rem; }}
  .dot {{ width:10px; height:10px; border-radius:50%; }}

  /* TABS */
  .tabs {{ display:flex; gap:0; border-bottom:1px solid var(--border); padding: 0 3rem; }}
  .tab {{
    font-family:'Space Mono',monospace; font-size:0.72rem; text-transform:uppercase;
    letter-spacing:0.1em; padding:0.8rem 1.2rem; cursor:pointer;
    color:var(--muted); border-bottom:2px solid transparent; margin-bottom:-1px;
    transition: color 0.2s, border-color 0.2s;
  }}
  .tab.active {{ color:var(--c0); border-bottom-color:var(--c0); }}
  .tab-content {{ display:none; padding: 2rem 3rem; }}
  .tab-content.active {{ display:block; }}

  /* SCATTER TAB */
  .scatter-layout {{ display:grid; grid-template-columns: 1fr 320px; gap:2rem; }}
  #scatter-wrap {{
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 4px; position:relative; overflow:hidden;
    aspect-ratio: 16/10; min-height: 400px;
  }}
  #scatter-wrap canvas {{ display:block; width:100%; height:100%; }}
  .axis-label {{ font-family:'Space Mono',monospace; font-size:0.62rem; color:var(--muted); position:absolute; letter-spacing:0.1em; text-transform:uppercase; }}
  .axis-x {{ bottom:8px; right:12px; }}
  .axis-y {{ top:12px; left:12px; }}

  /* TOOLTIP */
  #tooltip {{
    position:fixed; background: rgba(13,18,32,0.97);
    border: 1px solid var(--c0); border-radius:4px;
    padding: 0.6rem 0.9rem; font-family:'Space Mono',monospace; font-size:0.72rem;
    pointer-events:none; opacity:0; transition:opacity 0.1s;
    z-index:100; min-width:180px;
  }}
  #tooltip .tt-symbol {{ font-size:0.9rem; font-weight:700; font-family:'Syne',sans-serif; margin-bottom:0.3rem; }}
  #tooltip .tt-row {{ display:flex; justify-content:space-between; gap:1.5rem; color:var(--muted); }}
  #tooltip .tt-val {{ color:var(--text); }}

  /* SIDEBAR */
  .sidebar {{ display:flex; flex-direction:column; gap:1rem; }}
  .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius:4px; padding: 1.2rem; }}
  .panel-title {{ font-family:'Space Mono',monospace; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.15em; color:var(--muted); margin-bottom:1rem; border-bottom:1px solid var(--border); padding-bottom:0.6rem; }}
  .cluster-stat {{ margin-bottom:1rem; }}
  .cs-header {{ display:flex; align-items:center; gap:0.6rem; margin-bottom:0.4rem; }}
  .cs-name {{ font-weight:600; font-size:0.9rem; }}
  .cs-count {{ font-family:'Space Mono',monospace; font-size:0.7rem; color:var(--muted); margin-left:auto; }}
  .cs-bar-wrap {{ background: rgba(255,255,255,0.04); height:4px; border-radius:2px; }}
  .cs-bar {{ height:4px; border-radius:2px; }}
  .cs-desc {{ font-size:0.75rem; color:var(--muted); margin-top:0.4rem; line-height:1.5; }}
  #search {{ width:100%; background: rgba(255,255,255,0.04); border:1px solid var(--border); color:var(--text); font-family:'Space Mono',monospace; font-size:0.8rem; padding:0.5rem 0.8rem; border-radius:4px; outline:none; transition: border-color 0.2s; }}
  #search:focus {{ border-color: var(--c0); }}
  #search::placeholder {{ color: var(--muted); }}
  #coin-list {{ max-height:300px; overflow-y:auto; margin-top:0.8rem; }}
  #coin-list::-webkit-scrollbar {{ width:4px; }}
  #coin-list::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:2px; }}
  .coin-row {{ display:flex; align-items:center; gap:0.6rem; padding:0.35rem 0.2rem; border-bottom:1px solid rgba(255,255,255,0.03); cursor:pointer; transition:background 0.1s; border-radius:2px; }}
  .coin-row:hover {{ background:rgba(255,255,255,0.04); }}
  .cr-name {{ font-size:0.8rem; font-weight:600; flex:1; }}
  .cr-cluster {{ font-family:'Space Mono',monospace; font-size:0.65rem; padding:1px 5px; border-radius:2px; }}
  .cr-dist {{ font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--muted); }}

  /* METRICS TAB */
  .metrics-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:1.5rem; }}
  .metric-card {{ background:var(--panel); border:1px solid var(--border); border-radius:4px; padding:1.5rem; }}
  .mc-title {{ font-family:'Space Mono',monospace; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.15em; color:var(--muted); margin-bottom:1rem; }}
  .mc-big {{ font-size:2.5rem; font-weight:800; letter-spacing:-0.03em; }}
  .mc-sub {{ font-size:0.8rem; color:var(--muted); margin-top:0.3rem; }}
  .chart-wrap {{ background:var(--panel); border:1px solid var(--border); border-radius:4px; padding:1.5rem; }}
  .mini-chart {{ display:flex; align-items:flex-end; gap:6px; height:80px; margin-top:1rem; }}
  .bar-col {{ flex:1; display:flex; flex-direction:column; align-items:center; gap:4px; }}
  .bar {{ border-radius:2px 2px 0 0; width:100%; transition:opacity 0.2s; min-height:2px; }}
  .bar:hover {{ opacity:0.7; }}
  .bar-label {{ font-family:'Space Mono',monospace; font-size:0.6rem; color:var(--muted); }}
  .bar-val {{ font-family:'Space Mono',monospace; font-size:0.55rem; color:var(--text); }}
  .charts-row {{ display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-top:1.5rem; }}

  /* RANKING TAB */
  .ranking-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:2rem; }}
  .rank-table {{ background:var(--panel); border:1px solid var(--border); border-radius:4px; overflow:hidden; }}
  .rank-header {{ padding:1rem 1.2rem; border-bottom:1px solid var(--border); font-family:'Space Mono',monospace; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.15em; color:var(--muted); }}
  .rank-row {{ display:grid; grid-template-columns:28px 1fr 80px 80px; gap:0.5rem; padding:0.5rem 1.2rem; border-bottom:1px solid rgba(255,255,255,0.03); align-items:center; font-family:'Space Mono',monospace; font-size:0.72rem; }}
  .rank-row:hover {{ background:rgba(255,255,255,0.03); }}
  .rank-num {{ color:var(--muted); }}
  .rank-name {{ font-weight:700; font-family:'Syne',sans-serif; font-size:0.82rem; }}
  .rank-val {{ text-align:right; }}
  .rank-col-header {{ color:var(--muted); font-size:0.6rem; }}

  @media (max-width:900px) {{
    .scatter-layout, .ranking-grid, .charts-row {{ grid-template-columns:1fr; }}
    header, .tabs, .tab-content {{ padding-left:1.5rem; padding-right:1.5rem; }}
  }}
</style>
</head>
<body>

<header>
  <div>
    <div class="logo">CRYPTO <span>CLUSTER</span> REPORT</div>
    <div class="subtitle">K-Means · K={best_k} · Silhouette {best_silhouette:.4f} · {total} ativos</div>
  </div>
  <div class="legend">
    <div class="legend-item"><div class="dot" style="background:var(--c0)"></div>Cluster 0 — Altcoins ({c0_count})</div>
    <div class="legend-item"><div class="dot" style="background:var(--c1)"></div>Cluster 1 — Estáveis ({c1_count})</div>
  </div>
</header>

<div class="tabs">
  <div class="tab active" onclick="switchTab('scatter', this)">Scatter Plot</div>
  <div class="tab" onclick="switchTab('metrics', this)">Métricas</div>
  <div class="tab" onclick="switchTab('ranking', this)">Ranking</div>
</div>

<!-- TAB: SCATTER -->
<div class="tab-content active" id="tab-scatter">
  <div class="scatter-layout">
    <div id="scatter-wrap">
      <canvas id="scatter"></canvas>
      <div class="axis-label axis-x">Correlação com BTC →</div>
      <div class="axis-label axis-y">↑ Volatilidade</div>
    </div>
    <div class="sidebar">
      <div class="panel">
        <div class="panel-title">Clusters</div>
        <div class="cluster-stat">
          <div class="cs-header">
            <div class="dot" style="background:var(--c0)"></div>
            <div class="cs-name">Cluster 0 — Altcoins</div>
            <div class="cs-count">{c0_count} ativos</div>
          </div>
          <div class="cs-bar-wrap"><div class="cs-bar" style="background:var(--c0);width:{round(c0_count/total*100)}%"></div></div>
          <div class="cs-desc">Alta correlação com BTC, volatilidade relevante. Seguem o mercado cripto.</div>
        </div>
        <div class="cluster-stat">
          <div class="cs-header">
            <div class="dot" style="background:var(--c1)"></div>
            <div class="cs-name">Cluster 1 — Estáveis</div>
            <div class="cs-count">{c1_count} ativos</div>
          </div>
          <div class="cs-bar-wrap"><div class="cs-bar" style="background:var(--c1);width:{round(c1_count/total*100)}%"></div></div>
          <div class="cs-desc">Baixíssima volatilidade, descorrelacionados do BTC. Stablecoins e similares.</div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title">Buscar ativo</div>
        <input type="text" id="search" placeholder="ex: ETH, SOL, USDC...">
        <div id="coin-list"></div>
      </div>
    </div>
  </div>
</div>

<!-- TAB: MÉTRICAS -->
<div class="tab-content" id="tab-metrics">
  <div class="metrics-grid">
    <div class="metric-card">
      <div class="mc-title">Melhor K</div>
      <div class="mc-big" style="color:var(--c0)">{best_k}</div>
      <div class="mc-sub">clusters identificados automaticamente</div>
    </div>
    <div class="metric-card">
      <div class="mc-title">Silhouette Score</div>
      <div class="mc-big" style="color:var(--c0)">{best_silhouette:.4f}</div>
      <div class="mc-sub">quanto maior, mais separados os clusters (max 1.0)</div>
    </div>
    <div class="metric-card">
      <div class="mc-title">Total de Ativos</div>
      <div class="mc-big" style="color:var(--text)">{total}</div>
      <div class="mc-sub">{c0_count} altcoins · {c1_count} estáveis</div>
    </div>
  </div>
  <div class="charts-row">
    <div class="chart-wrap">
      <div class="mc-title">Silhouette Score por K</div>
      <div class="mini-chart" id="sil-chart"></div>
    </div>
    <div class="chart-wrap">
      <div class="mc-title">Inertia por K</div>
      <div class="mini-chart" id="ine-chart"></div>
    </div>
  </div>
</div>

<!-- TAB: RANKING -->
<div class="tab-content" id="tab-ranking">
  <div class="ranking-grid">
    <div class="rank-table">
      <div class="rank-header">Mais distantes do centróide (atípicos)</div>
      <div class="rank-row rank-col-header"><span>#</span><span>Ativo</span><span class="rank-val">Cluster</span><span class="rank-val">Distância</span></div>
      <div id="rank-far"></div>
    </div>
    <div class="rank-table">
      <div class="rank-header">Mais próximos do centróide (típicos)</div>
      <div class="rank-row rank-col-header"><span>#</span><span>Ativo</span><span class="rank-val">Cluster</span><span class="rank-val">Distância</span></div>
      <div id="rank-near"></div>
    </div>
    <div class="rank-table">
      <div class="rank-header">Maior volatilidade</div>
      <div class="rank-row rank-col-header"><span>#</span><span>Ativo</span><span class="rank-val">Cluster</span><span class="rank-val">Vol %</span></div>
      <div id="rank-vol"></div>
    </div>
    <div class="rank-table">
      <div class="rank-header">Maior correlação com BTC</div>
      <div class="rank-row rank-col-header"><span>#</span><span>Ativo</span><span class="rank-val">Cluster</span><span class="rank-val">Correl.</span></div>
      <div id="rank-corr"></div>
    </div>
  </div>
</div>

<div id="tooltip">
  <div class="tt-symbol" id="tt-symbol"></div>
  <div class="tt-row"><span>Volatilidade</span><span class="tt-val" id="tt-vol"></span></div>
  <div class="tt-row"><span>Correl. BTC</span><span class="tt-val" id="tt-corr"></span></div>
  <div class="tt-row"><span>Dist. centróide</span><span class="tt-val" id="tt-dist"></span></div>
  <div class="tt-row"><span>Cluster</span><span class="tt-val" id="tt-cluster"></span></div>
</div>

<script>
// ── Dados injetados pelo Python ──────────────────────────────────
const DATA = {assets_json};
const SILHOUETTE = {silhouette_json};
const INERTIA = {inertia_json};

// ── Tabs ─────────────────────────────────────────────────────────
function switchTab(id, el) {{
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  el.classList.add('active');
  if(id === 'scatter') setTimeout(drawScatter, 50);
  if(id === 'metrics') renderMetrics();
  if(id === 'ranking') renderRanking();
}}

// ── SCATTER ──────────────────────────────────────────────────────
const canvas = document.getElementById('scatter');
const ctx = canvas.getContext('2d');
let points = [];
let highlighted = -1;

function resizeScatter() {{
  const wrap = document.getElementById('scatter-wrap');
  if(!wrap) return;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = wrap.clientWidth * dpr;
  canvas.height = wrap.clientHeight * dpr;
  canvas.style.width = wrap.clientWidth + 'px';
  canvas.style.height = wrap.clientHeight + 'px';
  drawScatter();
}}

function getCoords(d) {{
  const pad = {{ l:48, r:24, t:24, b:36 }};
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.width, H = canvas.height;
  const minC = -0.15, maxC = 1.0;
  const minV = 0, maxV = 0.023;
  const x = pad.l*dpr + (d.corr - minC)/(maxC - minC) * (W - (pad.l+pad.r)*dpr);
  const y = H - pad.b*dpr - (d.vol - minV)/(maxV - minV) * (H - (pad.t+pad.b)*dpr);
  return [x, y];
}}

function drawScatter() {{
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0,0,W,H);
  ctx.strokeStyle = 'rgba(26,35,64,0.8)'; ctx.lineWidth = 1;
  for(let i=0;i<=10;i++) {{
    const x = 48*dpr + i*(W-72*dpr)/10;
    ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke();
    const y = 24*dpr + i*(H-60*dpr)/10;
    ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke();
  }}
  points = [];
  DATA.forEach((d,i) => {{
    const [x,y] = getCoords(d);
    const isHL = highlighted === i;
    const color = d.cluster === 0 ? '#00e5ff' : '#ff4d6d';
    const r = isHL ? 7*dpr : 4.5*dpr;
    if(isHL) {{ ctx.shadowBlur = 20*dpr; ctx.shadowColor = color; }}
    ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2);
    ctx.fillStyle = isHL ? color : (d.cluster===0 ? 'rgba(0,229,255,0.7)' : 'rgba(255,77,109,0.7)');
    ctx.fill();
    if(isHL) {{ ctx.strokeStyle='#fff'; ctx.lineWidth=1.5*dpr; ctx.stroke(); ctx.shadowBlur=0; }}
    points[i] = {{x,y,r:8*dpr,d}};
  }});
  ctx.fillStyle='rgba(74,90,122,0.8)';
  ctx.font = `${{9*(window.devicePixelRatio||1)}}px Space Mono,monospace`;
  ctx.textAlign='center';
  [-0.1,0,0.2,0.4,0.6,0.8,1.0].forEach(v => {{
    const x = 48*dpr + (v+0.15)/1.15*(W-72*dpr);
    ctx.fillText(v.toFixed(1), x, H-8*dpr);
  }});
}}

canvas.addEventListener('mousemove', e => {{
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio||1;
  const mx=(e.clientX-rect.left)*dpr, my=(e.clientY-rect.top)*dpr;
  let found=-1, minD=Infinity;
  points.forEach((p,i)=>{{ const d=Math.hypot(p.x-mx,p.y-my); if(d<p.r*2&&d<minD){{minD=d;found=i;}} }});
  if(found>=0) {{
    highlighted=found; canvas.style.cursor='pointer';
    const d=DATA[found];
    document.getElementById('tt-symbol').textContent=d.symbol+'/USDT';
    document.getElementById('tt-symbol').style.color=d.cluster===0?'#00e5ff':'#ff4d6d';
    document.getElementById('tt-vol').textContent=(d.vol*100).toFixed(4)+'%';
    document.getElementById('tt-corr').textContent=d.corr.toFixed(4);
    document.getElementById('tt-dist').textContent=d.dist.toFixed(4);
    document.getElementById('tt-cluster').textContent='Cluster '+d.cluster;
    const tt=document.getElementById('tooltip');
    tt.style.opacity='1'; tt.style.left=(e.clientX+14)+'px'; tt.style.top=(e.clientY-10)+'px';
  }} else {{
    highlighted=-1; canvas.style.cursor='default';
    document.getElementById('tooltip').style.opacity='0';
  }}
  drawScatter();
}});
canvas.addEventListener('mouseleave',()=>{{ highlighted=-1; document.getElementById('tooltip').style.opacity='0'; drawScatter(); }});

// Coin list
function renderList(filter='') {{
  const list = document.getElementById('coin-list');
  const filtered = DATA.filter(d=>d.symbol.toLowerCase().includes(filter.toLowerCase()));
  list.innerHTML = filtered.map((d,_)=>{{
    const idx = DATA.indexOf(d);
    return `<div class="coin-row" data-idx="${{idx}}">
      <div class="cr-name">${{d.symbol}}</div>
      <div class="cr-cluster" style="background:${{d.cluster===0?'var(--c0dim)':'var(--c1dim)'}};color:${{d.cluster===0?'var(--c0)':'var(--c1)'}}"">C${{d.cluster}}</div>
      <div class="cr-dist">${{d.dist.toFixed(2)}}</div>
    </div>`;
  }}).join('');
  list.querySelectorAll('.coin-row').forEach(row=>{{
    row.addEventListener('mouseenter',()=>{{ highlighted=parseInt(row.dataset.idx); drawScatter(); }});
    row.addEventListener('mouseleave',()=>{{ highlighted=-1; drawScatter(); }});
  }});
}}
document.getElementById('search').addEventListener('input',e=>renderList(e.target.value));
renderList();

// ── METRICS ──────────────────────────────────────────────────────
function renderMetrics() {{
  // Silhouette chart
  const silEl = document.getElementById('sil-chart');
  const silVals = Object.values(SILHOUETTE);
  const maxSil = Math.max(...silVals);
  silEl.innerHTML = Object.entries(SILHOUETTE).map(([k,v])=>{{
    const h = Math.max(4, (v/maxSil)*72);
    const active = parseFloat(v) === parseFloat(Object.values(SILHOUETTE).reduce((a,b)=>Math.max(a,b)));
    return `<div class="bar-col">
      <div class="bar-val">${{v}}</div>
      <div class="bar" style="height:${{h}}px;background:${{active?'var(--c0)':'rgba(0,229,255,0.3)'}}"></div>
      <div class="bar-label">K=${{k}}</div>
    </div>`;
  }}).join('');

  // Inertia chart
  const ineEl = document.getElementById('ine-chart');
  const ineVals = Object.values(INERTIA);
  const maxIne = Math.max(...ineVals);
  ineEl.innerHTML = Object.entries(INERTIA).map(([k,v])=>{{
    const h = Math.max(4, (v/maxIne)*72);
    return `<div class="bar-col">
      <div class="bar-val">${{Math.round(v)}}</div>
      <div class="bar" style="height:${{h}}px;background:rgba(123,97,255,0.6)"></div>
      <div class="bar-label">K=${{k}}</div>
    </div>`;
  }}).join('');
}}

// ── RANKING ───────────────────────────────────────────────────────
function rankRow(i, d, val, fmt) {{
  const color = d.cluster===0?'var(--c0)':'var(--c1)';
  return `<div class="rank-row">
    <span class="rank-num">${{i+1}}</span>
    <span class="rank-name">${{d.symbol}}</span>
    <span class="rank-val" style="color:${{color}}">C${{d.cluster}}</span>
    <span class="rank-val">${{fmt(val)}}</span>
  </div>`;
}}

function renderRanking() {{
  const sorted_far = [...DATA].sort((a,b)=>b.dist-a.dist).slice(0,15);
  const sorted_near = [...DATA].sort((a,b)=>a.dist-b.dist).slice(0,15);
  const sorted_vol = [...DATA].sort((a,b)=>b.vol-a.vol).slice(0,15);
  const sorted_corr = [...DATA].sort((a,b)=>b.corr-a.corr).slice(0,15);
  document.getElementById('rank-far').innerHTML = sorted_far.map((d,i)=>rankRow(i,d,d.dist,v=>v.toFixed(3))).join('');
  document.getElementById('rank-near').innerHTML = sorted_near.map((d,i)=>rankRow(i,d,d.dist,v=>v.toFixed(3))).join('');
  document.getElementById('rank-vol').innerHTML = sorted_vol.map((d,i)=>rankRow(i,d,d.vol,v=>(v*100).toFixed(3)+'%')).join('');
  document.getElementById('rank-corr').innerHTML = sorted_corr.map((d,i)=>rankRow(i,d,d.corr,v=>v.toFixed(4))).join('');
}}

// ── INIT ──────────────────────────────────────────────────────────
window.addEventListener('resize', resizeScatter);
resizeScatter();
</script>
</body>
</html>"""