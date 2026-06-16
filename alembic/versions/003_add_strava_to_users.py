"""add strava oauth columns to users

Revision ID: 003_strava
Revises: c62672f67488
Create Date: 2026-06-16 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003_strava'
down_revision: Union[str, None] = 'c62672f67488'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('strava_athlete_id', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('strava_access_token', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('strava_refresh_token', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('strava_token_expires_at', sa.Integer(), nullable=True))
    op.create_unique_constraint('uq_users_strava_athlete_id', 'users', ['strava_athlete_id'])


def downgrade() -> None:
    op.drop_constraint('uq_users_strava_athlete_id', 'users', type_='unique')
    op.drop_column('users', 'strava_token_expires_at')
    op.drop_column('users', 'strava_refresh_token')
    op.drop_column('users', 'strava_access_token')
    op.drop_column('users', 'strava_athlete_id')
