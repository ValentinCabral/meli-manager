"""MELI Manager — Publication Price Calculator"""

import math
from config import FEE_RATES, CAMPAIGN_OPTIONS


def calcular_precio_venta(costo: float, margen_deseado: float,
                          listing_type: str, campaign: str) -> dict:
    """
    Calcula el precio de venta necesario para obtener un margen deseado
    después de comisiones de MercadoLibre.

    costo: precio de costo del producto
    margen_deseado: porcentaje de margen sobre el costo (ej: 20 = 20%)
    listing_type: gold_special | gold_pro
    campaign: no-campaign | 3x_campaign | 9x_campaign | 12x_campaign | pcj-co-funded
    """
    fee_rate = _get_fee_rate(listing_type, campaign)

    # Fórmula: precio = costo * (1 + margen/100) / (1 - fee_rate)
    # Esto asegura que: precio - (precio * fee_rate) >= costo * (1 + margen/100)
    factor_costo = 1 + (margen_deseado / 100)
    precio_base = costo * factor_costo / (1 - fee_rate)
    precio_venta = math.ceil(precio_base)  # Redondeo hacia arriba

    # Cálculos
    comision = math.ceil(precio_venta * fee_rate)
    ganancia_neta = precio_venta - comision - costo

    return {
        "costo": round(costo, 2),
        "margen_deseado": margen_deseado,
        "precio_venta": precio_venta,
        "comision_ml": comision,
        "fee_rate": round(fee_rate * 100, 2),
        "ganancia_neta": ganancia_neta,
        "margen_real": round((ganancia_neta / costo) * 100, 2) if costo > 0 else 0,
        "listing_type": listing_type,
        "campaign": campaign,
    }


def calcular_todas_las_opciones(costo: float, margen_deseado: float) -> list:
    """Calcula precio para todas las combinaciones listing_type + campaign."""
    resultados = []
    for listing_type, campañas in CAMPAIGN_OPTIONS.items():
        for camp in campañas:
            res = calcular_precio_venta(costo, margen_deseado,
                                       listing_type, camp["id"])
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
                                listing_type: str, campaign: str) -> dict:
    """
    Calcula el precio mínimo de venta para garantizar una ganancia neta mínima.
    Esto replica lo que hicimos con las 20 publicaciones.

    Precio = (costo + ganancia_minima) / (1 - fee_rate)
    """
    fee_rate = _get_fee_rate(listing_type, campaign)

    precio_base = (costo + ganancia_minima) / (1 - fee_rate)
    precio_venta = math.ceil(precio_base)

    comision = math.ceil(precio_venta * fee_rate)
    ganancia_neta = precio_venta - comision - costo

    return {
        "costo": round(costo, 2),
        "ganancia_minima_solicitada": round(ganancia_minima, 2),
        "precio_venta": precio_venta,
        "comision_ml": comision,
        "fee_rate": round(fee_rate * 100, 2),
        "ganancia_neta": ganancia_neta,
        "cumple_minimo": ganancia_neta >= ganancia_minima,
        "listing_type": listing_type,
        "campaign": campaign,
    }
