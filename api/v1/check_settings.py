from flask_restful import Resource

from flask import request, jsonify
from pydantic import ValidationError, parse_obj_as
from pylon.core.tools import log


class API(Resource):
    url_params = [
        '<string:integration_name>',
        '<string:mode>/<string:integration_name>',
    ]

    def __init__(self, module):
        self.module = module

    def post(self, integration_name: str, **kwargs):
        integration = self.module.get_by_name(integration_name)
        if not integration:
            return {'error': 'integration not found'}, 404
        try:
            settings = integration.settings_model.parse_obj(request.json)
        except ValidationError as e:
            # return e.json(), 400
            return e.errors(), 400

        check_connection_response = settings.check_connection()
        if not request.json.get('save_action'):
            if check_connection_response is True:
                return 'OK', 200
            return [{'loc': ['check_connection'], 'msg': check_connection_response}], 400
