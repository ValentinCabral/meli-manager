"""MELI Manager — MercadoLibre API Client (Multi-Cuenta + OAuth)"""

import requests
import time
from urllib.parse import urlencode
from config import ML_CLIENT_ID, ML_CLIENT_SECRET, ML_SITE_ID


class MeliClient:
    """Cliente multi-cuenta para la API de MercadoLibre.

    Ya no lee credenciales de config globalmente. Cada instancia
    recibe las credenciales de la cuenta a la que pertenece.
    """

    BASE_URL = "https://api.mercadolibre.com"
    AUTH_URL = "https://api.mercadolibre.com/oauth/token"
    AUTH_AUTHORIZE = "https://auth.mercadolibre.com.ar/authorization"

    def __init__(self, client_id=None, client_secret=None, refresh_token=None,
                 site_id=None):
        self.client_id = client_id or ML_CLIENT_ID
        self.client_secret = client_secret or ML_CLIENT_SECRET
        self.refresh_token = refresh_token
        self.site_id = site_id or ML_SITE_ID
        self.access_token = None
        self.token_expires_at = 0
        self.user_id = None
        self.user_nickname = None

    # ─── OAuth Flow ──────────────────────────────────────────

    @classmethod
    def get_auth_url(cls, redirect_uri: str, state: str = "") -> str:
        """Genera la URL de autorización de MELI para el OAuth flow."""
        params = {
            "response_type": "code",
            "client_id": ML_CLIENT_ID,
            "redirect_uri": redirect_uri,
        }
        if state:
            params["state"] = state
        return f"{cls.AUTH_AUTHORIZE}?{urlencode(params)}"

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str) -> dict:
        """Intercambia un authorization code por access+refresh tokens.

        Returns:
            dict con access_token, refresh_token, user_id, nickname, o error.
        """
        payload = {
            "grant_type": "authorization_code",
            "client_id": ML_CLIENT_ID,
            "client_secret": ML_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        try:
            resp = requests.post(cls.AUTH_URL, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Obtener nickname del usuario
            access_token = data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            me = requests.get(f"{cls.BASE_URL}/users/me", headers=headers, timeout=10)
            me_data = me.json() if me.ok else {}

            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": data.get("refresh_token", ""),
                "expires_in": data.get("expires_in", 21600),
                "user_id": str(me_data.get("id", "")),
                "nickname": me_data.get("nickname", ""),
                "email": me_data.get("email", ""),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_credentials(self, refresh_token: str, access_token: str = None,
                        client_id: str = None, client_secret: str = None):
        """Cambia las credenciales de esta instancia (para switchear cuenta)."""
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.token_expires_at = 0  # forzar refresh si es necesario
        if client_id:
            self.client_id = client_id
        if client_secret:
            self.client_secret = client_secret

    def _refresh_access_token(self):
        """Obtiene un nuevo access_token usando el refresh_token."""
        if not self.refresh_token:
            raise ValueError("No hay refresh_token para esta cuenta")

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        resp = requests.post(self.AUTH_URL, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        if data.get("refresh_token"):
            self.refresh_token = data["refresh_token"]
        self.token_expires_at = time.time() + data.get("expires_in", 21600) - 300
        return self.access_token

    def _ensure_token(self):
        """Asegura tener un token válido."""
        if not self.access_token or time.time() >= self.token_expires_at:
            self._refresh_access_token()

    def _headers(self):
        self._ensure_token()
        return {"Authorization": f"Bearer {self.access_token}"}

    # ─── Conexión ───────────────────────────────────────────

    def check_connection(self) -> dict:
        """Verifica la conexión con la API de MELI y actualiza user info."""
        try:
            self._ensure_token()
            resp = requests.get(f"{self.BASE_URL}/users/me",
                                headers=self._headers(), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            self.user_id = data["id"]
            self.user_nickname = data["nickname"]
            return {
                "connected": True,
                "user_id": data["id"],
                "nickname": data["nickname"],
                "email": data.get("email", ""),
                "refresh_token": self.refresh_token,
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    # ─── Productos / Catálogo ───────────────────────────────

    def buscar_catalogo(self, query: str, limit: int = 10) -> list:
        """Busca productos en el catálogo de MELI."""
        self._ensure_token()
        url = f"{self.BASE_URL}/sites/{self.site_id}/search"
        params = {"q": query, "limit": limit, "catalog_listing": "true"}
        resp = requests.get(url, headers=self._headers(), params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        productos = []
        for r in data.get("results", []):
            productos.append({
                "id": r["id"],
                "title": r["title"],
                "price": r.get("price", 0),
                "catalog_product_id": r.get("catalog_product_id", ""),
                "thumbnail": r.get("thumbnail", ""),
                "permalink": r.get("permalink", ""),
            })
        return productos

    def get_catalog_product(self, product_id: str) -> dict:
        """Obtiene información de un producto de catálogo."""
        self._ensure_token()
        resp = requests.get(f"{self.BASE_URL}/products/{product_id}",
                            headers=self._headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        pics = [p["url"] for p in data.get("pictures", [])]
        attrs = {}
        for a in data.get("attributes", []):
            attrs[a["id"]] = a.get("value_name", "")
        return {
            "id": data["id"],
            "name": data["name"],
            "pictures": pics,
            "attributes": attrs,
        }

    # ─── Publicaciones ──────────────────────────────────────

    def crear_publicacion(self, catalog_product_id: str, price: float,
                          listing_type: str = "gold_special",
                          campaign_tag: str = "",
                          stock: int = 1,
                          category_id: str = "MLA1055",
                          family_name: str = "") -> dict:
        """Crea una publicación en MercadoLibre como catalog_listing."""
        datos = {
            "category_id": category_id,
            "price": price,
            "currency_id": "ARS",
            "available_quantity": stock,
            "buying_mode": "buy_it_now",
            "listing_type_id": listing_type,
            "condition": "new",
            "catalog_product_id": catalog_product_id,
            "catalog_listing": True,
            "pictures": [],
            "attributes": [
                {"id": "CARRIER", "value_name": "Liberado"},
                {"id": "ITEM_CONDITION", "value_name": "Nuevo"},
            ],
            "tags": ["immediate_payment"],
            "shipping": {
                "mode": "me2",
                "free_shipping": True,
            },
        }

        if family_name:
            datos["family_name"] = family_name

        if campaign_tag:
            datos["tags"].append(campaign_tag)

        self._ensure_token()
        resp = requests.post(f"{self.BASE_URL}/items",
                             headers={**self._headers(), "Content-Type": "application/json"},
                             json=datos, timeout=30)
        try:
            resp.raise_for_status()
            data = resp.json()
            return {
                "success": True,
                "item_id": data["id"],
                "title": data.get("title", ""),
                "price": data.get("price", price),
                "status": data.get("status", ""),
                "permalink": data.get("permalink", ""),
            }
        except requests.HTTPError:
            return {"success": False, "error": resp.text, "status_code": resp.status_code}

    def get_publicacion(self, item_id: str) -> dict:
        """Obtiene información de una publicación existente."""
        self._ensure_token()
        resp = requests.get(f"{self.BASE_URL}/items/{item_id}",
                            headers=self._headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            "id": data["id"],
            "title": data.get("title", ""),
            "price": data.get("price", 0),
            "status": data.get("status", ""),
            "listing_type": data.get("listing_type_id", ""),
            "available_quantity": data.get("available_quantity", 0),
            "sold_quantity": data.get("sold_quantity", 0),
            "permalink": data.get("permalink", ""),
            "tags": data.get("tags", []),
            "catalog_listing": data.get("catalog_listing", False),
        }

    def actualizar_precio(self, item_id: str, price: float) -> dict:
        """Actualiza el precio de una publicación."""
        self._ensure_token()
        resp = requests.put(f"{self.BASE_URL}/items/{item_id}",
                            headers={**self._headers(), "Content-Type": "application/json"},
                            json={"price": price}, timeout=15)
        try:
            resp.raise_for_status()
            return {"success": True, "item_id": item_id, "price": price}
        except requests.HTTPError:
            return {"success": False, "error": resp.text}

    def actualizar_stock(self, item_id: str, stock: int) -> dict:
        """Actualiza el stock de una publicación."""
        self._ensure_token()
        resp = requests.put(f"{self.BASE_URL}/items/{item_id}",
                            headers={**self._headers(), "Content-Type": "application/json"},
                            json={"available_quantity": stock}, timeout=15)
        try:
            resp.raise_for_status()
            return {"success": True, "item_id": item_id, "stock": stock}
        except requests.HTTPError:
            return {"success": False, "error": resp.text}

    def pausar_publicacion(self, item_id: str) -> dict:
        """Pausa una publicación."""
        self._ensure_token()
        resp = requests.put(f"{self.BASE_URL}/items/{item_id}",
                            headers={**self._headers(), "Content-Type": "application/json"},
                            json={"status": "paused"}, timeout=15)
        try:
            resp.raise_for_status()
            return {"success": True, "item_id": item_id, "status": "paused"}
        except requests.HTTPError:
            return {"success": False, "error": resp.text}

    def activar_publicacion(self, item_id: str) -> dict:
        """Activa una publicación pausada."""
        self._ensure_token()
        resp = requests.put(f"{self.BASE_URL}/items/{item_id}",
                            headers={**self._headers(), "Content-Type": "application/json"},
                            json={"status": "active"}, timeout=15)
        try:
            resp.raise_for_status()
            return {"success": True, "item_id": item_id, "status": "active"}
        except requests.HTTPError:
            return {"success": False, "error": resp.text}

    # ─── Precios / Comisiones ───────────────────────────────

    def get_listing_prices(self, price: float, listing_type: str,
                           campaign_tag: str = "") -> list:
        """Obtiene la estructura de comisiones para un precio dado."""
        self._ensure_token()
        params = {
            "price": price,
            "listing_type_id": listing_type,
            "domain_id": "MLA-CELLPHONES",
        }
        if campaign_tag:
            params["tags"] = campaign_tag

        resp = requests.get(
            f"{self.BASE_URL}/sites/{self.site_id}/listing_prices",
            headers=self._headers(), params=params, timeout=15
        )
        try:
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError:
            return []

    # ─── Campañas ────────────────────────────────────────────

    def get_campaigns(self, category_id: str = "MLA1055") -> list:
        """Obtiene las campañas disponibles para una categoría."""
        self._ensure_token()
        resp = requests.get(
            f"{self.BASE_URL}/special_installments/campaigns",
            headers=self._headers(),
            params={"category_id": category_id},
            timeout=15
        )
        try:
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError:
            return []

    def check_campaign_enabled(self, campaign_tag: str,
                                category_id: str = "MLA1055") -> bool:
        """Verifica si una campaña está habilitada para una categoría."""
        self._ensure_token()
        try:
            resp = requests.post(
                f"{self.BASE_URL}/special_installments/{campaign_tag}/categories/{category_id}/enabled",
                headers=self._headers(), timeout=15
            )
            if resp.status_code == 200:
                return resp.json().get("enabled", False)
            return False
        except Exception:
            return False

    def get_seller_items(self, status: str = "active") -> list:
        """Obtiene los IDs de items del vendedor (hasta 50)."""
        self._ensure_token()
        if not self.user_id:
            me = self.check_connection()
            if not me.get("connected"):
                return []
        resp = requests.get(
            f"{self.BASE_URL}/users/{self.user_id}/items/search",
            headers=self._headers(),
            params={"status": status, "limit": 50},
            timeout=15
        )
        try:
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
        except requests.HTTPError:
            return []

    def sync_all_items(self, status: str = "active") -> list:
        """Sincroniza TODOS los items del vendedor con batch requests.

        Obtiene IDs en batches de 50 y pide detalles en batches de 20
        para minimizar requests HTTP.
        Returns:
            list[dict] con datos de cada item (title, price, status, etc.).
        """
        self._ensure_token()
        if not self.user_id:
            me = self.check_connection()
            if not me.get("connected"):
                return []

        all_items = []
        offset = 0
        limit = 50
        batch_size = 20  # MELI permite hasta ~20 IDs por GET /items?ids=

        while True:
            try:
                resp = requests.get(
                    f"{self.BASE_URL}/users/{self.user_id}/items/search",
                    headers=self._headers(),
                    params={"status": status, "limit": limit, "offset": offset},
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
                item_ids = data.get("results", [])
                total = data.get("paging", {}).get("total", 0)

                if not item_ids:
                    break

                # Pedir detalles en BATCHES de 20 (una request HTTP cada 20 items)
                for i in range(0, len(item_ids), batch_size):
                    batch_ids = item_ids[i:i + batch_size]
                    try:
                        resp = requests.get(
                            f"{self.BASE_URL}/items",
                            headers=self._headers(),
                            params={"ids": ",".join(batch_ids)},
                            timeout=30
                        )
                        resp.raise_for_status()
                        batch_results = resp.json()

                        for entry in batch_results:
                            item_data = entry.get("body", entry)
                            if "error" in item_data:
                                all_items.append({
                                    "id": item_data.get("id", ""),
                                    "error": "could not fetch detail",
                                })
                            else:
                                all_items.append({
                                    "id": item_data["id"],
                                    "title": item_data.get("title", ""),
                                    "price": item_data.get("price", 0),
                                    "status": item_data.get("status", ""),
                                    "listing_type": item_data.get("listing_type_id", ""),
                                    "available_quantity": item_data.get("available_quantity", 0),
                                    "sold_quantity": item_data.get("sold_quantity", 0),
                                    "permalink": item_data.get("permalink", ""),
                                    "tags": item_data.get("tags", []),
                                    "catalog_product_id": item_data.get("catalog_product_id", ""),
                                })
                    except Exception:
                        for item_id in batch_ids:
                            all_items.append({
                                "id": item_id,
                                "error": "could not fetch batch",
                            })

                offset += limit
                if offset >= total:
                    break

            except requests.HTTPError:
                break

        return all_items

    # ─── Órdenes / Ventas ────────────────────────────────────

    def sync_all_orders(self, since_days: int = 365) -> list[dict]:
        """Sincroniza órdenes pagadas desde MELI.

        Obtiene órdenes con status=paid desde (hoy - since_days) hasta hoy,
        paginando de a 50. Sin delay entre páginas (mismo patrón que sync_all_items).

        Returns:
            list[dict] con datos de cada orden: id, date_created, status,
            payments[], order_items[], buyer, etc.
        """
        self._ensure_token()
        if not self.user_id:
            me = self.check_connection()
            if not me.get("connected"):
                return []

        from datetime import datetime, timedelta

        today = datetime.utcnow()
        since = today - timedelta(days=since_days)
        date_from = since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        date_to = today.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        all_orders = []
        offset = 0
        limit = 50

        while True:
            try:
                resp = requests.get(
                    f"{self.BASE_URL}/orders/search",
                    headers=self._headers(),
                    params={
                        "seller": self.user_id,
                        "order.status": "paid",
                        "order.date_created.from": date_from,
                        "order.date_created.to": date_to,
                        "offset": offset,
                        "limit": limit,
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                total = data.get("paging", {}).get("total", 0)

                if not results:
                    break

                for order in results:
                    payments = order.get("payments", [])
                    total_paid = 0.0
                    marketplace_fee = 0.0
                    shipping_cost = 0.0
                    if payments:
                        total_paid = sum(
                            p.get("total_paid_amount", 0) or 0 for p in payments
                        )
                        marketplace_fee = sum(
                            p.get("marketplace_fee", 0) or 0 for p in payments
                        )
                        shipping_cost = sum(
                            p.get("shipping_cost", 0) or 0 for p in payments
                        )

                    buyer = order.get("buyer", {}) or {}

                    items_raw = order.get("order_items", []) or []
                    items = []
                    for oi in items_raw:
                        item_data = oi.get("item", {}) or {}
                        qty = oi.get("quantity", 1) or 1
                        unit_price = oi.get("unit_price", 0) or 0
                        items.append({
                            "meli_item_id": str(item_data.get("id", "")),
                            "item_title": item_data.get("title", ""),
                            "quantity": qty,
                            "unit_price": unit_price,
                            "total_amount": unit_price * qty,
                        })

                    all_orders.append({
                        "meli_order_id": str(order["id"]),
                        "total_paid_amount": total_paid or order.get("total_amount", 0),
                        "marketplace_fee": marketplace_fee,
                        "shipping_cost": shipping_cost,
                        "status": order.get("status", "paid"),
                        "date_created": order.get("date_created"),
                        "buyer_nickname": buyer.get("nickname", ""),
                        "buyer_id": str(buyer.get("id", "")) if buyer.get("id") else "",
                        "items": items,
                    })

                offset += limit
                if offset >= total:
                    break

            except requests.HTTPError:
                break

        return all_orders
