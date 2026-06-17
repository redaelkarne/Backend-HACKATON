"""add tyres table

Revision ID: 004_tyres
Revises: 003_strava
Create Date: 2026-06-17 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_tyres"
down_revision: Union[str, None] = "003_strava"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tyres",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("product_type", sa.String(100), nullable=True),
        sa.Column("cycle_type", sa.String(100), nullable=True),
        sa.Column("segment", sa.String(200), nullable=True),
        sa.Column("bead", sa.String(100), nullable=True),
        sa.Column("width_etrto", sa.String(20), nullable=True),
        sa.Column("diameter_etrto", sa.String(20), nullable=True),
        sa.Column("type_tube", sa.String(100), nullable=True),
        sa.Column("valve_tube", sa.String(100), nullable=True),
        sa.Column("valve_length", sa.String(20), nullable=True),
        sa.Column("ean_code", sa.String(50), nullable=True),
        sa.Column("discontinued_date", sa.String(20), nullable=True),
        sa.Column("weight_g", sa.String(20), nullable=True),
        sa.Column("market_perimeter", sa.String(200), nullable=True),
        sa.Column("web_range_name", sa.String(300), nullable=True),
        sa.Column("web_diameter_mm", sa.String(20), nullable=True),
        sa.Column("web_diameter_inch", sa.String(20), nullable=True),
        sa.Column("web_width_mm", sa.String(20), nullable=True),
        sa.Column("web_width_inch", sa.String(20), nullable=True),
        sa.Column("rim_type", sa.String(100), nullable=True),
        sa.Column("web_product_designation", sa.String(300), nullable=True),
        sa.Column("fitting", sa.String(50), nullable=True),
        sa.Column("tpi", sa.String(50), nullable=True),
        sa.Column("min_pressure_bar", sa.String(20), nullable=True),
        sa.Column("max_pressure_bar", sa.String(20), nullable=True),
        sa.Column("min_pressure_psi", sa.String(20), nullable=True),
        sa.Column("max_pressure_psi", sa.String(20), nullable=True),
        sa.Column("recommended_inner_tube", sa.String(200), nullable=True),
        sa.Column("sidewall_type", sa.String(100), nullable=True),
        sa.Column("sealing", sa.String(100), nullable=True),
        sa.Column("shore", sa.String(50), nullable=True),
        sa.Column("sidewall_color", sa.String(50), nullable=True),
        sa.Column("tread_pattern_color", sa.String(50), nullable=True),
        sa.Column("terrain_types", sa.String(300), nullable=True),
        sa.Column("use", sa.String(100), nullable=True),
        sa.Column("rubber_technologies", sa.String(200), nullable=True),
        sa.Column("casing_technologies", sa.String(200), nullable=True),
        sa.Column("tread_pattern_technologies", sa.String(200), nullable=True),
        sa.Column("reinforcement_technologies", sa.String(200), nullable=True),
        sa.Column("ebike_technologies", sa.String(200), nullable=True),
        sa.Column("reflective_strip", sa.String(10), nullable=True),
        sa.Column("knurling_strip", sa.String(10), nullable=True),
        sa.Column("shoulder_color", sa.String(50), nullable=True),
        sa.Column("border_color", sa.String(50), nullable=True),
        sa.Column("cycle_type_web", sa.String(100), nullable=True),
        sa.Column("pic1", sa.Text(), nullable=True),
        sa.Column("pic2", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tyres")
