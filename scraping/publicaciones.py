"""Publicaciones: scroll en la cuadrícula, enlaces y datos de cada post."""
import re
from datetime import datetime

from playwright.sync_api import Page

from config import BASE, MAX_POSTS
from scraping.utilidades import NUM, a_numero, buscar, descripcion, pausa

# "12 likes, 3 comments - usuario on March 3, 2024: "texto"."
LIKES = re.compile(NUM + r"\s+(likes?|me gusta)", re.I)
COMENTARIOS = re.compile(NUM + r"\s+(comments?|comentarios?)", re.I)
TEXTO = re.compile(r':\s*"(.*)"\s*\.?\s*$', re.S)
ENLACE_POST = re.compile(r"/(p|reel)/([A-Za-z0-9_-]+)")
# "... on October 14, 2026: ..." (los reels no tienen etiqueta <time>)
FECHA_TEXTO = re.compile(r"on ([A-Z][a-z]+ \d{1,2}, \d{4}):")


def recolectar_urls(page: Page) -> list[str]:
    """Hace scroll en la cuadrícula del perfil y junta los enlaces a publicaciones."""
    urls: list[str] = []
    rondas_sin_nuevos = 0
    while len(urls) < MAX_POSTS and rondas_sin_nuevos < 3:
        antes = len(urls)
        hrefs = page.eval_on_selector_all("a[href]", "els => els.map(a => a.href)")
        for href in hrefs:
            m = ENLACE_POST.search(href)
            if m:
                url = f"{BASE}/{m.group(1)}/{m.group(2)}/"
                if url not in urls and len(urls) < MAX_POSTS:
                    urls.append(url)
        rondas_sin_nuevos = rondas_sin_nuevos + 1 if len(urls) == antes else 0
        print(f"Enlaces de publicaciones encontrados: {len(urls)}")
        page.mouse.wheel(0, 2500)
        pausa(page)
    return urls


def fecha_desde_texto(desc: str) -> str:
    """'... on October 14, 2026: ...' -> '2026-10-14'"""
    texto = buscar(FECHA_TEXTO, desc)
    try:
        return datetime.strptime(texto, "%B %d, %Y").date().isoformat()
    except ValueError:
        return ""


def extraer_post(page: Page, url: str) -> dict:
    desc = descripcion(page)
    try:
        fecha = page.locator("time[datetime]").first.get_attribute("datetime", timeout=3000) or ""
    except Exception:
        fecha = ""
    if not fecha:
        fecha = fecha_desde_texto(desc)
    return {
        "url": url,
        "type": "reel" if "/reel/" in url else "post",
        "likes": a_numero(buscar(LIKES, desc)),
        "comments": a_numero(buscar(COMENTARIOS, desc)),
        "date": fecha,
        "caption": buscar(TEXTO, desc),
        "rawDescription": desc,
    }


def extraer_publicaciones(page: Page) -> list[dict]:
    posts = []
    for url in recolectar_urls(page):
        page.goto(url)
        pausa(page)
        post = extraer_post(page, url)
        posts.append(post)
        print(f"[{len(posts)}] {url}  likes={post['likes']}")
    return posts
