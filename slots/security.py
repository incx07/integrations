from pylon.core.tools import web, log


class Slot:

    @web.slot('integrations_security_app_content')
    def content(self, context, slot, payload):
        with context.app.app_context():
            disabled_sections = ("clouds", "code_scanners")
            sections = [section for section in self.section_list() if section.name not in disabled_sections]
            return self.descriptor.render_template(
                'security/app/content.html',
                integrations_section_list=sections
            )

    @web.slot('integrations_security_app_scripts')
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/app/scripts.html',
                integrations_section_list=self.section_list()
            )

    @web.slot('integrations_security_app_styles')
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/app/styles.html',
                integrations_section_list=self.section_list()
            )
