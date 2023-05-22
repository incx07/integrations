# from ..shared.db_manager import Base, engine

from tools import db


def init_db():
    from .models.integration import IntegrationAdmin, IntegrationProject
    db.get_shared_metadata().create_all(bind=db.engine)

