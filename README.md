# md2img

> Convierte Markdown en imágenes PNG de alta resolución via API REST.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-1.49-45ba4b?logo=playwright&logoColor=white)](https://playwright.dev)
[![Python](https://img.shields.io/badge/Python-3.12-3776ab?logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ed?logo=docker&logoColor=white)](https://docker.com)

---

## ¿Cómo funciona?

```
Markdown  →  HTML + tema CSS  →  Chromium headless  →  PNG
```

Playwright abre la página en un navegador headless y toma un screenshot del contenido completo, lo que garantiza un renderizado pixel-perfect con soporte completo de fuentes, tablas, bloques de código y listas de tareas.

---

## Inicio rápido

### Con Docker (recomendado)

```bash
# 1. Clona el repositorio
git clone https://github.com/tu-usuario/md2img.git
cd md2img

# 2. Configura la API key
cp .env.example .env
# edita .env y pon tu clave en API_KEY=...

# 3. Levanta el servicio
docker compose up --build
```

La API queda disponible en `http://localhost:3030`.

### Sin Docker (desarrollo local)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

export API_KEY=dev-key-local
uvicorn main:app --reload --port 3030
```

---

## Autenticación

Todos los endpoints `/render` requieren una API key.

| Método | Ejemplo |
|---|---|
| Header (recomendado) | `X-API-Key: tu-clave` |
| Query param | `?api_key=tu-clave` |

> [!IMPORTANT]
> Si la variable de entorno `API_KEY` no está definida, el servicio lanzará un error en el primer request. No existe modo abierto.

---

## Endpoints

### `POST /render` — JSON body

```bash
curl -X POST http://localhost:3030/render \
  -H "X-API-Key: tu-clave" \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Hola mundo\n\nEsto es **negrita** y `código`.",
    "theme": "dark",
    "width": 900,
    "scale": 2.0
  }' \
  --output resultado.png
```

### `GET /render` — Query params

```bash
curl "http://localhost:3030/render?markdown=**hola**&theme=dracula&api_key=tu-clave" \
  --output resultado.png
```

### `GET /` — Info

```bash
curl http://localhost:3030/
```

### `GET /health` — Health check

```bash
curl http://localhost:3030/health
# → {"status": "ok"}
```

---

## Parámetros

| Parámetro | Tipo | Default | Rango | Descripción |
|---|---|---|---|---|
| `markdown` | `string` | — | — | Texto Markdown a renderizar |
| `theme` | `string` | `light` | ver abajo | Tema de color |
| `width` | `integer` | `800` | 320–2400 | Ancho del canvas en píxeles |
| `font_size` | `integer` | `16` | 10–32 | Tamaño de fuente base en px |
| `scale` | `float` | `2.0` | 1.0–3.0 | Device pixel ratio (calidad retina) |
| `return_base64` | `boolean` | `false` | — | Solo POST: devuelve JSON con imagen en base64 |

### Respuesta base64 (solo POST)

```bash
curl -X POST http://localhost:3030/render \
  -H "X-API-Key: tu-clave" \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Test", "return_base64": true}'

# → {"image": "<base64>", "mime": "image/png"}
```

---

## Temas

| Tema | Vista previa |
|---|---|
| `light` | Fondo blanco, texto oscuro — estilo GitHub |
| `dark` | Fondo `#0d1117`, texto claro — estilo GitHub Dark |
| `solarized` | Paleta Solarized clásica |
| `dracula` | Paleta Dracula con púrpuras y cyans |

---

## Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `API_KEY` | **Sí** | Clave secreta para autenticar requests |
| `PYTHONUNBUFFERED` | No | Logs en tiempo real (definida en docker-compose) |

---

## Stack

| Capa | Tecnología |
|---|---|
| Framework web | FastAPI 0.115 |
| Servidor ASGI | Uvicorn |
| Renderizado | Playwright 1.49 (Chromium headless) |
| Conversión MD→HTML | markdown2 2.5 |
| Validación | Pydantic v2 |
| Contenedor | Docker / Docker Compose |

---

## Documentación interactiva

Una vez levantado el servidor, accede a la documentación Swagger en:

```
http://localhost:3030/docs
```

---

## Licencia

MIT
