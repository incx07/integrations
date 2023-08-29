from collections import defaultdict
from functools import reduce
from queue import Empty
from typing import Optional, List

from pylon.core.tools import log
from sqlalchemy import desc, asc, Boolean
from pydantic import parse_obj_as, ValidationError

from ..models.integration import IntegrationProject, IntegrationAdmin, IntegrationDefault
from ..models.pd.integration import IntegrationPD, SecretField, IntegrationDefaultPD
from ..models.pd.registration import RegistrationForm, SectionRegistrationForm

from tools import rpc_tools, VaultClient, db
from tools import constants as c

from pylon.core.tools import web


def _usecret_field(integration_db, project_id, is_local):
    settings = integration_db.settings
    secret_access_key = SecretField.parse_obj(settings['secret_access_key'])
    settings['secret_access_key'] = secret_access_key.unsecret(project_id=project_id)
    settings['integration_id'] = integration_db.id
    settings['is_local'] = is_local
    return settings


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

        results = parse_obj_as(List[IntegrationPD], results)
        results = self.process_default_integrations(project_id, results)

        if not group_by_section:
            return results

        def reducer(accum: dict, new_value: IntegrationPD) -> dict:
            accum[new_value.section.name].append(new_value)
            return accum

        return reduce(reducer, results, defaultdict(list))

    @rpc('get_project_integrations_by_name')
    def get_project_integrations_by_name(self, project_id: Optional[int], integration_name: str
                                         ) -> List[IntegrationPD]:
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
        results = parse_obj_as(List[IntegrationPD], results)
        return self.process_default_integrations(project_id, results)

    @rpc('get_project_integrations_by_section')
    def get_project_integrations_by_section(self, project_id: Optional[int], section_name: str,
                                            ) -> List[IntegrationPD]:
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
        results = parse_obj_as(List[IntegrationPD], results)
        return self.process_default_integrations(project_id, results)

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
    def get_by_id(self, project_id: Optional[int], integration_id: int) -> Optional[IntegrationProject]:
        """
        Get integration by id. Works properly if you know: inherited this integration or not.
        :param project_id: id of project, where integration was created. If None - integration
        from administration mode
        :param integration_id: id of integration
        :return: integration ORM object or None
        """        
        if project_id is not None:
            with db.with_project_schema_session(project_id) as tenant_session:
                return tenant_session.query(IntegrationProject).filter(
                    IntegrationProject.id == integration_id,
                ).one_or_none()
        return IntegrationAdmin.query.filter(
            IntegrationAdmin.id == integration_id,
        ).one_or_none()
    
    @rpc('get_by_uid')
    def get_by_uid(self, integration_uid: int, project_id: Optional[int] = None) -> Optional[IntegrationProject]:
        """
        Get integration by unique id. You can specify current project_id but not necessary.
        :param integration_uid: uid of integration
        :param project_id: id of current project
        :return: integration ORM object or None
        """   
        if project_id is not None:
            with db.with_project_schema_session(project_id) as tenant_session:
                if integration := tenant_session.query(IntegrationProject).filter(
                    IntegrationProject.uid == integration_uid,
                ).one_or_none():
                    return integration
        if integration := IntegrationAdmin.query.filter(
            IntegrationAdmin.uid == integration_uid,
        ).one_or_none():
            return integration
        projects = self.context.rpc_manager.call.project_list()
        for project in projects:
            with db.with_project_schema_session(project['id']) as tenant_session:
                if integration := tenant_session.query(IntegrationProject).filter(
                    IntegrationProject.uid == integration_uid,
                ).one_or_none():
                    return integration

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
            mode = c.DEFAULT_MODE if integration_data['project_id'] else c.ADMINISTRATION_MODE
            secret_path = f"{field}_{mode}_{integration_data['id']}"
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
        cloud_integrations = self.process_default_integrations(project_id, integrations["clouds"])
        cloud_regions = [
            {
                "name": f"{region.name.split('_')[0]} {region.config.get('name')}"
                        f"{' - shared' if region.config.get('is_shared') else ''}"
                        f"{' - default' if region.is_default else ''}",
                "cloud_settings": {
                    "integration_name": region.name,
                    "id": region.id,
                    'project_id': region.project_id,
                    **region.settings
                }
            } for region in cloud_integrations]
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
    def get_administration_integrations_by_name(self, integration_name: str, 
                                                only_shared: bool = False
                                                ) -> List[IntegrationPD]:
        if integration_name not in self.integrations.keys():
            return []
        filters = [IntegrationAdmin.name == integration_name]
        if only_shared:
            filters.append(IntegrationAdmin.config['is_shared'].astext.cast(Boolean) == True)
        results = IntegrationAdmin.query.filter(
            *filters
        ).order_by(
            asc(IntegrationAdmin.section),
            desc(IntegrationAdmin.is_default),
            asc(IntegrationAdmin.name),
            desc(IntegrationAdmin.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('get_administration_integrations_by_section')
    def get_administration_integrations_by_section(self, section_name: str,
                                                   only_shared: bool = False
                                                   ) -> List[IntegrationPD]:
        if section_name not in self.sections.keys():
            return []
        filters = [IntegrationAdmin.section == section_name]
        if only_shared:
            filters.append(IntegrationAdmin.config['is_shared'].astext.cast(Boolean) == True)
        results = IntegrationAdmin.query.filter(
            *filters
        ).order_by(
            desc(IntegrationAdmin.is_default),
            asc(IntegrationAdmin.name),
            desc(IntegrationAdmin.id)
        ).all()
        results = parse_obj_as(List[IntegrationPD], results)
        return results

    @rpc('process_default_integrations')
    def process_default_integrations(self, project_id, integrations):
        default_integrations = self.get_defaults(project_id)

        def _is_default(default_integrations, integration):
            for default_integration in default_integrations:
                if (integration.project_id == default_integration.project_id and 
                    integration.name == default_integration.name and 
                    integration.id == default_integration.integration_id
                ):
                    return True
            return False                   

        for integration in integrations:
            integration.is_default = False
            if _is_default(default_integrations, integration):
                integration.is_default = True
        return sorted(integrations, key=lambda i: not i.is_default)

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
                # desc(IntegrationProject.is_default),
                asc(IntegrationProject.name),
                desc(IntegrationProject.id)
            ).all()
        results_admin = IntegrationAdmin.query.filter(
            IntegrationAdmin.name.in_(self.integrations.keys()),
            IntegrationAdmin.config['is_shared'].astext.cast(Boolean) == True
        ).group_by(
            IntegrationAdmin.section,
            IntegrationAdmin.id
        ).order_by(
            asc(IntegrationAdmin.section),
            desc(IntegrationAdmin.is_default),
            asc(IntegrationAdmin.name),
            desc(IntegrationAdmin.id)
        ).all()
        results_project = parse_obj_as(List[IntegrationPD], results_project)
        results_admin = parse_obj_as(List[IntegrationPD], results_admin)
        results = self.process_default_integrations(project_id, results_project + results_admin)
        if not group_by_section:
            return results

        def reducer(accum: dict, new_value: IntegrationPD) -> dict:
            accum[new_value.section.name].append(new_value)
            return accum
        return reduce(reducer, results, defaultdict(list))

    @rpc('get_all_integrations_by_name')
    def get_all_integrations_by_name(self, project_id: int, integration_name: str) -> List[IntegrationPD]:
        results_project = self.get_project_integrations_by_name(project_id, integration_name)
        results_admin = self.get_administration_integrations_by_name(integration_name, True)
        return self.process_default_integrations(project_id, results_project + results_admin)


    @rpc('get_all_integrations_by_section')
    def get_all_integrations_by_section(self, project_id: int, section_name: str) -> List[IntegrationPD]:
        results_project = self.get_project_integrations_by_section(project_id, section_name)
        results_admin = self.get_administration_integrations_by_section(section_name, True)
        return self.process_default_integrations(project_id, results_project + results_admin)

    @rpc('update_attrs')
    def update_attrs(self, 
            integration_id: int, 
            project_id: Optional[int], 
            update_dict: dict, 
            return_result: bool = False
        ) -> Optional[dict]:
        update_dict.pop('id', None)
        if project_id:
            with db.with_project_schema_session(project_id) as tenant_session:        
                log.info('update_attrs called %s', [integration_id, project_id, update_dict])
                tenant_session.query(IntegrationProject).filter(
                    IntegrationProject.id == integration_id
                ).update(update_dict)
                tenant_session.commit()
                if return_result:
                    return tenant_session.query(IntegrationProject).get(integration_id).to_json()
        else:
            IntegrationAdmin.query.filter(
                IntegrationAdmin.id == integration_id
            ).update(update_dict)
            IntegrationAdmin.commit()
            if return_result:
                return IntegrationAdmin.query.get(integration_id).to_json()

    @rpc('make_default_integration')
    def make_default_integration(self, integration, project_id):
        with db.with_project_schema_session(project_id) as tenant_session: 
            if default_integration := tenant_session.query(IntegrationDefault).filter(
                IntegrationDefault.name == integration.name,
                IntegrationDefault.is_default == True,
            ).one_or_none():
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
            if default_integration := tenant_session.query(IntegrationDefault).filter(
                IntegrationDefault.name == integration.name,
                IntegrationDefault.is_default == True,
                IntegrationDefault.integration_id == integration.id,
            ).one_or_none():
                tenant_session.delete(default_integration)
                tenant_session.commit()

    @rpc('get_defaults')
    def get_defaults(self, project_id, name=None):
        with db.with_project_schema_session(project_id) as tenant_session: 
            if name:
                if integration := tenant_session.query(IntegrationDefault).filter(
                    IntegrationDefault.name == name,
                ).one_or_none():
                    return IntegrationDefaultPD.from_orm(integration)
            else:
                results = tenant_session.query(IntegrationDefault).all()
                return parse_obj_as(List[IntegrationDefaultPD], results)

    @rpc('get_admin_defaults')
    def get_admin_defaults(self, name=None):
        if name:
            if integration := IntegrationAdmin.query.filter(
                IntegrationAdmin.is_default == True, 
                IntegrationAdmin.name == name,
            ).one_or_none():
                return IntegrationPD.from_orm(integration)
        else:
            results= IntegrationAdmin.query.filter(
                IntegrationAdmin.is_default == True, 
            ).all()
            return parse_obj_as(List[IntegrationPD], results)

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
    def get_s3_settings(self, project_id, integration_id=None, is_local=True):
        integration_name = 's3_integration'
        try:
            if integration_id and is_local:
                with db.with_project_schema_session(project_id) as tenant_session:
                    if integration_db := tenant_session.query(IntegrationProject).filter(
                        IntegrationProject.id == integration_id,
                        IntegrationProject.name == integration_name
                    ).one_or_none():
                        return _usecret_field(integration_db, project_id, is_local=True)
            elif integration_id:
                if integration_db := IntegrationAdmin.query.filter(
                    IntegrationAdmin.id == integration_id, 
                    IntegrationAdmin.name == integration_name,
                    IntegrationAdmin.config['is_shared'].astext.cast(Boolean) == True
                ).one_or_none():
                    return _usecret_field(integration_db, project_id, is_local=False)
            # in case if integration_id is not provided - try to find default integration:
            else: 
                with db.with_project_schema_session(project_id) as tenant_session:
                    default_integration = tenant_session.query(IntegrationDefault).filter(
                        IntegrationDefault.name == integration_name
                    ).one_or_none()
                    if default_integration and default_integration.project_id:
                        if integration_db := tenant_session.query(IntegrationProject).filter(
                            IntegrationProject.id == default_integration.integration_id,
                            IntegrationProject.name == integration_name
                        ).one_or_none():
                            return _usecret_field(integration_db, project_id, is_local=True)
                    elif default_integration:
                        if integration_db := IntegrationAdmin.query.filter(
                            IntegrationAdmin.id == default_integration.integration_id,
                            IntegrationAdmin.name == integration_name,
                            IntegrationAdmin.config['is_shared'].astext.cast(Boolean) == True
                        ).one_or_none():
                            return _usecret_field(integration_db, project_id, is_local=False)
        except Exception as e:
            log.warning(f'Cannot receive S3 settings for project {project_id}')
            log.debug(e)

    @rpc('get_s3_admin_settings')
    def get_s3_admin_settings(self, integration_id=None):
        integration_name = 's3_integration'
        try:
            if integration_id:
                if integration_db := IntegrationAdmin.query.filter(
                    IntegrationAdmin.id == integration_id, 
                    IntegrationAdmin.name == integration_name,
                ).one_or_none():
                    return _usecret_field(integration_db, None, is_local=False)
            # in case if integration_id is not provided - try to find default integration:
            else: 
                if integration_db := IntegrationAdmin.query.filter(
                    IntegrationAdmin.name == integration_name,
                    IntegrationAdmin.is_default == True,
                ).one_or_none():
                    return _usecret_field(integration_db, None, is_local=False)
        except Exception as e:
            log.warning(f'Cannot receive S3 settings in administration mode')
            log.debug(e)

    # @rpc('create_default_s3_for_new_project')
    # def create_default_s3_for_new_project(self, project_id):
    #     if integration_db := IntegrationAdmin.query.filter(
    #         IntegrationAdmin.name == 's3_integration',
    #         IntegrationAdmin.config['is_shared'].astext.cast(Boolean) == True,
    #         IntegrationAdmin.is_default == True,
    #     ).one_or_none():
    #         with db.with_project_schema_session(project_id) as tenant_session:
    #             default_integration = IntegrationDefault(name=integration_db.name,
    #                                                     project_id=None,
    #                                                     integration_id = integration_db.id,
    #                                                     is_default=True,
    #                                                     section=integration_db.section
    #                                                     )
    #             tenant_session.add(default_integration)
    #             tenant_session.commit()
