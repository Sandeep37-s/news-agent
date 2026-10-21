from contextlib import contextmanager
import portalocker
from sqlalchemy import text
from .config import ROOT
from .db import engine

class AlreadyRunning(Exception):
    pass

@contextmanager
def monitoring_lock():
    if engine.dialect.name=='postgresql':
        with engine.connect() as connection:
            acquired=connection.scalar(text('SELECT pg_try_advisory_lock(84219017)'))
            if not acquired:
                raise AlreadyRunning('A monitoring run is already active')
            try:
                yield
            finally:
                connection.execute(text('SELECT pg_advisory_unlock(84219017)'))
    else:
        lock=portalocker.Lock(str(ROOT/'data/monitor.lock'),timeout=0)
        try:
            lock.acquire()
        except portalocker.LockException as exc:
            raise AlreadyRunning('A monitoring run is already active') from exc
        try:
            yield
        finally:
            lock.release()
