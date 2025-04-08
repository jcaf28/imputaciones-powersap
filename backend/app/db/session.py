# PATH: backend/app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.core.config import Config

config = Config()

engine = create_engine(config.get_connection_string())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = scoped_session(SessionLocal)

# generador que crea una nueva sesión cuando se invoca y la cierra cuando ya no se necesita. Al usar scoped_session, garantizas que la sesión será única por cada hilo o solicitud, lo que es útil para aplicaciones web.

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

class DatabaseSession:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        self.db = self.session()
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()

database_session = DatabaseSession(session)
