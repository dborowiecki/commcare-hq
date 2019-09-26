from corehq.warehouse.const import (
    DOMAIN_DIM_SLUG,
    FORM_FACT_SLUG,
    FORM_STAGING_SLUG,
    USER_DIM_SLUG,
)
from corehq.warehouse.dbaccessors import get_forms_by_last_modified
from corehq.warehouse.etl import CustomSQLETLMixin, HQToWarehouseETLMixin
from corehq.warehouse.loaders.base import BaseLoader, BaseStagingLoader
from corehq.warehouse.models import FormFact, FormStagingTable


class FormStagingLoader(HQToWarehouseETLMixin, BaseStagingLoader):
    """
    Represents the staging table to dump data before loading into the FormFact

    Grain: form_id
    """
    slug = FORM_STAGING_SLUG
    model_cls = FormStagingTable
    log_frequency = 100000

    def field_mapping(self):
        return [
            ('form_id', 'form_id'),
            ('domain', 'domain'),
            ('app_id', 'app_id'),
            ('xmlns', 'xmlns'),
            ('user_id', 'user_id'),

            ('received_on', 'received_on'),
            ('deleted_on', 'deleted_on'),
            ('edited_on', 'edited_on'),
            ('build_id', 'build_id'),

            ('time_end', 'time_end'),
            ('time_start', 'time_start'),
            ('commcare_version', 'commcare_version'),
            ('app_version', 'app_version'),
        ]

    def record_iter(self, start_datetime, end_datetime):
        return get_forms_by_last_modified(start_datetime, end_datetime)


class FormFactLoader(CustomSQLETLMixin, BaseLoader):
    """
    Contains all `XFormInstance`s

    Grain: form_id
    """
    # TODO: Write Update SQL Query
    slug = FORM_FACT_SLUG
    model_cls = FormFact

    def dependant_slugs(self):
        return [
            USER_DIM_SLUG,
            DOMAIN_DIM_SLUG,
            FORM_STAGING_SLUG,
        ]
