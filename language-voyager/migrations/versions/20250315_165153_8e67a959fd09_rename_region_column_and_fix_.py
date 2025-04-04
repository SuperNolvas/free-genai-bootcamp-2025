"""rename_region_column_and_fix_relationships

Revision ID: 8e67a959fd09
Revises: 10682eed9882
Create Date: 2025-03-15 16:51:53.630608+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e67a959fd09'
down_revision: Union[str, None] = '10682eed9882'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_progress', sa.Column('region_name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_progress', 'region_name')
    # ### end Alembic commands ###
