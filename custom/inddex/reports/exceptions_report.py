from memoized import memoized

from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from custom.inddex.ucr.report_bases.multi_tabular_report import MultiTabularReport


class MockDataProvider():
    rows = [['a', 'a'], ['b','b'], ['c','c']]
    headers = DataTablesHeader(
                DataTablesColumn('Header1'),
                DataTablesColumn('Header2'),
            )
    total_row = None
    title = 'Mock title'
    slug = 'Mocked slug'


class ExceptionReport(MultiTabularReport):
    title = "Exception Report"
    fields = [
        #Filters go here
    ]
    name = "Exception Reports"
    slug = 'exception_report'
    default_rows = 10
    exportable = True

    @property
    @memoized
    def data_providers(self):
        config = self.report_config
        return [MockDataProvider(), MockDataProvider()]
