import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "graph"))
from builder import build_graphs
from metrics import compute_metrics

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#" + "".join(f"{int(v):02X}" for v in rgb)


def _lerp_color(a, b, t):
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return _rgb_to_hex((ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t))


def export_sigma(data_dir=None):
    data_dir = Path(data_dir or ROOT / "data")
    dashboard = ROOT / "dashboard"
    dashboard.mkdir(exist_ok=True)
    _, g = build_graphs(data_dir)
    metrics = compute_metrics(g, data_dir)
    lats = [v["lat"] for v in g.vs]
    lngs = [v["lng"] for v in g.vs]
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    prs = [metrics[v["nombre"]]["pagerank"] for v in g.vs]
    min_pr, max_pr = min(prs), max(prs)

    nodes = []
    for v in g.vs:
        name = v["nombre"]
        pr = metrics[name]["pagerank"]
        t = (pr - min_pr) / ((max_pr - min_pr) or 1)
        nodes.append(
            {
                "key": name,
                "attributes": {
                    "label": name,
                    "x": (v["lng"] - min_lng) / ((max_lng - min_lng) or 1) * 1000,
                    "y": (v["lat"] - min_lat) / ((max_lat - min_lat) or 1) * 1000,
                    "size": t * 20 + 5,
                    "color": _lerp_color("#E1F5EE", "#085041", t),
                    "pagerank": pr,
                    "betweenness": metrics[name]["betweenness"],
                    "grado": int(round(metrics[name]["degree"] * (g.vcount() - 1))),
                    "poblacion": v["poblacion"],
                },
            }
        )
    edges = []
    for i, e in enumerate(g.es):
        a = g.vs[e.source]["nombre"]
        b = g.vs[e.target]["nombre"]
        edges.append({"key": f"e_{i}_{a.lower()}_{b.lower()}".replace(" ", "_"), "source": a, "target": b, "attributes": {"weight": e["peso"], "size": max(1, e["peso"] / 2)}})
    data = {"attributes": {"name": "Red cultural Boyacá - Rupestre AI"}, "nodes": nodes, "edges": edges}
    (dashboard / "graph_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (dashboard / "index.html").write_text(HTML_TEMPLATE.replace("__GRAPH_DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
    print(f"[✓] Dashboard Sigma generado en {dashboard / 'index.html'}")
    return data


HTML_TEMPLATE = r'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Rupestre AI - Sigma</title>
  <script src="https://cdn.jsdelivr.net/npm/graphology@0.25.4/dist/graphology.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/graphology-layout-forceatlas2@0.10.1/build/graphology-layout-forceatlas2.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/sigma@2.4.0/build/sigma.min.js"></script>
  <style>
    :root { --ink:#1f2421; --line:#d8ded8; --bg:#f4f8f5; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Arial, sans-serif; color:var(--ink); background:var(--bg); }
    main { display:grid; grid-template-columns: 1fr 340px; height:100vh; }
    #container { position:relative; background:#fbfdfb; }
    #sigma { width:100%; height:100%; }
    aside { border-left:1px solid var(--line); padding:18px; overflow:auto; }
    h1 { margin:0 0 16px; font-size:24px; }
    .bar { margin:9px 0; }
    .bar span { display:flex; justify-content:space-between; font-size:12px; }
    .bar i { display:block; height:9px; background:#1D9E75; width:0; transition:width .8s ease; }
    #tooltip { position:absolute; display:none; pointer-events:none; background:white; border:1px solid var(--line); padding:8px; font-size:12px; box-shadow:0 8px 24px rgba(0,0,0,.12); }
    .legend { height:12px; background:linear-gradient(90deg,#E1F5EE,#085041); margin-top:8px; }
  </style>
</head>
<body>
<main>
  <div id="container"><div id="sigma"></div><div id="tooltip"></div></div>
  <aside>
    <h1>Rupestre AI</h1>
    <h3>Top 10 ranking</h3>
    <div id="ranking"></div>
    <label>Umbral de peso: <strong id="thresholdValue">1</strong></label>
    <input id="threshold" type="range" min="1" max="10" value="1" />
    <h3>Leyenda color</h3>
    <div class="legend"></div>
    <p>bajo → alto PageRank</p>
  </aside>
</main>
<script>
const GRAPH_DATA = __GRAPH_DATA__;
const graph = new graphology.Graph();
GRAPH_DATA.nodes.forEach(n => graph.addNode(n.key, n.attributes));
GRAPH_DATA.edges.forEach(e => graph.addEdgeWithKey(e.key, e.source, e.target, e.attributes));
const fa2 = window.graphologyLayoutForceAtlas2 || (window.graphologyLibrary && window.graphologyLibrary.layoutForceAtlas2);
if (fa2 && fa2.assign) fa2.assign(graph, { iterations:50, settings:{ gravity:0.05, scalingRatio:8 } });
const renderer = new Sigma(graph, document.getElementById('sigma'));
const tooltip = document.getElementById('tooltip');
renderer.on('enterNode', ({node, event}) => {
  const a = graph.getNodeAttributes(node);
  tooltip.style.display='block'; tooltip.style.left=event.x + 12 + 'px'; tooltip.style.top=event.y + 12 + 'px';
  tooltip.innerHTML = `<strong>${a.label}</strong><br>PageRank: ${a.pagerank.toFixed(4)}<br>Betweenness: ${a.betweenness.toFixed(4)}`;
});
renderer.on('leaveNode', () => tooltip.style.display='none');
let selected = null, threshold = 1;
renderer.on('clickNode', ({node}) => { selected = selected === node ? null : node; renderer.refresh(); });
function reducers() {
  renderer.setSetting('nodeReducer', (node, data) => {
    const res = {...data}; if (selected && node !== selected && !graph.areNeighbors(node, selected)) { res.color='#d8d8d8'; res.label=''; res.size=data.size*0.7; } return res;
  });
  renderer.setSetting('edgeReducer', (edge, data) => {
    const res = {...data}; if (data.weight < threshold) res.hidden = true;
    if (selected) { const ex=graph.extremities(edge); if (!ex.includes(selected)) res.hidden = true; } return res;
  });
}
reducers();
document.getElementById('threshold').addEventListener('input', e => { threshold=Number(e.target.value); document.getElementById('thresholdValue').textContent=threshold; reducers(); renderer.refresh(); });
const ranked = GRAPH_DATA.nodes.slice().sort((a,b)=>b.attributes.pagerank-a.attributes.pagerank).slice(0,10);
const max = ranked[0].attributes.pagerank;
document.getElementById('ranking').innerHTML = ranked.map(n => `<div class="bar"><span><b>${n.key}</b><em>${n.attributes.pagerank.toFixed(4)}</em></span><i style="width:${(n.attributes.pagerank/max)*100}%"></i></div>`).join('');
</script>
</body>
</html>'''


if __name__ == "__main__":
    try:
        export_sigma()
    except Exception as exc:
        print(f"[✗] Error en fase 8: {exc}")
