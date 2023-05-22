from pylon.core.tools import web, log
from tools import auth, theme


class Slot:

    @web.slot('integrations_security_app_content')
    # @auth.decorators.check_slot(["configuration.integrations"])
    def content(self, context, slot, payload):
        with context.app.app_context():
            allowed_sections = (
                "processing", 
                "scanners", 
                "reporters"
            )
            sections = [
                section for section in self.section_list() 
                if section.name in allowed_sections
            ]
            return self.descriptor.render_template(
                'security/app/content.html',
                integrations_section_list=sections
            )

    @web.slot('integrations_security_app_scripts')
    # @auth.decorators.check_slot(["configuration.integrations"])
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/app/scripts.html',
                integrations_section_list=self.section_list()
            )

    @web.slot('integrations_security_app_styles')
    # @auth.decorators.check_slot(["configuration.integrations"])
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/app/styles.html',
                integrations_section_list=self.section_list()
            )
