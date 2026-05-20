import json
import random
import sys
from pathlib import Path

import numpy as np

try:
    import igraph as ig
except Exception:
    ig = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from builder import build_graphs
except Exception:
    from graph.builder import build_graphs


SEED = 42


def _adjacency(g):
    n = g.vcount()
    adj = {i: set() for i in range(n)}
    weights = {}
    for e in g.es:
        adj[e.source].add(e.target)
        adj[e.target].add(e.source)
        weights[tuple(sorted((e.source, e.target)))] = e["peso"]
    return adj, weights


def _fallback_metrics(g):
    adj, _ = _adjacency(g)
    n = g.vcount()
    deg = [len(adj[i]) / max(n - 1, 1) for i in range(n)]
    pr = np.array([1 / n] * n, dtype=float)
    for _ in range(80):
        nxt = np.array([(1 - 0.85) / n] * n, dtype=float)
        for i in range(n):
            if adj[i]:
                share = pr[i] / len(adj[i])
                for j in adj[i]:
                    nxt[j] += 0.85 * share
        pr = nxt
    closeness = []
    for s in range(n):
        dist = {s: 0}
        q = [s]
        for u in q:
            for v in adj[u]:
                if v not in dist:
                    dist[v] = dist[u] + 1
                    q.append(v)
        closeness.append((len(dist) - 1) / sum(dist.values()) if sum(dist.values()) else 0)
    clustering = []
    for i in range(n):
        neigh = list(adj[i])
        if len(neigh) < 2:
            clustering.append(0)
            continue
        links = sum(1 for a in range(len(neigh)) for b in range(a + 1, len(neigh)) if neigh[b] in adj[neigh[a]])
        clustering.append(links / (len(neigh) * (len(neigh) - 1) / 2))
    eig = np.array(deg) / (max(deg) or 1)
    return deg, [0.0] * n, closeness, pr.tolist(), clustering, eig.tolist()


def compute_metrics(g_municipios, data_dir=None):
    random.seed(SEED)
    np.random.seed(SEED)
    if data_dir is None:
        data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir = Path(data_dir)

    n = g_municipios.vcount()
    if ig and g_municipios.__class__.__module__.startswith("igraph"):
        degree = [d / max(n - 1, 1) for d in g_municipios.degree()]
        betweenness = g_municipios.betweenness(directed=False, weights=None, normalized=True)
        closeness = g_municipios.closeness(mode="all", normalized=True)
        pagerank = g_municipios.pagerank(weights="peso", damping=0.85)
        clustering = [0.0 if x != x else x for x in g_municipios.transitivity_local_undirected(mode="zero")]
        eigenvector = g_municipios.eigenvector_centrality(directed=False, weights="peso")
    else:
        degree, betweenness, closeness, pagerank, clustering, eigenvector = _fallback_metrics(g_municipios)

    metrics = {}
    for i, v in enumerate(g_municipios.vs):
        name = v["nombre"]
        metrics[name] = {
            "degree": round(float(degree[i]), 6),
            "betweenness": round(float(betweenness[i]), 6),
            "closeness": round(float(closeness[i]), 6),
            "pagerank": round(float(pagerank[i]), 6),
            "clustering": round(float(clustering[i]), 6),
            "eigenvector": round(float(eigenvector[i]), 6),
        }

    (data_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Municipio        PageRank  Betweenness  Grado  Clustering")
    for name, vals in sorted(metrics.items(), key=lambda kv: kv[1]["pagerank"], reverse=True)[:5]:
        grado = int(round(vals["degree"] * (n - 1)))
        print(f"{name:<16} {vals['pagerank']:<8.4f} {vals['betweenness']:<11.3f} {grado:<5} {vals['clustering']:<.2f}")
    print(f"[✓] Métricas SNA guardadas en {data_dir / 'metrics.json'}")
    return metrics


if __name__ == "__main__":
    try:
        _, g = build_graphs(Path(__file__).resolve().parents[1] / "data")
        compute_metrics(g)
    except Exception as exc:
        print(f"[✗] Error en fase 3: {exc}")
