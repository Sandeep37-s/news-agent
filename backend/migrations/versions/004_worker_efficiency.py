"""Persist conditional-feed validators and index frequent small queries."""
from alembic import op
import sqlalchemy as sa

revision='004'
down_revision='003'
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('sources',sa.Column('fetch_state',sa.JSON(),nullable=False,server_default=sa.text("'{}'")))
    op.create_index('ix_runs_started_at','runs',['started_at'])
    op.create_index('ix_notifications_due','notifications',['status','next_attempt'])
    op.create_index('ix_audit_action_created','audit',['action','created_at'])
    op.create_index('ix_prompts_story_created','prompts',['story_id','created_at'])


def downgrade():
    for name,table in [('ix_runs_started_at','runs'),('ix_notifications_due','notifications'),('ix_audit_action_created','audit'),('ix_prompts_story_created','prompts')]:
        op.drop_index(name,table_name=table)
    op.drop_column('sources','fetch_state')
