"""MELI Manager — Configuration"""

import os
from dotenv import load_dotenv

load_dotenv()

# MercadoLibre API — setea en Environment Variables de Render
# Local: usa creds viejas por defecto; Render: setear ML_CLIENT_ID/SECRET con las nuevas
ML_CLIENT_ID = os.getenv("ML_CLIENT_ID", "3820687071874406")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET", "crSeIoEp4yQIzZwgoWGVhuE4X0EJpP9Y")
ML_REFRESH_TOKEN = os.getenv("ML_REFRESH_TOKEN", "")
ML_SITE_ID = os.getenv("ML_SITE_ID", "MLA")

# Defaults
DEFAULT_CATEGORY = "MLA1055"  # Celulares
DEFAULT_MARGEN = 20  # 20%
DEFAULT_LISTING_TYPE = "gold_special"

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meli_manager.db")

# Publication fee rates by scenario (MLA-CELLPHONES)
# These are the fees we calculated
FEE_RATES = {
    "gold_special": {
        "no-campaign": 0.1277,     # Sin cuotas
    },
    "gold_pro": {
        "no-campaign": 0.2507,     # 6 cuotas default
        "3x_campaign": 0.2117,     # 3 cuotas con campaña
        "9x_campaign": 0.2847,     # 9 cuotas con campaña
        "12x_campaign": 0.3197,    # 12 cuotas con campaña
    }
}

CAMPAIGN_OPTIONS = {
    "gold_special": [
        {"id": "no-campaign", "label": "Sin cuotas", "cuotas": 0, "fee": 0.1277},
        {"id": "pcj-co-funded", "label": "3 a 12 cuotas c/interés bajo", "cuotas": "3-12", "fee": 0.16},
    ],
    "gold_pro": [
        {"id": "3x_campaign", "label": "3 cuotas sin interés", "cuotas": 3, "fee": 0.2117},
        {"id": "no-campaign", "label": "6 cuotas sin interés", "cuotas": 6, "fee": 0.2507},
        {"id": "9x_campaign", "label": "9 cuotas sin interés", "cuotas": 9, "fee": 0.2847},
        {"id": "12x_campaign", "label": "12 cuotas sin interés", "cuotas": 12, "fee": 0.3197},
    ]
}
