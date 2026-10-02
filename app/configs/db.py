import os
from sqlmodel import create_engine, Session


database_url = os.getenv("DATABASE_URL")

engine = create_engine(database_url, echo = False)


def get_db_session():
    with Session(engine) as session:
        yield session
