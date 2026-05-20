import express from 'express';
import { WebSocketServer } from 'ws';
import http from 'http';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

app.use(express.json());
app.use(express.static(path.join(__dirname, '../dashboard')));

// Load data from JSON files
let pictogramas = [];
let interacciones = [];
let municipios = [];

function loadData() {
  try {
    pictogramas = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../data/pictogramas.json'), 'utf8')
    );
    interacciones = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../data/interacciones.json'), 'utf8')
    );
    municipios = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../data/municipios.json'), 'utf8')
    );
    console.log('✓ Data loaded successfully');
  } catch (error) {
    console.error('Error loading data:', error);
  }
}

loadData();

// API Routes
app.get('/api/pictogramas', (req, res) => {
  res.json(pictogramas);
});

app.get('/api/interacciones', (req, res) => {
  res.json(interacciones);
});

app.get('/api/municipios', (req, res) => {
  res.json(municipios);
});

app.post('/api/interacciones', (req, res) => {
  const newInteraccion = {
    ...req.body,
    fecha: new Date().toISOString().split('T')[0],
  };

  interacciones.push(newInteraccion);

  // Broadcast to all connected clients
  broadcast({
    type: 'new_interaccion',
    data: newInteraccion,
  });

  res.json(newInteraccion);
});

// WebSocket connection
wss.on('connection', (ws) => {
  console.log('New client connected');

  // Send initial data
  ws.send(
    JSON.stringify({
      type: 'init',
      pictogramas,
      interacciones,
      municipios,
    })
  );

  ws.on('message', (message) => {
    try {
      const parsed = JSON.parse(message);

      if (parsed.type === 'add_interaccion') {
        const newInteraccion = {
          ...parsed.data,
          fecha: new Date().toISOString().split('T')[0],
        };

        interacciones.push(newInteraccion);

        // Broadcast to all clients
        broadcast({
          type: 'new_interaccion',
          data: newInteraccion,
        });
      }
    } catch (error) {
      console.error('Error processing message:', error);
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

function broadcast(message) {
  wss.clients.forEach((client) => {
    if (client.readyState === 1) { // WebSocket.OPEN = 1
      client.send(JSON.stringify(message));
    }
  });
}

// Serve pictograma.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../dashboard/pictograma.html'));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════╗
║      Rupestre AI - Pictograma Server       ║
╠════════════════════════════════════════════╣
║  🌐 Servidor: http://localhost:${PORT}      ║
║  🔄 WebSocket: ws://localhost:${PORT}       ║
║  📊 Datos en tiempo real activo             ║
╚════════════════════════════════════════════╝
  `);
});
