#     Copyright 2020 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.


from typing import Optional, List

from flask_restful import Resource

from flask import request, make_response, jsonify
from pydantic import ValidationError, parse_obj_as
from requests import Response
from ..models.integration import Integration
from ..models.integration_pd import IntegrationPD

from ...shared.utils.rpc import RpcMixin


class CheckSettingsApi(Resource, RpcMixin):
    def post(self, integration_name: str) -> Response:
        integration = self.rpc.call.integrations_get_integration(integration_name)
        if not integration:
            return make_response({'error': 'integration not found'}, 404)
        try:
            settings = integration.settings_model.parse_obj(request.json)
        except ValidationError as e:
            return make_response(e.json(), 400)

        check_connection_response = settings.check_connection()
        if not request.json.get('save_action'):
            if check_connection_response:
                return make_response('OK', 200)
            return make_response(jsonify([{'loc': ['check_connection'], 'msg': 'Connection failed'}]), 400)


class IntegrationsApi(Resource, RpcMixin):
    def get(self, project_id: int) -> Response:
        results = Integration.query.filter(Integration.project_id == project_id).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return make_response(jsonify([i.dict() for i in results]), 200)

    def post(self, integration_name: str) -> Response:
        project_id = request.json.get('project_id')
        if not project_id:
            return make_response({'error': 'project_id not provided'}, 400)
        integration = self.rpc.call.integrations_get_integration(integration_name)
        if not integration:
            return make_response({'error': 'integration not found'}, 404)
        try:
            settings = integration.settings_model.parse_obj(request.json)
        except ValidationError as e:
            return make_response(e.json(), 400)

        db_integration = Integration(
            name=integration_name,
            project_id=request.json.get('project_id'),
            settings=settings.dict(),
            section=integration.section,
            description=request.json.get('description'),
        )
        db_integration.insert()
        if request.json.get('is_default'):
            db_integration.make_default()
        return make_response(IntegrationPD.from_orm(db_integration).dict(), 200)

    def put(self, integration_name: str, integration_id: int) -> Response:
        print('PUT', integration_name, integration_id, request.json)
        db_integration = Integration.query.filter(Integration.id == integration_id).first()
        integration = self.rpc.call.integrations_get_integration(db_integration.name)
        if not integration or not db_integration:
            return make_response({'error': 'integration not found'}, 404)
        try:
            # existing_settings = db_integration.settings
            # existing_settings.update({k: v for k, v in request.json.items()})
            # settings = integration.settings_model.parse_obj(existing_settings)
            settings = integration.settings_model.parse_obj(request.json)
        except ValidationError as e:
            return make_response(e.json(), 400)

        if request.json.get('is_default'):
            db_integration.make_default()

        db_integration.settings = settings.dict()
        db_integration.description = request.json.get('description'),
        db_integration.insert()
        return make_response(IntegrationPD.from_orm(db_integration).dict(), 200)

    def delete(self, integration_name: str, integration_id: int) -> Response:
        Integration.query.filter(Integration.id == integration_id).first().delete()
        # if request.json.get('is_default'):
        #     db_integration.make_default()
        return make_response('DELETED', 204)
