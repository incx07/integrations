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
import json
from functools import partial

import flask  # pylint: disable=E0401
import jinja2  # pylint: disable=E0401
from flask import request, make_response, session, redirect, Response

from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import module  # pylint: disable=E0611,E0401

from .api.validation import IntegrationsApi, CheckSettingsApi
from .components.integrations_list import render_integrations
from .components.security import create
from .init_db import init_db
from .rpc import register, get_project_integrations, \
    get_project_integrations_by_name, register_section
from ..shared.utils.api_utils import add_resource_to_api
from ..shared.utils.rpc import RpcMixin


class Module(module.ModuleModel):
    """ Pylon module """

    def __init__(self, settings, root_path, context):
        self.settings = settings
        self.root_path = root_path
        self.context = context
        self.rpc_prefix = 'integrations'

        self.integrations = dict()
        self.sections = dict()

    def init(self):
        """ Init module """
        log.info('Initializing module integrations')
        init_db()

        # RPC
        RpcMixin.set_rpc_manager(self.context.rpc_manager)

        self.context.rpc_manager.register_function(
            partial(register, self.integrations, self.context.slot_manager),
            name='_'.join([self.rpc_prefix, 'register'])
        )
        self.context.rpc_manager.register_function(
            lambda integration_name: self.integrations.get(integration_name),
            name='_'.join([self.rpc_prefix, 'get_integration'])
        )
        self.context.rpc_manager.register_function(
            lambda: self.integrations,
            name='_'.join([self.rpc_prefix, 'list'])
        )
        self.context.rpc_manager.register_function(
            partial(get_project_integrations, registered_integrations=self.integrations.keys()),
            name='_'.join([self.rpc_prefix, 'get_project_integrations'])
        )
        self.context.rpc_manager.register_function(
            partial(get_project_integrations_by_name, registered_integrations=self.integrations.keys()),
            name='_'.join([self.rpc_prefix, 'get_project_integrations_by_name'])
        )

        self.context.rpc_manager.register_function(
            partial(register_section, reg_dict_section=self.sections),
            name='_'.join([self.rpc_prefix, 'register_section'])
        )
        self.context.rpc_manager.register_function(
            lambda section_name: self.sections.get(section_name),
            name='_'.join([self.rpc_prefix, 'get_section'])
        )
        self.context.rpc_manager.register_function(
            # lambda: set((i.section for i in self.integrations.values())),
            lambda: self.sections.values(),
            name='_'.join([self.rpc_prefix, 'section_list'])
        )

        # blueprint endpoints
        bp = flask.Blueprint(
            'integrations', 'plugins.integrations',
            root_path=self.root_path,
            url_prefix=f'{self.context.url_prefix}/integr'
        )
        bp.jinja_loader = jinja2.ChoiceLoader([
            jinja2.loaders.PackageLoader("plugins.integrations", "templates"),
        ])
        bp.add_url_rule('/', 'get_registered', self.get_registered, methods=['GET'])
        self.context.app.register_blueprint(bp)

        # API
        add_resource_to_api(
            self.context.api, IntegrationsApi,
            '/integrations/<int:project_id>',
            '/integrations/<string:integration_name>',
            '/integrations/<string:integration_name>/<int:integration_id>'
        )
        add_resource_to_api(
            self.context.api, CheckSettingsApi,
            '/integrations/<string:integration_name>/check_settings',
        )

        # SLOTS
        self.context.slot_manager.register_callback('integrations', render_integrations)
        self.context.slot_manager.register_callback('integrations_security_create', create)



    def get_registered(self):
        from ..shared.connectors.auth import SessionProject
        SessionProject.set(1)

        def is_serializable(item):
            try:
                json.dumps(item)
                return True
            except (TypeError, OverflowError):
                return False

        serialize = lambda d: {k: {
                kk: vv if is_serializable(vv) else str(vv)
                for kk, vv in v.dict().items()
            } for k, v in d.items()
        }

        integrations = serialize(self.integrations)

        sections = serialize(self.sections)


        response = make_response({
            'sections': sections,
            'integrations': integrations
        }, 200)
        response.headers['Content-Type'] = 'application/json'


        return response


    def deinit(self):  # pylint: disable=R0201
        """ De-init module """
        log.info('De-initializing module integrations')
        self.integrations = dict()
