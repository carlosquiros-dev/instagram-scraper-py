"""Funciones pequeñas que usan perfil.py y publicaciones.py."""
import random
import re

from playwright.sync_api import Page

from config import DELAY

# Número como aparece en Instagram: "1,234", "1.2K", "3M"
NUM = r"([\d.,]+[KkMm]?)"


def pausa(page: Page):
    """Pausa variable (3-5 s), como una persona que no hace clic cada X segundos exactos."""
    page.wait_for_timeout((DELAY + random.uniform(0, 2)) * 1000)


def meta(page: Page, selector: str) -> str:
    """Lee el atributo content de una etiqueta <meta>."""
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
