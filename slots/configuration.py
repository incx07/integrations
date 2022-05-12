from flask import render_template



from pylon.core.tools import web, log

from tools import auth
from tools import theme


class Slot:  # pylint: disable=E1101,R0903
    """
        Slot Resource

        self is pointing to current Module instance

        web.slot decorator takes one argument: slot name
        Note: web.slot decorator must be the last decorator (at top)

        Slot resources use check_slot auth decorator
        auth.decorators.check_slot takes the following arguments:
        - permissions
        - scope_id=1
        - access_denied_reply=None -> can be set to content to return in case of 'access denied'

    """

    @web.slot('integrations_configuration_add_button')
    def add_button(self, context, slot, payload):
        with context.app.app_context():
            return render_template(
                'integrations:configuration/add_button.html',
                config=payload
            )

    @web.slot('integrations_configuration_content')
    def configuration_content(self, context, slot, payload):
        # log.warning('config payload %s', payload)
        project_id = self.context.rpc_manager.call.project_get_id()

        results = self.get_project_integrations(project_id)  # comes from RPC

        # payload['existing_integrations'] = results
        # payload['integrations_section_list'] = context.rpc_manager.call.integrations_section_list()

        with context.app.app_context():
            return render_template(
                'integrations:configuration/content.html',
                existing_integrations=results,
                integrations_section_list=context.rpc_manager.call.integrations_section_list()
            )

    @web.slot('integrations_configuration_styles')
    def configuration_styles(self, context, slot, payload):
        with context.app.app_context():
            return render_template(
                'integrations:configuration/styles.html',
                config=payload
            )

    @web.slot('integrations_configuration_scripts')
    def configuration_scripts(self, context, slot, payload):
        with context.app.app_context():
            return render_template(
                'integrations:configuration/scripts.html',
                config=payload
            )
