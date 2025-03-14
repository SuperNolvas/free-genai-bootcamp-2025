"""create points of interest table

Revision ID: 67c9c7564660
Revises: 9409fe98badc
Create Date: 2025-03-14 13:43:48.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67c9c7564660'
down_revision: Union[str, None] = '9409fe98badc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('points_of_interest',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('local_name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('local_description', sa.String(), nullable=True),
        sa.Column('poi_type', sa.String(), nullable=False),
        sa.Column('coordinates', sa.JSON(), nullable=False),
        sa.Column('region_id', sa.String(), nullable=False),
        sa.Column('difficulty_level', sa.Float(), nullable=False),
        sa.Column('content_ids', sa.JSON(), server_default='[]'),
        sa.Column('metadata', sa.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Add index on region_id for faster POI lookups by region
    op.create_index(op.f('ix_points_of_interest_region_id'), 'points_of_interest', ['region_id'], unique=False)
    # Add index on poi_type for faster filtering
    op.create_index(op.f('ix_points_of_interest_poi_type'), 'points_of_interest', ['poi_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_points_of_interest_poi_type'), table_name='points_of_interest')
    op.drop_index(op.f('ix_points_of_interest_region_id'), table_name='points_of_interest')
    op.drop_table('points_of_interest')
