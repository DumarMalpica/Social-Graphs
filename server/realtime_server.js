import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT      = path.join(__dirname, '..');

const app    = express();
const server = createServer(app);
const io     = new Server(server, { cors: { origin:'*', methods:['GET','POST'] } });
const PORT   = process.env.PORT || 5000;

// ─── File paths ──────────────────────────────────────────────────────────
const PATHS = {
  graphData:    path.join(ROOT, 'dashboard', 'graph_data.json'),
  municipios:   path.join(ROOT, 'data', 'municipios.json'),
  pictogramas:  path.join(ROOT, 'data', 'pictogramas.json'),
  interacciones:path.join(ROOT, 'data', 'interacciones.json'),
  uploads:      path.join(ROOT, 'data', 'uploads'),
};

// ─── Ensure uploads directory exists ────────────────────────────────────
if (!fs.existsSync(PATHS.uploads)) fs.mkdirSync(PATHS.uploads, { recursive:true });

// ─── In-memory state ─────────────────────────────────────────────────────
let graphState = { nodes:[], edges:[], events:[] };

function readJSON(filePath, fallback=[]) {
  try {
    if (fs.existsSync(filePath)) return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch(e) { console.warn(`⚠ Could not read ${path.basename(filePath)}:`, e.message); }
  return fallback;
}

function writeJSON(filePath, data) {
  try { fs.writeFileSync(filePath, JSON.stringify(data, null, 2)); }
  catch(e) { console.warn(`⚠ Could not write ${path.basename(filePath)}:`, e.message); }
}

function loadGraphState() {
  try {
    const raw = readJSON(PATHS.graphData, { nodes:[], edges:[] });
    graphState.nodes = raw.nodes || [];
    graphState.edges = raw.edges || [];
  } catch(e) { /* use empty state */ }
}

loadGraphState();

// ─── Middleware ───────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json({ limit:'12mb' }));

// Serve the new SPA as default, then other static dashboard files
app.use('/', express.static(path.join(ROOT, 'dashboard', 'spa')));
app.use('/', express.static(path.join(ROOT, 'dashboard')));

// ─── Root → SPA ────────────────────────────────────────────────────────
app.get('/', (_req, res) => {
  res.sendFile(path.join(ROOT, 'dashboard', 'spa', 'index.html'));
});

// ─── API: graph ──────────────────────────────────────────────────────────
app.get('/api/graph', (_req, res) => {
  res.json({ nodes: graphState.nodes, edges: graphState.edges });
});

// ─── API: municipios ─────────────────────────────────────────────────────
app.get('/api/municipios', (_req, res) => {
  const data = readJSON(PATHS.municipios, []);
  res.json(data);
});

// ─── API: pictogramas ────────────────────────────────────────────────────
app.get('/api/pictogramas', (_req, res) => {
  const data = readJSON(PATHS.pictogramas, []);
  res.json(data);
});

// ─── API: aportes — list ─────────────────────────────────────────────────
app.get('/api/aportes', (_req, res) => {
  const data = readJSON(PATHS.interacciones, []);
  res.json(data);
});

// ─── API: aportes — add ──────────────────────────────────────────────────
app.post('/api/aportes', (req, res) => {
  const { municipio_nombre, pictograma_id, tipo_aporte, confianza } = req.body;

  if (!municipio_nombre || !pictograma_id) {
    return res.status(400).json({ error:'municipio_nombre and pictograma_id are required' });
  }

  const newAporte = {
    municipio_nombre,
    pictograma_id,
    tipo_aporte:  tipo_aporte || 'imagen',
    confianza:    parseFloat(confianza) || 0.8,
    fecha:        new Date().toISOString().split('T')[0],
    usuario_id:   'u_' + Date.now().toString(36),
  };

  // Persist to interacciones.json
  const interacciones = readJSON(PATHS.interacciones, []);
  interacciones.push(newAporte);
  writeJSON(PATHS.interacciones, interacciones);

  // Compute new graph connections (municipal projection logic)
  // Two municipalities are connected when they share a pictograma
  const connections = [];
  const siblingsSet = new Set(
    interacciones
      .filter(a => a.pictograma_id === pictograma_id && a.municipio_nombre !== municipio_nombre)
      .map(a => a.municipio_nombre)
  );

  siblingsSet.forEach(other => {
    const key = [municipio_nombre, other].sort().join('||');

    // Find existing edge in graphState (handles both Graphology and WS-added formats)
    const existing = graphState.edges.find(e => {
      const s = e.data?.source || e.source;
      const t = e.data?.target || e.target;
      return s && t && [s, t].sort().join('||') === key;
    });

    if (existing) {
      const d    = existing.data || existing;
      const attr = existing.attributes || {};
      const peso = (d.peso || d.weight || attr.weight || 1) + 1;
      if (existing.data) existing.data.peso = peso;
      else if (existing.attributes) existing.attributes.weight = peso;
      else existing.peso = peso;
      connections.push({ source: municipio_nombre, target: other, peso });
    } else {
      const newEdge = { data:{ source: municipio_nombre, target: other, peso: 1 } };
      graphState.edges.push(newEdge);
      connections.push({ source: municipio_nombre, target: other, peso: 1 });
    }
  });

  // Broadcast new connections via WebSocket
  connections.forEach(conn => {
    io.emit('connection_created', { ...conn, timestamp: new Date().toISOString() });
  });

  // Broadcast the raw event too
  io.emit('event', {
    id:        Date.now(),
    type:      tipo_aporte,
    municipio_a: municipio_nombre,
    pictograma:  pictograma_id,
    timestamp: new Date().toISOString(),
  });

  res.json({ success:true, aporte: newAporte, connections });
});

// ─── API: aportes — save (trigger Python rebuild optionally) ─────────────
app.post('/api/aportes/save', (_req, res) => {
  // The data is already saved on each POST /api/aportes.
  // This endpoint is a hook for future pipeline triggers.
  res.json({ success:true, message:'Data persisted to interacciones.json' });
});

// ─── API: image upload ───────────────────────────────────────────────────
app.post('/api/upload', (req, res) => {
  const { image_base64, filename, sitio, tipo, estado } = req.body;

  if (!image_base64) return res.status(400).json({ error:'image_base64 is required' });

  // Strip data-URL header → raw base64
  const base64Data = image_base64.replace(/^data:image\/\w+;base64,/, '');
  const ext        = (filename || 'image.png').split('.').pop().toLowerCase() || 'png';
  const safeId     = `P-${Date.now().toString(36).toUpperCase()}`;
  const outFile    = path.join(PATHS.uploads, `${safeId}.${ext}`);

  try {
    fs.writeFileSync(outFile, Buffer.from(base64Data, 'base64'));

    // Optionally append to pictogramas.json
    if (sitio) {
      const pics = readJSON(PATHS.pictogramas, []);
      pics.push({ id:safeId, sitio, tipo:tipo||'geométrico', estado_conservacion:estado||'bueno',
                  antiguedad_aprox: 0, file: `${safeId}.${ext}` });
      writeJSON(PATHS.pictogramas, pics);
    }

    res.json({ success:true, id:safeId, file:`${safeId}.${ext}` });
  } catch(e) {
    console.error('Upload error:', e.message);
    res.status(500).json({ error:'Could not save image', detail: e.message });
  }
});

// ─── API: events (last 50) ───────────────────────────────────────────────
app.get('/api/events', (_req, res) => {
  res.json({ events: graphState.events.slice(-50) });
});

// ─── WebSocket ───────────────────────────────────────────────────────────
io.on('connection', socket => {
  console.log('✓ Client connected:', socket.id);

  // Send current state to new client
  socket.emit('init', {
    nodes:  graphState.nodes,
    edges:  graphState.edges,
    events: graphState.events.slice(-20),
  });

  socket.on('new_event', data => {
    if (!data?.type) return;
    const event = { id:Date.now(), timestamp:new Date().toISOString(), ...data };
    graphState.events.push(event);
    if (graphState.events.length > 100) graphState.events.shift();
    io.emit('event', event);
  });

  socket.on('add_connection', data => {
    if (!data?.source || !data?.target) return;
    const { source, target, weight=1, type='opinion' } = data;

    const key      = [source, target].sort().join('||');
    const existing = graphState.edges.find(e => {
      const s = e.data?.source || e.source;
      const t = e.data?.target || e.target;
      return s && t && [s,t].sort().join('||') === key;
    });

    let peso;
    if (existing) {
      const d = existing.data || existing;
      peso    = (d.peso || d.weight || 1) + weight;
      if (existing.data) existing.data.peso = peso;
      else existing.peso = peso;
    } else {
      peso = weight;
      graphState.edges.push({ data:{ source, target, peso:weight, type, created:new Date().toISOString() } });
    }

    io.emit('connection_created', { source, target, peso, timestamp:new Date().toISOString() });
  });

  socket.on('clear_graph', () => {
    graphState.edges = [];
    io.emit('graph_cleared', { timestamp:new Date().toISOString() });
  });

  socket.on('disconnect', () => console.log('✗ Client disconnected:', socket.id));
  socket.on('error', err  => console.error('Socket error:', err));
});

// ─── Start ────────────────────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════╗
║     Pictograma — Rupestre AI  v2         ║
╠══════════════════════════════════════════╣
║  🖥  SPA:      http://localhost:${PORT}       ║
║  📊 Graph:    http://localhost:${PORT}/api/graph  ║
║  ⚡ WebSocket: socket.io                 ║
╚══════════════════════════════════════════╝
  `);
});

process.on('uncaughtException',    err    => console.error('Uncaught:', err));
process.on('unhandledRejection',   reason => console.error('Rejection:', reason));
