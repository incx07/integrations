from pylon.core.tools import log

from flask import request
from pydantic import ValidationError, parse_obj_as

from tools import api_tools, auth, db
from ...models.integration import IntegrationProject, IntegrationAdmin
from ...models.pd.integration import IntegrationPD


class ProjectAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.create"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})
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

        with db.with_project_schema_session(project_id) as tenant_session:
            db_integration = IntegrationProject(
                name=integration_name,
                project_id=request.json.get('project_id'),
                settings=settings.dict(),
                section=integration.section,
                config=request.json.get('config'),
                status=request.json.get('status', 'success'),
            )
            db_integration.insert(tenant_session)
            if request.json.get('is_default'):
                self.module.make_default_integration(db_integration, project_id)
            try:
                return IntegrationPD.from_orm(db_integration).dict(), 200
            except ValidationError as e:
                return e.errors(), 400            

    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})
    def put(self, integration_id: int):
        project_id = request.json.get('project_id')
        if not project_id:
            return {'error': 'project_id not provided'}, 400
        with db.with_project_schema_session(project_id) as tenant_session:
            db_integration = tenant_session.query(IntegrationProject).filter(
                IntegrationProject.id == integration_id).first()
            integration = self.module.get_by_name(db_integration.name)
            if not integration or not db_integration:
                return {'error': 'integration not found'}, 404
            try:
                settings = integration.settings_model.parse_obj(request.json)
            except ValidationError as e:
                return e.errors(), 400

            if request.json.get('is_default'):
                self.module.make_default_integration(db_integration, project_id)
                # db_integration.make_default(tenant_session)

            db_integration.settings = settings.dict()
            db_integration.config = request.json.get('config')
            db_integration.insert(tenant_session)
            return IntegrationPD.from_orm(db_integration).dict(), 200

    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})
    def patch(self, project_id: int, integration_id: int):
        if request.json.get('local'):
            with db.with_project_schema_session(project_id) as tenant_session:
                db_integration = tenant_session.query(IntegrationProject).filter(
                    IntegrationProject.id == integration_id).first()
                integration = self.module.get_by_name(db_integration.name)
                if not integration or not db_integration:
                    return {'error': 'integration not found'}, 404
                self.module.make_default_integration(db_integration, project_id)
        else:
            db_integration = IntegrationAdmin.query.filter(
                IntegrationAdmin.id == integration_id).first()
            integration = self.module.get_by_name(db_integration.name)
            if not integration or not db_integration:
                return {'error': 'integration not found'}, 404
            db_integration.project_id = None
            self.module.make_default_integration(db_integration, project_id)
        return {'msg': 'integration set as default'}, 200

    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.delete"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})    
    def delete(self, project_id: int, integration_id: int):
        with db.with_project_schema_session(project_id) as tenant_session:
            db_integration = tenant_session.query(IntegrationProject).filter(
                IntegrationProject.id == integration_id).first()
            if db_integration:
                tenant_session.delete(db_integration)
                tenant_session.commit()
                self.module.delete_default_integration(db_integration, project_id)
        return integration_id, 204


class AdminAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.create"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})
    def post(self, integration_name: str, **kwargs):
        integration = self.module.get_by_name(integration_name)
        if not integration:
            return {'error': 'integration not found'}, 404
        try:
            settings = integration.settings_model.parse_obj(request.json)
        except ValidationError as e:
            return e.errors(), 400

        db_integration = IntegrationAdmin(
            name=integration_name,
            # project_id=request.json.get('project_id'),
            # mode=request.json.get('mode', 'default'),
            settings=settings.dict(),
            section=integration.section,
            config=request.json.get('config'),
            status=request.json.get('status', 'success'),
        )
        db_integration.insert()
        if request.json.get('is_default'):
            db_integration.make_default()
        return IntegrationPD.from_orm(db_integration).dict(), 200

    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})
    def put(self, integration_id: int, **kwargs):
        db_integration = IntegrationAdmin.query.filter(IntegrationAdmin.id == integration_id).first()
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
        db_integration.config = request.json.get('config')
        db_integration.insert()
        return IntegrationPD.from_orm(db_integration).dict(), 200

    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": True},
            "default": {"admin": True, "viewer": False, "editor": True},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})
    def patch(self, integration_id: int, **kwargs):
        db_integration = IntegrationAdmin.query.filter(IntegrationAdmin.id == integration_id).first()
        integration = self.module.get_by_name(db_integration.name)
        if not integration or not db_integration:
            return {'error': 'integration not found'}, 404
        db_integration.make_default()
        return {'msg': 'integration set as default'}, 200

    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.delete"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})    
    def delete(self, integration_id: int, **kwargs):
        IntegrationAdmin.query.filter(IntegrationAdmin.id == integration_id).delete()
        IntegrationAdmin.commit()
        return integration_id, 204

class API(api_tools.APIBase):
    url_params = [
        '<string:integration_name>',
        '<string:mode>/<string:integration_name>',
        '<int:integration_id>',
        '<string:mode>/<int:integration_id>',
        '<int:project_id>/<int:integration_id>',
        '<string:mode>/<int:project_id>/<int:integration_id>',
    ]

    mode_handlers = {
        'default': ProjectAPI,
        'administration': AdminAPI,
    }
