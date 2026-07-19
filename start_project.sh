#!/bin/bash

# Script para iniciar el backend y el frontend del Sistema Experto de Macroalgas de forma segura

# Función para detener todos los procesos al salir
cleanup() {
    echo -e "\n[i] Deteniendo servidores..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    exit 0
}

# Configurar trap para capturar CTRL+C (SIGINT) y SIGTERM
trap cleanup SIGINT SIGTERM

echo "========================================================="
echo "   Iniciando Sistema Experto de Macroalgas (Margarita)   "
echo "========================================================="

# 1. Iniciar backend usando el entorno virtual
if [ -d "venv" ]; then
    echo "[+] Iniciando servidor API backend (Python) con venv..."
    ./venv/bin/python3 main.py &
    BACKEND_PID=$!
else
    echo "[!] Advertencia: No se encontró la carpeta 'venv'."
    echo "[+] Intentando iniciar con python3 global..."
    python3 main.py &
    BACKEND_PID=$!
fi

# Esperar un momento a que el backend inicie
sleep 1.5

# 2. Iniciar frontend de Next.js
if [ -d "Frontend" ]; then
    echo "[+] Iniciando servidor de desarrollo frontend (Next.js)..."
    cd Frontend
    npm run dev
else
    echo "[ERROR] No se encontró la carpeta 'Frontend'."
    cleanup
fi
