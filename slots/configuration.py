from pylon.core.tools import web, log
# from flask import g
from flask import make_response, after_this_request
from tools import auth, theme
from datetime import datetime


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

    # @web.slot('integrations_configuration_add_button')
    # def add_button(self, context, slot, payload):
    #     with context.app.app_context():
    #         return self.descriptor.render_template(
    #             'configuration/add_button.html',
    #             config=payload
    #         )

    @web.slot('integrations_configuration_content')
    @auth.decorators.check_slot(["configuration.integrations"], access_denied_reply=theme.access_denied_part)
    def content(self, context, slot, payload):
        from tools import session_project
        
        @after_this_request
        def add_header(response):
            response.headers['Cache-Control'] = 'max-age=0, must-revalidate'
            response.headers['Last-Modified'] = datetime.now()
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '-1'
            return response

        project_id = session_project.get()
        existing_integrations = self.get_all_integrations(project_id)  # comes from RPC
        all_sections = tuple(i.dict(exclude={'test_planner_description'}) for i in self.section_list())
        for i in all_sections:
            # i['integrations'] = existing_integrations.get(i['name'], [])
            i['integrations'] = list(map(lambda x: x.dict(), existing_integrations.get(i['name'], [])))
            # i['integrations_parsed'] = [pd.dict() for pd in i['integrations']]
        with context.app.app_context():
            return self.descriptor.render_template(
                'configuration/content.html',
                existing_integrations=existing_integrations,
                integrations_section_list=self.section_list(),
                all_sections=all_sections
            )

    @web.slot('integrations_configuration_styles')
    @auth.decorators.check_slot(["configuration.integrations"])
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'configuration/styles.html',
                integrations_section_list=self.section_list()
            )

    @web.slot('integrations_configuration_scripts')
    @auth.decorators.check_slot(["configuration.integrations"])
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'configuration/scripts.html',
                integrations_section_list=self.section_list()
            )
