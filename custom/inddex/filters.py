from django.utils.translation import ugettext_noop

from corehq.apps.reports.filters.base import BaseSingleOptionFilter, BaseReportFilter, BaseDrilldownOptionFilter


class AgeFilter(BaseSingleOptionFilter):
    slug = 'age'
    label = 'Age'
    template = 'inddex/filters/age_filter.html'
    default_text = ugettext_noop("All")

    @property
    def options(self):
        return [(str(k), str(k))for k in range(0, 5)]


class SexFilter(BaseSingleOptionFilter):
    slug = 'sex'
    label = "Sex"
    default_text = ugettext_noop("All")

    @property
    def options(self):
        return [("Male", "Male"),
                ("Female", "Female")]


class SettlementAreaFilter(BaseSingleOptionFilter):
    slug = 'settlement'
    label = 'Settlement'
    default_text = ugettext_noop("All")

    @property
    def options(self):
        return [("Urban", "Urban"),
                ("Rural", "Rural")]


class PregnancyLactationStatus(BaseSingleOptionFilter):
    slug = 'pregnancy_lactation_status'
    label = 'Status'
    default_text = ugettext_noop("All")

    @property
    def options(self):
        return [("Pregnant", "Pregnant"),
                ("Lactating", "Lactating")]

