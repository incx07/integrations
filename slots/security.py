from pylon.core.tools import web, log


class Slot:

    @web.slot('integrations_security_app_content')
    def security_app_content(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/app/content.html',
                integrations_section_list=self.section_list()
            )

    @web.slot('integrations_security_app_scripts')
    def security_app_scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/app/scripts.html',
                integrations_section_list=self.section_list()
            )

    @web.slot('integrations_security_app_styles')
    def security_app_styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/app/styles.html',
                integrations_section_list=self.section_list()
            )
