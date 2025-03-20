"""add_tokyo_region_initial_data

Revision ID: 5fbfdc900386
Revises: 8ec3af3eaad6
Create Date: 2025-03-20 00:31:26.186785+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '5fbfdc900386'
down_revision: Union[str, None] = '8ec3af3eaad6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add initial Tokyo region data."""
    # Create a temp table reference for the regions table
    regions = table('regions',
        column('id', sa.String),
        column('name', sa.String),
        column('local_name', sa.String),
        column('description', sa.String),
        column('languages', sa.JSON),
        column('bounds', sa.JSON),
        column('center', sa.JSON),
        column('difficulty_level', sa.Float),
        column('requirements', sa.JSON),
        column('total_pois', sa.Integer),
        column('total_challenges', sa.Integer),
        column('recommended_level', sa.Float),
        column('region_metadata', sa.JSON),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )

    op.bulk_insert(regions, [
        {
            'id': 'tokyo-central',
            'name': 'Tokyo',
            'local_name': '東京',
            'description': 'The bustling central region of Tokyo, Japan\'s capital city.',
            'languages': ['ja'],
            'bounds': {
                'north': 35.8187,
                'south': 35.5311,
                'east': 139.9224,
                'west': 139.5804
            },
            'center': {
                'lat': 35.6762,
                'lon': 139.6503
            },
            'difficulty_level': 1.0,
            'requirements': {},  # No requirements for initial region
            'total_pois': 0,    # Will be updated as POIs are added
            'total_challenges': 0,
            'recommended_level': 0.0,
            'region_metadata': {
                'dialect': 'standard',
                'customs': {
                    'greetings': 'Bowing is common',
                    'etiquette': 'Remove shoes indoors'
                },
                'population': 'Very high density',
                'transportation': ['train', 'subway', 'bus']
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ])

def downgrade() -> None:
    """Remove Tokyo region data."""
    regions = table('regions',
        column('id', sa.String)
    )
    op.execute(
        regions.delete().where(regions.c.id == 'tokyo-central')
    )
