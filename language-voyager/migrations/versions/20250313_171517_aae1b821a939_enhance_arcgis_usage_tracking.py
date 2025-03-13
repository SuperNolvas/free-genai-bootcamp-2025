"""enhance_arcgis_usage_tracking

Revision ID: aae1b821a939
Revises: e4c9af91068b
Create Date: 2025-03-13 17:15:17.487033+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aae1b821a939'
down_revision: Union[str, None] = 'e4c9af91068b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns for enhanced usage tracking
    op.add_column('arcgis_usage', sa.Column('cached', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('arcgis_usage', sa.Column('request_path', sa.String(), nullable=True))
    
    # Create index for efficient monthly queries
    op.create_index('ix_usage_timestamp_op', 'arcgis_usage', ['timestamp', 'operation_type'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove added columns and index
    op.drop_index('ix_usage_timestamp_op')
    op.drop_column('arcgis_usage', 'request_path')
    op.drop_column('arcgis_usage', 'cached')
