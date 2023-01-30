from typing import Optional, Union

from pydantic.class_validators import validator
from pydantic.main import ModelMetaclass
from pydantic import BaseModel


def name_validator(cls, value: str):
    return value.lower()


class SectionRegistrationForm(BaseModel):
    name: str
    integration_description: Optional[str] = ''
    test_planner_description: Optional[str] = ''

    _lower_name = validator('name', allow_reuse=True)(name_validator)


class RegistrationForm(BaseModel):
    name: str
    section: str  # we manually manage relationships
    settings_model: Optional[ModelMetaclass]  # todo: replace for validation callback
    # integration_callback: Optional[Callable] = lambda context, slot, payload: None

    _lower_name = validator('name', allow_reuse=True)(name_validator)

    @validator('section')
    def section_validator(cls, value: Union[str, dict]):
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
        arbitrary_types_allowed = True
