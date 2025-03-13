"""enhance_arcgis_usage_tracking

Revision ID: e4c9af91068b
Revises: 
Create Date: 2025-03-13 17:11:28.087073+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e4c9af91068b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Create the initial arcgis_usage table
    op.create_table('arcgis_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(), nullable=True),
        sa.Column('credits_used', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_arcgis_usage_id'), 'arcgis_usage', ['id'], unique=False)

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_arcgis_usage_id'), table_name='arcgis_usage')
    op.drop_table('arcgis_usage')
