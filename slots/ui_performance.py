from pylon.core.tools import web, log


class Slot:

    @web.slot('integrations_ui_performance_content')
    def content(self, context, slot, payload):
        if payload is None:
            payload = {}
        with context.app.app_context():
            return self.descriptor.render_template(
                'ui_performance/content.html',
                reporters=self.get_section('reporters'),
                instance_name_prefix=payload.get('instance_name_prefix', '')
            )

    @web.slot('integrations_ui_performance_scripts')
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'ui_performance/scripts.html',
                reporters=self.get_section('reporters')
            )

    @web.slot('integrations_ui_performance_styles')
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'ui_performance/styles.html',
                reporters=self.get_section('reporters')
            )
