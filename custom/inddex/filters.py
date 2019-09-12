from django.utils.translation import ugettext_noop

from corehq.apps.reports.filters.base import BaseSingleOptionFilter, BaseReportFilter, BaseDrilldownOptionFilter


class AgeFilter(BaseDrilldownOptionFilter):
    slug = 'age'
    label = 'Age'

    @classmethod
    def get_labels(cls):
        return [
            ('From', 'Age...', 'from'),
            ('To', 'Age...', 'to'),
        ]

    @property
    def drilldown_map(self):
        return [{
            'val': 0,
            'text': '0',
            'next': [{
                'val': 100,
                'text': "100",
            }]
        }
        ]


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

