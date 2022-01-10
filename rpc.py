from queue import Empty
from typing import List, Union
from pydantic import parse_obj_as, ValidationError
from functools import reduce
from collections import defaultdict
from sqlalchemy import desc, asc

from .models.integration import Integration
from .models.integration_pd import IntegrationPD
from .models.registration_pd import RegistrationForm, SectionRegistrationForm

from ..shared.utils.rpc import RpcMixin


def register(reg_dict: dict, slot_manager, **kwargs) -> RegistrationForm:
    form_data = RegistrationForm(**kwargs)
    reg_dict[form_data.name] = form_data
    slot_manager.register_callback(
        f'integrations_{form_data.section}',
        form_data.integration_callback
    )
    return form_data


def get_project_integrations(project_id: int, *, registered_integrations: Union[set, tuple, list]) -> dict:
    results = Integration.query.filter(
        Integration.project_id == project_id,
        Integration.name.in_(registered_integrations)
    ).group_by(
        Integration.section,
        Integration.id
    ).order_by(
        asc(Integration.section),
        desc(Integration.is_default),
        desc(Integration.id)
    ).all()

    results = parse_obj_as(List[IntegrationPD], results)

    def reducer(cumulative: dict, new_value: IntegrationPD) -> dict:
        cumulative[new_value.section.name].append(new_value)
        return cumulative

    return reduce(reducer, results, defaultdict(list))


def get_project_integrations_by_name(project_id, integration_name, *, registered_integrations: Union[set, tuple, list]) -> list:
    if integration_name not in registered_integrations:
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


def register_section(reg_dict_section: dict, *, force_overwrite: bool = False, **kwargs) -> SectionRegistrationForm:
    form_data = SectionRegistrationForm(**kwargs)
    if form_data.name not in reg_dict_section or force_overwrite:
        reg_dict_section[form_data.name] = form_data
    return form_data


def get_by_id(integration_id: int) -> Integration:
    return Integration.query.filter(
        Integration.id == integration_id,
    ).one_or_none()


def security_test_create(data: dict, skip_validation_if_undefined: bool = True, **kwargs) -> dict:
    integration_data = dict()
    from pylon.core.tools import log
    rpc = RpcMixin().rpc
    # log.warning(data)
    for section, integration in data.items():
        integration_data[section] = dict()
        for k, v in integration.items():
            # log.warning('k')
            # log.warning(k)
            # log.warning('v')
            # log.warning(v)
            try:
                integration_data[section][k] = rpc.call_function_with_timeout(
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
                    # log.warning('OOO')
                    # log.warning(type(i))
                    # log.warning(i)
                    i['loc'] = [f'{section}_{k}', *i['loc']]
                # log.warning('OOO')
                # log.warning(e.errors())
                raise e
            except Exception as e:
                # log.warning('WWW')
                # log.warning(type(e))
                # log.warning(e)
                e.loc = [f'{section}_{k}', *getattr(e, 'loc', [])]
                raise e

    return {'integrations': integration_data}
