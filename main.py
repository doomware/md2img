import asyncio
import base64
import hashlib
import io
import os
import secrets
from enum import Enum
from typing import Optional

import markdown2
from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field

app = FastAPI(
    title="Markdown to Image API",
    description="Converts Markdown text into a PNG image.",
    version="1.0.0",
)

# ──────────────────────────────────────────────
# API Key auth
# ──────────────────────────────────────────────
_API_KEY: str | None = os.getenv("API_KEY")

_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_key_query  = APIKeyQuery(name="api_key",    auto_error=False)


async def require_api_key(
    header_key: str | None = Security(_key_header),
    query_key:  str | None = Security(_key_query),
) -> None:
    """Dependency that rejects requests without a valid API key."""
    if _API_KEY is None:
        raise RuntimeError(
            "API_KEY environment variable is not set. "
            "The service cannot start without a configured API key."
        )
    candidate = header_key or query_key
    if not candidate or not secrets.compare_digest(candidate, _API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. "
                   "Provide it via the X-API-Key header or the api_key query param.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Themes
# ──────────────────────────────────────────────
class Theme(str, Enum):
    light = "light"
    dark = "dark"
    solarized = "solarized"
    dracula = "dracula"


THEMES: dict[str, dict] = {
    "light": {
        "bg": "#ffffff",
        "text": "#1a1a1a",
        "code_bg": "#f5f5f5",
        "border": "#e0e0e0",
        "link": "#0969da",
        "blockquote_border": "#d0d7de",
        "blockquote_text": "#57606a",
        "heading": "#1a1a1a",
    },
    "dark": {
        "bg": "#0d1117",
        "text": "#e6edf3",
        "code_bg": "#161b22",
        "border": "#30363d",
        "link": "#58a6ff",
        "blockquote_border": "#3b434b",
        "blockquote_text": "#8b949e",
        "heading": "#e6edf3",
    },
    "solarized": {
        "bg": "#fdf6e3",
        "text": "#657b83",
        "code_bg": "#eee8d5",
        "border": "#d3cbb9",
        "link": "#268bd2",
        "blockquote_border": "#93a1a1",
        "blockquote_text": "#93a1a1",
        "heading": "#586e75",
    },
    "dracula": {
        "bg": "#282a36",
        "text": "#f8f8f2",
        "code_bg": "#44475a",
        "border": "#44475a",
        "link": "#8be9fd",
        "blockquote_border": "#6272a4",
        "blockquote_text": "#6272a4",
        "heading": "#bd93f9",
    },
}


# ──────────────────────────────────────────────
# HTML template
# ──────────────────────────────────────────────
def build_html(html_body: str, theme: str, width: int, font_size: int) -> str:
    t = THEMES[theme]
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: {t['bg']};
    color: {t['text']};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 'Helvetica Neue', Arial, sans-serif;
    font-size: {font_size}px;
    line-height: 1.7;
    padding: 40px 48px;
    width: {width}px;
    min-height: 100px;
  }}

  h1, h2, h3, h4, h5, h6 {{
    color: {t['heading']};
    font-weight: 600;
    margin: 1.2em 0 0.5em;
    line-height: 1.3;
  }}
  h1 {{ font-size: 2em; border-bottom: 1px solid {t['border']}; padding-bottom: 0.3em; }}
  h2 {{ font-size: 1.5em; border-bottom: 1px solid {t['border']}; padding-bottom: 0.3em; }}
  h3 {{ font-size: 1.25em; }}

  p {{ margin: 0.8em 0; }}

  a {{ color: {t['link']}; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  code {{
    background: {t['code_bg']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 0.1em 0.4em;
    font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
    font-size: 0.9em;
  }}

  pre {{
    background: {t['code_bg']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    margin: 1em 0;
  }}
  pre code {{
    background: none;
    border: none;
    padding: 0;
    font-size: 0.88em;
    line-height: 1.6;
  }}

  blockquote {{
    border-left: 4px solid {t['blockquote_border']};
    color: {t['blockquote_text']};
    padding: 0.5em 1em;
    margin: 1em 0;
    background: {t['code_bg']};
    border-radius: 0 6px 6px 0;
  }}

  ul, ol {{ padding-left: 1.6em; margin: 0.8em 0; }}
  li {{ margin: 0.3em 0; }}

  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
  }}
  th, td {{
    border: 1px solid {t['border']};
    padding: 8px 12px;
    text-align: left;
  }}
  th {{
    background: {t['code_bg']};
    font-weight: 600;
  }}
  tr:nth-child(even) {{ background: {t['code_bg']}; }}

  hr {{
    border: none;
    border-top: 1px solid {t['border']};
    margin: 1.5em 0;
  }}

  img {{ max-width: 100%; border-radius: 6px; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""


# ──────────────────────────────────────────────
# Core renderer
# ──────────────────────────────────────────────
async def render_md_to_png(
    markdown_text: str,
    theme: str = "light",
    width: int = 800,
    font_size: int = 16,
    scale: float = 2.0,
) -> bytes:
    html_body = markdown2.markdown(
        markdown_text,
        extras=[
            "fenced-code-blocks",
            "tables",
            "strike",
            "task_list",
            "footnotes",
            "header-ids",
            "break-on-newline",
        ],
    )
    full_html = build_html(html_body, theme, width, font_size)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.new_page(device_scale_factor=scale)
        await page.set_content(full_html, wait_until="networkidle")

        # Let the body grow to its natural height
        body_height = await page.evaluate(
            "document.body.scrollHeight"
        )
        await page.set_viewport_size({"width": int(width * scale), "height": body_height})
        await page.set_viewport_size({"width": width, "height": body_height})

        screenshot = await page.screenshot(full_page=True, type="png")
        await browser.close()

    return screenshot


# ──────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────
class MarkdownRequest(BaseModel):
    markdown: str = Field(..., description="Markdown text to render", examples=["# Hello\n\nThis is **bold**."])
    theme: Theme = Field(Theme.light, description="Color theme")
    width: int = Field(800, ge=320, le=2400, description="Canvas width in pixels")
    font_size: int = Field(16, ge=10, le=32, description="Base font size in pixels")
    scale: float = Field(2.0, ge=1.0, le=3.0, description="Device pixel ratio (retina scale)")
    return_base64: bool = Field(False, description="Return image as base64 JSON instead of binary PNG")


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────
@app.get("/", tags=["Info"])
async def root():
    return {
        "name": "Markdown to Image API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "POST /render": "Convert markdown to PNG (body JSON)",
            "GET  /render": "Convert markdown to PNG (query params)",
        },
        "themes": list(THEMES.keys()),
    }


@app.post("/render", tags=["Render"], summary="Render markdown → PNG (JSON body)",
          dependencies=[Depends(require_api_key)])
async def render_post(req: MarkdownRequest):
    if not req.markdown.strip():
        raise HTTPException(status_code=400, detail="markdown field cannot be empty")

    try:
        png_bytes = await render_md_to_png(
            req.markdown,
            theme=req.theme.value,
            width=req.width,
            font_size=req.font_size,
            scale=req.scale,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if req.return_base64:
        encoded = base64.b64encode(png_bytes).decode()
        return JSONResponse({"image": encoded, "mime": "image/png"})

    return Response(content=png_bytes, media_type="image/png")


@app.get("/render", tags=["Render"], summary="Render markdown → PNG (query string)",
         dependencies=[Depends(require_api_key)])
async def render_get(
    markdown: str = Query(..., description="Markdown text"),
    theme: Theme = Query(Theme.light),
    width: int = Query(800, ge=320, le=2400),
    font_size: int = Query(16, ge=10, le=32),
    scale: float = Query(2.0, ge=1.0, le=3.0),
):
    if not markdown.strip():
        raise HTTPException(status_code=400, detail="markdown cannot be empty")

    try:
        png_bytes = await render_md_to_png(
            markdown,
            theme=theme.value,
            width=width,
            font_size=font_size,
            scale=scale,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return Response(content=png_bytes, media_type="image/png")


@app.get("/health", tags=["Info"])
async def health():
    return {"status": "ok"}
