from typing import List, Optional
from pydantic import BaseModel


class TyreOut(BaseModel):
    id: int
    brand: Optional[str]
    product_type: Optional[str]
    cycle_type: Optional[str]
    segment: Optional[str]
    bead: Optional[str]
    width_etrto: Optional[str]
    diameter_etrto: Optional[str]
    type_tube: Optional[str]
    valve_tube: Optional[str]
    valve_length: Optional[str]
    ean_code: Optional[str]
    discontinued_date: Optional[str]
    weight_g: Optional[str]
    market_perimeter: Optional[str]
    web_range_name: Optional[str]
    web_diameter_mm: Optional[str]
    web_diameter_inch: Optional[str]
    web_width_mm: Optional[str]
    web_width_inch: Optional[str]
    rim_type: Optional[str]
    web_product_designation: Optional[str]
    fitting: Optional[str]
    tpi: Optional[str]
    min_pressure_bar: Optional[str]
    max_pressure_bar: Optional[str]
    min_pressure_psi: Optional[str]
    max_pressure_psi: Optional[str]
    recommended_inner_tube: Optional[str]
    sidewall_type: Optional[str]
    sealing: Optional[str]
    shore: Optional[str]
    sidewall_color: Optional[str]
    tread_pattern_color: Optional[str]
    terrain_types: Optional[str]
    use: Optional[str]
    rubber_technologies: Optional[str]
    casing_technologies: Optional[str]
    tread_pattern_technologies: Optional[str]
    reinforcement_technologies: Optional[str]
    ebike_technologies: Optional[str]
    reflective_strip: Optional[str]
    knurling_strip: Optional[str]
    shoulder_color: Optional[str]
    border_color: Optional[str]
    cycle_type_web: Optional[str]
    pic1: Optional[str]
    pic2: Optional[str]
    price: float

    model_config = {"from_attributes": True}


class TyreListData(BaseModel):
    items: List[TyreOut]
