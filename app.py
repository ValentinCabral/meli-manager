"""MELI Manager — Flask Application (Multi-Cuenta + OAuth)"""

import io
import os
import csv
import json
import secrets
from datetime import datetime

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, send_file, jsonify, session)

import database as db
import meli_client as meli
from calculator import (calcular_precio_venta, calcular_todas_las_opciones,
                        calcular_precio_garantizado)
from config import CAMPAIGN_OPTIONS, ML_CLIENT_ID

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "meli-manager-secret-key-change-in-production")
MELI_REDIRECT_URI = os.getenv("MELI_REDIRECT_URI", "http://localhost:5000/auth/meli/callback")

# Initialize DB at module level — runs on import, needed for gunicorn
db.init_db()


# ─── Helper: cuenta activa ──────────────────────────────────

def get_active_cuenta():
    """Devuelve la cuenta activa desde la DB. Si hay una en session, la prioriza."""
    cuenta_id = session.get("cuenta_id")
    if cuenta_id:
        cuenta = db.get_cuenta(cuenta_id)
        if cuenta:
            return cuenta
    return db.get_cuenta_activa()


def get_meli_client(cuenta=None):
    """Crea un MeliClient para la cuenta dada (o la activa)."""
    if not cuenta:
        cuenta = get_active_cuenta()
    if not cuenta:
        return meli.MeliClient()
    return meli.MeliClient(
        refresh_token=cuenta.get("refresh_token"),
        site_id=cuenta.get("site_id", "MLA"),
    )


# ─── Inicialización ──────────────────────────────────────────

@app.context_processor
def inject_cuentas():
    """Inyecta la cuenta activa y la lista de cuentas en todos los templates."""
    try:
        cuentas = db.listar_cuentas()
        cuenta = get_active_cuenta()
        return {"cuenta": cuenta, "cuentas": cuentas}
    except Exception:
        return {"cuenta": None, "cuentas": []}


# ─── Página Principal ───────────────────────────────────────

@app.route("/")
def dashboard():
    cuenta = get_active_cuenta()
    cuenta_id = cuenta["id"] if cuenta else None
    metricas = db.get_metricas(cuenta_id=cuenta_id)
    cuentas = db.listar_cuentas()
    pubs_recientes = db.listar_publicaciones_recientes(cuenta_id=cuenta_id, limite=5)
    return render_template("dashboard.html",
                           metricas=metricas,
                           cuenta=cuenta,
                           cuentas=cuentas,
                           publicaciones=pubs_recientes,
                           page="dashboard")


# ─── Cuentas MELI ───────────────────────────────────────────

@app.route("/cuentas")
def cuentas():
    cuentas_list = db.listar_cuentas()
    return render_template("cuentas.html",
                           cuentas=cuentas_list,
                           meli_client_id=ML_CLIENT_ID,
                           redirect_uri=MELI_REDIRECT_URI,
                           page="cuentas")


@app.route("/cuentas/<int:cid>/activar")
def cuenta_activar(cid):
    cuenta = db.get_cuenta(cid)
    if not cuenta:
        flash("Cuenta no encontrada", "danger")
        return redirect(url_for("cuentas"))
    db.activar_cuenta(cid)
    session["cuenta_id"] = cid
    flash(f"✓ Cuenta '{cuenta['nickname']}' activada", "success")
    # Verificar conexión
    client = get_meli_client(cuenta)
    result = client.check_connection()
    if result.get("connected"):
        session["meli_connected"] = True
        session["meli_nickname"] = result["nickname"]
        # Actualizar nickname + user_id si cambió
        if result["nickname"] != cuenta["nickname"] or result["user_id"] != cuenta.get("user_id"):
            db.actualizar_cuenta(cid,
                                 nickname=result["nickname"],
                                 user_id=str(result["user_id"]))
        # Guardar nuevo refresh_token si cambió
        if result.get("refresh_token") and result["refresh_token"] != cuenta["refresh_token"]:
            db.actualizar_cuenta(cid, refresh_token=result["refresh_token"])
    else:
        session["meli_connected"] = False
        flash(f"⚠️ No se pudo conectar: {result.get('error', 'desconocido')}", "warning")
    return redirect(url_for("cuentas"))


@app.route("/cuentas/<int:cid>/eliminar", methods=["POST"])
def cuenta_eliminar(cid):
    cuenta = db.get_cuenta(cid)
    if not cuenta:
        flash("Cuenta no encontrada", "danger")
        return redirect(url_for("cuentas"))
    if db.get_account_count() <= 1:
        flash("No podés eliminar la única cuenta", "danger")
        return redirect(url_for("cuentas"))
    # Si era la activa, activar otra
    if session.get("cuenta_id") == cid:
        session.pop("cuenta_id", None)
        session["meli_connected"] = False
    db.eliminar_cuenta(cid)
    flash(f"✓ Cuenta '{cuenta['nickname']}' eliminada", "success")
    return redirect(url_for("cuentas"))


# ─── OAuth: Conectar nueva cuenta MELI ─────────────────────

@app.route("/auth/meli/login")
def auth_meli_login():
    """Redirige al usuario a la pantalla de autorización de MELI."""
    state = secrets.token_hex(32)  # token aleatorio como Dropdeal
    session["oauth_state"] = state
    url = meli.MeliClient.get_auth_url(MELI_REDIRECT_URI, state)
    return redirect(url)


@app.route("/auth/meli/callback")
def auth_meli_callback():
    """Callback de OAuth: recibe el code y lo intercambia por tokens."""
    code = request.args.get("code")
    error = request.args.get("error")
    state = request.args.get("state")

    # Validar state anti-CSRF (como hace Dropdeal)
    expected_state = session.pop("oauth_state", None)
    if state and expected_state and state != expected_state:
        flash("❌ Error de seguridad: state inválido", "danger")
        return redirect(url_for("cuentas"))

    if error:
        flash(f"❌ Autorización cancelada: {error}", "warning")
        return redirect(url_for("cuentas"))

    if not code:
        flash("❌ No se recibió el código de autorización", "danger")
        return redirect(url_for("cuentas"))

    result = meli.MeliClient.exchange_code(code, MELI_REDIRECT_URI)
    if not result.get("success"):
        flash(f"❌ Error al conectar cuenta: {result.get('error', 'desconocido')}", "danger")
        return redirect(url_for("cuentas"))

    # Guardar la cuenta
    nickname = result.get("nickname", f"Usuario {result.get('user_id', '')}")
    refresh_token = result.get("refresh_token", "")
    user_id = str(result.get("user_id", ""))
    access_token = result.get("access_token", "")
    expires_in = result.get("expires_in", 21600)

    cid = db.crear_cuenta(
        nickname=nickname,
        refresh_token=refresh_token,
        user_id=user_id,
        site_id="MLA",
    )
    db.actualizar_cuenta(cid, access_token=access_token)

    # Activar la nueva cuenta
    db.activar_cuenta(cid)
    session["cuenta_id"] = cid
    session["meli_connected"] = True
    session["meli_nickname"] = nickname

    flash(f"✅ ¡Cuenta '{nickname}' conectada exitosamente!", "success")

    # Sincronizar publicaciones automáticamente
    client = get_meli_client(db.get_cuenta(cid))
    sync_result = _sync_cuenta_items(db.get_cuenta(cid), client)
    if sync_result.get("ok") and sync_result["total"] > 0:
        flash(f"📥 Sincronizadas {sync_result['total']} publicaciones desde MELI ({sync_result['creados']} nuevas)", "info")

    return redirect(url_for("dashboard"))


# ─── Conexión MELI (cuenta activa) ──────────────────────────

@app.route("/meli/check")
def meli_check():
    cuenta = get_active_cuenta()
    if not cuenta:
        flash("No hay cuentas configuradas. Conectá una desde Cuentas.", "warning")
        return redirect(url_for("cuentas"))

    client = get_meli_client(cuenta)
    result = client.check_connection()
    if result.get("connected"):
        session["meli_connected"] = True
        session["meli_nickname"] = result["nickname"]
        # Actualizar datos de la cuenta si cambiaron
        db.actualizar_cuenta(cuenta["id"],
                             nickname=result["nickname"],
                             user_id=str(result["user_id"]))
        if result.get("refresh_token") and result["refresh_token"] != cuenta["refresh_token"]:
            db.actualizar_cuenta(cuenta["id"], refresh_token=result["refresh_token"])
        flash(f"✓ Conectado como {result['nickname']}", "success")
    else:
        session["meli_connected"] = False
        flash(f"✗ Error de conexión: {result.get('error', 'desconocido')}", "danger")
    return redirect(url_for("dashboard"))


# ─── Sincronizar desde MELI ─────────────────────────────────

def _sync_cuenta_items(cuenta, client=None):
    """Sincroniza TODAS las publicaciones de una cuenta de MELI a la DB local.

    Para cada item activo en MELI:
    1. Crea/actualiza un producto local (nombre, stock, catalog_product_id)
    2. Crea/actualiza la publicación local vinculada al producto
    """
    if not client:
        client = get_meli_client(cuenta)
    if not client.user_id:
        result = client.check_connection()
        if not result.get("connected"):
            return {"ok": False, "error": result.get("error", "conexión fallida")}

    items = client.sync_all_items(status="active")

    # ── Cargar DB local UNA VEZ (evitar N+1) ─────────────────
    pubs_map: dict[str, dict] = {}  # meli_item_id -> publicación
    for p in db.listar_publicaciones(cuenta_id=cuenta["id"]):
        if p["meli_item_id"]:
            pubs_map[p["meli_item_id"]] = p

    prods_by_name: dict[str, dict] = {}  # nombre (base) -> producto
    for p in db.listar_productos(cuenta_id=cuenta["id"]):
        nombre_base = p["nombre"].strip().lower()
        if nombre_base:
            prods_by_name[nombre_base] = p
    # ──────────────────────────────────────────────────────────

    creados = 0
    actualizados = 0
    errores = 0

    def _nombre_base(titulo: str) -> str:
        """Extrae el nombre base del título (antes del ' - ' o sin variante)."""
        return (titulo.split(" - ")[0] if " - " in titulo else titulo[:100]).strip().lower()

    for item in items:
        if item.get("error"):
            errores += 1
            continue

        try:
            meli_id: str = item["id"]
            titulo: str = item.get("title", "")
            precio: float = item.get("price", 0)
            stock: int = item.get("available_quantity", 1)
            status: str = item.get("status", "active")
            permalink: str = item.get("permalink", "")
            listing_type: str = item.get("listing_type", "gold_special")
            campaign_tag: str = next(
                (t for t in item.get("tags", []) if t.endswith("_campaign")),
                ""
            )

            pub_existente = pubs_map.get(meli_id)

            if pub_existente:
                db.actualizar_publicacion(pub_existente["id"],
                                          precio=precio,
                                          stock=stock,
                                          estado=status,
                                          titulo=titulo,
                                          url=permalink)
                actualizados += 1
            else:
                # Reusar producto existente por nombre base (evita stock duplicado)
                nombre_base = _nombre_base(titulo)
                prod_existente = prods_by_name.get(nombre_base)

                if prod_existente:
                    pid = prod_existente["id"]
                    db.actualizar_producto(pid, stock=stock)
                else:
                    pid = db.crear_producto(
                        cuenta_id=cuenta["id"],
                        nombre=nombre_base.capitalize()[:100],
                        sku=meli_id,
                        stock=stock,
                    )
                    # Agregar al dict para próximos items con mismo nombre
                    prods_by_name[nombre_base] = {"id": pid, "nombre": nombre_base}

                db.crear_publicacion(
                    cuenta_id=cuenta["id"],
                    producto_id=pid,
                    precio=precio,
                    listing_type=listing_type,
                    campaign_tag=campaign_tag,
                    stock=stock,
                    meli_item_id=meli_id,
                    titulo=titulo,
                    estado=status,
                    url=permalink,
                )
                creados += 1
        except Exception as e:
            errores += 1

    return {
        "ok": True,
        "creados": creados,
        "actualizados": actualizados,
        "errores": errores,
        "total": creados + actualizados + errores,
    }


def _sync_cuenta_ordenes(cuenta, client=None):
    """Sincroniza órdenes pagadas de una cuenta de MELI a la DB local.

    Para cada orden en MELI:
    1. Hace upsert en ordenes (por meli_order_id)
    2. Reemplaza los items en orden_items
    """
    if not client:
        client = get_meli_client(cuenta)
    if not client.user_id:
        result = client.check_connection()
        if not result.get("connected"):
            return {"ok": False, "error": result.get("error", "conexión fallida")}

    orders = client.sync_all_orders(since_days=365)

    procesadas = 0
    errores = 0

    for order in orders:
        try:
            orden_id = db.upsert_orden(cuenta["id"], order)
            items = order.get("items", [])
            if items:
                db.upsert_orden_items(orden_id, items)
            procesadas += 1
        except Exception as e:
            errores += 1

    return {
        "ok": True,
        "procesadas": procesadas,
        "errores": errores,
        "total": procesadas + errores,
    }


@app.route("/meli/sync-orders")
def meli_sync_orders():
    """Sincroniza órdenes desde MELI."""
    cuenta = get_active_cuenta()
    if not cuenta:
        flash("No hay cuenta activa. Conectá una desde Cuentas.", "warning")
        return redirect(url_for("cuentas"))

    client = get_meli_client(cuenta)
    conn = client.check_connection()

    if not conn.get("connected"):
        session["meli_connected"] = False
        error_msg = conn.get("error", "desconocido")
        if "refresh_token" in str(error_msg).lower() or "401" in str(error_msg):
            flash("✗ Token expirado o inválido. Reconectá la cuenta desde Cuentas.", "danger")
        else:
            flash(f"✗ Error de conexión: {error_msg}", "danger")
        return redirect(url_for("cuentas"))

    session["meli_connected"] = True
    session["meli_nickname"] = conn["nickname"]
    db.actualizar_cuenta(cuenta["id"],
                         nickname=conn["nickname"],
                         user_id=str(conn["user_id"]))
    if conn.get("refresh_token") and conn["refresh_token"] != cuenta["refresh_token"]:
        db.actualizar_cuenta(cuenta["id"], refresh_token=conn["refresh_token"])
        cuenta["refresh_token"] = conn["refresh_token"]

    flash(f"🔌 Conectado como {conn['nickname']}. Sincronizando órdenes...", "info")

    result = _sync_cuenta_ordenes(cuenta, client)

    if result.get("ok"):
        flash(f"✅ Órdenes sincronizadas: {result['procesadas']} procesadas, {result['errores']} errores", "success")
        if client.refresh_token and client.refresh_token != cuenta.get("refresh_token"):
            db.actualizar_cuenta(cuenta["id"], refresh_token=client.refresh_token)
    else:
        flash(f"✗ Error en sync de órdenes: {result.get('error', 'desconocido')}", "danger")

    return redirect(url_for("dashboard"))


# ─── Visitas / Métricas ─────────────────────────────────────

def _sync_cuenta_visits(cuenta, client=None):
    """Sincroniza visitas de todas las publicaciones activas de una cuenta."""
    if not client:
        client = get_meli_client(cuenta)
    if not client.user_id:
        result = client.check_connection()
        if not result.get("connected"):
            return {"ok": False, "error": result.get("error", "conexión fallida")}

    # Obtener publicaciones activas desde DB local
    pubs = db.listar_publicaciones(cuenta_id=cuenta["id"])
    item_ids = [p["meli_item_id"] for p in pubs if p["meli_item_id"]]

    if not item_ids:
        return {"ok": True, "sincronizadas": 0, "total": 0}

    visits_data = client.sync_all_visits(item_ids)

    sincronizadas = 0
    for meli_item_id, visitas in visits_data.items():
        db.upsert_visita(cuenta["id"], meli_item_id, visitas)
        sincronizadas += 1

    return {
        "ok": True,
        "sincronizadas": sincronizadas,
        "total": len(item_ids),
    }


@app.route("/meli/sync-visits")
def meli_sync_visits():
    """Sincroniza visitas desde MELI y redirige a métricas."""
    cuenta = get_active_cuenta()
    if not cuenta:
        flash("Conectá una cuenta de MercadoLibre primero", "warning")
        return redirect(url_for("cuentas"))

    client = get_meli_client(cuenta)
    conn = client.check_connection()

    if not conn.get("connected"):
        session["meli_connected"] = False
        error_msg = conn.get("error", "desconocido")
        if "refresh_token" in str(error_msg).lower() or "401" in str(error_msg):
            flash("✗ Token expirado o inválido. Reconectá la cuenta desde Cuentas.", "danger")
        else:
            flash(f"✗ Error de conexión: {error_msg}", "danger")
        return redirect(url_for("cuentas"))

    session["meli_connected"] = True
    session["meli_nickname"] = conn["nickname"]
    db.actualizar_cuenta(cuenta["id"],
                         nickname=conn["nickname"],
                         user_id=str(conn["user_id"]))
    if conn.get("refresh_token") and conn["refresh_token"] != cuenta["refresh_token"]:
        db.actualizar_cuenta(cuenta["id"], refresh_token=conn["refresh_token"])
        cuenta["refresh_token"] = conn["refresh_token"]

    flash(f"🔌 Conectado como {conn['nickname']}. Sincronizando visitas...", "info")

    result = _sync_cuenta_visits(cuenta, client)

    if result.get("ok"):
        flash(f"✅ Sincronizadas {result['sincronizadas']} visitas", "success")
        if client.refresh_token and client.refresh_token != cuenta.get("refresh_token"):
            db.actualizar_cuenta(cuenta["id"], refresh_token=client.refresh_token)
    else:
        flash(f"✗ Error en sync de visitas: {result.get('error', 'desconocido')}", "danger")

    return redirect(url_for("metricas"))


@app.route("/metricas")
def metricas():
    """Muestra métricas de visitas con tabla ordenada por visitas DESC."""
    cuenta = get_active_cuenta()
    if not cuenta:
        flash("No hay cuenta activa", "warning")
        return redirect(url_for("cuentas"))

    metricas_rows = db.get_metricas_detalle(cuenta_id=cuenta["id"])

    return render_template("metricas.html",
                           metricas=metricas_rows,
                           page="metricas")


# ─── Stats / Analytics ─────────────────────────────────────

@app.route("/stats")
def stats():
    cuenta = get_active_cuenta()
    if not cuenta:
        flash("Conectá una cuenta primero", "warning")
        return redirect(url_for("cuentas"))

    meses = db.get_revenue_mensual(cuenta["id"])
    top = db.get_top_productos(cuenta["id"])
    resumen = db.get_stats_resumen(cuenta["id"])

    # Calcular variación porcentual
    act = resumen["actual"]["revenue"]
    ant = resumen["anterior"]["revenue"]
    variacion = ((act - ant) / ant * 100) if ant > 0 else 0

    return render_template("stats.html",
                           meses=meses,
                           top=top,
                           resumen=resumen,
                           variacion=variacion,
                           page="stats")


# ─── Ventas ──────────────────────────────────────────────────

@app.route("/ventas")
def ventas():
    """Muestra la sección de ventas con órdenes sincronizadas."""
    cuenta = get_active_cuenta()
    cuenta_id = cuenta["id"] if cuenta else None

    if not cuenta_id:
        flash("No hay cuenta activa. Conectá una desde Cuentas.", "warning")
        return redirect(url_for("cuentas"))

    fecha_desde = request.args.get("fecha_desde", "")
    fecha_hasta = request.args.get("fecha_hasta", "")
    estado = request.args.get("estado", "")
    page = request.args.get("page", 1, type=int)
    sort_order = request.args.get("sort_order", "desc")

    # Check if we have orders at all before querying
    total_orders = db.count_ordenes(cuenta_id, fecha_desde, fecha_hasta, estado)

    if total_orders == 0:
        return render_template("ventas.html",
                               ordenes=[],
                               pagina=1,
                               pages=1,
                               total=0,
                               per_page=50,
                               fecha_desde=fecha_desde,
                               fecha_hasta=fecha_hasta,
                               estado=estado,
                               sort_order=sort_order,
                               empty=True,
                               page="ventas")

    result = db.listar_ordenes(
        cuenta_id=cuenta_id,
        desde=fecha_desde,
        hasta=fecha_hasta,
        estado=estado,
        page=page,
        per_page=50,
        sort_order=sort_order,
    )

    return render_template("ventas.html",
                           ordenes=result["rows"],
                           pagina=result["page"],
                           pages=result["pages"],
                           total=result["total"],
                           per_page=result["per_page"],
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta,
                           estado=estado,
                           sort_order=sort_order,
                           empty=False,
                           page="ventas")


@app.route("/meli/sync")
def meli_sync():
    """Verifica conexión y sincroniza publicaciones desde MELI."""
    cuenta = get_active_cuenta()
    if not cuenta:
        flash("No hay cuenta activa. Conectá una desde Cuentas.", "warning")
        return redirect(url_for("cuentas"))

    # 1. Primero verificar la conexión y refrescar token si es necesario
    client = get_meli_client(cuenta)
    conn = client.check_connection()

    if not conn.get("connected"):
        session["meli_connected"] = False
        error_msg = conn.get("error", "desconocido")
        # Si es error de refresh_token, sugerir reconectar
        if "refresh_token" in str(error_msg).lower() or "401" in str(error_msg):
            flash(f"✗ Token expirado o inválido. Reconectá la cuenta desde Cuentas.", "danger")
        else:
            flash(f"✗ Error de conexión: {error_msg}", "danger")
        return redirect(url_for("cuentas"))

    # 2. Conexión OK — actualizar sesión y persistir token nuevo
    session["meli_connected"] = True
    session["meli_nickname"] = conn["nickname"]
    db.actualizar_cuenta(cuenta["id"],
                         nickname=conn["nickname"],
                         user_id=str(conn["user_id"]))
    if conn.get("refresh_token") and conn["refresh_token"] != cuenta["refresh_token"]:
        db.actualizar_cuenta(cuenta["id"], refresh_token=conn["refresh_token"])
        cuenta["refresh_token"] = conn["refresh_token"]

    flash(f"🔌 Conectado como {conn['nickname']}. Sincronizando publicaciones...", "info")

    # 3. Sincronizar
    result = _sync_cuenta_items(cuenta, client)

    if result.get("ok"):
        flash(f"✅ Sync completada: {result['creados']} creadas, {result['actualizados']} actualizadas, {result['errores']} errores", "success")
        if client.refresh_token and client.refresh_token != cuenta.get("refresh_token"):
            db.actualizar_cuenta(cuenta["id"], refresh_token=client.refresh_token)
    else:
        flash(f"✗ Error en sync: {result.get('error', 'desconocido')}", "danger")

    return redirect(url_for("dashboard"))


# ─── Productos ─────────────────────────────────────────────

@app.route("/productos")
def productos():
    cuenta = get_active_cuenta()
    search = request.args.get("search", "")
    prods = db.listar_productos_agrupados(cuenta_id=cuenta["id"] if cuenta else None, search=search)
    return render_template("products.html",
                           productos=prods,
                           search=search,
                           page="productos")


@app.route("/productos/nuevo", methods=["GET", "POST"])
def producto_nuevo():
    cuenta = get_active_cuenta()
    if request.method == "POST":
        pid = db.crear_producto(
            cuenta_id=cuenta["id"],
            nombre=request.form["nombre"],
            sku=request.form.get("sku", ""),
            marca=request.form.get("marca", ""),
            modelo=request.form.get("modelo", ""),
            color=request.form.get("color", ""),
            costo=float(request.form.get("costo", 0) or 0),
            stock=int(request.form.get("stock", 0) or 0),
            categoria_id=request.form.get("categoria_id", "MLA1055"),
            catalog_product_id=request.form.get("catalog_product_id", ""),
        )
        flash(f"✓ Producto '{request.form['nombre']}' creado", "success")
        return redirect(url_for("productos"))
    return render_template("product_form.html", producto=None, page="productos")


@app.route("/productos/<int:pid>/editar", methods=["GET", "POST"])
def producto_editar(pid):
    producto = db.get_producto(pid)
    if not producto:
        flash("Producto no encontrado", "danger")
        return redirect(url_for("productos"))
    if request.method == "POST":
        db.actualizar_producto(pid,
            nombre=request.form["nombre"],
            sku=request.form.get("sku", ""),
            marca=request.form.get("marca", ""),
            modelo=request.form.get("modelo", ""),
            color=request.form.get("color", ""),
            costo=float(request.form.get("costo", 0) or 0),
            stock=int(request.form.get("stock", 0) or 0),
            categoria_id=request.form.get("categoria_id", "MLA1055"),
            catalog_product_id=request.form.get("catalog_product_id", ""),
        )
        flash("✓ Producto actualizado", "success")
        return redirect(url_for("productos"))
    return render_template("product_form.html", producto=producto, page="productos")


@app.route("/productos/eliminar", methods=["POST"])
def producto_eliminar():
    """Elimina un producto (y sus variantes del mismo nombre)."""
    nombre = request.form.get("nombre", "")
    pid = request.form.get("pid", "")
    cuenta = get_active_cuenta()
    if nombre and cuenta:
        db.eliminar_productos_por_nombre(nombre, cuenta["id"])
        flash(f"✓ '{nombre}' y sus variantes eliminados", "success")
    elif pid:
        db.eliminar_producto(int(pid))
        flash("✓ Producto eliminado", "success")
    else:
        flash("✗ No se especificó producto", "warning")
    return redirect(url_for("productos"))


# ─── Calculadora ────────────────────────────────────────────

@app.route("/calculadora", methods=["GET", "POST"])
def calculadora():
    resultados = []
    costo = 0
    margen = 20
    modo = "margen"

    if request.method == "POST":
        costo = float(request.form.get("costo", 0) or 0)
        modo = request.form.get("modo", "margen")

        if modo == "garantizado":
            ganancia_min = float(request.form.get("ganancia_minima", 0) or 0)
            for lt, campañas in CAMPAIGN_OPTIONS.items():
                for camp in campañas:
                    res = calcular_precio_garantizado(
                        costo, ganancia_min, lt, camp["id"]
                    )
                    res["campaign_label"] = camp["label"]
                    res["cuotas"] = camp["cuotas"]
                    res["listing_type"] = lt
                    resultados.append(res)
        else:
            margen = float(request.form.get("margen", 20) or 20)
            resultados = calcular_todas_las_opciones(costo, margen)

    return render_template("calculator.html",
                           resultados=resultados,
                           costo=costo,
                           margen=margen,
                           modo=modo,
                           page="calculadora",
                           campaign_options=json.dumps(CAMPAIGN_OPTIONS))


@app.route("/api/calcular", methods=["POST"])
def api_calcular():
    data = request.json
    costo = float(data.get("costo", 0))
    margen = float(data.get("margen", 20))
    listing_type = data.get("listing_type", "gold_special")
    campaign = data.get("campaign", "no-campaign")
    res = calcular_precio_venta(costo, margen, listing_type, campaign)
    return jsonify(res)


# ─── Publicar en MELI ───────────────────────────────────────

@app.route("/publicar", methods=["GET", "POST"])
def publicar():
    cuenta = get_active_cuenta()
    if not cuenta:
        flash("Primero conectá una cuenta de MercadoLibre desde Cuentas", "warning")
        return redirect(url_for("cuentas"))

    productos = db.listar_productos_agrupados(cuenta_id=cuenta["id"])
    client = get_meli_client(cuenta)

    if request.method == "POST":
        producto_id = int(request.form["producto_id"])
        producto = db.get_producto(producto_id)
        if not producto:
            flash("Producto no encontrado", "danger")
            return redirect(url_for("publicar"))

        precio = float(request.form.get("precio", 0))
        listing_type = request.form.get("listing_type", "gold_special")
        campaign_tag = request.form.get("campaign_tag", "")
        stock = int(request.form.get("stock", 1))
        family_name = request.form.get("family_name", "")

        catalog_pid = producto.get("catalog_product_id") or ""
        if not catalog_pid:
            flash("El producto necesita un catalog_product_id para publicar", "danger")
            return redirect(url_for("publicar"))

        result = client.crear_publicacion(
            catalog_product_id=catalog_pid,
            price=precio,
            listing_type=listing_type,
            campaign_tag=campaign_tag,
            stock=stock,
            category_id=producto.get("categoria_id", "MLA1055"),
            family_name=family_name,
        )

        if result["success"]:
            db.crear_publicacion(
                cuenta_id=cuenta["id"],
                producto_id=producto_id,
                precio=precio,
                listing_type=listing_type,
                campaign_tag=campaign_tag,
                stock=stock,
                meli_item_id=result["item_id"],
                titulo=result.get("title", producto["nombre"]),
                estado="activo" if result.get("status") == "active" else "borrador",
                url=result.get("permalink", ""),
            )
            # Actualizar refresh_token si cambió
            if client.refresh_token and client.refresh_token != cuenta["refresh_token"]:
                db.actualizar_cuenta(cuenta["id"], refresh_token=client.refresh_token)
            flash(f"✓ Publicado: {result['item_id']}", "success")
        else:
            flash(f"✗ Error: {result.get('error', 'desconocido')}", "danger")

        return redirect(url_for("publicaciones"))

    return render_template("publish.html",
                           productos=productos,
                           campaign_options=CAMPAIGN_OPTIONS,
                           page="publicar")


@app.route("/publicaciones")
def publicaciones():
    cuenta = get_active_cuenta()
    search = request.args.get("search", "")
    pubs = db.listar_publicaciones(cuenta_id=cuenta["id"] if cuenta else None, search=search)

    # Adjuntar visitas si hay cuenta activa
    visitas_dict = {}
    if cuenta:
        visitas_dict = db.get_visitas(cuenta["id"])
    for pub in pubs:
        pub["visitas"] = visitas_dict.get(pub.get("meli_item_id", ""))

    return render_template("publications.html",
                           publicaciones=pubs,
                           search=search,
                           page="publicaciones")


@app.route("/publicaciones/<int:pid>/accion", methods=["POST"])
def publicacion_accion(pid):
    cuenta = get_active_cuenta()
    pub = db.get_publicacion(pid)
    if not pub:
        flash("Publicación no encontrada", "danger")
        return redirect(url_for("publicaciones"))

    accion = request.form.get("accion", "")
    meli_id = pub.get("meli_item_id", "")
    client = get_meli_client(cuenta)

    if accion == "pausar" and meli_id:
        r = client.pausar_publicacion(meli_id)
        if r.get("success"):
            db.actualizar_publicacion(pid, estado="pausado")
            flash(f"✓ Publicación {meli_id} pausada", "success")
        else:
            flash(f"✗ Error: {r.get('error', 'desconocido')}", "danger")
    elif accion == "activar" and meli_id:
        r = client.activar_publicacion(meli_id)
        if r.get("success"):
            db.actualizar_publicacion(pid, estado="activo")
            flash(f"✓ Publicación {meli_id} activada", "success")
        else:
            flash(f"✗ Error: {r.get('error', 'desconocido')}", "danger")
    elif accion == "actualizar_precio":
        precio = float(request.form.get("precio", 0))
        if meli_id and precio > 0:
            r = client.actualizar_precio(meli_id, precio)
            if r.get("success"):
                db.actualizar_publicacion(pid, precio=precio)
                flash(f"✓ Precio actualizado a ${precio:,.0f}", "success")
            else:
                flash(f"✗ Error: {r.get('error', 'desconocido')}", "danger")
    elif accion == "eliminar":
        if meli_id:
            client.pausar_publicacion(meli_id)
        db.eliminar_publicacion(pid)
        flash("✓ Publicación eliminada", "success")

    # Actualizar refresh_token si cambió
    if client.refresh_token and cuenta and client.refresh_token != cuenta.get("refresh_token"):
        db.actualizar_cuenta(cuenta["id"], refresh_token=client.refresh_token)

    return redirect(url_for("publicaciones"))


# ─── Importar / Exportar ────────────────────────────────────

MAX_EXCEL_ROWS = 5000


def _build_workbook(rows, sheet_name="Productos"):
    """Crea un workbook en memoria con openpyxl."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    headers = ["Nombre", "SKU", "Marca", "Modelo", "Color",
               "Costo", "Stock", "Variantes", "Publicaciones"]
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row_idx, row in enumerate(rows, 2):
        ws.cell(row=row_idx, column=1, value=row.get("nombre", ""))
        ws.cell(row=row_idx, column=2, value=row.get("sku", ""))
        ws.cell(row=row_idx, column=3, value=row.get("marca", ""))
        ws.cell(row=row_idx, column=4, value=row.get("modelo", ""))
        ws.cell(row=row_idx, column=5, value=row.get("color", ""))
        ws.cell(row=row_idx, column=6, value=row.get("costo", 0))
        ws.cell(row=row_idx, column=7, value=row.get("stock", 0))
        ws.cell(row=row_idx, column=8, value=row.get("variantes", 1))
        ws.cell(row=row_idx, column=9, value=row.get("publicaciones", 0))

    for col in range(1, len(headers) + 1):
        ws.column_dimensions[chr(64 + col)].width = 22

    return wb


@app.route("/importar", methods=["GET", "POST"])
def importar():
    cuenta = get_active_cuenta()
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Seleccioná un archivo", "warning")
            return redirect(url_for("importar"))

        filename = file.filename
        contenido = file.read()

        if not contenido.strip():
            flash("Archivo vacío", "warning")
            return redirect(url_for("importar"))

        filas_importadas = 0
        filas_errores = 0
        errores = []

        if filename.endswith(".csv"):
            decoded = contenido.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(decoded))
            for i, row in enumerate(reader):
                try:
                    db.crear_producto(
                        cuenta_id=cuenta["id"],
                        nombre=row.get("Nombre", ""),
                        sku=row.get("SKU", ""),
                        marca=row.get("Marca", ""),
                        modelo=row.get("Modelo", ""),
                        color=row.get("Color", ""),
                        costo=float(row.get("Costo", 0) or 0),
                        stock=int(row.get("Stock", 0) or 0),
                        categoria_id=row.get("Categoría ID", "MLA1055"),
                        catalog_product_id=row.get("Catalog Product ID", ""),
                    )
                    filas_importadas += 1
                except Exception as e:
                    filas_errores += 1
                    errores.append(f"Fila {i+2}: {e}")

        elif filename.endswith(".xlsx"):
            from openpyxl import load_workbook
            wb = load_workbook(io.BytesIO(contenido))
            ws = wb.active
            rows_iter = ws.iter_rows(min_row=2, values_only=True)
            for i, row in enumerate(rows_iter):
                try:
                    if not row[0] or not str(row[0]).strip():
                        continue
                    db.crear_producto(
                        cuenta_id=cuenta["id"],
                        nombre=str(row[0] or "").strip(),
                        sku=str(row[1] or "").strip(),
                        marca=str(row[2] or "").strip(),
                        modelo=str(row[3] or "").strip(),
                        color=str(row[4] or "").strip(),
                        costo=float(row[5] or 0),
                        stock=int(row[6] or 0),
                        categoria_id=str(row[7] or "MLA1055").strip(),
                        catalog_product_id=str(row[8] or "").strip(),
                    )
                    filas_importadas += 1
                except Exception as e:
                    filas_errores += 1
                    errores.append(f"Fila {i+2}: {e}")

        resultado = {
            "importadas": filas_importadas,
            "errores": filas_errores,
            "detalle_errores": errores[:10],
        }

        flash(f"Importación completada: {filas_importadas} filas, {filas_errores} errores", "success")
        return render_template("import_result.html", resultado=resultado, page="importar")

    return render_template("import_export.html", page="importar")


@app.route("/exportar")
def exportar():
    cuenta = get_active_cuenta()
    fmt = request.args.get("formato", "csv")
    productos = db.listar_productos_agrupados(cuenta_id=cuenta["id"] if cuenta else None)

    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Nombre", "SKU", "Marca", "Modelo", "Color",
                         "Costo", "Stock", "Variantes", "Publicaciones"])
        for p in productos:
            writer.writerow([
                p["nombre"], p["sku"], p["marca"], p["modelo"],
                p["color"], p["costo"], p["stock"],
                p["variantes"], p["publicaciones"],
            ])
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"productos_{datetime.now().strftime('%Y%m%d')}.csv",
        )
    else:
        wb = _build_workbook(productos)
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"productos_{datetime.now().strftime('%Y%m%d')}.xlsx",
        )


# ─── Configuración ──────────────────────────────────────────

@app.route("/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        db.set_config("default_listing_type", request.form.get("default_listing_type", "gold_special"))
        db.set_config("default_margen", request.form.get("default_margen", "20"))
        db.set_config("default_shipping", "me2")
        flash("✓ Configuración guardada", "success")
        return redirect(url_for("config"))

    config_data = db.get_all_config()
    return render_template("config.html",
                           config_data=config_data,
                           page="config")


# ─── Main ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  MELI Manager — App corriendo en http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="127.0.0.1", port=5000)
