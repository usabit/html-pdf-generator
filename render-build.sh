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
    libatspi2.0-0

# Instalar Chromium do Playwright (com verbose para debug)
echo "📦 Instalando Chromium..."
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0 python -m playwright install chromium --with-deps

# Verificar se o Chromium foi instalado
echo "🔍 Verificando instalação..."
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=True); print('✅ Chromium instalado com sucesso!'); browser.close(); p.stop()"

# Encontrar o caminho do binário do Chromium e exportar
echo "🔍 Encontrando caminho do Chromium..."
CHROMIUM_PATH=$(python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); path = p.chromium.executable_path; print(path); p.stop()")
echo "📂 Chromium path: $CHROMIUM_PATH"

# Exportar para ambiente do Render (adicionar ao .bashrc para persistência)
echo "export CHROMIUM_PATH=$CHROMIUM_PATH" >> $HOME/.bashrc
echo "✅ CHROMIUM_PATH configurado: $CHROMIUM_PATH"

# Limpar cache para economizar espaço
rm -rf /opt/render/.cache/ms-playwright/webkit*
rm -rf /opt/render/.cache/ms-playwright/firefox*

echo "✅ Build concluído com sucesso!"
