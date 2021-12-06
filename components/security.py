from flask import render_template


def create(context, slot, payload):
    payload['integrations_section_list'] = context.rpc_manager.call.integrations_section_list()
    return render_template(
        'integrations:security_app_create.html',
        config=payload
    )
