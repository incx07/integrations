from typing import Optional, Union
from uuid import uuid4

from pydantic import BaseModel, validator, constr
from pylon.core.tools import log

from .registration import SectionRegistrationForm

from tools import rpc_tools


class IntegrationBase(BaseModel):
    id: int
    project_id: Optional[int]
    name: str
    section: Union[str, SectionRegistrationForm]
    settings: dict
    is_default: bool
    config: dict
    task_id: Optional[str]
    status: Optional[str] = 'success'
    uid: str

    class Config:
        orm_mode = True


class IntegrationPD(IntegrationBase):
    @validator('uid', pre=True, always=True)
    def set_uid(cls, value: Optional[str]):
        if not value:
            return str(uuid4())
        return value

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

    @validator("config")
    def validate_description(cls, value, values):
        if not value.get('name'):
            value['name'] = f'Integration #{values["id"]}'
            return value
        return value


class IntegrationDefaultPD(BaseModel):
    id: int
    name: str
    integration_id: int
    project_id: Optional[int]
    is_default: bool = True
    section: Union[str, SectionRegistrationForm]

    class Config:
        orm_mode = True


class SecretField(BaseModel):
    from_secrets: bool = True
    value: str

    def unsecret(self, project_id: Optional[int] = None):
        from tools import VaultClient
        if self.from_secrets:
            if project_id:
                client = VaultClient.from_project(project_id)
            else:
                client = VaultClient()
            return client.unsecret(self.value)
        else:
            return self.value
