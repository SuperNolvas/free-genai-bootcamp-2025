"""add_content_history_column

Revision ID: add_content_history
Revises: 8f43c6f50c0d
Create Date: 2025-03-16 23:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'add_content_history'
down_revision: Union[str, None] = '8f43c6f50c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add content_history column with empty array default
    op.add_column('points_of_interest', 
                  sa.Column('content_history', 
                           JSONB, 
                           server_default='[]',
                           nullable=False))

def downgrade() -> None:
    op.drop_column('points_of_interest', 'content_history')