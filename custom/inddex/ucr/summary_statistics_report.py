from corehq.apps.reports.filters.dates import DatespanFilter
from corehq.apps.reports.filters.fixtures import AsyncLocationFilter
from custom.inddex.filters import AgeFilter, SexFilter, SettlementAreaFilter, PregnancyLactationStatus
from custom.inddex.ucr.multi_tabular_report import MultiTabularReport


class SummaryStatisticsReport(MultiTabularReport):
    title = "Summary Statistics Report"
    name = "Summary Statistics Reports"
    slug = 'summary_statistics_report'

    @property
    def fields(self):
        filters = [
            DatespanFilter,
            AsyncLocationFilter,
            AgeFilter,
            SexFilter,
            SettlementAreaFilter,
            PregnancyLactationStatus
        ]

        return filters

    @property
    def report_config(self):
        return {
            'domain': self.domain,
            'startdate': self.startdate,
            'enddate': self.enddate,
            'selected_location': self.selected_location,
            'age_range': self.age_range,
            'sex': self.sex,
            'settlement': self.settlement,
            'pregnancy_lactation_status': self.status,
        }

    @property
    def age_range(self):
        age_from = self.request.GET.get('age_from') or 0
        age_to = self.request.GET.get('age_to') or 100
        return age_from, age_to

    @property
    def sex(self):
        return self.request.GET.get('sex') or ''

    @property
    def settlement(self):
        return self.request.GET.get('settlement') or ''

    @property
    def status(self):
        return self.request.GET.get('pregnancy_lactation_status') or ''
