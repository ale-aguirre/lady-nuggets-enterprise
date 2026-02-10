#!/bin/bash

# ============================================
# RUNPOD SWAP MANAGER (ANTI-OOM)
# ============================================

set -e

echo "🧠 Verificando memoria RAM..."
free -h

echo ""
echo "💾 Creando archivo de SWAP (20GB)..."
echo "Esto evitará que el Pod muera al cargar modelos grandes como LTX."

# 1. Crear archivo (si no existe)
if [ ! -f "/workspace/swapfile" ]; then
    fallocate -l 20G /workspace/swapfile
    chmod 600 /workspace/swapfile
    mkswap /workspace/swapfile
    swapon /workspace/swapfile
    echo "✅ Swap de 20GB activado."
else
    # Verificar si está activo
    if swapon -s | grep -q "/workspace/swapfile"; then
        echo "✅ El Swap ya estaba activo."
    else
        swapon /workspace/swapfile
        echo "✅ Swap reactivado."
    fi
fi

echo ""
echo "📊 Estado final de memoria:"
free -h
