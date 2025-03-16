"""add poi content conflicts

Revision ID: 2025031601
Revises: add_content_version_indexes
Create Date: 2025-03-16 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025031601'
down_revision = 'add_content_version_indexes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Check if table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'poi_content_conflicts' not in inspector.get_table_names():
        op.create_table('poi_content_conflicts',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('poi_id', sa.String(), nullable=False),
            sa.Column('base_version', sa.Integer(), nullable=False),
            sa.Column('proposed_changes', sa.JSON(), nullable=False),
            sa.Column('conflict_type', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False, server_default='pending'),
            sa.Column('resolution_strategy', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('resolved_by', sa.String(), nullable=True),
            sa.Column('conflict_metadata', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['poi_id'], ['points_of_interest.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Add indexes for common queries
        op.create_index('idx_poi_content_conflicts_poi_id', 'poi_content_conflicts', ['poi_id'])
        op.create_index('idx_poi_content_conflicts_status', 'poi_content_conflicts', ['status'])

def downgrade() -> None:
    op.drop_index('idx_poi_content_conflicts_status')
    op.drop_index('idx_poi_content_conflicts_poi_id')
    op.drop_table('poi_content_conflicts')