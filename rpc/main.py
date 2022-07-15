from collections import defaultdict
from functools import reduce
from queue import Empty
from typing import Optional, List

from pylon.core.tools import log
from sqlalchemy import desc, asc
from pydantic import parse_obj_as, ValidationError

from ..models.integration import Integration
from ..models.pd.integration import IntegrationPD
from ..models.pd.registration import RegistrationForm, SectionRegistrationForm

from tools import rpc_tools

from pylon.core.tools import web


class RPC:
    rpc = lambda name: web.rpc(f'integrations_{name}', name)

    @rpc('register')
    @rpc_tools.wrap_exceptions(ValidationError)
    def register(self, **kwargs) -> RegistrationForm:
        # self.context.rpc_manager.register_function(
        #     partial(register, self.integrations, self.context.slot_manager),
        #     name='_'.join([self.rpc_prefix, 'register'])
        # )
        form_data = RegistrationForm(**kwargs)
        self.integrations[form_data.name] = form_data
        # self.context.slot_manager.register_callback(
        #     f'integrations_{form_data.section}',
        #     form_data.integration_callback
        # )
        return form_data

    @rpc('get_by_name')
    def get_by_name(self, integration_name: str) -> Optional[RegistrationForm]:
        # self.context.rpc_manager.register_function(
        #     lambda integration_name: self.integrations.get(integration_name),
        #     name='_'.join([self.rpc_prefix, 'get_integration'])
        # )
        return self.integrations.get(integration_name)

    @rpc('list_integrations')
    def list_integrations(self) -> dict:
        # self.context.rpc_manager.register_function(
        #     lambda: self.integrations,
        #     name='_'.join([self.rpc_prefix, 'list'])
        # )
        return self.integrations

    @rpc('get_project_integrations')
    def get_project_integrations(self, project_id: int) -> dict:
        # self.context.rpc_manager.register_function(
        #     partial(get_project_integrations, registered_integrations=self.integrations.keys()),
        #     name='_'.join([self.rpc_prefix, 'get_project_integrations'])
        # )
        results = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.name.in_(self.integrations.keys())
        ).group_by(
            Integration.section,
            Integration.id
        ).order_by(
            asc(Integration.section),
            desc(Integration.is_default),
            desc(Integration.id)
        ).all()

        results = parse_obj_as(List[IntegrationPD], results)

        def reducer(accum: dict, new_value: IntegrationPD) -> dict:
            accum[new_value.section.name].append(new_value)
            return accum

        return reduce(reducer, results, defaultdict(list))

    @rpc('get_project_integrations_by_name')
    def get_project_integrations_by_name(self, project_id: int, integration_name: str) -> list:
        # self.context.rpc_manager.register_function(
        #     partial(get_project_integrations_by_name, registered_integrations=self.integrations.keys()),
        #     name='_'.join([self.rpc_prefix, 'get_project_integrations_by_name'])
        # )
        if integration_name not in self.integrations.keys():
            return []
        results = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.name == integration_name
        ).order_by(
            asc(Integration.section),
            desc(Integration.is_default),
            desc(Integration.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('register_section')
    @rpc_tools.wrap_exceptions(ValidationError)
    def register_section(self, *, force_overwrite: bool = False, **kwargs) -> SectionRegistrationForm:
        # self.context.rpc_manager.register_function(
        #     partial(register_section, reg_dict_section=self.sections),
        #     name='_'.join([self.rpc_prefix, 'register_section'])
        # )
        form_data = SectionRegistrationForm(**kwargs)
        if form_data.name not in self.sections or force_overwrite:
            self.sections[form_data.name] = form_data
        return form_data

    @rpc('get_section')
    def get_section(self, section_name: str) -> Optional[SectionRegistrationForm]:

    # self.context.rpc_manager.register_function(
    #     lambda section_name: self.sections.get(section_name),
    #     name='_'.join([self.rpc_prefix, 'get_section'])
    # )
        return self.sections.get(section_name)

    @rpc('section_list')
    def section_list(self) -> list:
        return self.sections.values()

    @rpc('get_by_id')
    def get_by_id(self, integration_id: int) -> Optional[Integration]:
        # self.context.rpc_manager.register_function(
        #     get_by_id,
        #     name='_'.join([self.rpc_prefix, 'get_by_id'])
        # )
        return Integration.query.filter(
            Integration.id == integration_id,
        ).one_or_none()

    @web.rpc('security_test_create_integrations')
    @rpc_tools.wrap_exceptions(ValidationError)
    def security_test_create(
            self,
            data: dict,
            skip_validation_if_undefined: bool = True,
            **kwargs
    ) -> dict:
        # self.context.rpc_manager.register_function(
        #     security_test_create,
        #     name='_'.join(['security_test_create', self.rpc_prefix])
        # )
        integration_data = dict()

        for section, integration in data.items():
            integration_data[section] = dict()
            for k, v in integration.items():
                try:
                    integration_data[section][k] = self.context.rpc_manager.call_function_with_timeout(
                        func=f'security_test_create_integration_validate_{k}',
                        timeout=1,
                        data=v,
                        **kwargs
                    )
                except Empty:
                    log.warning(f'Cannot validate integration data for {k}')
                    if skip_validation_if_undefined:
                        integration_data[section][k] = v
                except ValidationError as e:
                    for i in e.errors():
                        i['loc'] = [f'{section}_{k}', *i['loc']]
                    raise e
                except Exception as e:
                    e.loc = [f'{section}_{k}', *getattr(e, 'loc', [])]
                    raise e
        return {'integrations': integration_data}

    @web.rpc('backend_performance_test_create_integrations')
    @rpc_tools.wrap_exceptions(ValidationError)
    def backend_performance_test_create(
            self,
            data: dict,
            skip_validation_if_undefined: bool = True,
            **kwargs
    ) -> dict:
        # self.context.rpc_manager.register_function(
        #     security_test_create,
        #     name='_'.join(['security_test_create', self.rpc_prefix])
        # )
        integration_data = dict()

        for section, integration in data.items():
            integration_data[section] = dict()
            for k, v in integration.items():
                try:
                    integration_data[section][k] = self.context.rpc_manager.call_function_with_timeout(
                        func=f'backend_performance_test_create_integration_validate_{k}',
                        timeout=1,
                        data=v,
                        **kwargs
                    )
                except Empty:
                    log.warning(f'Cannot validate integration data for {k}')
                    if skip_validation_if_undefined:
                        integration_data[section][k] = v
                except ValidationError as e:
                    for i in e.errors():
                        i['loc'] = [f'{section}_{k}', *i['loc']]
                    raise e
                except Exception as e:
                    e.loc = [f'{section}_{k}', *getattr(e, 'loc', [])]
                    raise e
        return {'integrations': integration_data}
