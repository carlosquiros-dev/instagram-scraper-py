"""Datos del perfil: nombre, biografía, seguidores, seguidos y nº de publicaciones."""
import re
from datetime import datetime, timezone

from playwright.sync_api import Page

from scraping.utilidades import NUM, a_numero, buscar, descripcion, meta

# "123 Followers, 45 Following, 67 Posts - See Instagram photos..."
SEGUIDORES = re.compile(NUM + r"\s+(followers|seguidores)", re.I)
SEGUIDOS = re.compile(NUM + r"\s+(following|seguidos)", re.I)
PUBLICACIONES = re.compile(NUM + r"\s+(posts|publicaciones)", re.I)
# Botones del perfil: marcan el fin de la biografía
BOTONES = {"Follow", "Following", "Message", "Seguir", "Siguiendo", "Enviar mensaje"}


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
