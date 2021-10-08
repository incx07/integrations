from typing import Dict, Optional, Any, Callable

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
        try:
            return current_app.config['CONTEXT'].rpc_manager.call.integrations_get_integration(
                values['name']
            ).settings_model.parse_obj(value).dict(exclude={'password'})
        except AttributeError:
            return

    class Config:
        orm_mode = True
