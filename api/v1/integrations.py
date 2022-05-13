from typing import List

from flask_restful import Resource

from flask import jsonify
from pydantic import ValidationError, parse_obj_as

from ...models.integration import Integration
from ...models.pd.integration import IntegrationPD


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        results = Integration.query.filter(Integration.project_id == project_id).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return jsonify([i.dict() for i in results]), 200
