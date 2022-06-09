from typing import Optional, Union

from pydantic import BaseModel, validator
from pylon.core.tools import log

from .registration import SectionRegistrationForm

from tools import rpc_tools


class IntegrationPD(BaseModel):

    id: int
    name: str
    section: Union[str, SectionRegistrationForm]
    settings: dict
    is_default: bool
    description: Optional[str]

    @validator("settings")
    def validate_settings(cls, value, values):
        integration = rpc_tools.RpcMixin().rpc.call.integrations_get_by_name(
            values['name']
        )
        if not integration:
            log.info('Integration [%s] was not found', values['name'])
            return dict()
        return integration.settings_model.parse_obj(value).dict(exclude={'password', 'passwd'})

    @validator("section")
    def validate_section(cls, value, values):
        section = rpc_tools.RpcMixin().rpc.call.integrations_get_section(value)
        if not section:
            log.info('Integration section [%s] was not found', value)
            return rpc_tools.RpcMixin().rpc.call.integrations_register_section(name=value)
        return section

    @validator("description")
    def validate_description(cls, value, values):
        if not value:
            return f'Integration #{values["id"]}'
        return value

    class Config:
        orm_mode = True