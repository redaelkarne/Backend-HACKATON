"""
Seed the tyres table from recommend.json.

Usage (from project root):
    docker compose exec api python seed_tyres.py
"""

import asyncio
import json
import os
import random

from app.database import AsyncSessionLocal
from app.models.models import Tyre
from sqlalchemy import select, text

KEY_MAP = {
    "Brand": "brand",
    "Product Type": "product_type",
    "Cycle Type": "cycle_type",
    "Segment": "segment",
    "Bead": "bead",
    "Width ETRTO": "width_etrto",
    "Diameter ETRTO": "diameter_etrto",
    "Type (Tube)": "type_tube",
    "Valve (Tube)": "valve_tube",
    "Valve Length": "valve_length",
    "EAN Code": "ean_code",
    "Discontinued Date": "discontinued_date",
    "Weight (g)": "weight_g",
    "Market Perimeter": "market_perimeter",
    "Web Range Name": "web_range_name",
    "Web Diameter (mm)": "web_diameter_mm",
    "Web Diameter (Inch)": "web_diameter_inch",
    "Web Width (mm)": "web_width_mm",
    "Web Width (Inch)": "web_width_inch",
    "Rim Type": "rim_type",
    "Web Product Designation": "web_product_designation",
    "Fitting": "fitting",
    "TPI": "tpi",
    "Minimum Pressure (Bar)": "min_pressure_bar",
    "Maximum Pressure (Bar)": "max_pressure_bar",
    "Minimum Pressure (Psi)": "min_pressure_psi",
    "Maximum Pressure (Psi)": "max_pressure_psi",
    "Recommended Inner Tube": "recommended_inner_tube",
    "Sidewall Type": "sidewall_type",
    "Sealing": "sealing",
    "Shore": "shore",
    "Sidewall Color": "sidewall_color",
    "Tread Pattern Color": "tread_pattern_color",
    "Terrain Types": "terrain_types",
    "Use": "use",
    "Rubber Technologies": "rubber_technologies",
    "Casing Technologies": "casing_technologies",
    "Tread Pattern Technologies": "tread_pattern_technologies",
    "Reinforcement Technologies": "reinforcement_technologies",
    "E-Bike Technologies": "ebike_technologies",
    "Reflective strip": "reflective_strip",
    "Knurling strip": "knurling_strip",
    "Shoulder Color": "shoulder_color",
    "Border Color": "border_color",
    "CYCLE TYPE WEB": "cycle_type_web",
    "PIC1": "pic1",
    "PIC2": "pic2",
}

JSON_PATH = os.path.join(os.path.dirname(__file__), "recommend.json")


async def seed():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Tyre).limit(1))
        if existing.scalar_one_or_none():
            print("Tyres table already has data — skipping seed.")
            return

        for rec in records:
            kwargs = {model_col: rec.get(json_key, "") or None for json_key, model_col in KEY_MAP.items()}
            kwargs["price"] = round(random.uniform(60, 115), 2)
            session.add(Tyre(**kwargs))

        await session.commit()
        print(f"Done. Inserted {len(records)} tyres.")


if __name__ == "__main__":
    asyncio.run(seed())
