from flask_restful import Resource
from flask import request


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        if request.args.get('name'):
            return [
                i.dict() for i in self.module.get_project_integrations_by_name(project_id, request.args['name'])
            ], 200
        if request.args.get('section'):
            return [
                i.dict() for i in self.module.get_project_integrations_by_section(project_id, request.args['section'])
            ], 200
        return [
            i.dict() for i in self.module.get_project_integrations(project_id, False)
        ], 200
