import json
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "graph"))
from builder import build_graphs

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _key(value):
    return (
        value.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
        .replace(" ", "-")
    )


VALIDATION_QUERIES = [
    """FOR m IN municipios
  LET aportes = LENGTH(FOR e IN aporta_conocimiento
                         FILTER e._from == m._id RETURN e)
  SORT aportes DESC LIMIT 5
  RETURN { municipio: m.nombre, aportes: aportes }""",
    """FOR p IN pictogramas
  LET muns = LENGTH(FOR e IN aporta_conocimiento
                      FILTER e._to == p._id
                      RETURN DISTINCT e._from)
  SORT muns DESC LIMIT 5
  RETURN { pictograma: p.id, sitio: p.sitio, municipios: muns }""",
    """FOR v, e, path IN 1..2 ANY "municipios/sogamoso"
  comparte_pictograma
  RETURN DISTINCT { municipio: v.nombre, distancia: LENGTH(path.edges) }""",
]


def _ping(host, port=8529, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def load_arangodb(data_dir=None):
    data_dir = Path(data_dir or ROOT / "data")
    host = os.getenv("ARANGO_HOST", "localhost")
    user = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_PASSWORD", "rupestre2024")
    db_name = "rupestre_db"

    municipios = json.loads((data_dir / "municipios.json").read_text(encoding="utf-8"))
    pictogramas = json.loads((data_dir / "pictogramas.json").read_text(encoding="utf-8"))
    interacciones = json.loads((data_dir / "interacciones.json").read_text(encoding="utf-8"))
    _, g_municipios = build_graphs(data_dir)

    dry_run = not _ping(host)
    if dry_run:
        print("[!] ArangoDB no disponible — activando modo dry-run")
        print("AQL/operaciones que se ejecutarían:")
        print('CREATE COLLECTION municipios, pictogramas, aporta_conocimiento(edge), comparte_pictograma(edge)')
        for m in municipios[:3]:
            print(f"UPSERT {{ _key: '{_key(m['nombre'])}' }} INSERT {m} UPDATE {m} IN municipios")
        print(f"... {len(municipios)} municipios, {len(pictogramas)} pictogramas, {len(interacciones)} aportes")
        for q in VALIDATION_QUERIES:
            print("\n" + q)
        return {"dry_run": True}

    try:
        from arango import ArangoClient

        client = ArangoClient(hosts=f"http://{host}:8529")
        sys_db = client.db("_system", username=user, password=password)
        if not sys_db.has_database(db_name):
            sys_db.create_database(db_name)
        db = client.db(db_name, username=user, password=password)
        for name, edge in [("municipios", False), ("pictogramas", False), ("aporta_conocimiento", True), ("comparte_pictograma", True)]:
            if not db.has_collection(name):
                db.create_collection(name, edge=edge)

        municipios_col = db.collection("municipios")
        pictogramas_col = db.collection("pictogramas")
        aporta_col = db.collection("aporta_conocimiento")
        comparte_col = db.collection("comparte_pictograma")
        for m in municipios:
            doc = {**m, "_key": _key(m["nombre"])}
            municipios_col.insert(doc, overwrite=True)
        for p in pictogramas:
            doc = {**p, "_key": p["id"].lower()}
            pictogramas_col.insert(doc, overwrite=True)
        for idx, row in enumerate(interacciones):
            aporta_col.insert(
                {
                    "_key": f"aporte-{idx}",
                    "_from": f"municipios/{_key(row['municipio_nombre'])}",
                    "_to": f"pictogramas/{row['pictograma_id'].lower()}",
                    **row,
                },
                overwrite=True,
            )
        for idx, e in enumerate(g_municipios.es):
            a = g_municipios.vs[e.source]["nombre"]
            b = g_municipios.vs[e.target]["nombre"]
            comparte_col.insert({"_key": f"comp-{idx}", "_from": f"municipios/{_key(a)}", "_to": f"municipios/{_key(b)}", "peso": e["peso"]}, overwrite=True)
        for q in VALIDATION_QUERIES:
            print(list(db.aql.execute(q)))
        print("[✓] Carga ArangoDB completada")
        return {"dry_run": False}
    except Exception as exc:
        print(f"[✗] Error en fase 5: {exc}")
        return {"dry_run": True, "error": str(exc)}


if __name__ == "__main__":
    load_arangodb()
