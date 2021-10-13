from typing import Optional

from arbiter.log import log
from flask import current_app

from pydantic import BaseModel, validator


class IntegrationPD(BaseModel):

    id: int
    name: str
    section: str
    settings: dict
    is_default: bool
    description: Optional[str]

    @validator("settings")
    def validate_settings(cls, value, values):
        integration = current_app.config['CONTEXT'].rpc_manager.call.integrations_get_integration(
            values['name']
        )
        if not integration:
            log('Integration %s was not found', values['name'])
            return dict()
        return integration.settings_model.parse_obj(value).dict(exclude={'password'})

    class Config:
        orm_mode = True
