"""MELI Manager — Publication Price Calculator"""

import math
from config import FEE_RATES, CAMPAIGN_OPTIONS


def calcular_precio_venta(costo: float, margen_deseado: float,
                          listing_type: str, campaign: str,
                          envio: float = 0, iibb_pct: float = 0) -> dict:
    """
    Calcula el precio de venta necesario para obtener un margen deseado
    después de comisiones de MercadoLibre.

    costo: precio de costo del producto
    margen_deseado: porcentaje de margen sobre el costo (ej: 20 = 20%)
    listing_type: gold_special | gold_pro
    campaign: no-campaign | 3x_campaign | 9x_campaign | 12x_campaign | pcj-co-funded
    envio: costo de envío (se suma al costo base)
    iibb_pct: porcentaje de IIBB sobre el precio de venta (ej: 3 = 3%)
    """
    fee_rate = _get_fee_rate(listing_type, campaign)
    fee_total = fee_rate + (iibb_pct / 100)
    costo_total = costo + envio

    # Fórmula: precio = costo_total * (1 + margen/100) / (1 - fee_total)
    factor_costo = 1 + (margen_deseado / 100)
    precio_base = costo_total * factor_costo / (1 - fee_total)
    precio_venta = math.ceil(precio_base)

    # Cálculos por componente
    comision = math.ceil(precio_venta * fee_rate)
    iibb = math.ceil(precio_venta * iibb_pct / 100)
    costos_totales = costo + envio + comision + iibb
    ganancia_neta = precio_venta - costos_totales

    return {
        "costo": round(costo, 2),
        "envio": round(envio, 2),
        "iibb_pct": iibb_pct,
        "iibb": iibb,
        "margen_deseado": margen_deseado,
        "precio_venta": precio_venta,
        "comision_ml": comision,
        "fee_rate": round(fee_rate * 100, 2),
        "fee_total_pct": round(fee_total * 100, 2),
        "ganancia_neta": ganancia_neta,
        "margen_real": round((ganancia_neta / costo) * 100, 2) if costo > 0 else 0,
        "listing_type": listing_type,
        "campaign": campaign,
    }


def calcular_todas_las_opciones(costo: float, margen_deseado: float,
                                 envio: float = 0, iibb_pct: float = 0) -> list:
    """Calcula precio para todas las combinaciones listing_type + campaign."""
    resultados = []
    for listing_type, campañas in CAMPAIGN_OPTIONS.items():
        for camp in campañas:
            res = calcular_precio_venta(costo, margen_deseado,
                                       listing_type, camp["id"],
                                       envio=envio, iibb_pct=iibb_pct)
            res["campaign_label"] = camp["label"]
            res["cuotas"] = camp["cuotas"]
            resultados.append(res)
    return resultados


def _get_fee_rate(listing_type: str, campaign: str) -> float:
    """Obtiene la tasa de comisión para una combinación dada."""
    rates = FEE_RATES.get(listing_type, {})
    # Para gold_special sin campaña específica, usar no-campaign
    if campaign in rates:
        return rates[campaign]
    # Fallback: usar el primer rate disponible
    if rates:
        return list(rates.values())[0]
    return 0.15  # fallback seguro


def calcular_precio_garantizado(costo: float, ganancia_minima: float,
                                listing_type: str, campaign: str,
                                envio: float = 0, iibb_pct: float = 0) -> dict:
    """
    Calcula el precio mínimo de venta para garantizar una ganancia neta mínima.

    Precio = (costo + envio + ganancia_minima) / (1 - fee_rate - iibb_pct/100)
    """
    fee_rate = _get_fee_rate(listing_type, campaign)
    fee_total = fee_rate + (iibb_pct / 100)
    costo_total = costo + envio

    precio_base = (costo_total + ganancia_minima) / (1 - fee_total)
    precio_venta = math.ceil(precio_base)

    comision = math.ceil(precio_venta * fee_rate)
    iibb = math.ceil(precio_venta * iibb_pct / 100)
    costos_totales = costo + envio + comision + iibb
    ganancia_neta = precio_venta - costos_totales

    return {
        "costo": round(costo, 2),
        "envio": round(envio, 2),
        "iibb_pct": iibb_pct,
        "iibb": iibb,
        "ganancia_minima_solicitada": round(ganancia_minima, 2),
        "precio_venta": precio_venta,
        "comision_ml": comision,
        "fee_rate": round(fee_rate * 100, 2),
        "fee_total_pct": round(fee_total * 100, 2),
        "ganancia_neta": ganancia_neta,
        "cumple_minimo": ganancia_neta >= ganancia_minima,
        "listing_type": listing_type,
        "campaign": campaign,
    }


def calcular_precio_por_neto_deseado(costo: float, neto_deseado: float,
                                     listing_type: str, campaign: str,
                                     envio: float = 0, iibb_pct: float = 0) -> dict:
    """
    Calcula el precio de venta para recibir un neto deseado después de comisiones.
    Útil para: "Quiero recibir $X después de comisiones, ¿a qué precio vendo?".

    neto_deseado: lo que querés recibir (después de comisiones, envío e IIBB)
    Precio = (neto_deseado + costo + envio) / (1 - fee_rate - iibb_pct/100)
    """
    fee_rate = _get_fee_rate(listing_type, campaign)
    fee_total = fee_rate + (iibb_pct / 100)
    costo_total = costo + envio

    precio_base = (costo_total + neto_deseado) / (1 - fee_total)
    precio_venta = math.ceil(precio_base)

    comision = math.ceil(precio_venta * fee_rate)
    iibb = math.ceil(precio_venta * iibb_pct / 100)
    costos_totales = costo + envio + comision + iibb
    ganancia_neta = precio_venta - costos_totales

    return {
        "costo": round(costo, 2),
        "envio": round(envio, 2),
        "iibb_pct": iibb_pct,
        "iibb": iibb,
        "neto_deseado": round(neto_deseado, 2),
        "precio_venta": precio_venta,
        "comision_ml": comision,
        "fee_rate": round(fee_rate * 100, 2),
        "fee_total_pct": round(fee_total * 100, 2),
        "recupero_costo": round(ganancia_neta, 2),
        "ganancia_neta": round(ganancia_neta, 2),
        "cumple_neto": (precio_venta - comision - envio - iibb) >= neto_deseado,
        "listing_type": listing_type,
        "campaign": campaign,
    }
