#!/bin/bash

# Script de build para Render - HTML to PDF API

echo "🚀 Iniciando build no Render..."

# Atualizar pip
pip install --upgrade pip

# Instalar dependências do projeto
pip install -r requirements.txt

# Instalar dependências do sistema para Playwright no Linux
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libgtk-3-0 \
    libatspi2.0-0 \
    libwayland-client0 \
    libwayland-cursor0 \
    libwayland-egl0

# Instalar Chromium do Playwright
python -m playwright install chromium

# Limpar cache para economizar espaço
rm -rf /opt/render/.cache/ms-playwright/webkit*
rm -rf /opt/render/.cache/ms-playwright/firefox*

echo "✅ Build concluído com sucesso!"
