from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Iterator

from taxed.state import conf
from .errors import DatabaseError
from .plogger import plog


engine = create_engine(conf.postgresql_dsn)

#NOTE: all arguments below come from FastApi docs at
# https://fastapi.tiangolo.com/tutorial/sql-databases/#create-the-database-models
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def db_commit(db: Session, response_builder):
    try:
        db.commit()
    except Exception as exc:
        plog.exception('db_commit error', exc)
        response_builder.add_error(DatabaseError)
        raise exc
