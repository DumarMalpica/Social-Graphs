#!/usr/bin/env python3
"""
Rupestre AI - Real-time Dashboard Master Script
Inicia el servidor, simulador y abre el navegador automáticamente
Un solo comando para ejecutar todo el sistema
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
import json
import platform
from pathlib import Path
from threading import Thread
import requests
import socket

# Configuración
PROJECT_ROOT = Path(__file__).parent.absolute()
SERVER_DIR = PROJECT_ROOT / 'server'
DASHBOARD_DIR = PROJECT_ROOT / 'dashboard'
PORT = 5000
URL = f'http://localhost:{PORT}'
MAX_RETRIES = 30
RETRY_DELAY = 1

# Procesos globales
processes = []

def log_header(text):
    """Imprime un encabezado formateado"""
    print(f'\n{"─" * 60}')
    print(f'  {text}')
    print(f'{"─" * 60}\n')

def log_success(text):
    """Imprime un mensaje de éxito"""
    print(f'✓ {text}')

def log_info(text):
    """Imprime un mensaje informativo"""
    print(f'ℹ {text}')

def log_error(text):
    """Imprime un mensaje de error"""
    print(f'✗ {text}', file=sys.stderr)

def log_warning(text):
    """Imprime un mensaje de advertencia"""
    print(f'⚠ {text}')

def cleanup():
    """Termina todos los procesos y limpia"""
    log_info('Limpiando procesos...')
    for proc in processes:
        try:
            if proc.poll() is None:  # Si sigue ejecutándose
                proc.terminate()
                proc.wait(timeout=3)
        except Exception as e:
            try:
                proc.kill()
            except:
                pass
    print('')

def signal_handler(sig, frame):
    """Maneja Ctrl+C"""
    print('\n')
    log_info('Deteniendo aplicación...')
    cleanup()
    sys.exit(0)

def check_port_available(port):
    """Verifica si el puerto está disponible"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def wait_for_server(max_retries=MAX_RETRIES):
    """Espera a que el servidor esté listo"""
    log_info(f'Esperando servidor en {URL}...')
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f'{URL}/api/graph', timeout=2)
            if response.status_code == 200:
                log_success(f'Servidor listo (intento {attempt + 1}/{max_retries})')
                return True
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                print(f'  Reintentando ({attempt + 1}/{max_retries})...', end='\r')
                time.sleep(RETRY_DELAY)
    
    return False

def check_nodejs():
    """Verifica si Node.js está instalado"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        if result.returncode == 0:
            log_success(f'Node.js detectado: {version}')
            return True
    except FileNotFoundError:
        pass
    return False

def install_dependencies():
    """Instala dependencias de npm"""
    if not (SERVER_DIR / 'node_modules').exists():
        log_info('Instalando dependencias de npm...')
        try:
            result = subprocess.run(
                ['npm', 'install', '--prefer-offline', '--no-audit'],
                cwd=SERVER_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                log_success('Dependencias instaladas')
                return True
            else:
                log_error(f'Error instalando dependencias: {result.stderr}')
                return False
        except subprocess.TimeoutExpired:
            log_error('Timeout al instalar dependencias')
            return False
        except Exception as e:
            log_error(f'Error: {e}')
            return False
    else:
        log_success('Dependencias ya instaladas')
        return True

def start_server():
    """Inicia el servidor Node.js"""
    log_info('Iniciando servidor Node.js...')
    
    if platform.system() == 'Windows':
        # En Windows, usar shell=True para mejor manejo de procesos
        proc = subprocess.Popen(
            ['node', 'realtime_server.js'],
            cwd=SERVER_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=True
        )
    else:
        proc = subprocess.Popen(
            ['node', 'realtime_server.js'],
            cwd=SERVER_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    
    processes.append(proc)
    
    # Leer output del servidor
    def read_output():
        try:
            for line in proc.stdout:
                if line and line.strip():
                    print(f'  [Server] {line.rstrip()}')
        except Exception as e:
            pass
    
    thread = Thread(target=read_output, daemon=True)
    thread.start()
    
    return proc

def start_simulator():
    """Inicia el simulador de eventos"""
    log_info('Iniciando simulador de eventos...')
    time.sleep(2)  # Esperar a que el servidor esté listo
    
    if platform.system() == 'Windows':
        proc = subprocess.Popen(
            ['node', 'event_simulator.js'],
            cwd=SERVER_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=True
        )
    else:
        proc = subprocess.Popen(
            ['node', 'event_simulator.js'],
            cwd=SERVER_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    
    processes.append(proc)
    
    # Leer output del simulador
    def read_output():
        try:
            for line in proc.stdout:
                if line and line.strip():
                    print(f'  [Sim] {line.rstrip()}')
        except Exception as e:
            pass
    
    thread = Thread(target=read_output, daemon=True)
    thread.start()
    
    return proc

def open_browser():
    """Abre el navegador automáticamente"""
    log_info(f'Abriendo navegador en {URL}...')
    time.sleep(1)
    
    try:
        webbrowser.open(URL)
        log_success('Navegador abierto')
        return True
    except Exception as e:
        log_warning(f'No se pudo abrir navegador automáticamente: {e}')
        log_info(f'Abre manualmente: {URL}')
        return False

def print_info():
    """Imprime información de acceso"""
    print(f'''
╔════════════════════════════════════════════════╗
║    🎉 Rupestre AI - Real-time Dashboard       ║
║              Sistema Iniciado                 ║
╠════════════════════════════════════════════════╣
║                                                ║
║  🌐 URL: {URL:<31} ║
║  📊 Dashboard: {URL}         ║
║                                                ║
║  🔧 Procesos:                                  ║
║     • Servidor WebSocket: ACTIVO               ║
║     • Simulador de eventos: ACTIVO             ║
║     • Navegador: ABIERTO                       ║
║                                                ║
║  ⌨️  Presiona Ctrl+C para detener              ║
║                                                ║
╚════════════════════════════════════════════════╝
''')

def main():
    """Función principal"""
    log_header('🚀 Rupestre AI - Real-time Graph Visualization')
    
    # Registrar manejador de señal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. Verificar Node.js
        log_info('Verificando requisitos...')
        if not check_nodejs():
            log_error('Node.js no está instalado')
            log_info('Descárgalo desde: https://nodejs.org/')
            sys.exit(1)
        
        # 2. Verificar puerto disponible
        if not check_port_available(PORT):
            log_error(f'Puerto {PORT} en uso')
            log_info(f'Libera el puerto o modifica la configuración')
            sys.exit(1)
        
        # 3. Instalar dependencias
        if not install_dependencies():
            log_error('No se pudieron instalar las dependencias')
            sys.exit(1)
        
        # 4. Iniciar servidor
        server_proc = start_server()
        time.sleep(2)
        
        # 5. Esperar a que el servidor esté listo
        if not wait_for_server():
            log_error('Servidor no respondió en tiempo límite')
            cleanup()
            sys.exit(1)
        
        # 6. Iniciar simulador
        simulator_proc = start_simulator()
        time.sleep(1)
        
        # 7. Abrir navegador
        open_browser()
        
        # 8. Mostrar información
        print_info()
        
        # 9. Mantener aplicación ejecutándose
        log_info('Sistema en ejecución...')
        log_info('Revisa la consola para eventos en vivo\n')
        
        # Monitorear procesos
        simulator_restart_count = 0
        while True:
            time.sleep(2)
            
            # Verificar si el servidor está vivo
            server_status = server_proc.poll()
            if server_status is not None:
                log_error(f'Servidor terminó (code {server_status})')
                cleanup()
                sys.exit(1)
            
            # Verificar si el simulador está vivo
            sim_status = simulator_proc.poll()
            if sim_status is not None and sim_status != 0:
                simulator_restart_count += 1
                if simulator_restart_count < 3:
                    log_warning(f'Simulador terminó, reiniciando... ({simulator_restart_count}/3)')
                    time.sleep(1)
                    simulator_proc = start_simulator()
                else:
                    log_error('Simulador no se puede reiniciar')
                    break
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_error(f'Error inesperado: {e}')
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
    finally:
        cleanup()

if __name__ == '__main__':
    main()
