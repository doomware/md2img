# AGENTS.md — md2img

Guía para agentes de IA que trabajen en este repositorio.

---

## ¿Qué hace este proyecto?

**md2img** es una API REST que convierte texto Markdown en imágenes PNG de alta resolución.
Usa **FastAPI** como framework web y **Playwright + Chromium** (headless) como motor de renderizado.
El flujo es: Markdown → HTML con tema aplicado → screenshot PNG via Chromium.

---

## Estructura del repositorio

```
md2img/
├── main.py              # Toda la lógica: API, auth, temas, renderizado
├── requirements.txt     # Dependencias Python
├── Dockerfile           # Imagen basada en python:3.12-slim + Chromium
├── docker-compose.yml   # Servicio en el puerto 3030
├── .env.example         # Plantilla de variables de entorno
└── AGENTS.md            # Este archivo
```

> No hay tests, migraciones, ni submódulos. Todo el código vive en `main.py`.

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

## Endpoints

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| `GET` | `/` | Info general y lista de temas | ❌ |
| `GET` | `/health` | Health check (usado por Docker) | ❌ |
| `POST` | `/render` | Renderiza Markdown (body JSON) | ✅ |
| `GET` | `/render` | Renderiza Markdown (query params) | ✅ |

Los endpoints `/render` requieren autenticación con API key.

---

## Autenticación

La API key se configura mediante la variable de entorno `API_KEY`.

- **Header (recomendado):** `X-API-Key: <clave>`
- **Query param:** `?api_key=<clave>`
- Si `API_KEY` no está definida en el entorno, el servicio lanza un `RuntimeError` en el primer request protegido — **no existe modo abierto**.
- La comparación usa `secrets.compare_digest` para evitar timing attacks.
- `/health` y `/` están exentos de autenticación intencionalmente.

---

## Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `API_KEY` | **Sí** | Clave secreta para autenticar requests a `/render` |
| `PYTHONUNBUFFERED` | No | Definida en docker-compose (logs en tiempo real) |

Crea un archivo `.env` basándote en `.env.example` antes de levantar el servicio.

---

## Temas disponibles

`light` · `dark` · `solarized` · `dracula`

Cada tema define: `bg`, `text`, `code_bg`, `border`, `link`, `blockquote_border`, `blockquote_text`, `heading`.
Los temas están en el dict `THEMES` dentro de `main.py`. Para añadir un tema nuevo, agrega una entrada allí y un valor al `Enum Theme`.

---

## Parámetros de renderizado

| Parámetro | Tipo | Default | Rango | Descripción |
|---|---|---|---|---|
| `markdown` | `str` | — | — | Texto Markdown a renderizar |
| `theme` | `enum` | `light` | light/dark/solarized/dracula | Tema de color |
| `width` | `int` | `800` | 320–2400 | Ancho del canvas en px |
| `font_size` | `int` | `16` | 10–32 | Tamaño de fuente base en px |
| `scale` | `float` | `2.0` | 1.0–3.0 | Device pixel ratio (retina) |
| `return_base64` | `bool` | `false` | — | Solo POST: devuelve JSON con imagen en base64 |

---

## Desarrollo local

```bash
# 1. Crear entorno virtual e instalar dependencias
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Configurar API key
echo "API_KEY=dev-key-local" > .env   # o exportar: export API_KEY=dev-key-local

# 3. Arrancar servidor
uvicorn main:app --reload --port 3030
```

---

## Docker

```bash
# Construir y levantar
API_KEY=tu-clave-secreta docker compose up --build

# O con archivo .env
cp .env.example .env   # editar .env con la key real
docker compose up --build
```

El healthcheck de Docker Compose consulta `/health` cada 30 segundos sin API key.

---

## Convenciones y reglas para agentes

1. **Un solo archivo de lógica.** No fragmentes el código en múltiples módulos a menos que el usuario lo pida explícitamente. Todo vive en `main.py`.
2. **Auth siempre activa.** No reintroduzcas un "modo dev" o bypass de autenticación. `API_KEY` es siempre obligatoria.
3. **`/health` y `/` sin auth.** Estos endpoints deben permanecer públicos para que el healthcheck de Docker funcione.
4. **Temas como dict + Enum.** Al añadir temas, actualiza tanto `THEMES` como el `Enum Theme`.
5. **No rompas la firma de `render_md_to_png`.** Los endpoints dependen de ella directamente.
6. **Pydantic v2.** Usa la API de v2 (`model_validator`, `Field`, etc.); no uses sintaxis de v1.
7. **Sin dependencias nuevas sin actualizar `requirements.txt`.**
8. **El puerto expuesto es 3030.** No lo cambies sin actualizar también `docker-compose.yml` y el healthcheck.
