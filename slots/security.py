from flask import render_template

from pylon.core.tools import web, log


class Slot:

    @web.slot('integrations_security_app_content')
    def security_app_content(self, context, slot, payload):
        integrations_section_list = context.rpc_manager.call.integrations_section_list()
        with context.app.app_context():
            return self.descriptor.render_template(
                'security/app.html',
                integrations_section_list=integrations_section_list
            )
