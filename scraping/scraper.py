"""Orquesta el scraping: cookies -> navegador -> perfil -> publicaciones -> JSON."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import BASE, HEADLESS, OUTPUT_DIR
from cookies import cookies_loader
from scraping.perfil import extraer_perfil
from scraping.publicaciones import extraer_publicaciones
from scraping.utilidades import pausa


def scrapear(usuario: str) -> Path | None:
    """Extrae el perfil y guarda output/<usuario>.json. Devuelve la ruta o None si falla."""
    # 1. Cookies: si existe el archivo, se usa; si no, se explica cómo generarlo
    archivo = cookies_loader.encontrar_archivo()
    if archivo is None:
        print("No hay ningún cookies*.json en la carpeta del proyecto.")
        print("Ejecuta: python main.py plantilla, llénala y muévela aquí.")
        return None
    try:
        cookies = cookies_loader.cargar(archivo)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error en {archivo.name}: {e}")
        return None
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
            print("Genera otra plantilla (python main.py plantilla) y copia cookies actuales.")
            return None
        if "this page isn't available" in page.content():
            print(f"El perfil @{usuario} no existe o no está disponible.")
            return None

        # 3. Perfil y 4. publicaciones
        perfil = extraer_perfil(page, usuario)
        if perfil["isPrivate"]:
            print("La cuenta es privada y tu cuenta no la sigue: solo se extrae el perfil.")
            perfil["posts"] = []
        else:
            perfil["posts"] = extraer_publicaciones(page)
        browser.close()

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
    print(f"Posts extraídos: {len(perfil['posts'])}")
    print(f"Guardado en {salida.resolve()}")
    return salida
