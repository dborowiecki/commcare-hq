from corehq.warehouse.const import (
    APP_STATUS_FACT_SLUG,
    APP_STATUS_FORM_STAGING_SLUG,
    APP_STATUS_SYNCLOG_STAGING_SLUG,
    APPLICATION_DIM_SLUG,
    DOMAIN_DIM_SLUG,
    FORM_STAGING_SLUG,
    SYNCLOG_STAGING_SLUG,
    USER_DIM_SLUG,
)
from corehq.warehouse.etl import CustomSQLETLMixin, slug_to_table_map
from corehq.warehouse.loaders.base import BaseLoader, BaseStagingLoader
from corehq.warehouse.models import (
    ApplicationStatusFact,
    AppStatusFormStaging,
    AppStatusSynclogStaging,
)


class AppStatusFormStagingLoader(CustomSQLETLMixin, BaseStagingLoader):
    slug = APP_STATUS_FORM_STAGING_SLUG
    model_cls = AppStatusFormStaging

    def dependant_slugs(self):
        return [
            APPLICATION_DIM_SLUG,
            USER_DIM_SLUG,
            DOMAIN_DIM_SLUG,
            FORM_STAGING_SLUG,
        ]

    def additional_sql_context(self):
        return slug_to_table_map([APP_STATUS_FACT_SLUG])


class AppStatusSynclogStagingLoader(CustomSQLETLMixin, BaseStagingLoader):
    slug = APP_STATUS_SYNCLOG_STAGING_SLUG
    model_cls = AppStatusSynclogStaging

    def dependant_slugs(self):
        return [
            APPLICATION_DIM_SLUG,
            USER_DIM_SLUG,
            DOMAIN_DIM_SLUG,
            SYNCLOG_STAGING_SLUG,
        ]

    def additional_sql_context(self):
        return slug_to_table_map([APP_STATUS_FACT_SLUG])


class ApplicationStatusFactLoader(CustomSQLETLMixin, BaseLoader):
    """
    Application Status Report Fact Table

    Grain: app_id, user_id
    """
    slug = APP_STATUS_FACT_SLUG
    model_cls = ApplicationStatusFact

    def dependant_slugs(self):
        return [
            APP_STATUS_SYNCLOG_STAGING_SLUG,
            APP_STATUS_FORM_STAGING_SLUG
        ]
