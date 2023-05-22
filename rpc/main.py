from collections import defaultdict
from functools import reduce
from queue import Empty
from typing import Optional, List

from pylon.core.tools import log
from sqlalchemy import desc, asc
from pydantic import parse_obj_as, ValidationError

from ..models.integration import IntegrationProject, IntegrationAdmin, IntegrationDefault
from ..models.pd.integration import IntegrationPD, SecretField, IntegrationProjectPD
from ..models.pd.registration import RegistrationForm, SectionRegistrationForm

from tools import rpc_tools, VaultClient, db
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
    def get_project_integrations(self, project_id: int, group_by_section: bool = True) -> dict:
        with db.with_project_schema_session(project_id) as tenant_session:
            results = tenant_session.query(IntegrationProject).filter(
                IntegrationProject.project_id == project_id,
                IntegrationProject.name.in_(self.integrations.keys()),
            ).group_by(
                IntegrationProject.section,
                IntegrationProject.id
            ).order_by(
                asc(IntegrationProject.section),
                # desc(IntegrationProject.is_default),
                asc(IntegrationProject.name),
                desc(IntegrationProject.id)
            ).all()

        results = parse_obj_as(List[IntegrationProjectPD], results)

        if not group_by_section:
            return results

        def reducer(accum: dict, new_value: IntegrationProjectPD) -> dict:
            accum[new_value.section.name].append(new_value)
            return accum

        return reduce(reducer, results, defaultdict(list))

    @rpc('get_project_integrations_by_name')
    def get_project_integrations_by_name(self, project_id: Optional[int], integration_name: str
                                         ) -> List[IntegrationProjectPD]:
        if integration_name not in self.integrations.keys():
            return []
        with db.with_project_schema_session(project_id) as tenant_session:
            results = tenant_session.query(IntegrationProject).filter(
                IntegrationProject.project_id == project_id,
                IntegrationProject.name == integration_name
            ).order_by(
                asc(IntegrationProject.section),
                desc(IntegrationProject.is_default),
                asc(IntegrationProject.name),
                desc(IntegrationProject.id)
            ).all()
        results = parse_obj_as(List[IntegrationProjectPD], results)
        return results

    @rpc('get_project_integrations_by_section')
    def get_project_integrations_by_section(self, project_id: Optional[int], section_name: str,
                                            ) -> List[IntegrationProjectPD]:
        if section_name not in self.sections.keys():
            return []
        with db.with_project_schema_session(project_id) as tenant_session:
            results = tenant_session.query(IntegrationProject).filter(
                IntegrationProject.project_id == project_id,
                IntegrationProject.section == section_name
            ).order_by(
                desc(IntegrationProject.is_default),
                asc(IntegrationProject.name),
                desc(IntegrationProject.id)
            ).all()
        results = parse_obj_as(List[IntegrationProjectPD], results)
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
    def get_by_id(self, project_id: int, integration_id: int) -> Optional[IntegrationProject]:
        if project_id is not None:
            with db.with_project_schema_session(project_id) as tenant_session:
                return tenant_session.query(IntegrationProject).filter(
                    IntegrationProject.id == integration_id,
                ).one_or_none()
        return IntegrationAdmin.query.filter(
            IntegrationAdmin.id == integration_id,
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
        project_id = integration_data.get("project_id")
        if project_id is not None:
            vault_client = VaultClient.from_project(project_id)
        else:
            vault_client = VaultClient()
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
        results = IntegrationAdmin.query.filter(
            IntegrationAdmin.name.in_(self.integrations.keys())
        ).group_by(
            IntegrationAdmin.section,
            IntegrationAdmin.id
        ).order_by(
            asc(IntegrationAdmin.section),
            desc(IntegrationAdmin.is_default),
            asc(IntegrationAdmin.name),
            desc(IntegrationAdmin.id)
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
        results = IntegrationAdmin.query.filter(
            IntegrationAdmin.name == integration_name
        ).order_by(
            asc(IntegrationAdmin.section),
            desc(IntegrationAdmin.is_default),
            asc(IntegrationAdmin.name),
            desc(IntegrationAdmin.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('get_administration_integrations_by_section')
    def get_administration_integrations_by_section(self, section_name: str) -> List[
        IntegrationPD]:
        if section_name not in self.sections.keys():
            return []
        results = IntegrationAdmin.query.filter(
            IntegrationAdmin.section == section_name,
        ).order_by(
            desc(IntegrationAdmin.is_default),
            asc(IntegrationAdmin.name),
            desc(IntegrationAdmin.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('process_default_integrations')
    def process_default_integrations(self, project_id, integrations):
        for integration in integrations:
            integration.is_default = False
            if self.is_default(project_id, integration.dict()):
                integration.is_default = True
        return integrations

    @rpc('get_all_integrations')
    def get_all_integrations(self, project_id: int, group_by_section: bool = True) -> dict:
        with db.with_project_schema_session(project_id) as tenant_session:
            results_project = tenant_session.query(IntegrationProject).filter(
                IntegrationProject.project_id == project_id,
                IntegrationProject.name.in_(self.integrations.keys())
            ).group_by(
                IntegrationProject.section,
                IntegrationProject.id
            ).order_by(
                asc(IntegrationProject.section),
                desc(IntegrationProject.is_default),
                asc(IntegrationProject.name),
                desc(IntegrationProject.id)
            ).all()
        results_admin = IntegrationAdmin.query.filter(
            IntegrationAdmin.name.in_(self.integrations.keys())
        ).group_by(
            IntegrationAdmin.section,
            IntegrationAdmin.id
        ).order_by(
            asc(IntegrationAdmin.section),
            desc(IntegrationAdmin.is_default),
            asc(IntegrationAdmin.name),
            desc(IntegrationAdmin.id)
        ).all()
        results_project = parse_obj_as(List[IntegrationProjectPD], results_project)
        results_admin = parse_obj_as(List[IntegrationPD], results_admin)
        results_admin = self.process_default_integrations(project_id, results_admin)
        results = results_project + results_admin
        if not group_by_section:
            return results

        def reducer(accum: dict, new_value: IntegrationPD) -> dict:
            accum[new_value.section.name].append(new_value)
            return accum
        return reduce(reducer, results, defaultdict(list))

    @rpc('get_all_integrations_by_name')
    def get_all_integrations_by_name(self, project_id: int, integration_name: str) -> List[IntegrationPD]:
        results_admin = self.get_administration_integrations_by_name(integration_name)
        results_admin = self.process_default_integrations(project_id, results_admin)
        return self.get_project_integrations_by_name(project_id, integration_name) + results_admin


    @rpc('get_all_integrations_by_section')
    def get_all_integrations_by_section(self, project_id: int, section_name: str) -> List[IntegrationPD]:
        results_admin = self.get_administration_integrations_by_section(section_name)
        results_admin = self.process_default_integrations(project_id, results_admin)
        return self.get_project_integrations_by_section(project_id, section_name) + results_admin

    @rpc('update_attrs')
    def update_attrs(self, integration_id: int, project_id: int, update_dict: dict, return_result: bool = False
                     ) -> Optional[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:        
            log.info('update_attrs called %s', [integration_id, project_id, update_dict])
            update_dict.pop('id', None)
            tenant_session.query(IntegrationProject).filter(
                IntegrationProject.id == integration_id
            ).update(update_dict)
            tenant_session.commit()
            if return_result:
                return tenant_session.query(IntegrationProject).get(integration_id).to_json()

    @rpc('make_default_integration')
    def make_default_integration(self, integration, project_id):
        with db.with_project_schema_session(project_id) as tenant_session: 
            default_integration = tenant_session.query(IntegrationDefault).filter(
                IntegrationDefault.name == integration.name,
                IntegrationDefault.is_default == True,
            ).one_or_none()
            if default_integration:
                default_integration.project_id = integration.project_id
                default_integration.integration_id = integration.id
                tenant_session.commit()
            else:
                default_integration = IntegrationDefault(name=integration.name,
                                                         project_id=integration.project_id, 
                                                         integration_id = integration.id,
                                                         is_default=True,
                                                         section=integration.section
                                                         )
                tenant_session.add(default_integration)
                tenant_session.commit()

    @rpc('delete_default_integration')
    def delete_default_integration(self, integration, project_id):
        with db.with_project_schema_session(project_id) as tenant_session: 
            default_integration = tenant_session.query(IntegrationDefault).filter(
                IntegrationDefault.name == integration.name,
                IntegrationDefault.is_default == True,
                IntegrationDefault.integration_id == integration.id,
            ).one_or_none()
            if default_integration:
                tenant_session.delete(default_integration)
                tenant_session.commit()

    @rpc('get_defaults')
    def get_defaults(self, project_id):
        with db.with_project_schema_session(project_id) as tenant_session: 
            return tenant_session.query(IntegrationDefault).all()

    @rpc('is_default')
    def is_default(self, project_id, integration_data):
        with db.with_project_schema_session(project_id) as tenant_session: 
            return tenant_session.query(IntegrationDefault).filter(
                IntegrationDefault.name == integration_data['name'],
                IntegrationDefault.is_default == True,
                IntegrationDefault.integration_id == integration_data['id'],
                IntegrationDefault.project_id == integration_data['project_id'],
            ).one_or_none()

    @rpc('get_s3_settings')
    def get_s3_settings(self, project_id, integration_id=None):

        def _usecret_field(integration_db):
            settings = integration_db.settings
            secret_access_key = SecretField.parse_obj(settings['secret_access_key'])
            settings['secret_access_key'] = secret_access_key.unsecret(project_id=project_id)
            return settings
        try:
            if integration_id:
                with db.with_project_schema_session(project_id) as tenant_session:
                    integration_db = tenant_session.query(IntegrationProject).filter(
                        IntegrationProject.id == integration_id
                    ).one_or_none()
                    if integration_db:
                        return _usecret_field(integration_db)
            else:
                with db.with_project_schema_session(project_id) as tenant_session:
                    default_integration = tenant_session.query(IntegrationDefault).filter(
                        IntegrationDefault.name == 's3_integration'
                    ).one_or_none()
                    if default_integration and default_integration.project_id:
                        integration_db = tenant_session.query(IntegrationProject).filter(
                            IntegrationProject.id == default_integration.integration_id
                        ).one_or_none()
                        if integration_db:
                            return _usecret_field(integration_db)
                    elif default_integration:
                        integration_db = IntegrationAdmin.query.filter(
                            IntegrationAdmin.id == default_integration.integration_id
                        ).one_or_none()
                        if integration_db:
                            return _usecret_field(integration_db)
        except Exception as e:
            log.warning(f'Cannot receive S3 settings of project {project_id}')
