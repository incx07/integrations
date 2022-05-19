from typing import Optional, Callable

from pydantic.class_validators import validator
from pydantic.main import ModelMetaclass
from pydantic import BaseModel

from tools import rpc_tools


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
    settings_model: Optional[ModelMetaclass]  # todo: replace for validation callback
    # integration_callback: Optional[Callable] = lambda context, slot, payload: None

    @validator('name')
    def name_validator(cls, value, values):
        return value.lower()

    @validator('section')
    def section_validator(cls, value, values):
        # section = rpc_tools.RpcMixin().rpc.call.integrations_get_section(value)
        from tools import integrations_tools

        section = integrations_tools.get_section(value)
        if not section:
            if isinstance(value, str):
                section = integrations_tools.register_section(name=value)
            else:
                section = integrations_tools.register_section(**value)

        return section.name

    class Config:
        json_encoders = {
            ModelMetaclass: lambda v: str(type(v)),
        }
