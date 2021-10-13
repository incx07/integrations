from typing import List, Union

from sqlalchemy import desc

from .models.integration import Integration
from .models.integration_pd import IntegrationPD
from .models.registration_pd import RegistrationForm

from pydantic import parse_obj_as
from functools import reduce
from collections import defaultdict


def register(reg_dict: dict, slot_manager, **kwargs) -> None:
    form_data = RegistrationForm(**kwargs)
    reg_dict[form_data.name] = form_data
    slot_manager.register_callback(
        f'integrations_{form_data.section}',
        form_data.integration_callback
    )


def get_integration(reg_dict: dict, integration_name: str) -> RegistrationForm:
    return reg_dict.get(integration_name)


def get_project_integrations(project_id: int, *, registered_integrations: Union[set, tuple, list]) -> dict:
    results = Integration.query.filter(
        Integration.project_id == project_id,
        Integration.name.in_(registered_integrations)
    ).group_by(
        Integration.section,
        Integration.id
    ).order_by(
        desc(Integration.is_default),
        desc(Integration.id)
    ).all()

    results = parse_obj_as(List[IntegrationPD], results)

    def reducer(cumulative: dict, new_value: IntegrationPD) -> dict:
        cumulative[new_value.section].append(new_value)
        return cumulative

    return reduce(reducer, results, defaultdict(list))


def get_project_integrations_by_name(project_id, integration_name, *, registered_integrations: Union[set, tuple, list]) -> list:
    if integration_name not in registered_integrations:
        return []
    results = Integration.query.filter(
        Integration.project_id == project_id,
        Integration.name == integration_name
    ).order_by(
        desc(Integration.is_default),
        desc(Integration.id)
    ).all()
    results = parse_obj_as(List[IntegrationPD], results)
    return results
