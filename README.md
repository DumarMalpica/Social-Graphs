# Rupestre AI — Red Cultural Boyacá

Dashboard interactivo para registrar y visualizar conexiones entre municipios de Boyacá a través de pictogramas precolombinos.

## Requisitos

- [Node.js 18+](https://nodejs.org/)
- [Python 3.8+](https://www.python.org/downloads/)

## Ejecutar

```bash
python run_realtime.py
```

Eso es todo. El script instala lo necesario, levanta el servidor y abre el navegador en `http://localhost:5000`.

Para detener: `Ctrl+C`

---

## Uso del dashboard

1. **Tab Imagen** — sube una foto de un pictograma y registra su sitio, tipo y estado de conservación.
2. **Tab Aportes** — selecciona un municipio y un pictograma para registrar un aporte.
   - Cuando **dos o más municipios** reportan el mismo pictograma, aparece una **conexión** entre ellos en el grafo.
   - Al seleccionar un pictograma se muestra qué municipios ya lo reportaron.
3. **Tab Matriz** — vista de adyacencia de las conexiones actuales.

En el grafo puedes hacer clic en cualquier nodo para ver sus métricas (PageRank, grado, población) y sus conexiones.

---

## Solución de problemas

| Problema | Solución |
|---|---|
| Puerto 5000 ocupado | Cambia `PORT` en `server/realtime_server.js` y `run_realtime.py` |
| `UnicodeEncodeError` en Windows | Ejecuta `$env:PYTHONIOENCODING='utf-8'; python run_realtime.py` |
| npm no encontrado | Instala Node.js y reinicia la terminal |
