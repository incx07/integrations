from pylon.core.tools import web, log


class Slot:

    @web.slot('integrations_backend_performance_content')
    def security_app_content(self, context, slot, payload):
        if payload is None:
            payload = {}
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/content.html',
                reporters=self.get_section('reporters'),
                instance_name_prefix=payload.get('instance_name_prefix', '')
            )

    @web.slot('integrations_backend_performance_scripts')
    def security_app_scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/scripts.html',
                reporters=self.get_section('reporters')
            )

    @web.slot('integrations_backend_performance_styles')
    def security_app_styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/styles.html',
                reporters=self.get_section('reporters')
            )
