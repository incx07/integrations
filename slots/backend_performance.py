from pylon.core.tools import web, log
from tools import auth, theme


class Slot:

    @web.slot('integrations_backend_performance_content')
    # @auth.decorators.check_slot(["configuration.integrations"], access_denied_reply=theme.access_denied_part)
    def content(self, context, slot, payload):
        if payload is None:
            payload = {}
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/content.html',
                processing=self.get_section('processing'),
                reporters=self.get_section('reporters'),
                system=self.get_section('system'),
                instance_name_prefix=payload.get('instance_name_prefix', '')
            )

    @web.slot('integrations_backend_performance_scripts')
    # @auth.decorators.check_slot(["configuration.integrations"])
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/scripts.html',
                processing=self.get_section('processing'),
                reporters=self.get_section('reporters'), 
                system=self.get_section('system')
            )

    @web.slot('integrations_backend_performance_styles')
    # @auth.decorators.check_slot(["configuration.integrations"])
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/styles.html',
                processing=self.get_section('processing'),
                reporters=self.get_section('reporters'),
                system=self.get_section('system')
            )
