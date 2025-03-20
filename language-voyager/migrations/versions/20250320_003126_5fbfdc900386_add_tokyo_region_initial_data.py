"""add_tokyo_region_initial_data

Revision ID: 5fbfdc900386
Revises: 8ec3af3eaad6
Create Date: 2025-03-20 00:31:26.186785+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fbfdc900386'
down_revision: Union[str, None] = '8ec3af3eaad6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
