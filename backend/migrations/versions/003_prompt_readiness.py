"""Preserve research-gap warnings with each immutable prompt snapshot."""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('prompts', sa.Column('readiness', sa.JSON(), nullable=False, server_default=sa.text("'{}'")))


def downgrade():
    op.drop_column('prompts', 'readiness')
