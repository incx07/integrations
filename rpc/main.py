from collections import defaultdict
from functools import reduce
from queue import Empty
from typing import Optional, List

from pylon.core.tools import log
from sqlalchemy import desc, asc
from pydantic import parse_obj_as, ValidationError

from ..models.integration import Integration
from ..models.pd.integration import IntegrationPD, SecretField
from ..models.pd.registration import RegistrationForm, SectionRegistrationForm

from tools import rpc_tools, secrets_tools

from pylon.core.tools import web


class RPC:
    rpc = lambda name: web.rpc(f'integrations_{name}', name)

    @rpc('register')
    @rpc_tools.wrap_exceptions(ValidationError)
    def register(self, **kwargs) -> RegistrationForm:
        form_data = RegistrationForm(**kwargs)
        self.integrations[form_data.name] = form_data
        return form_data

    @rpc('get_by_name')
    def get_by_name(self, integration_name: str) -> Optional[RegistrationForm]:
        return self.integrations.get(integration_name)

    @rpc('list_integrations')
    def list_integrations(self) -> dict:
        return self.integrations

    @rpc('get_project_integrations')
    def get_project_integrations(self, project_id: int, group_by_section: bool = True) -> dict:
        results = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.name.in_(self.integrations.keys())
        ).group_by(
            Integration.section,
            Integration.id
        ).order_by(
            asc(Integration.section),
            desc(Integration.is_default),
            asc(Integration.name),
            desc(Integration.id)
        ).all()

        results = parse_obj_as(List[IntegrationPD], results)

        if not group_by_section:
            return results

        def reducer(accum: dict, new_value: IntegrationPD) -> dict:
            accum[new_value.section.name].append(new_value)
            return accum

        return reduce(reducer, results, defaultdict(list))

    @rpc('get_project_integrations_by_name')
    def get_project_integrations_by_name(self, project_id: int, integration_name: str) -> List[IntegrationPD]:
        if integration_name not in self.integrations.keys():
            return []
        results = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.name == integration_name
        ).order_by(
            asc(Integration.section),
            desc(Integration.is_default),
            asc(Integration.name),
            desc(Integration.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('get_project_integrations_by_section')
    def get_project_integrations_by_section(self, project_id: int, section_name: str) -> List[IntegrationPD]:
        if section_name not in self.sections.keys():
            return []
        results = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.section == section_name
        ).order_by(
            desc(Integration.is_default),
            asc(Integration.name),
            desc(Integration.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('register_section')
    @rpc_tools.wrap_exceptions(ValidationError)
    def register_section(self, *, force_overwrite: bool = False, **kwargs
    ) -> SectionRegistrationForm:
        form_data = SectionRegistrationForm(**kwargs)
        if form_data.name not in self.sections or force_overwrite:
            self.sections[form_data.name] = form_data
        return form_data

    @rpc('get_section')
    def get_section(self, section_name: str) -> Optional[SectionRegistrationForm]:
        return self.sections.get(section_name)

    @rpc('section_list')
    def section_list(self) -> list:
        return self.sections.values()

    @rpc('get_by_id')
    def get_by_id(self, integration_id: int) -> Optional[Integration]:
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
        integration_data = dict()

        for section, integration in data.items():
            integration_data[section] = dict()
            for k, v in integration.items():
                try:
                    integration_data[section][
                        k] = self.context.rpc_manager.call_function_with_timeout(
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
        integration_data = dict()

        for section, integration in data.items():
            integration_data[section] = dict()
            for k, v in integration.items():
                try:
                    integration_data[section][
                        k] = self.context.rpc_manager.call_function_with_timeout(
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

    @web.rpc('ui_performance_test_create_integrations')
    @rpc_tools.wrap_exceptions(ValidationError)
    def ui_performance_test_create(
            self,
            data: dict,
            skip_validation_if_undefined: bool = True,
            **kwargs
    ) -> dict:
        integration_data = dict()

        for section, integration in data.items():
            integration_data[section] = dict()
            for k, v in integration.items():
                try:
                    integration_data[section][
                        k] = self.context.rpc_manager.call_function_with_timeout(
                        func=f'ui_performance_test_create_integration_validate_{k}',
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

    @rpc('process_secrets')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def process_secrets(self, integration_data: dict) -> dict:
        """
        Processes secret field in settings of integration
        Finds all secret field and if it exists and given raw,
        writes to secret and replaced field in database with link

        :return: settings of integration dict
        """
        project_id = integration_data["project_id"]
        secrets = secrets_tools.get_project_hidden_secrets(project_id)
        settings: dict = integration_data["settings"]

        for field, value in settings.items():
            try:
                secret_field = SecretField.parse_obj(value)
            except ValidationError:
                continue
            if secret_field.from_secrets:
                continue

            secret_path = f"{field}_{integration_data['id']}"
            secrets[secret_path] = secret_field.value

            secret_field.value = "{{" + f"secret.{secret_path}" + "}}"
            secret_field.from_secrets = True

            settings[field] = secret_field.dict()

        secrets_tools.set_project_hidden_secrets(integration_data["project_id"], secrets)

        return settings

    @rpc('get_cloud_integrations')
    def get_cloud_integrations(self, project_id: int) -> list:
        """
        Gets project integrations in cloud section
        """
        integrations = self.get_project_integrations(project_id)
        cloud_regions = [
            {
                "name": f"{region.name.split('_')[0]} {region.description}"
                        f"{' - default' if region.is_default else ''}",
                "cloud_settings": {
                    "integration_name": region.name,
                    "id": region.id,
                    **region.settings
                }
            } for region in integrations["clouds"]]
        return cloud_regions

    @rpc('set_task_id')
    def set_task_id(self, integration_id, task_id):
        integration = Integration.query.get(integration_id)
        if not integration:
            return
        integration.task_id = task_id
        integration.commit()

