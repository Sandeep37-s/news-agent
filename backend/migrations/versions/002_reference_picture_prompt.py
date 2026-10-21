"""Persist the paired reference-picture prompt without changing saved story prompts."""
from alembic import op
import sqlalchemy as sa

revision='002'
down_revision='001'

def upgrade():
    op.add_column('prompts',sa.Column('reference_picture_content',sa.Text(),nullable=False,server_default=''))

def downgrade():
    op.drop_column('prompts','reference_picture_content')
