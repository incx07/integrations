from pylon.core.tools import log

from flask import request
from pydantic import ValidationError, parse_obj_as

from tools import api_tools
from ...models.integration import Integration
from ...models.pd.integration import IntegrationPD


class ProjectAPI(api_tools.APIModeHandler):
    def post(self, integration_name: str):
        project_id = request.json.get('project_id')
        if not project_id:
            return {'error': 'project_id not provided'}, 400
        integration = self.module.get_by_name(integration_name)
        if not integration:
            return {'error': 'integration not found'}, 404
        try:
            settings = integration.settings_model.parse_obj(request.json)
        except ValidationError as e:
            return e.errors(), 400

        db_integration = Integration(
            name=integration_name,
            project_id=request.json.get('project_id'),
            mode=request.json.get('mode', 'default'),
            settings=settings.dict(),
            section=integration.section,
            description=request.json.get('description'),
            status=request.json.get('status', 'success'),
        )
        db_integration.insert()
        if request.json.get('is_default'):
            db_integration.make_default()
        return IntegrationPD.from_orm(db_integration).dict(), 200

class AdminAPI(api_tools.APIModeHandler):
    def post(self, integration_name: str):
        # project_id = request.json.get('project_id')
        # if not project_id:
        #     return {'error': 'project_id not provided'}, 400
        integration = self.module.get_by_name(integration_name)
        if not integration:
            return {'error': 'integration not found'}, 404
        try:
            settings = integration.settings_model.parse_obj(request.json)
        except ValidationError as e:
            return e.errors(), 400

        db_integration = Integration(
            name=integration_name,
            # project_id=request.json.get('project_id'),
            mode=request.json.get('mode', 'default'),
            settings=settings.dict(),
            section=integration.section,
            description=request.json.get('description'),
            status=request.json.get('status', 'success'),
        )
        db_integration.insert()
        if request.json.get('is_default'):
            db_integration.make_default()
        return IntegrationPD.from_orm(db_integration).dict(), 200


class API(api_tools.APIBase):
    url_params = [
        '<string:integration_name>',
        '<string:mode>/<string:integration_name>',
        '<int:integration_id>',
        '<string:mode>/<int:integration_id>',
    ]

    mode_handlers = {
        'default': ProjectAPI,
        'administration': AdminAPI,
    }

    def put(self, integration_id: int, **kwargs):
        db_integration = Integration.query.filter(Integration.id == integration_id).first()
        integration = self.module.get_by_name(db_integration.name)
        if not integration or not db_integration:
            return {'error': 'integration not found'}, 404
        try:
            settings = integration.settings_model.parse_obj(request.json)
        except ValidationError as e:
            return e.errors(), 400

        if request.json.get('is_default'):
            db_integration.make_default()

        db_integration.settings = settings.dict()
        db_integration.description = request.json.get('description'),
        db_integration.insert()
        return IntegrationPD.from_orm(db_integration).dict(), 200
    
    def patch(self, integration_id: int, **kwargs):
        db_integration = Integration.query.filter(Integration.id == integration_id).first()
        integration = self.module.get_by_name(db_integration.name)
        if not integration or not db_integration:
            return {'error': 'integration not found'}, 404
        db_integration.make_default()
        return {'msg': 'integration was set as default'}, 200
    
    def delete(self, integration_id: int, **kwargs):
        Integration.query.filter(Integration.id == integration_id).delete()
        Integration.commit()
        # if request.json.get('is_default'):
        #     db_integration.make_default()
        return integration_id, 204
