from typing import Dict, Optional, Any, Callable

from pydantic.class_validators import validator
from pydantic.main import ModelMetaclass

from pydantic import BaseModel

from ...shared.utils.rpc import RpcMixin


class SectionRegistrationForm(BaseModel):
    name: str
    integration_description: Optional[str] = ''
    test_planner_description: Optional[str] = ''

    @validator('name')
    def name_validator(cls, value, values):
        return value.lower()


class RegistrationForm(BaseModel):
    name: str
    section: str  # we manually manage relationships
    settings_model: ModelMetaclass
    integration_callback: Callable

    @validator('name')
    def name_validator(cls, value, values):
        return value.lower()

    @validator('section')
    def section_validator(cls, value, values):
        section = RpcMixin().rpc.call.integrations_get_section(value)
        if not section:
            if isinstance(value, str):
                section = RpcMixin().rpc.call.integrations_register_section(name=value)
            # elif isinstance(value, SectionRegistrationForm):
            #     section = cls.rpc.call.integrations_register_section(value.dict())
            else:
                section = RpcMixin().rpc.call.integrations_register_section(**value)

        return section.name

    class Config:
        json_encoders = {
            ModelMetaclass: lambda v: str(type(v)),
        }

    def get_section(self):
        self.rpc.call.integrations_get_section(self.section)
