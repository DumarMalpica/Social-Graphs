# Rupestre AI

Rupestre AI es una fase inicial académica para la UPTC en Sogamoso, Colombia. El objetivo es modelar una red cultural sintética de municipios de Boyacá que aportan datos, imágenes e interpretaciones sobre pictogramas precolombinos, con énfasis en análisis social de conocimiento, reconstrucción digital y circulación de interpretaciones.

Todos los datos incluidos se generan sintéticamente desde código. No se usan datasets externos ni APIs de terceros.

## Flujo de módulos

```text
mock_generator → builder → metrics → stellargraph_embeddings
      ↓             ↓
  arangodb     ndlib_propagation
      ↓             ↓
cytoscape_export  sigma_export
      ↓             ↓
cytoscape.html    index.html
```

## Instalación

```bash
cd rupestre_ai
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "import igraph, numpy; print('Entorno verificado')"
```

StellarGraph 1.2.1 puede requerir Python 3.8 y TensorFlow 2.8-2.12. Si hay conflicto, el módulo de embeddings activa un fallback sintético con la misma interfaz.

## Ejecución en orden

```bash
python data/mock_generator.py
python graph/builder.py
python graph/metrics.py
python ml/stellargraph_embeddings.py
python db/arangodb_loader.py
python simulation/ndlib_propagation.py
python viz/cytoscape_export.py
python viz/sigma_export.py
```

Artefactos principales:

- `data/municipios.json`, `data/pictogramas.json`, `data/interacciones.json`
- `data/metrics.json`, `data/embeddings.json`
- `exports/red_rupestre.graphml`
- `exports/propagacion_comparativa.png`
- `dashboard/cytoscape.html`
- `dashboard/index.html`

## Herramientas y rol

- `igraph`: construcción de grafo bipartito, proyección municipal, GraphML y métricas SNA.
- `StellarGraph + TensorFlow`: entrenamiento GraphSAGE para embeddings de municipios; fallback sintético si el entorno no es compatible.
- `Cytoscape.js`: dashboard rápido autocontenido para exploración de nodos, aportes y pesos.
- `ArangoDB + python-arango`: persistencia documental y de aristas para consultas AQL.
- `NDlib`: simulación SIR e Independent Cascade; usa NetworkX solo como conversión interna requerida.
- `Sigma.js + Graphology`: presentación interactiva final con ranking y filtros.
- `GraphML`: export para SocNetV y análisis exploratorio externo.

## Datos sintéticos

- Municipios: 20 nodos con coordenadas aproximadas, población, actividad y número de investigadores.
- Pictogramas: 15 nodos con sitio rupestre verosímil, tipo, antigüedad aproximada y conservación.
- Interacciones: aportes entre municipios y pictogramas con usuario, fecha, confianza y tipo de aporte.

## Abrir GraphML en SocNetV

1. Ejecuta `python graph/builder.py`.
2. Abre SocNetV.
3. En la barra superior selecciona `File > Open`.
4. Busca `exports/red_rupestre.graphml`.
5. Selecciona el archivo y pulsa `Open`.
6. En la vista principal aparecerá la red de municipios; usa los paneles de SocNetV para layout, centralidades y componentes.

Captura textual esperada de la UI:

```text
SocNetV
File  Edit  View  Graph  Analyze
[canvas central con nodos municipales]
Status: 20 vertices, conexiones ponderadas cargadas desde GraphML
```

## Conectar ArangoDB real

Por defecto el loader intenta `localhost:8529`, usuario `root`, password `rupestre2024`, base `rupestre_db`.

Puedes sobreescribir credenciales:

```bash
set ARANGO_HOST=localhost
set ARANGO_USER=root
set ARANGO_PASSWORD=rupestre2024
python db/arangodb_loader.py
```

Si ArangoDB no responde en 3 segundos, el script activa modo dry-run y muestra las operaciones AQL que ejecutaría.
