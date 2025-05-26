from typing import Iterator
from contextlib import contextmanager
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker, scoped_session


def fetch_engine(sql_connection_string: str) -> Engine:
    return create_engine(sql_connection_string)

def fetch_session_maker(engine: Engine) -> scoped_session[Session]:
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)

@contextmanager
def session_scope(scoped_session_factory: scoped_session[Session]) -> Iterator[Session]:
    session = scoped_session_factory()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        scoped_session_factory.remove()


engine = fetch_engine('postgresql+psycopg2://nextplore_user:MigrateMe2024!@localhost:5432/nextplore')
session_maker = fetch_session_maker(engine)

import uuid
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    name = Column(Text)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'))
    sub = Column(Text, unique=True)
    role = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

def backend_session_scope():
    engine = fetch_engine('postgresql+psycopg2://nextplore_user:MigrateMe2024!@localhost:5432/nextplore')
    session_maker = fetch_session_maker(engine)
    return session_scope(session_maker)

