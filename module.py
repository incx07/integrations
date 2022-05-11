#!/usr/bin/python3
# coding=utf-8

#   Copyright 2021 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Module """
from functools import partial

from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import module  # pylint: disable=E0611,E0401

# from .api.validation import IntegrationsApi, CheckSettingsApi
# from .slots.integrations_list import render_integrations, render_default_add_button
# from .slots.security import create
from .init_db import init_db
# from .rpc import register, get_project_integrations, \
#     get_project_integrations_by_name, register_section, get_by_id, security_test_create
# from ..shared.utils.api_utils import add_resource_to_api
# from ..shared.utils.rpc import RpcMixin

from tools import theme


class Module(module.ModuleModel):
    """ Pylon module """

    def __init__(self, context, descriptor):
        self.context = context
        self.descriptor = descriptor
        self.rpc_prefix = 'integrations'

        self.integrations = dict()
        self.sections = dict()

    def init(self):
        """ Init module """
        log.info('Initializing module')
        init_db()

        self.descriptor.init_rpcs()
        # RPC
        # RpcMixin.set_rpc_manager(self.context.rpc_manager)

        # self.context.rpc_manager.register_function(
        #     partial(register, self.integrations, self.context.slot_manager),
        #     name='_'.join([self.rpc_prefix, 'register'])
        # )
        # self.context.rpc_manager.register_function(
        #     lambda integration_name: self.integrations.get(integration_name),
        #     name='_'.join([self.rpc_prefix, 'get_integration'])
        # )
        # self.context.rpc_manager.register_function(
        #     lambda: self.integrations,
        #     name='_'.join([self.rpc_prefix, 'list'])
        # )
        # self.context.rpc_manager.register_function(
        #     partial(get_project_integrations, registered_integrations=self.integrations.keys()),
        #     name='_'.join([self.rpc_prefix, 'get_project_integrations'])
        # )

        # self.context.rpc_manager.register_function(
        #     partial(get_project_integrations_by_name, registered_integrations=self.integrations.keys()),
        #     name='_'.join([self.rpc_prefix, 'get_project_integrations_by_name'])
        # )
        #
        # self.context.rpc_manager.register_function(
        #     partial(register_section, reg_dict_section=self.sections),
        #     name='_'.join([self.rpc_prefix, 'register_section'])
        # )
        # self.context.rpc_manager.register_function(
        #     lambda section_name: self.sections.get(section_name),
        #     name='_'.join([self.rpc_prefix, 'get_section'])
        # )
        # self.context.rpc_manager.register_function(
        #     # lambda: set((i.section for i in self.integrations.values())),
        #     lambda: self.sections.values(),
        #     name='_'.join([self.rpc_prefix, 'section_list'])
        # )
        # self.context.rpc_manager.register_function(
        #     get_by_id,
        #     name='_'.join([self.rpc_prefix, 'get_by_id'])
        # )
        # self.context.rpc_manager.register_function(
        #     security_test_create,
        #     name='_'.join(['security_test_create', self.rpc_prefix])
        # )

        # blueprint endpoints
        self.descriptor.init_blueprint()

        # API
        self.descriptor.init_api()
        # add_resource_to_api(
        #     self.context.api, IntegrationsApi,
        #     '/integrations/<int:project_id>',
        #     '/integrations/<string:integration_name>',
        #     '/integrations/<string:integration_name>/<int:integration_id>'
        # )
        # add_resource_to_api(
        #     self.context.api, CheckSettingsApi,
        #     '/integrations/<string:integration_name>/check_settings',
        # )


        # SLOTS
        self.descriptor.init_slots()
        # self.context.slot_manager.register_callback(self.rpc_prefix, render_integrations)
        # self.context.slot_manager.register_callback(f'{self.rpc_prefix}_security_create', create)
        # self.context.slot_manager.register_callback(f'{self.rpc_prefix}_default_add_button', render_default_add_button)

        theme.register_subsection(
            'configuration', 'integrations',
            'Integrations',
            title="Integrations",
            kind="slot",
            prefix="configuration_integrations_",
            weight=5,
        )


    def deinit(self):  # pylint: disable=R0201
        """ De-init module """
        log.info('De-initializing module integrations')
        self.integrations = dict()
        self.sections = dict()
