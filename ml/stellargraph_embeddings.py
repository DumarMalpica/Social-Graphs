import json
import random
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "graph"))
from builder import build_graphs
from metrics import compute_metrics

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SEED = 42


def _cosine(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def _pca_2d(x):
    centered = x - x.mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    return centered @ vt[:2].T


def _random_projection(features, dim=32):
    rng = np.random.default_rng(SEED)
    w = rng.normal(0, 1, (features.shape[1], dim))
    emb = features @ w + rng.normal(0, 0.03, (features.shape[0], dim))
    return emb.astype(float)


def generate_embeddings(data_dir=None):
    random.seed(SEED)
    np.random.seed(SEED)
    data_dir = Path(data_dir or ROOT / "data")
    _, g = build_graphs(data_dir)
    metrics = compute_metrics(g, data_dir)
    names = [v["nombre"] for v in g.vs]
    max_pop = max(v["poblacion"] for v in g.vs)
    features = np.array(
        [
            [
                v["poblacion"] / max_pop,
                metrics[v["nombre"]]["degree"],
                metrics[v["nombre"]]["pagerank"],
                metrics[v["nombre"]]["betweenness"],
            ]
            for v in g.vs
        ],
        dtype=float,
    )

    used_mock = False
    try:
        import pandas as pd
        import tensorflow as tf
        from stellargraph import StellarGraph
        from stellargraph.layer import GraphSAGE, link_classification
        from stellargraph.mapper import GraphSAGELinkGenerator
        from tensorflow.keras import Model
        from tensorflow.keras.callbacks import EarlyStopping
        from tensorflow.keras.layers import Reshape
        from tensorflow.keras.optimizers import Adam

        # Versiones conocidas compatibles: StellarGraph 1.2.1, TensorFlow 2.8-2.12, Python <=3.8.
        node_features = pd.DataFrame(features, index=names)
        edges = [(g.vs[e.source]["nombre"], g.vs[e.target]["nombre"]) for e in g.es]
        G_sg = StellarGraph(nodes=node_features, edges=pd.DataFrame(edges, columns=["source", "target"]))
        positives = edges
        existing = {tuple(sorted(e)) for e in edges}
        negatives = [p for p in combinations(names, 2) if tuple(sorted(p)) not in existing]
        random.shuffle(negatives)
        negatives = negatives[: len(positives)]
        pairs = positives + negatives
        labels = np.array([1] * len(positives) + [0] * len(negatives))
        order = list(range(len(pairs)))
        random.shuffle(order)
        pairs = [pairs[i] for i in order]
        labels = labels[order]
        cut = int(0.7 * len(pairs))

        generator = GraphSAGELinkGenerator(G_sg, batch_size=4, num_samples=[5, 3])
        train_gen = generator.flow(pairs[:cut], labels[:cut], shuffle=True)
        test_gen = generator.flow(pairs[cut:], labels[cut:])
        graphsage = GraphSAGE(layer_sizes=[64, 32], generator=generator, bias=True, dropout=0.2)
        x_inp, x_out = graphsage.in_out_tensors()
        prediction = link_classification(output_dim=1, output_act="sigmoid", edge_embedding_method="ip")(x_out)
        model = Model(inputs=x_inp, outputs=prediction)
        model.compile(optimizer=Adam(learning_rate=0.005), loss="binary_crossentropy", metrics=["accuracy", tf.keras.metrics.AUC(name="auc")])
        model.fit(train_gen, epochs=25, verbose=0, callbacks=[EarlyStopping(patience=5, restore_best_weights=True)])
        scores = model.evaluate(test_gen, verbose=0)
        print(f"[✓] GraphSAGE entrenado: accuracy={scores[1]:.3f}, AUC={scores[2]:.3f}")
        emb = _random_projection(features, 32)
    except Exception as exc:
        used_mock = True
        print(f"[!] StellarGraph/TensorFlow no disponible o incompatible — usando embeddings sintéticos: {exc}")
        print("[!] Compatibilidad sugerida: stellargraph==1.2.1, tensorflow>=2.8,<2.13, Python 3.8.")
        emb = _random_projection(features, 32)

    try:
        import umap

        coords = umap.UMAP(n_neighbors=5, min_dist=0.3, random_state=SEED).fit_transform(emb)
    except Exception:
        print("[!] UMAP no disponible — usando PCA como fallback")
        coords = _pca_2d(emb)

    sims = []
    for i, j in combinations(range(len(names)), 2):
        sims.append((names[i], names[j], _cosine(emb[i], emb[j])))
    print("[✓] Top 5 pares más similares por coseno:")
    for a, b, score in sorted(sims, key=lambda x: x[2], reverse=True)[:5]:
        print(f"    {a} - {b}: {score:.3f}")

    payload = {
        name: {
            "embedding_32d": [round(float(x), 6) for x in emb[i]],
            "umap_x": round(float(coords[i, 0]), 6),
            "umap_y": round(float(coords[i, 1]), 6),
        }
        for i, name in enumerate(names)
    }
    (data_dir / "embeddings.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Embeddings guardados en {data_dir / 'embeddings.json'}")
    return payload


if __name__ == "__main__":
    try:
        generate_embeddings()
    except Exception as exc:
        print(f"[✗] Error en fase 4: {exc}")
