"""Análisis de personalidad Big Five (OCEAN) a partir de las publicaciones extraídas."""
import json
from datetime import datetime, timezone

from analisis.gemini_client import crear_cliente, pedir_json
from config import CONSENTIMIENTO, MODELO_GEMINI, N_POSTS_ANALISIS, OUTPUT_DIR

# clave en el JSON -> (letra OCEAN, nombre en español)
RASGOS = {
    "apertura": ("O", "Apertura a la experiencia"),
    "responsabilidad": ("C", "Responsabilidad"),
    "extraversion": ("E", "Extraversión"),
    "amabilidad": ("A", "Amabilidad"),
    "neuroticismo": ("N", "Neuroticismo"),
}


def preparar_posts(perfil: dict, n: int) -> list[dict]:
    """Las n publicaciones más recientes con texto, solo con los campos útiles."""
    con_texto = [p for p in perfil["posts"] if p.get("caption")]
    return [
        {"fecha": p["date"], "tipo": p["type"], "likes": p["likes"],
         "comentarios": p["comments"], "texto": p["caption"]}
        for p in con_texto[:n]
    ]


def construir_prompt(perfil: dict, posts: list[dict]) -> str:
    return f"""Eres un psicólogo experto en el modelo de personalidad Big Five (OCEAN).
Analiza la personalidad que proyecta públicamente este perfil de Instagram,
basándote ÚNICAMENTE en la información dada. Es un ejercicio académico autorizado
por la titular de la cuenta: una aproximación, no un diagnóstico clínico.

PERFIL
- Nombre: {perfil["fullName"]}
- Biografía: {perfil["biography"]}
- Seguidores: {perfil["followers"]} | Seguidos: {perfil["following"]} | Publicaciones: {perfil["postsCount"]}

ÚLTIMAS {len(posts)} PUBLICACIONES
{json.dumps(posts, ensure_ascii=False, indent=2)}

Responde SOLO con un JSON con esta estructura:
{{
  "rasgos": {{
    "<rasgo>": {{
      "puntaje": <entero de 0 a 100>,
      "nivel": "bajo" | "medio" | "alto",
      "justificacion": "<1-2 frases basadas en las publicaciones>"
    }}
  }},
  "tipo_personalidad": "<etiqueta corta, máximo 6 palabras>",
  "conclusion": "<2-3 frases que expliquen el tipo de personalidad>",
  "confianza": "baja" | "media" | "alta",
  "limitaciones": "<1 frase sobre por qué puede no ser exacto>"
}}
Los rasgos deben ser exactamente: {", ".join(RASGOS)}."""


def validar(resultado: dict) -> dict:
    """Asegura que estén los 5 rasgos y que los puntajes estén entre 0 y 100."""
    rasgos = resultado.get("rasgos", {})
    faltan = [r for r in RASGOS if r not in rasgos]
    if faltan:
        raise ValueError(f"Gemini no devolvió estos rasgos: {faltan}")
    for r in RASGOS:
        rasgos[r]["puntaje"] = max(0, min(100, int(rasgos[r].get("puntaje", 0))))
    return resultado


def analizar(perfil: dict) -> dict:
    """Envía las publicaciones a Gemini y guarda output/<usuario>_bigfive.json."""
    posts = preparar_posts(perfil, N_POSTS_ANALISIS)
    if not posts:
        raise ValueError("No hay publicaciones con texto para analizar.")
    print(f"Analizando @{perfil['username']} con {len(posts)} publicaciones usando {MODELO_GEMINI}...")

    resultado, tokens = pedir_json(crear_cliente(), construir_prompt(perfil, posts))
    resultado = validar(resultado)
    resultado["meta"] = {
        "usuario": perfil["username"],
        "modelo": MODELO_GEMINI,
        "postsAnalizados": len(posts),
        "tokens": tokens,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "consentimiento": CONSENTIMIENTO,
    }

    salida = OUTPUT_DIR / f"{perfil['username']}_bigfive.json"
    salida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")

    for clave, (letra, nombre) in RASGOS.items():
        r = resultado["rasgos"][clave]
        print(f"  {letra} {nombre:<27} {r['puntaje']:>3}/100 ({r['nivel']})")
    print(f"Tipo de personalidad: {resultado.get('tipo_personalidad', '')}")
    print(f"Tokens usados: {tokens['entrada']} entrada + {tokens['salida']} salida")
    return resultado
