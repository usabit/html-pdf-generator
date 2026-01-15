#!/usr/bin/env python3
"""
API HTTP Simples para converter slides HTML em PDF
"""

import asyncio
import http.server
import json
import os
import socketserver
import tempfile
import time
import uuid
from pathlib import Path

from playwright.async_api import async_playwright
from PyPDF2 import PdfMerger

# Caminho do executável do Chromium no Render
# O Playwright instala em diferentes locais dependendo do sistema operacional
CHROMIUM_PATH = os.getenv("CHROMIUM_PATH", None)


class APIHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Expose-Headers", "*")
        self.send_header("Access-Control-Max-Age", "86400")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Endpoint de download para SSE
        if self.path.startswith("/download/"):
            filename = self.path.replace("/download/", "")
            pdf_path = f"temp_{filename}"

            if not Path(pdf_path).exists():
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "File not found"}).encode())
                return

            with open(pdf_path, "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header(
                    "Content-Disposition", f'attachment; filename="{filename}"'
                )
                self.end_headers()
                self.wfile.write(f.read())

            # Remove após download
            Path(pdf_path).unlink(missing_ok=True)
            return

        # Endpoint GET padrão
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response = {
            "message": "HTML Slides to PDF API",
            "endpoints": {
                "POST /generate-pdf": "Generate PDF from URLs",
                "GET /download/{filename}": "Download generated PDF",
            },
        }
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return

        if self.path == "/generate-pdf":
            self.handle_generate_pdf(data)
        else:
            self.send_error(404)

    def handle_generate_pdf(self, data):
        try:
            # Parâmetros obrigatórios
            url = data.get("url")
            total_slides = data.get("totalSlides")

            # Parâmetros opcionais
            output_filename = data.get("output_filename", f"slides_{uuid.uuid4()}.pdf")

            if not url:
                raise ValueError("Deve fornecer 'url'")

            if not total_slides:
                raise ValueError("Deve fornecer 'totalSlides'")

            # Gera o PDF
            asyncio.run(
                self.convert_multiple_urls_to_pdf(url, total_slides, output_filename)
            )

            download_url = f"/download/{output_filename}"

            # Retorna JSON com URL de download
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "success": True,
                "message": "PDF gerado com sucesso!",
                "filename": output_filename,
                "download_url": download_url,
            }
            self.wfile.write(json.dumps(response).encode())

            # NOTA: O PDF não é removido aqui pois o front vai fazer download

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    async def convert_multiple_urls_to_pdf(
        self, base_url, total_slides, output_filename
    ):
        async with async_playwright() as p:
            # Otimizações para velocidade
            # Usa o caminho do Chromium se especificado (para Render), senão usa padrão
            launch_options = {
                "args": [
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                ]
            }

            if CHROMIUM_PATH:
                launch_options["executable_path"] = CHROMIUM_PATH

            browser = await p.chromium.launch(**launch_options)
            page = await browser.new_page()

            # Configura viewport com margem de segurança para compensar cortes
            # e garantir que o conteúdo caiba em uma página
            slide_width = 1280  # 1230 + 50px margem
            slide_height = 750  # 692 + 58px margem
            await page.set_viewport_size({"width": slide_width, "height": slide_height})

            temp_dir = Path(tempfile.gettempdir()) / f"slides_{uuid.uuid4()}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            slide_files = []

            for i in range(1, total_slides + 1):  # De 1 até totalSlides
                url = f"{base_url}/{i}"

                try:
                    print(f"Carregando: {url}")

                    start = time.time()

                    # Tenta carregar a página com wait_until="load"
                    await page.goto(url, timeout=60000, wait_until="load")
                    print(f"  - goto levou: {time.time() - start:.2f}s")

                    # DEBUG: Mostra o que está na página
                    page_text = await page.evaluate("() => document.body.innerText")
                    print(
                        f"  - Texto na página (primeiros 200 chars): {page_text[:200]}"
                    )

                    # Espera o .printable ter conteúdo de verdade
                    print(f"  - Aguardando conteúdo do .printable...")
                    start_wait = time.time()

                    for attempt in range(30):  # 30 tentativas (30 segundos max)
                        content_check = await page.evaluate(
                            """() => {
                            const printable = document.querySelector('.printable');
                            if (!printable) return { found: false };

                            const text = printable.innerText.trim();
                            const hasLoading = text.toLowerCase().includes('carregando') ||
                                             text.toLowerCase().includes('loading');

                            return {
                                found: true,
                                textLength: text.length,
                                hasLoading: hasLoading,
                                preview: text.substring(0, 100)
                            };
                        }"""
                        )

                        if content_check.get("found"):
                            if (
                                not content_check.get("hasLoading")
                                and content_check.get("textLength", 0) > 50
                            ):
                                print(
                                    f"  - Conteúdo pronto! ({time.time() - start_wait:.2f}s)"
                                )
                                print(
                                    f"  - Preview: {content_check.get('preview', '')}"
                                )
                                break
                            else:
                                print(
                                    f"  - Tentativa {attempt + 1}: ainda carregando (length={content_check.get('textLength', 0)}, hasLoading={content_check.get('hasLoading')})"
                                )

                        await page.wait_for_timeout(1000)

                    # Captura PDF
                    temp_path = temp_dir / f"slide_{i}.pdf"

                    start = time.time()
                    await page.evaluate(
                        """() => {
                        // Remove badge do Lovable
                        const lovableBadge = document.getElementById('lovable-badge');
                        if (lovableBadge) {
                            lovableBadge.remove();
                        }

                        const printable = document.querySelector('.printable');
                        if (!printable) {
                            return { success: false, error: 'No .printable found' };
                        }

                        // Remove classes de estilo
                        printable.classList.remove('overflow-hidden',
                            'rounded-2xl', 'shadow-2xl', 'rounded-xl',
                            'shadow-xl', 'rounded', 'shadow', 'p-4', 'p-6', 'p-8');

                        // Reset completo de estilos
                        printable.style.margin = '0';
                        printable.style.padding = '0';
                        printable.style.border = 'none';
                        printable.style.boxShadow = 'none';
                        printable.style.overflow = 'hidden';
                        printable.style.width = '100vw';
                        printable.style.height = '100vh';
                        printable.style.display = 'flex';
                        printable.style.flexDirection = 'column';

                        // Também limpa o body e html
                        document.body.style.margin = '0';
                        document.body.style.padding = '0';
                        document.body.style.overflow = 'hidden';
                        document.body.style.width = '100vw';
                        document.body.style.height = '100vh';
                        document.documentElement.style.margin = '0';
                        document.documentElement.style.padding = '0';
                        document.documentElement.style.overflow = 'hidden';

                        return { success: true };
                    }"""
                    )
                    print(f"  - evaluate levou: {time.time() - start:.2f}s")

                    start = time.time()
                    await page.pdf(
                        path=str(temp_path),
                        width=f"{slide_width}px",
                        height=f"{slide_height}px",
                        print_background=True,
                        prefer_css_page_size=False,
                        page_ranges="1",  # Apenas primeira página
                        margin={
                            "top": "0px",
                            "right": "0px",
                            "bottom": "0px",
                            "left": "0px",
                        },
                    )
                    print(f"  - PDF gerado em: {time.time() - start:.2f}s")

                    slide_files.append(temp_path)
                    print(f"Página {i}/{total_slides} gerada")

                except Exception as e:
                    print(f"Erro na página {i}: {e}")
                    raise e

            await browser.close()

            # Mescla todos os PDFs
            output_path = f"temp_{output_filename}"
            merger = PdfMerger()
            for slide_file in sorted(slide_files):
                merger.append(str(slide_file))
            merger.write(output_path)
            merger.close()


def run_server():
    PORT = 3000

    with socketserver.TCPServer(("", PORT), APIHandler) as httpd:
        print(f"✅ API rodando em http://localhost:{PORT}")
        print("\n📌 Endpoint:")
        print("  POST /generate-pdf              - Gerar PDF de múltiplas URLs")
        print("\n  GET  /download/{filename}       - Baixar PDF gerado")
        print("\nCtrl+C para parar")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Servidor parado")


if __name__ == "__main__":
    run_server()
