from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TyreRecommendationRequest(BaseModel):
    bike_type: Literal["road", "gravel", "mtb", "city", "ebike"] = Field(
        ...,
        description=(
            "Type of bike:\n"
            "- **road** — Road / racing bike\n"
            "- **gravel** — Gravel / adventure bike\n"
            "- **mtb** — Mountain bike\n"
            "- **city** — City / commuting / trekking bike\n"
            "- **ebike** — Dedicated e-bike (any discipline)"
        ),
        examples=["road"],
    )

    riding_style: Literal[
        "racing",
        "endurance",
        "all_road",
        "touring",
        "trekking",
        "urban",
        "cross_country",
        "trail",
        "enduro",
        "downhill",
    ] = Field(
        ...,
        description=(
            "How you ride. Use only the values relevant to the selected `bike_type`:\n\n"
            "**road** → `racing`, `endurance`\n\n"
            "**gravel** → `endurance`, `all_road`, `touring`\n\n"
            "**mtb** → `cross_country`, `trail`, `enduro`, `downhill`\n\n"
            "**city** → `urban`, `trekking`, `touring`\n\n"
            "**ebike** → pick the value matching the e-bike discipline\n\n"
            "Values:\n"
            "- **racing** — Competitive road racing\n"
            "- **endurance** — Long-distance road or gravel\n"
            "- **all_road** — Mixed surface gravel riding\n"
            "- **touring** — Loaded / long-distance touring\n"
            "- **trekking** — City trekking and commuting\n"
            "- **urban** — Daily urban commuting\n"
            "- **cross_country** — XC MTB racing / fast trails\n"
            "- **trail** — All-mountain trail riding\n"
            "- **enduro** — Aggressive enduro / all-mountain\n"
            "- **downhill** — Downhill / bike park"
        ),
        examples=["racing"],
    )

    terrain: Literal[
        "asphalt",
        "mixed",
        "offroad_hard",
        "offroad_mixed",
        "offroad_soft",
    ] = Field(
        ...,
        description=(
            "Main riding surface. Use only the values relevant to the selected `bike_type`:\n\n"
            "**road** → `asphalt`\n\n"
            "**gravel** → `asphalt`, `mixed`, `offroad_hard`\n\n"
            "**mtb** → `offroad_hard`, `offroad_mixed`, `offroad_soft`\n\n"
            "**city** → `asphalt`, `mixed`\n\n"
            "**ebike** → `asphalt`, `mixed`, `offroad_hard`, `offroad_mixed`\n\n"
            "Values:\n"
            "- **asphalt** — Tarmac only\n"
            "- **mixed** — Tarmac + light dirt / gravel tracks\n"
            "- **offroad_hard** — Packed dirt, dry trails\n"
            "- **offroad_mixed** — Roots, rocks, variable damp sections\n"
            "- **offroad_soft** — Mud, sand, loose soil"
        ),
        examples=["asphalt"],
    )

    budget_level: Literal["racing", "competition", "performance", "access"] = Field(
        ...,
        description=(
            "Price / performance segment (independent of bike type):\n"
            "- **racing** — PREMIUM RACING LINE — top-of-range, club/pro racers\n"
            "- **competition** — PREMIUM COMPETITION LINE — high performance, serious riders\n"
            "- **performance** — PREMIUM PERFORMANCE LINE — mid-range, regular sport riders\n"
            "- **access** — ACCESS LINE — entry level, casual / commuting"
        ),
        examples=["competition"],
    )

    tubeless: bool = Field(
        ...,
        description=(
            "Tyre mounting system:\n"
            "- **true** — Tubeless Ready (TLR): no inner tube, lower rolling resistance, "
            "self-sealing against small punctures. Requires tubeless-compatible rims.\n"
            "- **false** — Tube Type: standard inner tube required. Works with any rim."
        ),
        examples=[True],
    )

    e_bike: bool = Field(
        default=False,
        description=(
            "Whether an e-bike reinforced tyre is required:\n"
            "- **true** — Filters for E-BIKE READY / E-50 tyres: reinforced casing and higher "
            "speed rating for the extra weight and speed of motor-assisted bikes. "
            "Always send `true` when `bike_type` is `ebike`.\n"
            "- **false** — No e-bike constraint. Standard tyres are returned."
        ),
        examples=[False],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bike_type": "road",
                    "riding_style": "racing",
                    "terrain": "asphalt",
                    "budget_level": "competition",
                    "tubeless": True,
                    "e_bike": False,
                }
            ]
        }
    }


class TyreCandidate(BaseModel):
    brand: str
    model: str
    category: str
    segment: Optional[str] = None
    use: Optional[str] = None
    terrain_types: Optional[str] = None
    sealing: Optional[str] = None
    reasons: Optional[List[str]] = None
    product_url: Optional[str] = None


class TyreRecommendationPayload(BaseModel):
    recommendation_id: str
    primary_tyre: TyreCandidate
    alternatives: List[TyreCandidate] = []
