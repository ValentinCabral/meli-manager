"""MELI Manager — Gemini AI Client

Integración con Google Gemini AI gratuita para mejorar la app.
Funcionalidades:
  - Búsqueda inteligente en catálogo MELI (cuando la API falla)
  - Generación de descripciones de productos
  - Optimización de términos de búsqueda
"""

import json
import os
import database as db

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


MODEL_NAME = "gemini-2.0-flash-exp"


def get_api_key() -> str:
    """Obtiene la API key de Gemini desde la DB o variable de entorno."""
    key = db.get_config("gemini_api_key", "")
    if not key:
        key = os.getenv("GEMINI_API_KEY", "")
    return key


def is_available() -> bool:
    """Verifica si Gemini está disponible (módulo + API key)."""
    if not HAS_GEMINI:
        return False
    return bool(get_api_key())


def _get_client():
    """Configura y devuelve el cliente Gemini."""
    if not HAS_GEMINI:
        return None
    key = get_api_key()
    if not key:
        return None
    return genai.Client(api_key=key)


def buscar_catalogo(query: str, max_results: int = 5) -> list:
    """Busca productos en el catálogo de MELI usando Gemini.

    Útil cuando la API de búsqueda de MELI devuelve 403.
    Gemini usa su conocimiento para sugerir productos del catálogo.

    Returns lista de dicts con: title, price_approx, catalog_product_id, permalink
    """
    client = _get_client()
    if not client:
        return []

    prompt = f"""Sos un asistente que conoce el catálogo de MercadoLibre Argentina.

Buscá el producto: "{query}"

Devolvé SOLO un JSON con una lista de hasta {max_results} productos del catálogo
de MercadoLibre que coincidan. Para CADA producto incluí:
- title: nombre exacto del producto en MELI
- price_approx: precio aproximado actual (número, sin símbolo)
- catalog_product_id: el catalog_product_id real de MELI (como "MLAXXXXXXX")
- permalink: URL completa de la publicación en MELI
- reason: por qué coincide con la búsqueda

SOLO devolví el JSON, sin markdown ni explicaciones adicionales.
Formato:
{{"results": [{{"title": "...", "price_approx": 12345, "catalog_product_id": "MLA...", "permalink": "https://www.mercadolibre.com.ar/...", "reason": "..."}}]}}

Si no encontrás nada en tu conocimiento, devolvé {{"results": []}}.
"""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        text = response.text.strip()
        # Limpiar posibles marcadores markdown
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text
            if "```" in text:
                text = text.split("```")[0]
        data = json.loads(text)
        return data.get("results", [])
    except Exception as e:
        print(f"  [Gemini] Error en buscar_catalogo: {e}")
        return []


def generar_descripcion(nombre: str, marca: str = "", modelo: str = "",
                        color: str = "", categoria: str = "Celulares") -> str:
    """Genera una descripción para un producto usando Gemini."""
    client = _get_client()
    if not client:
        return ""

    specs = []
    if marca:
        specs.append(f"Marca: {marca}")
    if modelo:
        specs.append(f"Modelo: {modelo}")
    if color:
        specs.append(f"Color: {color}")
    specs_str = "\n".join(specs) if specs else "Sin especificaciones adicionales"

    prompt = f"""Sos un experto en redacción de descripciones para MercadoLibre Argentina.

Producto: {nombre}
Categoría: {categoria}
Especificaciones:
{specs_str}

Escribí una descripción atractiva y profesional para la publicación en MercadoLibre.
La descripción debe:
- Ser en español argentino
- Entre 100 y 200 palabras
- Destacar las características principales
- Incluir beneficios para el comprador
- NO incluir precios, promociones ni datos de envío
- Ser apta para catalog_listing

Devolvé SOLO la descripción, sin ningún otro texto.
"""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"  [Gemini] Error en generar_descripcion: {e}")
        return ""


def mejorar_query(query: str) -> str:
    """Mejora el término de búsqueda para encontrar mejores resultados en MELI."""
    client = _get_client()
    if not client:
        return query

    prompt = f"""Optimizá esta búsqueda para encontrar el producto exacto en MercadoLibre Argentina.
Eliminá palabras irrelevantes, corregí ortografía, usá términos de catálogo de MELI.

Búsqueda original: "{query}"

Devolvé SOLO el término de búsqueda optimizado (máximo 10 palabras), sin explicaciones.
"""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        result = response.text.strip()
        return result.strip('"\' \n\r')
    except Exception:
        return query
