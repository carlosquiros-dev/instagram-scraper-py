"""Conexión con la API de Gemini. La clave se lee del archivo .env (nunca del código)."""
import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from config import MODELO_GEMINI

REINTENTOS = 4


def crear_cliente() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el archivo .env")
    return genai.Client(api_key=api_key)


def _generar(client: genai.Client, prompt: str):
    """Llama a Gemini; si el servidor está saturado (429/500/503) espera y reintenta."""
    for intento in range(REINTENTOS + 1):
        try:
            return client.models.generate_content(
                model=MODELO_GEMINI,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",  # obliga a responder en JSON
                    temperature=0.2,                        # respuestas más consistentes
                ),
            )
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or intento == REINTENTOS:
                raise
            espera = 10 * 2 ** intento  # 10 s, 20 s, 40 s, 80 s
            print(f"Gemini respondió {e.code} (saturado). Reintento {intento + 1}/{REINTENTOS} en {espera} s...")
            time.sleep(espera)


def pedir_json(client: genai.Client, prompt: str) -> tuple[dict, dict]:
    """Envía el prompt y devuelve (respuesta como dict, tokens usados)."""
    respuesta = _generar(client, prompt)
    uso = respuesta.usage_metadata
    tokens = {
        "entrada": getattr(uso, "prompt_token_count", 0) or 0,
        "salida": getattr(uso, "candidates_token_count", 0) or 0,
    }
    return json.loads(respuesta.text), tokens
