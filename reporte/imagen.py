"""Genera en el Escritorio una carpeta con la imagen del análisis Big Five."""
import textwrap
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # dibuja sin abrir ventanas
import matplotlib.pyplot as plt

from analisis.big_five import RASGOS
from config import escritorio

COLOR_BARRA = "#3b6ea5"
COLOR_TEXTO = "#222222"
COLOR_SUAVE = "#666666"


def _escribir(fig, y: float, texto: str, ancho: int, tamano: float, **kwargs) -> float:
    """Escribe texto con salto de línea automático y devuelve la nueva posición y."""
    color = kwargs.pop("color", COLOR_TEXTO)
    lineas = textwrap.wrap(texto, ancho) or [""]
    for linea in lineas:
        fig.text(0.07, y, linea, fontsize=tamano, color=color, **kwargs)
        y -= tamano * 0.0021
    return y


def generar_imagen(perfil: dict, resultado: dict) -> Path:
    usuario = perfil["username"]
    carpeta = escritorio() / f"BigFive_{usuario}"
    carpeta.mkdir(exist_ok=True)
    archivo = carpeta / f"bigfive_{usuario}.png"

    fig = plt.figure(figsize=(10, 13), dpi=150)
    fig.patch.set_facecolor("white")

    # --- Encabezado ---
    fig.text(0.07, 0.955, "Análisis de personalidad Big Five (OCEAN)",
             fontsize=20, fontweight="bold", color=COLOR_TEXTO)
    meta = resultado["meta"]
    fig.text(0.07, 0.928, f"{perfil['fullName']} (@{usuario})  ·  {meta['postsAnalizados']} publicaciones "
             f"analizadas  ·  {date.today().strftime('%d/%m/%Y')}", fontsize=11, color=COLOR_SUAVE)

    # --- Gráfico de barras ---
    ax = fig.add_axes([0.33, 0.66, 0.60, 0.24])
    claves = list(RASGOS)[::-1]  # de arriba hacia abajo: O, C, E, A, N
    puntajes = [resultado["rasgos"][c]["puntaje"] for c in claves]
    etiquetas = [f"{RASGOS[c][0]}  {RASGOS[c][1]}" for c in claves]
    barras = ax.barh(etiquetas, puntajes, color=COLOR_BARRA, height=0.55)
    for barra, c in zip(barras, claves):
        r = resultado["rasgos"][c]
        ax.text(barra.get_width() + 1.5, barra.get_y() + barra.get_height() / 2,
                f"{r['puntaje']}  ({r['nivel']})", va="center", fontsize=10, color=COLOR_TEXTO)
    ax.set_xlim(0, 115)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="y", labelsize=11, length=0)
    ax.tick_params(axis="x", labelsize=9, colors=COLOR_SUAVE)
    ax.grid(axis="x", color="#e5e5e5")
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)

    # --- Justificación de cada rasgo ---
    y = 0.615
    for c, (letra, nombre) in RASGOS.items():
        r = resultado["rasgos"][c]
        fig.text(0.07, y, f"{letra} · {nombre}: {r['nivel']}", fontsize=11, fontweight="bold", color=COLOR_TEXTO)
        y = _escribir(fig, y - 0.022, r.get("justificacion", ""), 105, 10, color=COLOR_SUAVE) - 0.012

    # --- Conclusión ---
    y -= 0.01
    fig.add_artist(plt.Line2D([0.07, 0.93], [y + 0.012, y + 0.012], color="#cccccc", linewidth=1))
    fig.text(0.07, y - 0.02, "Conclusión", fontsize=14, fontweight="bold", color=COLOR_TEXTO)
    fig.text(0.07, y - 0.05, f"Tipo de personalidad: {resultado.get('tipo_personalidad', '')}",
             fontsize=13, fontweight="bold", color=COLOR_BARRA)
    y = _escribir(fig, y - 0.078, resultado.get("conclusion", ""), 95, 11)

    # --- Pie de página ---
    y -= 0.015
    y = _escribir(fig, y, f"Confianza del análisis: {resultado.get('confianza', '?')}. "
                          f"{resultado.get('limitaciones', '')}", 115, 9, color=COLOR_SUAVE)
    _escribir(fig, y - 0.004, f"{meta['consentimiento']} Generado con {meta['modelo']} como ejercicio "
                              "académico; es una aproximación, no un diagnóstico psicológico.",
              115, 9, color=COLOR_SUAVE)

    # bbox_inches="tight" agranda la imagen si el texto de Gemini es largo y no cabe
    fig.savefig(archivo, facecolor="white", bbox_inches="tight", pad_inches=0.5)
    plt.close(fig)
    print(f"Imagen guardada en: {archivo}")
    return archivo
