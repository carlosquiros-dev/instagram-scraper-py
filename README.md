# Instagram Scraper (Python + Playwright)

Laboratorio de **Arquitectura de Software**: un scraper en **Python** que usa **Playwright** para extraer información de un perfil de Instagram mediante **inyección manual de cookies de sesión**.

> ⚠️ Proyecto con fines exclusivamente académicos. Los términos de uso de Instagram prohíben la recolección automatizada de datos; se usó una cuenta de prueba, un volumen bajo de peticiones con pausas entre acciones, y los datos extraídos no se publican ni se usan con otro fin.

## ¿Qué extrae?

| Dato | Campo |
|---|---|
| Nombre | `fullName` |
| Biografía | `biography` |
| Nº de seguidores | `followers` |
| Nº de seguidos | `following` |
| Nº total de publicaciones | `postsCount` |
| Hasta 50 publicaciones | `posts[]` → `url`, `type` (post/reel), `likes`, `comments`, `date`, `caption` |

## Tecnologías

| Herramienta | Rol |
|---|---|
| **Python 3.10+** | Lenguaje |
| **[Playwright](https://playwright.dev/python/)** | Librería que controla el navegador (el "conductor") |
| **Chromium** | Navegador que carga Instagram y ejecuta su JavaScript (el "motor") |

### ¿Por qué Playwright?

Instagram es una *Single Page Application*: el HTML inicial casi no tiene contenido y los datos se cargan con JavaScript. Un parser de HTML (como BeautifulSoup) vería una página vacía. Playwright, creado por Microsoft en 2020, controla un navegador real, espera automáticamente a que los elementos carguen y permite inyectar cookies con `context.add_cookies()`.

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

> 🔒 Los archivos `cookies*.json` están en `.gitignore`: contienen el `sessionid`, que equivale a la contraseña.

## Arquitectura

Cada módulo tiene una sola responsabilidad:

```
generar_plantilla.py          (manual)                    scraper.py
────────────────────          ────────                    ──────────
Crea en el Escritorio   ──►   Copiar los 5 valores  ──►   usa cookies_loader.py para buscar
cookies1.json, cookies2…      desde DevTools y mover      y validar el cookiesN.json más reciente,
(plantilla vacía)             el archivo al proyecto      inyecta las cookies en Chromium y extrae
```

| Archivo | Responsabilidad | ¿Se ejecuta? |
|---|---|---|
| `generar_plantilla.py` | Crear la plantilla vacía de cookies | Sí, cuando se necesitan cookies nuevas |
| `cookies_loader.py` | Buscar, validar y convertir las cookies al formato de Playwright | No, lo usa `scraper.py` |
| `scraper.py` | Inyectar cookies, navegar y extraer los datos | Sí |

Flujo de `scraper.py`:

1. **Cookies:** carga el `cookiesN.json` de número más alto y lo inyecta (`context.add_cookies`).
2. **Perfil:** abre `instagram.com/<usuario>/` y lee `<meta og:description>` (*"2,589 Followers, 2,516 Following, 349 Posts"*), `og:title` y la cabecera (biografía).
3. **Publicaciones:** hace scroll en la cuadrícula, junta los enlaces `/p/` y `/reel/` y abre cada uno para leer likes, comentarios, fecha y texto.
4. **Ritmo:** pausas aleatorias de 3–5 s entre acciones para no saturar el servidor.
5. **Salida:** guarda `output/<usuario>.json`.

## Estructura

```
instagram-scraper-py/
├── generar_plantilla.py
├── cookies_loader.py
├── scraper.py
├── requirements.txt
├── .gitignore
├── cookiesN.json         # (ignorado) cookies copiadas a mano
└── output/               # (ignorado) datos extraídos
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

## Uso

1. Generar la plantilla:
   ```powershell
   python generar_plantilla.py
   ```
   Se crea `cookies1.json` en el Escritorio:
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
4. Configurar el perfil en `scraper.py` (opcional):
   ```python
   USUARIO = "usuario_a_estudiar"
   MAX_POSTS = 50
   DELAY = 3
   ```
5. Ejecutar:
   ```powershell
   python scraper.py
   ```

### Ejemplo de salida (datos ficticios)

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

## Errores comunes

| Mensaje | Causa | Solución |
|---|---|---|
| `No hay ningún cookies*.json` | Falta el archivo en la carpeta del proyecto | Generar la plantilla, llenarla y moverla |
| `Faltan valores en cookiesN.json` | Alguna cookie quedó vacía | Copiar el valor que falta |
| `las cookies expiraron o son incorrectas` | La sesión fue invalidada | Generar otra plantilla y copiar cookies nuevas |
| `La cuenta es privada` | La cuenta de prueba no sigue al perfil | Solo se extraen los datos del perfil |

## Autor

[@carlosquiros-dev](https://github.com/carlosquiros-dev) — Arquitectura de Software.
