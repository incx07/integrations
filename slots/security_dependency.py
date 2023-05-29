from pylon.core.tools import web
from tools import auth, theme


class Slot:

    @web.slot('integrations_security_dependency_content')
    # @auth.decorators.check_slot(["configuration.integrations"])
    def content(self, context, slot, payload):
        with context.app.app_context():
            allowed_sections = (
                "processing", 
                "reporters", 
                "dependency_scanners"
            )
            sections = [
                section for section in self.section_list() 
                if section.name in allowed_sections
            ]
            return self.descriptor.render_template(
                'security/code/content.html',
                integrations_section_list=sections
            )

    @web.slot('integrations_security_dependency_scripts')
    # @auth.decorators.check_slot(["configuration.integrations"])
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/code/scripts.html',
                integrations_section_list=self.section_list()
            )

    @web.slot('integrations_security_dependency_styles')
    # @auth.decorators.check_slot(["configuration.integrations"])
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/code/styles.html',
                integrations_section_list=self.section_list()
            )
