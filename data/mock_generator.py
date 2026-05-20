import json
import random
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SEED = 42


MUNICIPIOS_BASE = [
    ("Tunja", 5.5353, -73.3678, 202000),
    ("Sogamoso", 5.7167, -72.9333, 114000),
    ("Chiquinquirá", 5.6167, -73.8167, 65000),
    ("Duitama", 5.8333, -73.0333, 115000),
    ("Paipa", 5.7833, -73.1167, 32000),
    ("Villa de Leyva", 5.6333, -73.5167, 18000),
    ("Moniquirá", 5.8833, -73.5667, 25000),
    ("Samacá", 5.4833, -73.4833, 16000),
    ("Ráquira", 5.5333, -73.6333, 13000),
    ("Nobsa", 5.7667, -72.9500, 17000),
    ("Tibasosa", 5.7500, -73.0000, 14000),
    ("Firavitoba", 5.6667, -72.9833, 9000),
    ("Aquitania", 5.5167, -72.8833, 11000),
    ("Tota", 5.5500, -72.9000, 6000),
    ("Gámeza", 5.8000, -72.7833, 5500),
    ("Tópaga", 5.7500, -72.8000, 5200),
    ("Mongua", 5.7167, -72.7167, 5800),
    ("Socha", 6.0333, -72.6833, 9500),
    ("Jericó", 5.9833, -72.5833, 7000),
    ("Belén", 6.0167, -72.9333, 8500),
]

SITIOS = [
    "Cerro de Monserrate Sogamoso",
    "Cuevas del Indio Ráquira",
    "Alto de los Molinos Tunja",
    "Abrigos de Iza y Firavitoba",
    "Piedra Pintada de Tibasosa",
    "Farallones de Gámeza",
    "Cerro de la Culebra Tópaga",
    "Abrigo del Lago de Tota",
    "Lajas de Aquitania",
    "Peñas del Morro en Mongua",
    "Cueva de la Salina en Socha",
    "Alto de la Cruz en Jericó",
    "Piedras de Belén",
    "Abrigos de Villa de Leyva",
    "Cerro del Cacique en Duitama",
]

TIPOS_PICTOGRAMA = ["zoomorfo", "antropomorfo", "geométrico", "solar", "abstracto"]
ESTADOS = ["bueno", "regular", "deteriorado"]
TIPOS_APORTE = ["imagen", "interpretacion", "georeferencia", "transcripcion"]


def _write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_mock_data(data_dir="data"):
    random.seed(SEED)
    np.random.seed(SEED)
    out = Path(data_dir)
    out.mkdir(parents=True, exist_ok=True)

    activos = set(random.sample([m[0] for m in MUNICIPIOS_BASE], 14))
    municipios = [
        {
            "nombre": nombre,
            "lat": lat,
            "lng": lng,
            "poblacion": pob,
            "activo": nombre in activos,
            "num_investigadores": random.randint(1, 15),
        }
        for nombre, lat, lng, pob in MUNICIPIOS_BASE
    ]

    pictogramas = [
        {
            "id": f"P-{i:03d}",
            "sitio": SITIOS[i - 1],
            "tipo": random.choice(TIPOS_PICTOGRAMA),
            "antiguedad_aprox": random.randint(500, 3000),
            "estado_conservacion": random.choice(ESTADOS),
        }
        for i in range(1, 16)
    ]

    start = date(2023, 1, 1)
    end = date(2025, 3, 1)
    days = (end - start).days
    target = random.randint(80, 100)
    pair_counts = defaultdict(int)
    interacciones = []

    while len(interacciones) < target:
        municipio = random.choice(municipios)["nombre"]
        pictograma = random.choice(pictogramas)["id"]
        if pair_counts[(municipio, pictograma)] >= 4:
            continue
        pair_counts[(municipio, pictograma)] += 1
        fecha = start + timedelta(days=random.randint(0, days))
        interacciones.append(
            {
                "municipio_nombre": municipio,
                "pictograma_id": pictograma,
                "tipo_aporte": random.choice(TIPOS_APORTE),
                "usuario_id": f"u_{random.randint(100, 999)}",
                "fecha": fecha.isoformat(),
                "confianza": round(random.uniform(0.1, 1.0), 2),
            }
        )

    _write_json(out / "municipios.json", municipios)
    _write_json(out / "pictogramas.json", pictogramas)
    _write_json(out / "interacciones.json", interacciones)

    dist = Counter(i["tipo_aporte"] for i in interacciones)
    print(f"[✓] Municipios generados: {len(municipios)}")
    print(f"[✓] Pictogramas generados: {len(pictogramas)}")
    print(f"[✓] Interacciones generadas: {len(interacciones)}")
    print(f"[✓] Distribución de tipos de aporte: {dict(dist)}")
    return {"municipios": municipios, "pictogramas": pictogramas, "interacciones": interacciones}


if __name__ == "__main__":
    try:
        generate_mock_data(Path(__file__).resolve().parent)
    except Exception as exc:
        print(f"[✗] Error en fase 1: {exc}")
