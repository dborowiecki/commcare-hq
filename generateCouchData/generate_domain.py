from __future__ import absolute_import
from __future__ import unicode_literals

import corehq.apps.domain.models as model
from django.utils.crypto import get_random_string

class DeploymentGenerator:
    @classmethod
    def create_deployment(cls, city, countries, region='Worldwide', description='Dummy description', public=True):
        deployment = model.Deployment()
        deployment.city = city
        deployment.countries = countries
        deployment.region = region
        deployment.description = description
        deployment.public = public

        return deployment

class ReportConfigGenerator:
    @classmethod
    def create_report_config(cls, report, name, previewers_only, **kwargs):
        new_set = model.DynamicReportConfig()
        new_set.report = report  # fully-qualified path to template report class
        new_set.name = name  # report display name in sidebar
        new_set.kwargs = kwargs # arbitrary settings to configure report
        new_set.previewers_only = previewers_only
        return new_set

class ReportSetGenerator:
    @classmethod
    def create_report_set(cls, section_title, report_config=None):
        new_set = model.DynamicReportSet()
        new_set.section_title = section_title
        new_set.reports = report_config or new_set.reports
        return new_set


SUB = [u'Maternal, Newborn, & Child Health', u'Family Planning', u'HIV/AIDS', u'Emergency Response']
AREA = ['Other', 'Health']
PROJECT_STATES = ["", "POC", "transition", "at-scale"]
BUSINESS_UNITS = ["", "DSA", "DSI", "DWA", "INC"]
COMMCARE_EDITIONS = ['', "plus", "community", "standard", "pro", "advanced", "enterprise"]


class DomainGenerator:
    @classmethod
    def create_domain(cls, name, is_active=False, secure_submissions=True, use_sql_backend=False):
        new_domain = model.Domain().get_or_create_with_name(name, is_active, secure_submissions, use_sql_backend)
        return new_domain

    @classmethod
    def active_for_user(cls, domain, user):
        domain.active_for_user(user)

    @classmethod
    def add_deployment(cls, domain, deployment):
        domain.deployment = deployment
        domain.save()

    @classmethod
    def add_organization(cls, domain, org_name):
        domain.update_internal(organization_name=org_name)

    @classmethod
    def set_areas(cls, domain, area='Other', subarea=None):
        if area not in ['Health', 'Other'] or subarea not in SUB:
            raise ValueError('Area should be health or other')

        domain.update_internal(sub_area=subarea,area=area)
        #domain.save()

    @classmethod
    def change_edition(cls, domain, edition):
        domain.update_internal(commcare_edition=edition)

    @classmethod
    def change_business_unit(cls, domain, business_unit=''):
        if business_unit not in BUSINESS_UNITS:
            raise ValueError('Units not supported')
        domain.update_internal(business_unit=business_unit)

    @classmethod
    def change_project_state(cls, domain, state=''):
        if state not in PROJECT_STATES:
            raise ValueError("State not supported")

        domain.update_internal(project_state=state)
