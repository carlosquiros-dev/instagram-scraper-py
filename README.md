# Instagram Scraper + Big Five (Python + Playwright + Gemini)

Laboratorio de **Arquitectura de Software**: un sistema en **Python** que
1. extrae información de un perfil de Instagram con **Playwright** mediante **inyección manual de cookies de sesión**, y
2. analiza la personalidad que proyecta el perfil con el modelo **Big Five (OCEAN)** usando la API de **Gemini**, generando una imagen con el resultado.

> ⚠️ Proyecto con fines exclusivamente académicos. Los términos de uso de Instagram prohíben la recolección automatizada de datos; se usó una cuenta de prueba, un volumen bajo de peticiones con pausas entre acciones, y los datos extraídos no se publican ni se usan con otro fin. El análisis de personalidad se realizó **con autorización de la titular de la cuenta** y es una aproximación, no un diagnóstico psicológico.

## ¿Qué hace?

**Scraping** (`output/<usuario>.json`):

| Dato | Campo |
|---|---|
| Nombre | `fullName` |
| Biografía | `biography` |
| Nº de seguidores / seguidos | `followers` / `following` |
| Nº total de publicaciones | `postsCount` |
| Hasta 50 publicaciones | `posts[]` → `url`, `type` (post/reel), `likes`, `comments`, `date`, `caption` |

**Análisis Big Five** (`output/<usuario>_bigfive.json` + imagen en el Escritorio):

| Letra | Rasgo | Mide |
|---|---|---|
| **O** | Apertura a la experiencia | Curiosidad, interés por ideas nuevas |
| **C** | Responsabilidad | Organización, disciplina |
| **E** | Extraversión | Sociabilidad, energía social |
| **A** | Amabilidad | Empatía, cooperación |
| **N** | Neuroticismo | Inestabilidad emocional |

Cada rasgo recibe un puntaje de 0 a 100, un nivel (bajo/medio/alto) y una justificación, además de un **tipo de personalidad** y una conclusión.

## Tecnologías

| Herramienta | Rol |
|---|---|
| **Python 3.10+** | Lenguaje |
| **[Playwright](https://playwright.dev/python/)** | Controla el navegador (el "conductor") |
| **Chromium** | Navegador que carga Instagram y ejecuta su JavaScript (el "motor") |
| **Gemini 3.8 Flash** (`google-genai`) | Modelo de IA que realiza el análisis Big Five |
| **python-dotenv** | Lee la API key desde `.env` sin escribirla en el código |
| **matplotlib** | Dibuja la imagen del resultado |

### ¿Por qué Playwright?

Instagram es una *Single Page Application*: el HTML inicial casi no tiene contenido y los datos se cargan con JavaScript. Un parser de HTML (como BeautifulSoup) vería una página vacía. Playwright controla un navegador real, espera automáticamente a que los elementos carguen y permite inyectar cookies con `context.add_cookies()`.

## Cookies e inyección de sesión

HTTP no tiene estado: cada petición es independiente. Al iniciar sesión, Instagram responde con `Set-Cookie: sessionid=...` y el navegador reenvía esa cookie en cada petición; así el servidor sabe quién es el usuario (como el brazalete de un concierto).

En este laboratorio las cookies se **copian a mano** desde DevTools y se **inyectan** en Chromium, sin automatizar el inicio de sesión:

| Cookie | Función |
|---|---|
| `sessionid` | Identifica la sesión iniciada. Quien la tenga entra a la cuenta sin contraseña |
| `csrftoken` | Token anti-CSRF: evita que otra web haga acciones en nombre del usuario |
| `ds_user_id` | ID numérico de la cuenta |
| `ig_did` | Identificador del dispositivo/navegador |
| `mid` | Identificador de la máquina, asignado en la primera visita |

Una sesión deja de ser válida al **cerrar sesión**, **cambiar la contraseña**, cuando **caduca** o si Instagram la invalida. Cerrar el navegador **no** la invalida.

> 🔒 `cookies*.json` y `.env` están en `.gitignore`: contienen el `sessionid` y la API key, que equivalen a contraseñas.

## Arquitectura

El proyecto está dividido en paquetes, cada uno con **una sola responsabilidad**. `main.py` es el único que decide en qué orden se ejecutan.

```
                       main.py  (punto de entrada)
                          │
     ┌────────────────────┼─────────────────────┬──────────────────┐
     ▼                    ▼                     ▼                  ▼
  cookies/            scraping/             analisis/          reporte/
  plantilla y         Chromium + datos      Gemini + OCEAN     imagen PNG
  carga de cookies    de Instagram
     └────────────────────┴───────── config.py ─┴──────────────────┘
```

Flujo de datos (cada etapa guarda su resultado y la siguiente lo lee):

```
cookies1.json → [cookies] → [scraping] → output/<usuario>.json
                                               → [analisis] → output/<usuario>_bigfive.json
                                                                   → [reporte] → Escritorio/BigFive_<usuario>/*.png
```

Gracias a esto cada etapa se puede ejecutar por separado: analizar no obliga a volver a scrapear, y rehacer la imagen no gasta tokens.

### Detalle de cada módulo

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Lee el comando de la terminal (`argparse`) y ejecuta las etapas en orden |
| `config.py` | Todos los ajustes: usuario, nº de posts, pausas, modelo de Gemini, rutas |
| `cookies/generar_plantilla.py` | Crea la plantilla vacía `cookiesN.json` en el Escritorio |
| `cookies/cookies_loader.py` | Busca el `cookiesN.json` más reciente, valida que no falte ninguna cookie y la convierte al formato de Playwright |
| `scraping/scraper.py` | Orquesta el scraping: inyecta las cookies, abre el perfil, comprueba la sesión y guarda el JSON |
| `scraping/perfil.py` | Nombre, biografía y contadores (desde `<meta og:description>`, `og:title` y la cabecera) |
| `scraping/publicaciones.py` | Scroll en la cuadrícula, enlaces `/p/` y `/reel/`, y datos de cada publicación |
| `scraping/utilidades.py` | Pausa aleatoria (3–5 s), lectura de `<meta>` y conversión de números (`"1.2K"` → 1200) |
| `analisis/gemini_client.py` | Conexión con Gemini (API key desde `.env`), respuesta forzada en JSON y reintentos ante errores 429/500/503 |
| `analisis/big_five.py` | Prepara los 10 posts, arma el prompt, valida los 5 rasgos y guarda el resultado |
| `reporte/imagen.py` | Dibuja el gráfico de barras OCEAN, las justificaciones y la conclusión |

## Estructura

```
instagram-scraper-py/
├── main.py
├── config.py
├── cookies/
│   ├── generar_plantilla.py
│   └── cookies_loader.py
├── scraping/
│   ├── scraper.py
│   ├── perfil.py
│   ├── publicaciones.py
│   └── utilidades.py
├── analisis/
│   ├── gemini_client.py
│   └── big_five.py
├── reporte/
│   └── imagen.py
├── requirements.txt
├── .gitignore
├── .env                  # (ignorado) GEMINI_API_KEY
├── cookiesN.json         # (ignorado) cookies copiadas a mano
└── output/               # (ignorado) datos extraídos y análisis
```

## Instalación

```powershell
git clone https://github.com/carlosquiros-dev/instagram-scraper-py.git
cd instagram-scraper-py
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

Crear un archivo `.env` en la raíz con la API key de Gemini ([Google AI Studio](https://aistudio.google.com/)):

```
GEMINI_API_KEY=tu_clave
```

## Uso

| Comando | Qué hace |
|---|---|
| `python main.py plantilla` | Crea `cookiesN.json` en el Escritorio |
| `python main.py scrapear` | Extrae el perfil → `output/<usuario>.json` |
| `python main.py analizar` | Big Five con Gemini + imagen (usa el JSON ya extraído) |
| `python main.py imagen` | Rehace solo la imagen con el último análisis (0 tokens) |
| `python main.py` | Scrapear + analizar |

Para otro perfil: `python main.py scrapear --usuario otro_usuario`.

Pasos la primera vez:

1. `python main.py plantilla` → se crea `cookies1.json` en el Escritorio:
   ```json
   {
     "sessionid": "",
     "csrftoken": "",
     "ds_user_id": "",
     "ig_did": "",
     "mid": ""
   }
   ```
2. Iniciar sesión en Instagram en el navegador, abrir **F12 → Application → Cookies → https://www.instagram.com** y copiar el *Value* de cada cookie entre las comillas.
3. Mover el archivo a la carpeta del proyecto.
4. Ajustar `config.py` si hace falta:
   ```python
   USUARIO = "usuario_a_estudiar"
   MAX_POSTS = 50
   N_POSTS_ANALISIS = 10
   MODELO_GEMINI = "gemini-3.8-flash"
   ```
5. `python main.py`

### Ejemplo de salida del scraping (datos ficticios)

```json
{
  "username": "usuario_ejemplo",
  "fullName": "Usuario Ejemplo",
  "biography": "Texto de la biografía",
  "followers": 1234,
  "following": 321,
  "postsCount": 87,
  "isPrivate": false,
  "posts": [
    {
      "url": "https://www.instagram.com/p/ABC123xyz/",
      "type": "post",
      "likes": 150,
      "comments": 12,
      "date": "2026-05-10T18:30:00.000Z",
      "caption": "Texto de la publicación"
    }
  ]
}
```

### Ejemplo de salida del análisis (datos ficticios)

```json
{
  "rasgos": {
    "apertura": { "puntaje": 78, "nivel": "alto", "justificacion": "..." },
    "responsabilidad": { "puntaje": 82, "nivel": "alto", "justificacion": "..." },
    "extraversion": { "puntaje": 74, "nivel": "alto", "justificacion": "..." },
    "amabilidad": { "puntaje": 65, "nivel": "medio", "justificacion": "..." },
    "neuroticismo": { "puntaje": 20, "nivel": "bajo", "justificacion": "..." }
  },
  "tipo_personalidad": "Extrovertida, organizada y abierta",
  "conclusion": "...",
  "confianza": "media",
  "meta": { "modelo": "gemini-3.8-flash", "postsAnalizados": 10, "tokens": { "entrada": 1724, "salida": 478 } }
}
```

## Uso de la API de Gemini

- Se envían solo **10 publicaciones** en **una sola llamada**: cada análisis usa unos 2.200 tokens.
- El plan gratuito tiene un límite de **solicitudes por día** (se reinicia diariamente); se consulta en Google AI Studio → *Límite de frecuencia*.
- Si Gemini responde **429, 500 o 503** (saturado), el programa reintenta automáticamente con espera exponencial (10, 20, 40 y 80 s).

## Errores comunes

| Mensaje | Causa | Solución |
|---|---|---|
| `No hay ningún cookies*.json` | Falta el archivo en la carpeta del proyecto | `python main.py plantilla`, llenarla y moverla |
| `Faltan valores en cookiesN.json` | Alguna cookie quedó vacía | Copiar el valor que falta |
| `las cookies expiraron o son incorrectas` | La sesión fue invalidada | Generar otra plantilla y copiar cookies nuevas |
| `La cuenta es privada` | La cuenta de prueba no sigue al perfil | Solo se extraen los datos del perfil |
| `Falta GEMINI_API_KEY en el archivo .env` | No existe `.env` o el nombre está mal | Crear `.env` con `GEMINI_API_KEY=tu_clave` |
| `404 NOT_FOUND` (Gemini) | El modelo ya no está disponible | Cambiar `MODELO_GEMINI` en `config.py` |
| `503 UNAVAILABLE` (Gemini) | Modelo saturado | Se reintenta solo; si persiste, esperar unos minutos |

## Autor

[@carlosquiros-dev](https://github.com/carlosquiros-dev) — Arquitectura de Software.
