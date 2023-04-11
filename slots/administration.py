from pylon.core.tools import web, log
# from flask import g

from tools import session_project


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

    @web.slot('administration_integrations_configuration_content')
    def content(self, context, slot, payload):
        existing_integrations = self.get_administration_integrations()  # comes from RPC
        all_sections = tuple(i.dict(exclude={'test_planner_description'}) for i in self.section_list())
        for i in all_sections:
            # i['integrations'] = existing_integrations.get(i['name'], [])
            i['integrations'] = list(map(lambda x: x.dict(), existing_integrations.get(i['name'], [])))
            # i['integrations_parsed'] = [pd.dict() for pd in i['integrations']]

        with context.app.app_context():
            log.info(f'existing_integrations {existing_integrations}')
            log.info(f'integrations_section_list {self.section_list()}')
            log.info(f'all_sections {all_sections}')
            return self.descriptor.render_template(
                'administration/content.html',
                existing_integrations=existing_integrations,
                integrations_section_list=self.section_list(),
                all_sections=all_sections
            )

    @web.slot('administration_integrations_configuration_styles')
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'administration/styles.html',
                integrations_section_list=self.section_list()
            )

    @web.slot('administration_integrations_configuration_scripts')
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'administration/scripts.html',
                integrations_section_list=self.section_list()
            )
