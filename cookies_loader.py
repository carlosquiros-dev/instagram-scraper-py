"""Busca el archivo de cookies en la carpeta del proyecto, lo valida
y lo convierte en cookies que Playwright puede inyectar en el navegador."""
import json
import re
from pathlib import Path

from generar_plantilla import COOKIE_NAMES

PATRON_ARCHIVO = re.compile(r"cookies(\d*)\.json")


def _numero(archivo: Path) -> int:
    m = PATRON_ARCHIVO.fullmatch(archivo.name)
    return int(m.group(1)) if m and m.group(1) else 0


def encontrar_archivo(carpeta: Path = Path(".")) -> Path | None:
    """Devuelve el cookies*.json con el número más alto (el más reciente)."""
    archivos = [p for p in carpeta.iterdir() if PATRON_ARCHIVO.fullmatch(p.name)]
    return max(archivos, key=_numero, default=None)


def cargar(archivo: Path) -> list[dict]:
    """Lee el archivo y arma las cookies. Lanza ValueError si falta alguna."""
    datos = json.loads(archivo.read_text(encoding="utf-8"))

    faltan = [n for n in COOKIE_NAMES if not str(datos.get(n, "")).strip()]
    if faltan:
        raise ValueError(f"Faltan valores en {archivo.name}: {faltan}")

    return [
        {"name": n, "value": str(datos[n]).strip(),
         "domain": ".instagram.com", "path": "/", "secure": True}
        for n in COOKIE_NAMES
    ]