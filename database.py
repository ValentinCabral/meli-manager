"""MELI Manager — Database (SQLite) Multi-Cuenta"""

import sqlite3
import os
from datetime import datetime
from config import DB_PATH, ML_CLIENT_ID, ML_CLIENT_SECRET, ML_REFRESH_TOKEN, ML_SITE_ID


def get_db():
    """Obtiene conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    """Inicializa el esquema y migra datos existentes."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS cuentas_meli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT,
            user_id TEXT,
            refresh_token TEXT NOT NULL,
            access_token TEXT,
            expires_at TIMESTAMP,
            active BOOLEAN DEFAULT 0,
            site_id TEXT DEFAULT 'MLA',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL DEFAULT 1,
            nombre TEXT NOT NULL,
            sku TEXT,
            marca TEXT,
            modelo TEXT,
            color TEXT,
            costo REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            categoria_id TEXT DEFAULT 'MLA1055',
            catalog_product_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas_meli(id),
            UNIQUE(cuenta_id, sku)
        );

        CREATE TABLE IF NOT EXISTS publicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL DEFAULT 1,
            producto_id INTEGER NOT NULL,
            meli_item_id TEXT,
            titulo TEXT,
            precio REAL NOT NULL,
            listing_type TEXT NOT NULL DEFAULT 'gold_special',
            campaign_tag TEXT,
            stock INTEGER DEFAULT 1,
            estado TEXT DEFAULT 'borrador',
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas_meli(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS historial_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL DEFAULT 1,
            producto_id INTEGER,
            precio_anterior REAL,
            precio_nuevo REAL,
            motivo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas_meli(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS importaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL DEFAULT 1,
            archivo TEXT,
            filas_importadas INTEGER DEFAULT 0,
            filas_errores INTEGER DEFAULT 0,
            resultado TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas_meli(id)
        );

        CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL REFERENCES cuentas_meli(id),
            meli_order_id TEXT NOT NULL UNIQUE,
            total_paid_amount REAL DEFAULT 0,
            marketplace_fee REAL DEFAULT 0,
            shipping_cost REAL DEFAULT 0,
            status TEXT DEFAULT 'paid',
            date_created TIMESTAMP,
            buyer_nickname TEXT DEFAULT '',
            buyer_id TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orden_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER NOT NULL REFERENCES ordenes(id),
            meli_item_id TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            item_title TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS visitas_publicacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL REFERENCES cuentas_meli(id),
            meli_item_id TEXT NOT NULL,
            visitas INTEGER DEFAULT 0,
            fecha TEXT DEFAULT (date('now')),
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(cuenta_id, meli_item_id)
        );
    """)

    # Migración: agregar columnas faltantes en tablas existentes
    migraciones = [
        ("productos", "cuenta_id", "INTEGER NOT NULL DEFAULT 1 REFERENCES cuentas_meli(id)"),
        ("publicaciones", "cuenta_id", "INTEGER NOT NULL DEFAULT 1 REFERENCES cuentas_meli(id)"),
        ("historial_precios", "cuenta_id", "INTEGER NOT NULL DEFAULT 1 REFERENCES cuentas_meli(id)"),
        ("importaciones", "cuenta_id", "INTEGER NOT NULL DEFAULT 1 REFERENCES cuentas_meli(id)"),
    ]
    for tabla, columna, definicion in migraciones:
        try:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")
        except sqlite3.OperationalError:
            pass  # ya existe

    # Seed: crear cuenta default desde .env si no hay ninguna cuenta
    cuenta_default = cursor.execute("SELECT COUNT(*) as c FROM cuentas_meli").fetchone()["c"]
    if cuenta_default == 0 and ML_REFRESH_TOKEN:
        cursor.execute("""
            INSERT INTO cuentas_meli (nickname, refresh_token, active, site_id)
            VALUES (?, ?, 1, ?)
        """, (f"Cuenta {ML_SITE_ID} (desde .env)", ML_REFRESH_TOKEN, ML_SITE_ID))
        cuenta_id = cursor.lastrowid
        # Migrar productos/publicaciones existentes a esta cuenta
        cursor.execute("UPDATE productos SET cuenta_id = ? WHERE cuenta_id = 1", (cuenta_id,))
        cursor.execute("UPDATE publicaciones SET cuenta_id = ? WHERE cuenta_id = 1", (cuenta_id,))
        cursor.execute("UPDATE historial_precios SET cuenta_id = ? WHERE cuenta_id = 1", (cuenta_id,))
        cursor.execute("UPDATE importaciones SET cuenta_id = ? WHERE cuenta_id = 1", (cuenta_id,))

    conn.commit()
    conn.close()


# ─── Cuentas MELI CRUD ─────────────────────────────────────

def get_account_count():
    conn = get_db()
    c = conn.execute("SELECT COUNT(*) as c FROM cuentas_meli").fetchone()["c"]
    conn.close()
    return c


def listar_cuentas():
    conn = get_db()
    rows = conn.execute("""
        SELECT c.*,
               (SELECT COUNT(*) FROM productos WHERE cuenta_id = c.id) as total_productos,
               (SELECT COUNT(*) FROM publicaciones WHERE cuenta_id = c.id AND estado = 'activo') as total_publicaciones
        FROM cuentas_meli c
        ORDER BY c.active DESC, c.created_at ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cuenta(cuenta_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM cuentas_meli WHERE id = ?", (cuenta_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_cuenta_activa():
    conn = get_db()
    row = conn.execute("SELECT * FROM cuentas_meli WHERE active = 1 LIMIT 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    # Fallback: primera cuenta
    conn = get_db()
    row = conn.execute("SELECT * FROM cuentas_meli ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


def activar_cuenta(cuenta_id):
    conn = get_db()
    conn.execute("UPDATE cuentas_meli SET active = 0")
    conn.execute("UPDATE cuentas_meli SET active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (cuenta_id,))
    conn.commit()
    conn.close()


def crear_cuenta(nickname, refresh_token, user_id="", site_id="MLA"):
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO cuentas_meli (nickname, user_id, refresh_token, site_id)
        VALUES (?, ?, ?, ?)
    """, (nickname, user_id, refresh_token, site_id))
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid


def actualizar_cuenta(cuenta_id, **kwargs):
    campos = []
    valores = []
    for k, v in kwargs.items():
        if k in ("nickname", "user_id", "refresh_token", "access_token",
                 "expires_at", "site_id"):
            campos.append(f"{k} = ?")
            valores.append(v)
    if not campos:
        return
    campos.append("updated_at = CURRENT_TIMESTAMP")
    valores.append(cuenta_id)
    conn = get_db()
    conn.execute(f"UPDATE cuentas_meli SET {', '.join(campos)} WHERE id = ?", valores)
    conn.commit()
    conn.close()


def eliminar_cuenta(cuenta_id):
    conn = get_db()
    conn.execute("DELETE FROM importaciones WHERE cuenta_id = ?", (cuenta_id,))
    conn.execute("DELETE FROM historial_precios WHERE cuenta_id = ?", (cuenta_id,))
    conn.execute("DELETE FROM publicaciones WHERE cuenta_id = ?", (cuenta_id,))
    conn.execute("DELETE FROM productos WHERE cuenta_id = ?", (cuenta_id,))
    conn.execute("DELETE FROM cuentas_meli WHERE id = ?", (cuenta_id,))
    conn.commit()
    conn.close()


# ─── Productos CRUD ──────────────────────────────────────────

def listar_productos(cuenta_id=None, search="", categoria="", con_stock_bajo=False):
    conn = get_db()
    query = "SELECT * FROM productos WHERE 1=1"
    params = []
    if cuenta_id:
        query += " AND cuenta_id = ?"
        params.append(cuenta_id)
    if search:
        query += " AND (nombre LIKE ? OR sku LIKE ? OR marca LIKE ? OR modelo LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like, like])
    if categoria:
        query += " AND categoria_id = ?"
        params.append(categoria)
    if con_stock_bajo:
        query += " AND stock <= 3 AND stock > 0"
    query += " ORDER BY updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_productos_agrupados(cuenta_id=None, search=""):
    """Lista productos agrupados por nombre (una vez por producto real).

    Cada fila incluye:
      - id, nombre, sku, marca, modelo, color, costo, stock
      - catalog_product_id, variantes, publicaciones
    """
    conn = get_db()
    query = """
        SELECT
            p.id,
            p.nombre,
            MAX(p.sku) as sku,
            p.marca,
            p.modelo,
            p.color,
            MAX(p.costo) as costo,
            MAX(p.stock) as stock,
            MAX(p.catalog_product_id) as catalog_product_id,
            COUNT(*) as variantes,
            (SELECT COUNT(*) FROM publicaciones WHERE producto_id IN (
                SELECT id FROM productos WHERE nombre = p.nombre AND cuenta_id = p.cuenta_id
            )) as publicaciones
        FROM productos p
        WHERE 1=1
    """
    params = []
    if cuenta_id:
        query += " AND p.cuenta_id = ?"
        params.append(cuenta_id)
    if search:
        query += " AND p.nombre LIKE ?"
        params.append(f"%{search}%")
    query += " GROUP BY p.nombre, p.cuenta_id ORDER BY p.nombre"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_producto(producto_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def crear_producto(cuenta_id, nombre, sku="", marca="", modelo="", color="",
                   costo=0, stock=0, categoria_id="MLA1055",
                   catalog_product_id=""):
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO productos (cuenta_id, nombre, sku, marca, modelo, color, costo, stock, categoria_id, catalog_product_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cuenta_id, nombre, sku, marca, modelo, color, costo, stock, categoria_id, catalog_product_id))
    conn.commit()
    prod_id = cursor.lastrowid
    conn.close()
    return prod_id


def actualizar_producto(producto_id, **kwargs):
    campos = []
    valores = []
    for k, v in kwargs.items():
        if k in ("nombre", "sku", "marca", "modelo", "color", "costo", "stock",
                 "categoria_id", "catalog_product_id"):
            campos.append(f"{k} = ?")
            valores.append(v)
    if not campos:
        return
    campos.append("updated_at = CURRENT_TIMESTAMP")
    valores.append(producto_id)
    conn = get_db()
    conn.execute(f"UPDATE productos SET {', '.join(campos)} WHERE id = ?", valores)
    conn.commit()
    conn.close()


def eliminar_producto(producto_id):
    conn = get_db()
    conn.execute("DELETE FROM publicaciones WHERE producto_id = ?", (producto_id,))
    conn.execute("DELETE FROM historial_precios WHERE producto_id = ?", (producto_id,))
    conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()
    conn.close()


def eliminar_productos_por_nombre(nombre, cuenta_id):
    """Elimina todos los productos con el mismo nombre (variantes)."""
    conn = get_db()
    conn.execute("""
        DELETE FROM publicaciones WHERE producto_id IN (
            SELECT id FROM productos WHERE nombre = ? AND cuenta_id = ?
        )
    """, (nombre, cuenta_id))
    conn.execute("""
        DELETE FROM historial_precios WHERE producto_id IN (
            SELECT id FROM productos WHERE nombre = ? AND cuenta_id = ?
        )
    """, (nombre, cuenta_id))
    conn.execute("DELETE FROM productos WHERE nombre = ? AND cuenta_id = ?", (nombre, cuenta_id))
    conn.commit()
    conn.close()


# ─── Publicaciones CRUD ──────────────────────────────────────

def listar_publicaciones(cuenta_id=None, search=""):
    conn = get_db()
    query = """
        SELECT p.*, pr.nombre as producto_nombre, pr.sku as producto_sku
        FROM publicaciones p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE 1=1
    """
    params = []
    if cuenta_id:
        query += " AND p.cuenta_id = ?"
        params.append(cuenta_id)
    if search:
        query += " AND (p.titulo LIKE ? OR pr.nombre LIKE ? OR p.meli_item_id LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])
    query += " ORDER BY p.updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_publicacion(pub_id):
    conn = get_db()
    row = conn.execute("""
        SELECT p.*, pr.nombre as producto_nombre, pr.sku as producto_sku
        FROM publicaciones p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.id = ?
    """, (pub_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def crear_publicacion(cuenta_id, producto_id, precio, listing_type="gold_special",
                      campaign_tag="", stock=1, meli_item_id="",
                      titulo="", estado="borrador", url=""):
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO publicaciones (cuenta_id, producto_id, meli_item_id, titulo, precio,
                                   listing_type, campaign_tag, stock, estado, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cuenta_id, producto_id, meli_item_id, titulo, precio,
          listing_type, campaign_tag, stock, estado, url))
    conn.commit()
    pub_id = cursor.lastrowid
    conn.close()
    return pub_id


def actualizar_publicacion(pub_id, **kwargs):
    campos = []
    valores = []
    for k, v in kwargs.items():
        if k in ("precio", "listing_type", "campaign_tag", "stock",
                 "estado", "meli_item_id", "titulo", "url"):
            campos.append(f"{k} = ?")
            valores.append(v)
    if not campos:
        return
    campos.append("updated_at = CURRENT_TIMESTAMP")
    valores.append(pub_id)
    conn = get_db()
    conn.execute(f"UPDATE publicaciones SET {', '.join(campos)} WHERE id = ?", valores)
    conn.commit()
    conn.close()


def listar_publicaciones_recientes(cuenta_id=None, limite=5):
    """Últimas N publicaciones (con producto) para el dashboard."""
    conn = get_db()
    query = """
        SELECT p.*, pr.nombre as producto_nombre, pr.sku as producto_sku
        FROM publicaciones p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE 1=1
    """
    params = []
    if cuenta_id:
        query += " AND p.cuenta_id = ?"
        params.append(cuenta_id)
    query += " ORDER BY p.updated_at DESC LIMIT ?"
    params.append(limite)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def eliminar_publicacion(pub_id):
    conn = get_db()
    conn.execute("DELETE FROM publicaciones WHERE id = ?", (pub_id,))
    conn.commit()
    conn.close()


# ─── Configuración ──────────────────────────────────────────

def get_config(clave, default=""):
    conn = get_db()
    row = conn.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
    conn.close()
    return row["valor"] if row else default


def set_config(clave, valor):
    conn = get_db()
    conn.execute("""
        INSERT INTO configuracion (clave, valor, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor, updated_at = CURRENT_TIMESTAMP
    """, (clave, valor))
    conn.commit()
    conn.close()


def get_all_config():
    conn = get_db()
    rows = conn.execute("SELECT * FROM configuracion ORDER BY clave").fetchall()
    conn.close()
    return {r["clave"]: r["valor"] for r in rows}


# ─── Órdenes CRUD ────────────────────────────────────────

def upsert_orden(cuenta_id, data):
    """Inserta o actualiza una orden por meli_order_id. Devuelve el id."""
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO ordenes (cuenta_id, meli_order_id, total_paid_amount, marketplace_fee,
                             shipping_cost, status, date_created, buyer_nickname, buyer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(meli_order_id) DO UPDATE SET
            total_paid_amount = excluded.total_paid_amount,
            marketplace_fee = excluded.marketplace_fee,
            shipping_cost = excluded.shipping_cost,
            status = excluded.status,
            buyer_nickname = excluded.buyer_nickname,
            buyer_id = excluded.buyer_id,
            updated_at = CURRENT_TIMESTAMP
    """, (
        cuenta_id,
        data["meli_order_id"],
        data.get("total_paid_amount", 0),
        data.get("marketplace_fee", 0),
        data.get("shipping_cost", 0),
        data.get("status", "paid"),
        data.get("date_created"),
        data.get("buyer_nickname", ""),
        data.get("buyer_id", ""),
    ))
    conn.commit()
    orden_id = cursor.lastrowid
    conn.close()
    return orden_id


def upsert_orden_items(orden_id, items):
    """Reemplaza los items de una orden: elimina viejos e inserta nuevos."""
    conn = get_db()
    conn.execute("DELETE FROM orden_items WHERE orden_id = ?", (orden_id,))
    for item in items:
        conn.execute("""
            INSERT INTO orden_items (orden_id, meli_item_id, quantity, unit_price, total_amount, item_title)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            orden_id,
            item.get("meli_item_id", ""),
            item.get("quantity", 1),
            item.get("unit_price", 0),
            item.get("total_amount", 0),
            item.get("item_title", ""),
        ))
    conn.commit()
    conn.close()


def listar_ordenes(cuenta_id, desde="", hasta="", estado="",
                   page=1, per_page=50, sort_order="desc"):
    """Lista órdenes con filtros y paginación. Incluye items concatenados."""
    conn = get_db()
    params = [cuenta_id]
    where = "WHERE o.cuenta_id = ?"

    if desde:
        where += " AND o.date_created >= ?"
        params.append(desde)
    if hasta:
        where += " AND o.date_created <= ?"
        params.append(hasta)
    if estado:
        where += " AND o.status = ?"
        params.append(estado)

    total_row = conn.execute(f"SELECT COUNT(*) as c FROM ordenes o {where}", params).fetchone()
    total = total_row["c"]

    order_dir = "ASC" if sort_order.lower() == "asc" else "DESC"
    offset = (page - 1) * per_page
    if offset < 0:
        offset = 0
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, pages))

    rows = conn.execute(f"""
        SELECT o.*, GROUP_CONCAT(oi.item_title, ' | ') as items
        FROM ordenes o
        LEFT JOIN orden_items oi ON o.id = oi.orden_id
        {where}
        GROUP BY o.id
        ORDER BY o.date_created {order_dir}
        LIMIT ? OFFSET ?
    """, params + [per_page, offset]).fetchall()

    conn.close()
    return {
        "rows": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
    }


def get_revenue_total(cuenta_id=None):
    """Suma total_paid_amount de órdenes. Devuelve 0.0 si no hay."""
    conn = get_db()
    if cuenta_id:
        row = conn.execute(
            "SELECT COALESCE(SUM(total_paid_amount), 0) as v FROM ordenes WHERE cuenta_id = ?",
            (cuenta_id,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COALESCE(SUM(total_paid_amount), 0) as v FROM ordenes"
        ).fetchone()
    conn.close()
    return row["v"]


def count_ordenes(cuenta_id, desde="", hasta="", estado=""):
    """Cuenta órdenes con filtros para paginación."""
    conn = get_db()
    params = [cuenta_id]
    where = "WHERE cuenta_id = ?"
    if desde:
        where += " AND date_created >= ?"
        params.append(desde)
    if hasta:
        where += " AND date_created <= ?"
        params.append(hasta)
    if estado:
        where += " AND status = ?"
        params.append(estado)
    row = conn.execute(f"SELECT COUNT(*) as c FROM ordenes {where}", params).fetchone()
    conn.close()
    return row["c"]


# ─── Visitas CRUD ─────────────────────────────────────────

def upsert_visita(cuenta_id, meli_item_id, visitas):
    """Inserta o actualiza visitas de una publicación. Upsert por (cuenta_id, meli_item_id)."""
    conn = get_db()
    conn.execute("""
        INSERT INTO visitas_publicacion (cuenta_id, meli_item_id, visitas)
        VALUES (?, ?, ?)
        ON CONFLICT(cuenta_id, meli_item_id) DO UPDATE SET
            visitas = excluded.visitas,
            fecha = date('now'),
            synced_at = CURRENT_TIMESTAMP
    """, (cuenta_id, meli_item_id, visitas))
    conn.commit()
    conn.close()


def get_visitas(cuenta_id):
    """Devuelve {meli_item_id: visitas} para todos los items sincronizados."""
    conn = get_db()
    rows = conn.execute(
        "SELECT meli_item_id, visitas FROM visitas_publicacion WHERE cuenta_id = ?",
        (cuenta_id,)
    ).fetchall()
    conn.close()
    return {r["meli_item_id"]: r["visitas"] for r in rows}


def get_metricas_detalle(cuenta_id):
    """Devuelve publicaciones LEFT JOIN visitas, ordenado por visitas DESC.

    Cada fila incluye todos los campos de publicaciones + v.visitas, v.fecha.
    """
    conn = get_db()
    rows = conn.execute("""
        SELECT p.*, v.visitas, v.fecha as visitas_fecha,
               pr.nombre as producto_nombre, pr.sku as producto_sku
        FROM publicaciones p
        LEFT JOIN visitas_publicacion v ON p.meli_item_id = v.meli_item_id
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.cuenta_id = ?
        ORDER BY COALESCE(v.visitas, 0) DESC
    """, (cuenta_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Dashboard / Métricas ───────────────────────────────────

def get_metricas(cuenta_id=None):
    conn = get_db()

    def _q(sql, params=None):
        return conn.execute(sql, params or []).fetchone()

    if cuenta_id:
        total_productos = _q("SELECT COUNT(*) as c FROM productos WHERE cuenta_id = ?", [cuenta_id])["c"]
        stock_total = _q("""
            SELECT COALESCE(SUM(sub.stock), 0) as v FROM (
                SELECT MAX(stock) as stock FROM productos
                WHERE cuenta_id = ? GROUP BY nombre
            ) sub
        """, [cuenta_id])["v"]
        stock_bajo = _q("SELECT COUNT(*) as c FROM productos WHERE cuenta_id = ? AND stock <= 3 AND stock > 0", [cuenta_id])["c"]
        total_publicaciones = _q("SELECT COUNT(*) as c FROM publicaciones WHERE estado IN ('active', 'activo') AND cuenta_id = ?", [cuenta_id])["c"]
        valor_costo = _q("""
            SELECT COALESCE(SUM(sub.valor), 0) as v FROM (
                SELECT MAX(costo * stock) as valor FROM productos
                WHERE cuenta_id = ? GROUP BY nombre
            ) sub
        """, [cuenta_id])["v"]
        valor_venta = _q("""
            SELECT COALESCE(SUM(sub.stock * sub.precio), 0) as v FROM (
                SELECT
                    p.nombre,
                    MAX(p.stock) as stock,
                    (SELECT MAX(precio) FROM publicaciones
                     WHERE producto_id IN (SELECT id FROM productos WHERE nombre = p.nombre AND cuenta_id = p.cuenta_id)
                     AND estado IN ('active', 'activo')
                     LIMIT 1) as precio
                FROM productos p
                WHERE p.cuenta_id = ?
                GROUP BY p.nombre, p.cuenta_id
                HAVING precio IS NOT NULL
            ) sub
        """, [cuenta_id])["v"]
        ingresos_reales = _q("SELECT COALESCE(SUM(total_paid_amount), 0) as v FROM ordenes WHERE cuenta_id = ?", [cuenta_id])["v"]
    else:
        total_productos = _q("SELECT COUNT(*) as c FROM productos")["c"]
        stock_total = _q("""
            SELECT COALESCE(SUM(sub.stock), 0) as v FROM (
                SELECT MAX(stock) as stock FROM productos GROUP BY nombre
            ) sub
        """)["v"]
        stock_bajo = _q("SELECT COUNT(*) as c FROM productos WHERE stock <= 3 AND stock > 0")["c"]
        total_publicaciones = _q("SELECT COUNT(*) as c FROM publicaciones WHERE estado IN ('active', 'activo')")["c"]
        valor_costo = _q("""
            SELECT COALESCE(SUM(sub.valor), 0) as v FROM (
                SELECT MAX(costo * stock) as valor FROM productos GROUP BY nombre
            ) sub
        """)["v"]
        valor_venta = _q("""
            SELECT COALESCE(SUM(sub.stock * sub.precio), 0) as v FROM (
                SELECT
                    p.nombre,
                    MAX(p.stock) as stock,
                    (SELECT MAX(precio) FROM publicaciones
                     WHERE producto_id IN (SELECT id FROM productos WHERE nombre = p.nombre AND cuenta_id = p.cuenta_id)
                     AND estado IN ('active', 'activo')
                     LIMIT 1) as precio
                FROM productos p
                GROUP BY p.nombre, p.cuenta_id
                HAVING precio IS NOT NULL
            ) sub
        """)["v"]
        ingresos_reales = _q("SELECT COALESCE(SUM(total_paid_amount), 0) as v FROM ordenes")["v"]

    conn.close()
    return {
        "total_productos": total_productos,
        "stock_total": stock_total,
        "stock_bajo": stock_bajo,
        "total_publicaciones": total_publicaciones,
        "valor_inventario": round(valor_costo, 2),
        "valor_venta_meli": round(ingresos_reales, 2),
    }
