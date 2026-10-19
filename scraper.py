"""Scraper basado en la PÁGINA (DOM): Playwright abre el perfil con las
cookies inyectadas y lee lo que se ve en pantalla."""
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

import cookies_loader

# --- Configuración ---
USUARIO = "alondra_cgp"   # perfil a estudiar (sin @)
MAX_POSTS = 50            # tope de publicaciones a extraer
DELAY = 3                 # pausa base entre acciones (segundos)
HEADLESS = False          # False = ves el navegador trabajando

BASE = "https://www.instagram.com"
OUTPUT_DIR = Path("output")

# "123 Followers, 45 Following, 67 Posts - See Instagram photos..."
NUM = r"([\d.,]+[KkMm]?)"
SEGUIDORES = re.compile(NUM + r"\s+(followers|seguidores)", re.I)
SEGUIDOS = re.compile(NUM + r"\s+(following|seguidos)", re.I)
PUBLICACIONES = re.compile(NUM + r"\s+(posts|publicaciones)", re.I)
# "12 likes, 3 comments - usuario on March 3, 2024: "texto"."
LIKES = re.compile(NUM + r"\s+(likes?|me gusta)", re.I)
COMENTARIOS = re.compile(NUM + r"\s+(comments?|comentarios?)", re.I)
TEXTO = re.compile(r':\s*"(.*)"\s*\.?\s*$', re.S)
ENLACE_POST = re.compile(r"/(p|reel)/([A-Za-z0-9_-]+)")
# "... on October 14, 2026: ..." (los reels no tienen etiqueta <time>)
FECHA_TEXTO = re.compile(r"on ([A-Z][a-z]+ \d{1,2}, \d{4}):")
# Botones del perfil: marcan el fin de la biografía
BOTONES = {"Follow", "Following", "Message", "Seguir", "Siguiendo", "Enviar mensaje"}


def pausa(page: Page):
    """Pausa variable, como una persona que no hace clic cada X segundos exactos."""
    page.wait_for_timeout((DELAY + random.uniform(0, 2)) * 1000)


def meta(page: Page, selector: str) -> str:
    loc = page.locator(selector)
    return (loc.first.get_attribute("content") or "") if loc.count() else ""


def descripcion(page: Page) -> str:
    return meta(page, "meta[property='og:description']") or meta(page, "meta[name='description']")


def buscar(patron: re.Pattern, texto: str) -> str:
    m = patron.search(texto)
    return m.group(1) if m else ""


def a_numero(s: str) -> int:
    """'1,234' -> 1234 ; '1.2K' -> 1200 ; '3M' -> 3000000"""
    if not s:
        return 0
    multiplicador = {"K": 1_000, "M": 1_000_000}.get(s[-1].upper(), 1)
    if multiplicador > 1:
        return round(float(s[:-1].replace(",", ".")) * multiplicador)
    return int(re.sub(r"[.,]", "", s))


def extraer_bio(cabecera: str, nombre: str, usuario: str) -> str:
    """La bio son las líneas de la cabecera que vienen después de los contadores
    y antes de los botones / historias destacadas."""
    lineas = [l.strip() for l in cabecera.splitlines() if l.strip()]
    inicio = -1
    for i, l in enumerate(lineas):
        if l.lower().endswith(("following", "seguidos")):
            inicio = i + 1
    if inicio < 0:
        return ""
    bio = []
    for i, l in enumerate(lineas[inicio:]):
        if i == 0 and l == nombre:
            continue
        if l.startswith(("Followed by", "Seguido por", "See translation")) or l == usuario or l in BOTONES:
            break
        bio.append(l)
    return "\n".join(bio)


def extraer_perfil(page: Page, usuario: str) -> dict:
    desc = descripcion(page)
    titulo = meta(page, "meta[property='og:title']")  # "Nombre (@usuario) • Instagram..."
    nombre = titulo.split(" (@")[0] if " (@" in titulo else ""

    try:
        cabecera = page.locator("header").first.inner_text(timeout=5000)
    except Exception:
        cabecera = ""
        print("No se encontró la cabecera del perfil.")

    html = page.content()
    return {
        "username": usuario,
        "fullName": nombre,
        "biography": extraer_bio(cabecera, nombre, usuario),
        "followers": a_numero(buscar(SEGUIDORES, desc)),
        "following": a_numero(buscar(SEGUIDOS, desc)),
        "postsCount": a_numero(buscar(PUBLICACIONES, desc)),
        "isPrivate": "This account is private" in html or "Esta cuenta es privada" in html,
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "rawDescription": desc,
    }


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


def main():
    usuario = sys.argv[1] if len(sys.argv) > 1 else USUARIO

    # 1. Cookies: si existe el archivo, se usa; si no, se explica cómo generarlo
    archivo = cookies_loader.encontrar_archivo()
    if archivo is None:
        print("No hay ningún cookies*.json en la carpeta del proyecto.")
        print("Ejecuta: python generar_plantilla.py, llénala y muévela aquí.")
        return
    try:
        cookies = cookies_loader.cargar(archivo)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error en {archivo.name}: {e}")
        return
    print(f"Usando cookies de: {archivo.name}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(locale="en-US")  # idioma fijo: textos predecibles
        context.add_cookies(cookies)                   # <- INYECCIÓN DE COOKIES
        page = context.new_page()

        # 2. Abrir el perfil como lo haría una persona
        page.goto(f"{BASE}/{usuario}/")
        pausa(page)

        if "/accounts/login" in page.url:
            print("Instagram pidió iniciar sesión: las cookies expiraron o son incorrectas.")
            print("Genera otra plantilla (python generar_plantilla.py) y copia cookies actuales.")
            return
        if "this page isn't available" in page.content():
            print(f"El perfil @{usuario} no existe o no está disponible.")
            return

        # 3. Perfil
        perfil = extraer_perfil(page, usuario)

        # 4. Publicaciones
        posts = []
        if perfil["isPrivate"]:
            print("La cuenta es privada y tu cuenta no la sigue: solo se extrae el perfil.")
        else:
            for url in recolectar_urls(page):
                page.goto(url)
                pausa(page)
                post = extraer_post(page, url)
                posts.append(post)
                print(f"[{len(posts)}] {url}  likes={post['likes']}")
        perfil["posts"] = posts

        # 5. Guardar
        OUTPUT_DIR.mkdir(exist_ok=True)
        salida = OUTPUT_DIR / f"{usuario}.json"
        salida.write_text(json.dumps(perfil, indent=2, ensure_ascii=False), encoding="utf-8")

        print("=================================")
        print(f"Perfil:     @{usuario} ({perfil['fullName']})")
        print(f"Biografía:  {perfil['biography']}")
        print(f"Seguidores: {perfil['followers']}")
        print(f"Seguidos:   {perfil['following']}")
        print(f"Posts:      {perfil['postsCount']}")
        print(f"Posts extraídos: {len(posts)}")
        print(f"Guardado en {salida.resolve()}")

        browser.close()


if __name__ == "__main__":
    main()