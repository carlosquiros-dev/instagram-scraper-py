"""Configuración general del proyecto: todo lo que se puede cambiar está aquí."""
from pathlib import Path

# --- Scraping ---
USUARIO = "alondra_cgp"   # perfil a estudiar (sin @)
MAX_POSTS = 50            # tope de publicaciones a extraer
DELAY = 3                 # pausa base entre acciones (segundos)
HEADLESS = False          # False = ves el navegador trabajando

# --- Análisis Big Five ---
N_POSTS_ANALISIS = 10              # pocas publicaciones = pocos tokens
MODELO_GEMINI = "gemini-3.8-flash"  # modelo rápido y barato de Gemini
CONSENTIMIENTO = "Análisis realizado con autorización de la titular de la cuenta."

# --- Rutas ---
BASE = "https://www.instagram.com"
OUTPUT_DIR = Path("output")


def escritorio() -> Path:
    """Devuelve la carpeta del Escritorio (con o sin OneDrive, en inglés o español)."""
    home = Path.home()
    for carpeta in [home / "Desktop", home / "OneDrive" / "Desktop",
                    home / "Escritorio", home / "OneDrive" / "Escritorio"]:
        if carpeta.is_dir():
            return carpeta
    return home
