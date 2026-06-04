import requests
import time
import subprocess
import json
import os

print("--- LIMPIANDO ESTADO ---")
json.dump([], open("data/interacciones.json", "w"))
d = json.load(open("dashboard/graph_data.json"))
d["edges"] = []
json.dump(d, open("dashboard/graph_data.json", "w"))

print("--- INICIANDO SERVIDOR ---")
proc = subprocess.Popen(["node", "server/realtime_server.js"], cwd=os.getcwd())
time.sleep(2)

try:
    print("--- PRUEBA 1: Chiquinquirá ---")
    r1 = requests.post("http://localhost:5000/api/aportes", json={
        "municipio_nombre": "Chiquinquirá",
        "pictograma_id": "P-006",
        "tipo_aporte": "imagen",
        "confianza": 0.8
    })
    print("Respuesta 1:", r1.json())
    
    time.sleep(1)
    g1 = requests.get("http://localhost:5000/api/graph").json()
    print("Aristas en grafo (esperado 0):", len(g1.get("edges", [])))
    for e in g1.get("edges", []):
        print(e)

    print("\n--- PRUEBA 2: Socha ---")
    r2 = requests.post("http://localhost:5000/api/aportes", json={
        "municipio_nombre": "Socha",
        "pictograma_id": "P-006",
        "tipo_aporte": "imagen",
        "confianza": 0.8
    })
    print("Respuesta 2:", r2.json())
    
    time.sleep(1)
    g2 = requests.get("http://localhost:5000/api/graph").json()
    print("Aristas en grafo (esperado 1):", len(g2.get("edges", [])))
    for e in g2.get("edges", []):
        print(e)
        
finally:
    proc.terminate()
    proc.wait()
    print("\n--- PRUEBA TERMINADA ---")
