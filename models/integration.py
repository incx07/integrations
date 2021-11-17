from plugins.shared.db_manager import Base
from plugins.shared.models.abstract_base import AbstractBaseMixin
from plugins.shared.utils.rpc import RpcMixin
from sqlalchemy import Integer, Column, String, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSON


class Integration(AbstractBaseMixin, RpcMixin, Base):
    __tablename__ = "integration"
    __table_args__ = (
        Index(
            'ix_project_default_uc',  # Index name
            'project_id', 'name',  # Columns which are part of the index
            unique=True,
            postgresql_where=Column('is_default')  # The condition
        ),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=False)
    project_id = Column(Integer, unique=False)
    settings = Column(JSON, unique=False, default={})
    is_default = Column(Boolean, default=False, nullable=False)
    section = Column(String(64), unique=False, nullable=False)
    description = Column(String(256), unique=False, nullable=True, default='Default integration')

    def make_default(self):
        Integration.query.filter(
            Integration.project_id == self.project_id,
            Integration.name == self.name,
            Integration.is_default == True,
            Integration.id != self.id
        ).update({Integration.is_default: False})
        self.is_default = True
        self.insert()

    def insert(self):
        if not Integration.query.filter(
            Integration.project_id == self.project_id,
            Integration.name == self.name,
            Integration.is_default == True,
        ).one_or_none():
            self.is_default = True

        super().insert()
