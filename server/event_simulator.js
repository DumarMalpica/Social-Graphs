import { io as ioClient } from 'socket.io-client';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Rutas posibles para el archivo de datos
const possiblePaths = [
  path.join(__dirname, '..', 'dashboard', 'graph_data.json'),
  path.join(process.cwd(), 'dashboard', 'graph_data.json'),
];

// Municipios disponibles del grafo real
const DEFAULT_MUNICIPIOS = [
  'Tunja', 'Sogamoso', 'Chiquinquirá', 'Duitama', 'Paipa',
  'Villa de Leyva', 'Moniquirá', 'Samacá', 'Ráquira', 'Nobsa',
  'Tibasosa', 'Firavitoba', 'Aquitania', 'Tota', 'Gámeza',
  'Tópaga', 'Mongua', 'Socha', 'Jericó', 'Belén'
];

const PICTOGRAMAS = [
  'P-001', 'P-002', 'P-003', 'P-004', 'P-005',
  'P-006', 'P-007', 'P-008', 'P-009', 'P-010',
  'P-011', 'P-012', 'P-013', 'P-014', 'P-015'
];

const ACCIONES = [
  { tipo: 'upload', desc: 'subió un pictograma' },
  { tipo: 'opinion', desc: 'opinó sobre' },
  { tipo: 'analisis', desc: 'realizó análisis de' },
  { tipo: 'debate', desc: 'debatió sobre' }
];

let socket;
let isRunning = true;

function getRandomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function getRandomIntBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

async function connectToServer() {
  return new Promise((resolve) => {
    socket = ioClient('http://localhost:5000', {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    socket.on('connect', () => {
      console.log('✓ Simulador conectado al servidor');
      resolve();
    });

    socket.on('connect_error', (err) => {
      console.log('⚠ Error de conexión, reintentando...', err.message);
    });

    socket.on('disconnect', () => {
      console.log('✗ Desconectado del servidor');
    });
  });
}

function getMunicipios() {
  try {
    for (const filePath of possiblePaths) {
      if (fs.existsSync(filePath)) {
        const data = fs.readFileSync(filePath, 'utf-8');
        const parsed = JSON.parse(data);
        if (parsed.nodes && parsed.nodes.length > 0) {
          return parsed.nodes.map(n => n.data.id);
        }
      }
    }
  } catch (err) {
    // Silenciar errores, usar defaults
  }
  return DEFAULT_MUNICIPIOS;
}

async function simulateEvent() {
  try {
    const municipios = getMunicipios();
    
    if (!municipios || municipios.length === 0) {
      console.log('Esperando municipios...');
      return;
    }
    
    const accion = getRandomItem(ACCIONES);
    const picto = getRandomItem(PICTOGRAMAS);
    
    let municipio_a, municipio_b;
    
    if (accion.tipo === 'upload') {
      municipio_a = getRandomItem(municipios);
      municipio_b = picto;
    } else {
      municipio_a = getRandomItem(municipios);
      const othersMunicipios = municipios.filter(m => m !== municipio_a);
      if (othersMunicipios.length === 0) {
        return;
      }
      municipio_b = getRandomItem(othersMunicipios);
    }

    // Evento para log
    const eventData = {
      type: accion.tipo,
      municipio_a,
      municipio_b,
      pictograma: picto,
      timestamp: new Date().toISOString(),
      description: `${municipio_a} ${accion.desc} ${municipio_b}`
    };

    if (socket && socket.connected) {
      socket.emit('new_event', eventData);

      // Crear conexión
      if (accion.tipo !== 'upload') {
        socket.emit('add_connection', {
          source: municipio_a,
          target: municipio_b,
          weight: getRandomIntBetween(1, 3),
          type: accion.tipo
        });
      }

      console.log(`📌 ${eventData.description}`);
    }
  } catch (err) {
    console.error('Error simulando evento:', err.message);
  }
}

async function startSimulation() {
  console.log('\n🎬 Iniciando simulador de eventos...\n');
  
  try {
    await connectToServer();
    
    // Esperar a que el cliente reciba la inicialización
    await new Promise(resolve => setTimeout(resolve, 1000));

    console.log('📡 Generando eventos simulados cada 2-5 segundos...\n');
    console.log('Presiona Ctrl+C para detener\n');

    // Generar eventos periódicamente con intervalo aleatorio
    let currentInterval = getRandomIntBetween(2000, 5000);
    let intervalHandle = null;

    const scheduleNextEvent = () => {
      currentInterval = getRandomIntBetween(2000, 5000);
      intervalHandle = setTimeout(() => {
        if (isRunning && socket && socket.connected) {
          simulateEvent();
        }
        scheduleNextEvent();
      }, currentInterval);
    };

    scheduleNextEvent();

    // Manejo de Ctrl+C
    process.on('SIGINT', () => {
      isRunning = false;
      if (intervalHandle) clearTimeout(intervalHandle);
      console.log('\n\n✓ Simulador detenido');
      setTimeout(() => process.exit(0), 500);
    });

  } catch (err) {
    console.error('Error iniciando simulador:', err);
    setTimeout(() => process.exit(1), 500);
  }
}

// Iniciar simulación
startSimulation();
