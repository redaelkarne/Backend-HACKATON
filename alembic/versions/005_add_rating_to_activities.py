"""add rating column to activities

Revision ID: 005_rating
Revises: 004_tyres
Create Date: 2026-06-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_rating"
down_revision: Union[str, None] = "004_tyres"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = [row[0] for row in bind.execute(sa.text("SHOW COLUMNS FROM activities")).fetchall()]
    if "rating" not in cols:
        op.add_column("activities", sa.Column("rating", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("activities", "rating")
