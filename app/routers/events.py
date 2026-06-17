from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.common import ApiResponse, build_meta

router = APIRouter(prefix="/events", tags=["Events"])

_EVENTS = [
    {
        "id": 1,
        "title": "La Marmotte",
        "category": "Cyclosportive",
        "date_start": "05/07/2026",
        "date_end": "05/07/2026",
        "location": "Bourg-d'Oisans",
        "region": "Auvergne-Rhône-Alpes",
        "country": "FRANCE",
        "distance_km": 174,
        "elevation_m": 5000,
        "description": "La cyclosportive mythique des Alpes passant par l'Alpe d'Huez, le Col du Galibier et le Col du Télégraphe.",
        "website": "https://www.sportcommunication.info/la-marmotte",
    },
    {
        "id": 2,
        "title": "Gran Fondo du Ventoux",
        "category": "Gran Fondo",
        "date_start": "19/07/2026",
        "date_end": "19/07/2026",
        "location": "Carpentras",
        "region": "Provence-Alpes-Côte d'Azur",
        "country": "FRANCE",
        "distance_km": 145,
        "elevation_m": 3500,
        "description": "Montée mythique du Mont Ventoux depuis Bédoin avec passage par les Dentelles de Montmirail.",
        "website": "https://www.granfonduventoux.fr",
    },
    {
        "id": 3,
        "title": "Cyclosportive des Vosges",
        "category": "Cyclosportive",
        "date_start": "30/08/2026",
        "date_end": "30/08/2026",
        "location": "Gérardmer",
        "region": "Grand Est",
        "country": "FRANCE",
        "distance_km": 120,
        "elevation_m": 2800,
        "description": "Tour des plus beaux cols vosgiens au départ du lac de Gérardmer.",
        "website": None,
    },
    {
        "id": 4,
        "title": "L'Étape du Tour 2026",
        "category": "Cyclosportive",
        "date_start": "12/07/2026",
        "date_end": "12/07/2026",
        "location": "Nice",
        "region": "Provence-Alpes-Côte d'Azur",
        "country": "FRANCE",
        "distance_km": 138,
        "elevation_m": 4000,
        "description": "Vivez une étape du Tour de France en conditions réelles, sur route fermée à la circulation.",
        "website": "https://www.letapedutour.com",
    },
    {
        "id": 5,
        "title": "Paris-Brest-Paris (Randonnée)",
        "category": "Randonnée",
        "date_start": "17/08/2027",
        "date_end": "22/08/2027",
        "location": "Rambouillet",
        "region": "Île-de-France",
        "country": "FRANCE",
        "distance_km": 1200,
        "elevation_m": 11000,
        "description": "La plus grande randonnée cycliste du monde, 1200 km à parcourir en moins de 90 heures.",
        "website": "https://www.paris-brest-paris.org",
    },
    {
        "id": 6,
        "title": "Bordeaux-Saintes",
        "category": "Cyclosportive",
        "date_start": "06/09/2026",
        "date_end": "06/09/2026",
        "location": "Bordeaux",
        "region": "Nouvelle-Aquitaine",
        "country": "FRANCE",
        "distance_km": 100,
        "elevation_m": 800,
        "description": "Cyclosportive traversant vignobles et campagnes charentaises.",
        "website": None,
    },
    {
        "id": 7,
        "title": "La Pyrénéenne",
        "category": "Gran Fondo",
        "date_start": "13/09/2026",
        "date_end": "13/09/2026",
        "location": "Lourdes",
        "region": "Occitanie",
        "country": "FRANCE",
        "distance_km": 160,
        "elevation_m": 4600,
        "description": "Traversée des Pyrénées avec ascension du Col du Tourmalet et du Col d'Aubisque.",
        "website": "https://www.lapyreneenne.fr",
    },
    {
        "id": 8,
        "title": "Raid Roussillon VTT",
        "category": "VTT / Gravel",
        "date_start": "27/09/2026",
        "date_end": "27/09/2026",
        "location": "Perpignan",
        "region": "Occitanie",
        "country": "FRANCE",
        "distance_km": 85,
        "elevation_m": 2200,
        "description": "Parcours gravel entre mer et montagne à travers les Corbières et le Roussillon.",
        "website": None,
    },
]


@router.get("", response_model=ApiResponse[list[dict]])
async def list_events(
    country: Optional[str] = Query(None, description="Filter by country name (case-insensitive)"),
    category: Optional[str] = Query(None, description="Filter by category, e.g. 'Gran Fondo'"),
    region: Optional[str] = Query(None, description="Filter by French region (case-insensitive)"),
):
    """Return upcoming cycling events in France."""
    events = list(_EVENTS)

    if country:
        events = [e for e in events if e["country"].lower() == country.lower()]
    if category:
        events = [e for e in events if category.lower() in e["category"].lower()]
    if region:
        events = [e for e in events if region.lower() in e["region"].lower()]

    return ApiResponse(data=events, meta=build_meta())
