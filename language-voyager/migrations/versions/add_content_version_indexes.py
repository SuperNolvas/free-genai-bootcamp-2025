"""add_content_version_indexes

Revision ID: add_content_version_indexes
Revises: add_content_history
Create Date: 2025-03-16 23:50:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_content_version_indexes'
down_revision: Union[str, None] = 'add_content_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for version tracking and querying
    op.create_index(
        'ix_points_of_interest_content_version',
        'points_of_interest',
        ['content_version']
    )
    op.create_index(
        'ix_points_of_interest_updated_at',
        'points_of_interest',
        ['updated_at']
    )

def downgrade() -> None:
    op.drop_index('ix_points_of_interest_content_version')
    op.drop_index('ix_points_of_interest_updated_at')