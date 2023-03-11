from pylon.core.tools import web, log


class Slot:

    @web.slot('integrations_security_sast_content')
    def content(self, context, slot, payload):
        with context.app.app_context():
            disabled_sections = ("clouds", "scanners")
            sections = [section for section in self.section_list() if section.name not in disabled_sections]
            return self.descriptor.render_template(
                'security/code/content.html',
                integrations_section_list=sections
            )

    @web.slot('integrations_security_sast_scripts')
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/code/scripts.html',
                integrations_section_list=self.section_list()
            )

    @web.slot('integrations_security_sast_styles')
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/code/styles.html',
                integrations_section_list=self.section_list()
            )
