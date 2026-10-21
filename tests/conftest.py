import os
import tempfile
from pathlib import Path
import pytest

TEST_DIR=tempfile.TemporaryDirectory(prefix='news-studio-tests-')
os.environ['DATABASE_URL']='sqlite:///'+str(Path(TEST_DIR.name)/'tests.db').replace('\\','/')
os.environ['ADMIN_PASSWORD']='test-password-with-16-characters'
os.environ['SESSION_SECRET']='test-only-session-secret-at-least-32-characters'
os.environ['TELEGRAM_BOT_TOKEN']=''
os.environ['TELEGRAM_CHAT_IDS']=''

from backend.db import Base,engine,Session
from backend.bootstrap import bootstrap

def pytest_sessionfinish(session,exitstatus):
    engine.dispose()
    TEST_DIR.cleanup()

@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    from sqlalchemy import text
    with engine.begin() as connection:
        connection.execute(text('DROP TABLE IF EXISTS alembic_version'))
    Base.metadata.create_all(engine)
    bootstrap()
    yield

@pytest.fixture
def db():
    with Session() as session: yield session

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from backend.api import app,attempts
    attempts.clear()
    with TestClient(app) as c:
        c.post('/api/login',json={'password':os.environ['ADMIN_PASSWORD']})
        c.headers['X-Studio-Action']='1'
        yield c
