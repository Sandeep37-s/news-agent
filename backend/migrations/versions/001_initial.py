"""Initial studio schema. Frozen table definitions, independent of runtime models."""
from alembic import op
import sqlalchemy as sa
revision = '001'
down_revision = None

def upgrade():
    op.create_table('sources', sa.Column('id',sa.String(36),primary_key=True), sa.Column('name',sa.String(200),nullable=False),sa.Column('url',sa.Text,unique=True,nullable=False),sa.Column('kind',sa.String(30),nullable=False),sa.Column('region',sa.String(20),nullable=False),sa.Column('category',sa.String(50),nullable=False),sa.Column('enabled',sa.Boolean,nullable=False),sa.Column('primary',sa.Boolean,nullable=False),sa.Column('origin_group',sa.String(100),nullable=False),sa.Column('options',sa.JSON,nullable=False))
    op.create_table('stories',sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.Text,nullable=False),sa.Column('fingerprint',sa.String(64),unique=True,nullable=False),sa.Column('region',sa.String(20),nullable=False,index=True),sa.Column('category',sa.String(50),nullable=False,index=True),sa.Column('subcategory',sa.String(60),nullable=False),sa.Column('status',sa.String(40),nullable=False,index=True),sa.Column('score',sa.Float,nullable=False),sa.Column('scoring',sa.JSON,nullable=False),sa.Column('research',sa.JSON,nullable=False),sa.Column('created_at',sa.String(40),nullable=False,index=True),sa.Column('updated_at',sa.String(40),nullable=False))
    op.create_table('articles',sa.Column('id',sa.String(36),primary_key=True),sa.Column('source_id',sa.String(36),sa.ForeignKey('sources.id'),nullable=False),sa.Column('story_id',sa.String(36),sa.ForeignKey('stories.id'),nullable=False,index=True),sa.Column('url',sa.Text,unique=True,nullable=False),sa.Column('title',sa.Text,nullable=False),sa.Column('summary',sa.Text,nullable=False),sa.Column('publisher',sa.String(200),nullable=False),sa.Column('origin_group',sa.String(100),nullable=False),sa.Column('published_at',sa.String(40)),sa.Column('event_at',sa.String(40)),sa.Column('retrieved_at',sa.String(40),nullable=False))
    op.create_table('runs',sa.Column('id',sa.String(36),primary_key=True),sa.Column('status',sa.String(30),nullable=False),sa.Column('started_at',sa.String(40),nullable=False),sa.Column('finished_at',sa.String(40)),sa.Column('new_stories',sa.Integer,nullable=False),sa.Column('articles',sa.Integer,nullable=False),sa.Column('source_results',sa.JSON,nullable=False))
    op.create_table('notifications',sa.Column('id',sa.String(36),primary_key=True),sa.Column('story_id',sa.String(36),sa.ForeignKey('stories.id'),nullable=False),sa.Column('chat_id',sa.String(100),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('attempts',sa.Integer,nullable=False),sa.Column('error',sa.Text,nullable=False),sa.Column('next_attempt',sa.String(40),nullable=False),sa.Column('updated_at',sa.String(40),nullable=False),sa.UniqueConstraint('story_id','chat_id'))
    op.create_table('settings',sa.Column('key',sa.String(100),primary_key=True),sa.Column('value',sa.JSON,nullable=False),sa.Column('version',sa.Integer,nullable=False))
    op.create_table('audit',sa.Column('id',sa.String(36),primary_key=True),sa.Column('action',sa.String(100),nullable=False),sa.Column('subject',sa.String(100),nullable=False),sa.Column('details',sa.JSON,nullable=False),sa.Column('created_at',sa.String(40),nullable=False))
    op.create_table('prompts',sa.Column('id',sa.String(36),primary_key=True),sa.Column('story_id',sa.String(36),sa.ForeignKey('stories.id'),nullable=False),sa.Column('content',sa.Text,nullable=False),sa.Column('channel_version',sa.Integer,nullable=False),sa.Column('created_at',sa.String(40),nullable=False))

def downgrade():
    for name in ['prompts','audit','settings','notifications','runs','articles','stories','sources']:
        op.drop_table(name)
