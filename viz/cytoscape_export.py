import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "graph"))
from builder import build_graphs
from metrics import compute_metrics

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COLORS = {
    "Tunja": "#534AB7",
    "Sogamoso": "#1D9E75",
    "Chiquinquirá": "#D85A30",
    "Duitama": "#BA7517",
}


def export_cytoscape(data_dir=None):
    data_dir = Path(data_dir or ROOT / "data")
    dashboard = ROOT / "dashboard"
    dashboard.mkdir(exist_ok=True)
    _, g = build_graphs(data_dir)
    metrics = compute_metrics(g, data_dir)
    interacciones = json.loads((data_dir / "interacciones.json").read_text(encoding="utf-8"))

    top_pics = defaultdict(list)
    grouped = defaultdict(Counter)
    for row in interacciones:
        grouped[row["municipio_nombre"]][row["pictograma_id"]] += 1
    for municipio, counter in grouped.items():
        top_pics[municipio] = [p for p, _ in counter.most_common(3)]

    max_pr = max(v["pagerank"] for v in metrics.values())
    nodes = []
    for v in g.vs:
        name = v["nombre"]
        pr = metrics[name]["pagerank"]
        nodes.append(
            {
                "data": {
                    "id": name,
                    "label": name,
                    "pagerank": pr,
                    "betweenness": metrics[name]["betweenness"],
                    "grado": int(round(metrics[name]["degree"] * (g.vcount() - 1))),
                    "poblacion": v["poblacion"],
                    "color": COLORS.get(name, "#888780"),
                    "size": 20 + (pr / max_pr) * 60,
                    "top_pictogramas": top_pics.get(name, []),
                }
            }
        )
    edges = [
        {"data": {"source": g.vs[e.source]["nombre"], "target": g.vs[e.target]["nombre"], "peso": e["peso"]}}
        for e in g.es
    ]
    graph_data = {"nodes": nodes, "edges": edges}
    html = HTML_TEMPLATE.replace("__GRAPH_DATA__", json.dumps(graph_data, ensure_ascii=False))
    out = dashboard / "cytoscape.html"
    out.write_text(html, encoding="utf-8")
    print(f"[✓] Dashboard Cytoscape generado en {out}")
    return graph_data


HTML_TEMPLATE = r'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Rupestre AI - Cytoscape</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
  <style>
    :root { --ink:#20201d; --muted:#6b6a64; --line:#d9d6cc; --bg:#f6f4ee; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Arial, sans-serif; color:var(--ink); background:var(--bg); }
    main { display:flex; height:100vh; width:100vw; }
    #cy { width:70%; height:100%; border-right:1px solid var(--line); background:#fbfaf6; }
    aside { width:30%; min-width:320px; padding:18px; overflow:auto; }
    h1 { margin:0 0 14px; font-size:24px; }
    label { display:block; margin:14px 0 6px; color:var(--muted); font-size:13px; }
    input[type="search"], input[type="range"] { width:100%; }
    button { border:1px solid var(--line); background:white; padding:9px 11px; margin:10px 8px 0 0; cursor:pointer; }
    #panel { margin-top:18px; line-height:1.55; }
    .metric { display:flex; justify-content:space-between; border-bottom:1px solid var(--line); padding:6px 0; }
  </style>
</head>
<body>
<main>
  <div id="cy"></div>
  <aside>
    <h1>Rupestre AI</h1>
    <label for="search">Buscar municipio</label>
    <input id="search" type="search" placeholder="Sogamoso" />
    <label for="threshold">Umbral de peso: <span id="thresholdValue">1</span></label>
    <input id="threshold" type="range" min="1" max="10" value="1" />
    <button id="reset">Reset layout</button>
    <button id="png">Exportar PNG</button>
    <div id="panel">Selecciona un municipio.</div>
  </aside>
</main>
<script>
const GRAPH_DATA = __GRAPH_DATA__;
const maxPr = Math.max(...GRAPH_DATA.nodes.map(n => n.data.pagerank));
const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: GRAPH_DATA.nodes.concat(GRAPH_DATA.edges),
  style: [
    { selector:'node', style:{ 'label':'data(label)', 'background-color':'data(color)', 'width':'mapData(pagerank, 0, ' + maxPr + ', 20, 80)', 'height':'mapData(pagerank, 0, ' + maxPr + ', 20, 80)', 'font-size':12, 'text-valign':'center', 'text-halign':'center', 'color':'#20201d', 'text-outline-width':2, 'text-outline-color':'#fbfaf6' } },
    { selector:'edge', style:{ 'width':'mapData(peso, 1, 10, 1, 8)', 'line-color':'#b9b5aa', 'curve-style':'bezier' } },
    { selector:'.faded', style:{ 'opacity':0.12 } },
    { selector:'.found', style:{ 'border-width':5, 'border-color':'#111' } }
  ],
  layout:{ name:'cose', randomize:false, nodeRepulsion:8000 }
});
function showNode(n) {
  const d = n.data();
  document.getElementById('panel').innerHTML = `<h2>${d.label}</h2>
    <div class="metric"><span>PageRank</span><strong>${d.pagerank.toFixed(4)}</strong></div>
    <div class="metric"><span>Betweenness</span><strong>${d.betweenness.toFixed(4)}</strong></div>
    <div class="metric"><span>Grado</span><strong>${d.grado}</strong></div>
    <div class="metric"><span>Población</span><strong>${d.poblacion.toLocaleString('es-CO')}</strong></div>
    <h3>Top pictogramas</h3><p>${(d.top_pictogramas || []).join(', ') || 'Sin aportes'}</p>`;
}
cy.on('tap', 'node', evt => showNode(evt.target));
document.getElementById('search').addEventListener('input', e => {
  const q = e.target.value.toLowerCase(); cy.elements().removeClass('found faded');
  if (!q) return; const found = cy.nodes().filter(n => n.data('label').toLowerCase().includes(q));
  cy.nodes().not(found).addClass('faded'); found.addClass('found'); if (found.length) cy.animate({ fit:{ eles:found, padding:80 }, duration:350 });
});
document.getElementById('threshold').addEventListener('input', e => {
  const value = Number(e.target.value); document.getElementById('thresholdValue').textContent = value;
  cy.edges().forEach(edge => edge.style('display', edge.data('peso') < value ? 'none' : 'element'));
});
document.getElementById('reset').onclick = () => cy.layout({ name:'cose', randomize:false, nodeRepulsion:8000 }).run();
document.getElementById('png').onclick = () => { const a=document.createElement('a'); a.href=cy.png({ full:true, scale:2 }); a.download='red_rupestre.png'; a.click(); };
</script>
</body>
</html>'''


if __name__ == "__main__":
    try:
        export_cytoscape()
    except Exception as exc:
        print(f"[✗] Error en fase 7: {exc}")
