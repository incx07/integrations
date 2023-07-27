from sqlalchemy import Boolean

from ..models.integration import IntegrationAdmin, IntegrationDefault
from ..models.pd.integration import SecretField

from tools import rpc_tools, VaultClient, db

from pylon.core.tools import web, log


def _usecret_field(integration_db, project_id):
    settings = integration_db.settings
    secret_access_key = SecretField.parse_obj(settings['secret_access_key'])
    settings['secret_access_key'] = secret_access_key.unsecret(project_id=project_id)
    return settings


class Event:
    @web.event('project_created')
    def create_default_s3_for_new_project(self, context, event, project: dict, **kwargs) -> None:
        log.info('Creating default integration for project %s', project)
        project_id = project['id']
        if integration_db := IntegrationAdmin.query.filter(
                IntegrationAdmin.name == 's3_integration',
                IntegrationAdmin.config['is_shared'].astext.cast(Boolean) == True,
                IntegrationAdmin.is_default == True,
        ).one_or_none():
            with db.with_project_schema_session(project_id) as tenant_session:
                default_integration = IntegrationDefault(
                    name=integration_db.name,
                    project_id=None,
                    integration_id=integration_db.id,
                    is_default=True,
                    section=integration_db.section
                )
                tenant_session.add(default_integration)
                tenant_session.commit()
