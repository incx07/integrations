from typing import List

from flask import render_template
from plugins.integrations.models.integration import Integration
from plugins.integrations.models.integration_pd import IntegrationPD
from pydantic import parse_obj_as


def render_integrations(context, slot, payload):

    results = context.rpc_manager.call.integrations_get_project_integrations(payload['id'])

    # print('existing_integrations', results)

    payload['existing_integrations'] = results
    payload['integrations_sections'] = {*context.rpc_manager.call.integrations_sections(), *results.keys()}

    return render_template(
        'integrations_list.html',
        config=payload
    )
