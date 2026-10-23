"""Punto de entrada del proyecto.

  python main.py plantilla   -> crea cookiesN.json en el Escritorio
  python main.py scrapear    -> extrae el perfil y guarda output/<usuario>.json
  python main.py analizar    -> Big Five con Gemini + imagen (usa el JSON ya extraído)
  python main.py imagen      -> rehace solo la imagen con el último análisis (0 tokens)
  python main.py             -> scrapear + analizar
"""
import argparse
import json

from config import OUTPUT_DIR, USUARIO


def analizar_y_reportar(usuario: str):
    # Se importa aquí para que "plantilla" y "scrapear" no necesiten Gemini ni matplotlib
    from analisis.big_five import analizar
    from reporte.imagen import generar_imagen

    entrada = OUTPUT_DIR / f"{usuario}.json"
    if not entrada.exists():
        print(f"No existe {entrada}. Ejecuta primero: python main.py scrapear")
        return
    perfil = json.loads(entrada.read_text(encoding="utf-8"))
    try:
        resultado = analizar(perfil)
    except Exception as e:
        print(f"Error en el análisis: {e}")
        return
    generar_imagen(perfil, resultado)


def solo_imagen(usuario: str):
    """Vuelve a dibujar la imagen con el análisis guardado, sin llamar a Gemini."""
    from reporte.imagen import generar_imagen

    perfil_json = OUTPUT_DIR / f"{usuario}.json"
    analisis_json = OUTPUT_DIR / f"{usuario}_bigfive.json"
    if not analisis_json.exists():
        print(f"No existe {analisis_json}. Ejecuta primero: python main.py analizar")
        return
    generar_imagen(json.loads(perfil_json.read_text(encoding="utf-8")),
                   json.loads(analisis_json.read_text(encoding="utf-8")))


def main():
    parser = argparse.ArgumentParser(description="Scraper de Instagram + análisis Big Five")
    parser.add_argument("accion", nargs="?", default="todo",
                        choices=["plantilla", "scrapear", "analizar", "imagen", "todo"])
    parser.add_argument("--usuario", default=USUARIO, help="perfil a estudiar (sin @)")
    args = parser.parse_args()

    if args.accion == "plantilla":
        from cookies.generar_plantilla import generar
        generar()
        return

    if args.accion == "imagen":
        solo_imagen(args.usuario)
        return

    if args.accion in ("scrapear", "todo"):
        from scraping.scraper import scrapear
        if scrapear(args.usuario) is None:
            return

    if args.accion in ("analizar", "todo"):
        analizar_y_reportar(args.usuario)


if __name__ == "__main__":
    main()
