from memoized import memoized

from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from corehq.apps.reports.generic import GenericTabularReport
from corehq.apps.reports.sqlreport import SqlData
from corehq.apps.reports.standard import CustomProjectReport
from custom.inddex.ucr.multi_tabular_report import MultiTabularReport
from custom.inddex.ucr.summary_statistics_report import SummaryStatisticsReport


class SummaryStatsNutrientDataProvider(SqlData):
    total_row = None
    title = 'Summary stats per nutrient for total sample'
    slug = 'summary_statistics_report_nutrient'

    headers = DataTablesHeader(
                DataTablesColumn('Nutrient'),
                DataTablesColumn('Mean'),
                DataTablesColumn('Median'),
                DataTablesColumn('Std.Dev'),
                DataTablesColumn('5_percent'),
                DataTablesColumn('25_percent'),
                DataTablesColumn('50_percent'),
                DataTablesColumn('75_percent'),
                DataTablesColumn('95_percent')
            )

    @property
    def rows(self):
        # TODO: calculate methods
        return [['n', 'm', 'm', 'std', 5, 25, 50, 75,95]]


class SummaryStatsRespondentDataProvider(SqlData):
    total_row = None
    title = 'Summary stats per nutrient per respondent'
    slug = 'summary_statistics_report_respondent'

    headers = DataTablesHeader(
                DataTablesColumn('Respondent'),
                DataTablesColumn('# of Recalls'),
                DataTablesColumn('Nutrient'),
                DataTablesColumn('Mean'),
                DataTablesColumn('Median'),
                DataTablesColumn('Std.Dev'),
                DataTablesColumn('5_percent'),
                DataTablesColumn('25_percent'),
                DataTablesColumn('50_percent'),
                DataTablesColumn('75_percent'),
                DataTablesColumn('95_percent')
            )

    @property
    def rows(self):
        # TODO: calculate methods
        return [['resp a', 2, 'n', 'm', 'm', 'std', 5, 25, 50, 75, 95]]


class SummaryStatisticsReport(SummaryStatisticsReport):
    default_rows = 10
    exportable = True

    @property
    @memoized
    def data_providers(self):
        config = self.report_config
        print("REQUEST WYGLĄDA TAK {}".format(self.request.GET))
        print("MÓJ SUPER CONFIG LOOKS TAK {}".format(config))
        return [
            SummaryStatsNutrientDataProvider(config=config),
            SummaryStatsRespondentDataProvider(config=config)
        ]
