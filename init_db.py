# from ..shared.db_manager import Base, engine

from tools import db


def init_db():
    from .models.integration import Integration
    db.Base.metadata.create_all(bind=db.engine)

