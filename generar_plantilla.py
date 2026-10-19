"""Crea en el Escritorio una plantilla vacía cookies1.json, cookies2.json, ...
para copiar a mano las cookies desde DevTools."""
import json
from pathlib import Path

# Las 5 cookies de sesión de Instagram
COOKIE_NAMES = ["sessionid", "csrftoken", "ds_user_id", "ig_did", "mid"]


def encontrar_escritorio() -> Path:
    home = Path.home()
    for carpeta in [home / "Desktop", home / "OneDrive" / "Desktop",
                    home / "Escritorio", home / "OneDrive" / "Escritorio"]:
        if carpeta.is_dir():
            return carpeta
    return home


def main():
    escritorio = encontrar_escritorio()

    # Siguiente número libre: cookies1.json, cookies2.json, ...
    n = 1
    while (escritorio / f"cookies{n}.json").exists() or Path(f"cookies{n}.json").exists():
        n += 1
    archivo = escritorio / f"cookies{n}.json"

    plantilla = {nombre: "" for nombre in COOKIE_NAMES}
    archivo.write_text(json.dumps(plantilla, indent=2), encoding="utf-8")

    print(f"Plantilla creada en: {archivo}")
    print("\nPasos:")
    print(" 1. Abre Instagram en el navegador con tu cuenta de prueba.")
    print(" 2. F12 -> Application -> Cookies -> https://www.instagram.com")
    print(' 3. Copia el Value de cada cookie entre las comillas "" del archivo.')
    print(f" 4. Mueve cookies{n}.json a la carpeta del proyecto: {Path.cwd()}")
    print(" 5. Ejecuta: python scraper.py")


if __name__ == "__main__":
    main()