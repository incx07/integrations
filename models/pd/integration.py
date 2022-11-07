from typing import Optional, Union

from pydantic import BaseModel, validator
from pylon.core.tools import log

from .registration import SectionRegistrationForm

from tools import rpc_tools, secrets_tools, session_project


class IntegrationPD(BaseModel):
    id: int
    name: str
    section: Union[str, SectionRegistrationForm]
    settings: dict
    is_default: bool
    description: Optional[str]
    task_id: Optional[str]

    @validator("settings")
    def validate_settings(cls, value, values):
        integration = rpc_tools.RpcMixin().rpc.call.integrations_get_by_name(
            values['name']
        )
        if not integration:
            log.info('Integration [%s] was not found', values['name'])
            return dict()
        # return integration.settings_model.parse_obj(value).dict(exclude={'password', 'passwd'})
        return integration.settings_model.parse_obj(value).dict()

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


class SecretField(BaseModel):
    from_secrets: bool
    value: str

    def unsecret(self, project_id: int):
        if self.from_secrets:
            return secrets_tools.unsecret(
                self.value,
                project_id=project_id
            )
        else:
            return self.value
