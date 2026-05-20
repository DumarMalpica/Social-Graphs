import json
import math
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

try:
    import igraph as ig
except Exception:
    ig = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class SimpleVertex:
    def __init__(self, attrs):
        self.attrs = attrs

    def __getitem__(self, key):
        return self.attrs[key]

    def __setitem__(self, key, value):
        self.attrs[key] = value

    def attribute_names(self):
        return list(self.attrs.keys())


class SimpleEdge:
    def __init__(self, source, target, attrs):
        self.source = source
        self.target = target
        self.attrs = attrs

    def __getitem__(self, key):
        return self.attrs[key]

    def __setitem__(self, key, value):
        self.attrs[key] = value


class SimpleGraph:
    def __init__(self, directed=False):
        self.directed = directed
        self.vs = []
        self.es = []

    def add_vertex(self, **attrs):
        self.vs.append(SimpleVertex(attrs))

    def add_edge(self, source, target, **attrs):
        self.es.append(SimpleEdge(source, target, attrs))

    def vcount(self):
        return len(self.vs)

    def ecount(self):
        return len(self.es)

    def density(self):
        n = self.vcount()
        return 0 if n < 2 else (2 * self.ecount()) / (n * (n - 1))

    def components(self):
        parent = list(range(self.vcount()))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for e in self.es:
            union(e.source, e.target)
        return {find(i) for i in range(self.vcount())}

    def write_graphml(self, path):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">']
        lines.append(f'<graph edgedefault="{"directed" if self.directed else "undirected"}">')
        for idx, v in enumerate(self.vs):
            label = str(v.attrs.get("nombre", v.attrs.get("name", idx)))
            lines.append(f'<node id="{idx}"><data key="label">{_xml(label)}</data></node>')
        for idx, e in enumerate(self.es):
            lines.append(f'<edge id="e{idx}" source="{e.source}" target="{e.target}"><data key="peso">{e.attrs.get("peso", 1)}</data></edge>')
        lines.extend(["</graph>", "</graphml>"])
        Path(path).write_text("\n".join(lines), encoding="utf-8")


def _xml(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _load(data_dir):
    base = Path(data_dir)
    return (
        json.loads((base / "municipios.json").read_text(encoding="utf-8")),
        json.loads((base / "pictogramas.json").read_text(encoding="utf-8")),
        json.loads((base / "interacciones.json").read_text(encoding="utf-8")),
    )


def _make_graph(directed=False):
    return ig.Graph(directed=directed) if ig else SimpleGraph(directed=directed)


def _add_vertices(g, attrs):
    if ig:
        g.add_vertices(len(attrs))
        for i, row in enumerate(attrs):
            for key, value in row.items():
                g.vs[i][key] = value
    else:
        for row in attrs:
            g.add_vertex(**row)


def _add_edges(g, edge_tuples, attrs):
    if ig:
        g.add_edges(edge_tuples)
        for key in attrs[0].keys() if attrs else []:
            g.es[key] = [a[key] for a in attrs]
    else:
        for (s, t), attr in zip(edge_tuples, attrs):
            g.add_edge(s, t, **attr)


def build_graphs(data_dir="data/"):
    municipios, pictogramas, interacciones = _load(data_dir)
    exports = Path(data_dir).resolve().parent / "exports"
    exports.mkdir(parents=True, exist_ok=True)

    vertex_attrs = []
    for m in municipios:
        vertex_attrs.append({**m, "name": m["nombre"], "tipo": "municipio"})
    for p in pictogramas:
        vertex_attrs.append({**p, "name": p["id"], "tipo": "pictograma"})

    g_bipartite = _make_graph(directed=True)
    _add_vertices(g_bipartite, vertex_attrs)
    idx = {v["name"]: i for i, v in enumerate(g_bipartite.vs)}

    grouped = defaultdict(list)
    for row in interacciones:
        grouped[(row["municipio_nombre"], row["pictograma_id"])].append(row)

    edge_tuples, edge_attrs = [], []
    for (mun, pic), rows in sorted(grouped.items()):
        edge_tuples.append((idx[mun], idx[pic]))
        edge_attrs.append(
            {
                "peso": len(rows),
                "confianza_promedio": round(sum(r["confianza"] for r in rows) / len(rows), 4),
                "tipos_aporte": ",".join(sorted({r["tipo_aporte"] for r in rows})),
            }
        )
    _add_edges(g_bipartite, edge_tuples, edge_attrs)

    muni_attrs = [{**m, "name": m["nombre"]} for m in municipios]
    g_municipios = _make_graph(directed=False)
    _add_vertices(g_municipios, muni_attrs)
    muni_idx = {m["nombre"]: i for i, m in enumerate(municipios)}

    by_pic = defaultdict(set)
    for row in interacciones:
        by_pic[row["pictograma_id"]].add(row["municipio_nombre"])
    pair_weights = defaultdict(int)
    for muns in by_pic.values():
        for a, b in combinations(sorted(muns), 2):
            pair_weights[(a, b)] += 1

    m_edges = [(muni_idx[a], muni_idx[b]) for (a, b) in pair_weights]
    m_attrs = [{"peso": w} for w in pair_weights.values()]
    _add_edges(g_municipios, m_edges, m_attrs)

    g_bipartite.write_graphml(str(exports / "bipartite.graphml"))
    g_municipios.write_graphml(str(exports / "red_rupestre.graphml"))
    comps = len(g_municipios.components()) if not ig else len(g_municipios.components())
    print(f"[✓] Grafo bipartito construido: {g_bipartite.vcount()} nodos, {g_bipartite.ecount()} aristas")
    print(
        f"[✓] Red municipal construida: {g_municipios.vcount()} nodos, {g_municipios.ecount()} aristas, "
        f"densidad={g_municipios.density():.3f}, componentes={comps}"
    )
    return g_bipartite, g_municipios


if __name__ == "__main__":
    try:
        build_graphs(Path(__file__).resolve().parents[1] / "data")
    except Exception as exc:
        print(f"[✗] Error en fase 2: {exc}")
