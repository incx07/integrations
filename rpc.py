from typing import List, Union

from sqlalchemy import desc, asc

from .models.integration import Integration
from .models.integration_pd import IntegrationPD
from .models.registration_pd import RegistrationForm, SectionRegistrationForm

from pydantic import parse_obj_as
from functools import reduce
from collections import defaultdict


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
