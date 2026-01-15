# HTML Slides to PDF API

API HTTP em Python para converter slides HTML em PDF usando Playwright. Suporta múltiplas URLs e retorna o PDF gerado para download.

## 📥 Clonar o repositório

```bash
git clone https://github.com/usabit/html-pdf-generator.git
cd html-pdf-generator
```

Depois de clonar, siga os passos de instalação abaixo.

## 🚀 Instalação

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### Build Command no Render

```bash
pip install -r requirements.txt && python -m playwright install chromium
```

### Start Command no Render

```bash
python server.py
```

## ⚙️ Configuração

Não é necessário configurar nada adicional. A API roda diretamente após a instalação.

## 🌐 Deploy no Render

### Passo a passo

1. Acesse [render.com](https://render.com) e faça login com sua conta GitHub
2. Clique em **New +** → **Web Service**
3. Conecte o repositório: `usabit/html-pdf-generator`
4. Configure o Web Service:

**Build Command:**
```bash
pip install -r requirements.txt && python -m playwright install chromium
```

**Start Command:**
```bash
python server.py
```

**Instance:**
- **Type:** Free ou Starter ($7/mês recomendado para melhor performance)
- **CPU/RAM:** 1 CPU / 512 MB RAM (mínimo gratuito)

5. Clique em **Create Web Service**

### Variáveis de Ambiente (Opcional)

Se quiser mudar a porta padrão:
```
PORT=8080
```

### URL do Deploy

Após o deploy, você receberá uma URL como:
```
https://html-pdf-generator.onrender.com
```

### ⚠️ Notas Importantes

- **Plano Free:** O serviço dorme após 15 minutos de inatividade e reinicializa em ~30 segundos
- **Recomendação:** Use o plano Starter ($7/mês) para produção (sem sleep, mais performance)
- **Uptime Checker:** Para evitar sleep no plano gratuito, use [UptimeRobot](https://uptimerobot.com) fazendo ping a cada 5 minutos

### Redeploy Manual

Se precisar forçar um novo deploy:
1. Vá ao painel do Render
2. Clique no seu serviço
3. Clique em **Manual Deploy** → **Clear build cache & deploy**

## ▶️ Executar

```bash
python server.py
```

API roda em `http://localhost:3000`

## 📡 Endpoints

### POST `/generate-pdf`
Gera PDF a partir de múltiplas URLs (uma por slide).

**Parâmetros Obrigatórios:**
- `url` - URL base dos slides (ex: `https://exemplo.com/slides`)
- `totalSlides` - Número total de slides (gera URLs de `url/1` até `url/totalSlides`)

**Parâmetros Opcionais:**
- `output_filename` - Nome do arquivo PDF (padrão: `slides_{uuid}.pdf`)

**Request Body:**
```json
{
  "url": "https://exemplo.com/slides",
  "totalSlides": 4,
  "output_filename": "slides.pdf"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "PDF gerado com sucesso!",
  "filename": "slides.pdf",
  "download_url": "/download/slides.pdf"
}
```

### GET `/download/{filename}`
Baixa um PDF gerado anteriormente.

**Exemplo:**
```bash
curl http://localhost:3000/download/slides.pdf -o downloaded.pdf
```

### GET `/`
Retorna informações sobre a API.

**Resposta:**
```json
{
  "message": "HTML Slides to PDF API",
  "endpoints": {
    "POST /generate-pdf": "Generate PDF from URLs",
    "GET /download/{filename}": "Download generated PDF"
  }
}
```

## 🧪 Testar

```bash
# Testar API
curl -X POST http://localhost:3000/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/slides", "totalSlides": 4}'

# Baixar PDF gerado
curl http://localhost:3000/download/slides.pdf -o downloaded.pdf
```

## 📁 Arquivos

- `server.py` - API HTTP principal com todos os endpoints
- `requirements.txt` - Dependências Python

## ✅ Funcionalidades

- ✅ Gera PDF a partir de múltiplas URLs (uma URL por slide)
- ✅ Preserva estilos CSS completos dos slides
- ✅ Remove badges e elementos indesejados (Lovable badge, etc.)
- ✅ CORS habilitado
- ✅ Retorna URL para download do PDF gerado

## 🎯 Status: Funcionando!

Testado: 4 slides convertidos → PDF pronto para download ✅

## 💡 Exemplo de Uso

```javascript
// Gerar PDF
const response = await fetch('http://localhost:3000/generate-pdf', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://seus-slides.com',
    totalSlides: 5
  })
});

const data = await response.json();
// { success: true, filename: "slides_uuid.pdf", download_url: "/download/slides_uuid.pdf" }

// Baixar PDF
window.open(`http://localhost:3000${data.download_url}`);
```
