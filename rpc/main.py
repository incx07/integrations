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

from tools import rpc_tools, VaultClient
from tools import constants as c

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
    def get_project_integrations(self, project_id: int, group_by_section: bool = True,
            mode: str = c.DEFAULT_MODE
    ) -> dict:
        results = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.name.in_(self.integrations.keys()),
            Integration.mode == mode
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
    def get_project_integrations_by_name(self, project_id: Optional[int],
            integration_name: str,
            mode: str = c.DEFAULT_MODE
    ) -> List[IntegrationPD]:
        if integration_name not in self.integrations.keys():
            return []
        results = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.name == integration_name,
            Integration.mode == mode
        ).order_by(
            asc(Integration.section),
            desc(Integration.is_default),
            asc(Integration.name),
            desc(Integration.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('get_project_integrations_by_section')
    def get_project_integrations_by_section(self, project_id: Optional[int], section_name: str,
            mode: str = c.DEFAULT_MODE
    ) -> List[IntegrationPD]:
        if section_name not in self.sections.keys():
            return []
        results = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.section == section_name,
            Integration.mode == mode
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
        active_mode = integration_data["mode"]
        if active_mode == c.ADMINISTRATION_MODE:
            vault_client = VaultClient()
        else:
            vault_client = VaultClient.from_project(project_id)
        secrets = vault_client.get_project_hidden_secrets()
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

        vault_client.set_project_hidden_secrets(secrets)

        return settings

    @rpc('get_cloud_integrations')
    def get_cloud_integrations(self, project_id: int) -> list:
        """
        Gets project integrations in cloud section
        """
        integrations = self.get_project_integrations(project_id)
        admin_integrations = self.get_administration_integrations(group_by_section=True)
        integrations["clouds"].extend(admin_integrations["clouds"])

        cloud_regions = [
            {
                "name": f"{region.name.split('_')[0]} {region.description}"
                        f"{' - inherited' if region.mode == 'administration' else ''}"
                        f"{' - default' if region.is_default else ''}",
                "cloud_settings": {
                    "integration_name": region.name,
                    "id": region.id,
                    **region.settings
                }
            } for region in integrations["clouds"]]
        return cloud_regions

    @rpc('get_administration_integrations')
    def get_administration_integrations(self, group_by_section: bool = True) -> dict:
        results = Integration.query.filter(
            Integration.name.in_(self.integrations.keys()),
            Integration.mode == c.ADMINISTRATION_MODE
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

    @rpc('get_administration_integrations_by_name')
    def get_administration_integrations_by_name(self, integration_name: str) -> List[
        IntegrationPD]:
        if integration_name not in self.integrations.keys():
            return []
        results = Integration.query.filter(
            Integration.name == integration_name,
            Integration.mode == c.ADMINISTRATION_MODE
        ).order_by(
            asc(Integration.section),
            desc(Integration.is_default),
            asc(Integration.name),
            desc(Integration.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('get_administration_integrations_by_section')
    def get_administration_integrations_by_section(self, section_name: str) -> List[
        IntegrationPD]:
        if section_name not in self.sections.keys():
            return []
        results = Integration.query.filter(
            Integration.section == section_name,
            Integration.mode == c.ADMINISTRATION_MODE
        ).order_by(
            desc(Integration.is_default),
            asc(Integration.name),
            desc(Integration.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('get_all_integrations')
    def get_all_integrations(self, project_id: int, group_by_section: bool = True) -> dict:
        results_default = Integration.query.filter(
            Integration.project_id == project_id,
            Integration.name.in_(self.integrations.keys()),
            Integration.mode == c.DEFAULT_MODE
        ).group_by(
            Integration.section,
            Integration.id
        ).order_by(
            asc(Integration.section),
            desc(Integration.is_default),
            asc(Integration.name),
            desc(Integration.id)
        ).all()
        results_admin = Integration.query.filter(
            Integration.name.in_(self.integrations.keys()),
            Integration.mode == c.ADMINISTRATION_MODE
        ).group_by(
            Integration.section,
            Integration.id
        ).order_by(
            asc(Integration.section),
            desc(Integration.is_default),
            asc(Integration.name),
            desc(Integration.id)
        ).all()
        results_default = parse_obj_as(List[IntegrationPD], results_default)
        results_admin = parse_obj_as(List[IntegrationPD], results_admin)
        results = results_default + results_admin
        if not group_by_section:
            return results

        def reducer(accum: dict, new_value: IntegrationPD) -> dict:
            accum[new_value.section.name].append(new_value)
            return accum

        return reduce(reducer, results, defaultdict(list))

    @rpc('get_all_integrations_by_name')
    def get_all_integrations_by_name(self, project_id: int, integration_name: str) -> List[
        IntegrationPD]:
        return self.get_project_integrations_by_name(project_id, integration_name) + \
            self.get_administration_integrations_by_name(integration_name)

    @rpc('get_all_integrations_by_section')
    def get_all_integrations_by_section(self, project_id: int, section_name: str) -> List[
        IntegrationPD]:
        return self.get_project_integrations_by_section(project_id, section_name) + \
            self.get_administration_integrations_by_section(section_name)

    @rpc('update_attrs')
    def update_attrs(self, integration_id: int, update_dict: dict, return_result: bool = False
    ) -> Optional[dict]:
        log.info('update_attrs called %s', [integration_id, update_dict])
        update_dict.pop('id', None)
        Integration.query.filter(
            Integration.id == integration_id
        ).update(update_dict)
        Integration.commit()
        if return_result:
            return Integration.query.get(integration_id).to_json()
