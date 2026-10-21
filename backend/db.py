import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, Integer, Float, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import env

def now():
    return datetime.now(timezone.utc).isoformat()

def uid():
    return str(uuid.uuid4())

class Base(DeclarativeBase):
    pass

class Source(Base):
    __tablename__ = 'sources'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(Text, unique=True)
    kind: Mapped[str] = mapped_column(String(30), default='rss')
    region: Mapped[str] = mapped_column(String(20), default='india')
    category: Mapped[str] = mapped_column(String(50), default='national')
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    primary: Mapped[bool] = mapped_column(Boolean, default=False)
    origin_group: Mapped[str] = mapped_column(String(100), default='unknown')
    options: Mapped[dict] = mapped_column(JSON, default=dict)

class Story(Base):
    __tablename__ = 'stories'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    region: Mapped[str] = mapped_column(String(20), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    subcategory: Mapped[str] = mapped_column(String(60), default='')
    status: Mapped[str] = mapped_column(String(40), default='new', index=True)
    score: Mapped[float] = mapped_column(Float, default=0)
    scoring: Mapped[dict] = mapped_column(JSON, default=dict)
    research: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), default=now, index=True)
    updated_at: Mapped[str] = mapped_column(String(40), default=now)

class Article(Base):
    __tablename__ = 'articles'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'))
    story_id: Mapped[str] = mapped_column(ForeignKey('stories.id'), index=True)
    url: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    publisher: Mapped[str] = mapped_column(String(200))
    origin_group: Mapped[str] = mapped_column(String(100), default='unknown')
    published_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    event_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    retrieved_at: Mapped[str] = mapped_column(String(40), default=now)

class Run(Base):
    __tablename__ = 'runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    status: Mapped[str] = mapped_column(String(30), default='running')
    started_at: Mapped[str] = mapped_column(String(40), default=now)
    finished_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    new_stories: Mapped[int] = mapped_column(Integer, default=0)
    articles: Mapped[int] = mapped_column(Integer, default=0)
    source_results: Mapped[list] = mapped_column(JSON, default=list)

class Notification(Base):
    __tablename__ = 'notifications'
    __table_args__ = (UniqueConstraint('story_id', 'chat_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    story_id: Mapped[str] = mapped_column(ForeignKey('stories.id'))
    chat_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default='pending')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default='')
    next_attempt: Mapped[str] = mapped_column(String(40), default=now)
    updated_at: Mapped[str] = mapped_column(String(40), default=now)

class Setting(Base):
    __tablename__ = 'settings'
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)

class Audit(Base):
    __tablename__ = 'audit'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    action: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), default=now)

class Prompt(Base):
    __tablename__ = 'prompts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    story_id: Mapped[str] = mapped_column(ForeignKey('stories.id'))
    content: Mapped[str] = mapped_column(Text)
    reference_picture_content: Mapped[str] = mapped_column(Text, default='')
    readiness: Mapped[dict] = mapped_column(JSON, default=dict)
    channel_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String(40), default=now)

engine = create_engine(env.database_url, pool_pre_ping=True, **({'connect_args': {'check_same_thread': False, 'timeout': 30}} if env.database_url.startswith('sqlite') else {}))
Session = sessionmaker(engine, expire_on_commit=False)

def audit(db, action, subject, **details):
    db.add(Audit(action=action, subject=subject, details=details))
