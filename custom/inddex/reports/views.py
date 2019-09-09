from memoized import memoized

from corehq.apps.reports.datatables import DataTablesHeader, DataTablesColumn
from corehq.apps.userreports.reports.util import ReportExport
from corehq.apps.userreports.reports.view import CustomConfigurableReport


class MultiSheetReportExport(ReportExport):

    def __init__(self, title, table_data):
        '''

        :param title: Exported file title
        :param table_data: list of tuples, first element of tuple is sheet title, second is list of rows
        '''
        self.title = title
        self.table_data = table_data

    def build_export_data(self):
        sheets = []
        for name, rows in self.table_data:
            sheets.append([name, rows])
        return sheets

    @memoized
    def get_table(self):
        return self.build_export_data()


class ProcessDataReport(CustomConfigurableReport):
    # template_name = 'reports/base_template.html' # TODO: Need template that prevents showing tables

    @property
    def table_data(self):
        #TODO: instead of mock data retun proper calculations
        return [("Raport 1", [['head 1', 'head2'], ['row1','row11']]),
                ("Raport 2",  [['head 2', 'head2'], ['row2','row22']]),
                ("Raport 3", ['a'])]

    @property
    @memoized
    def report_export(self):
        return MultiSheetReportExport('Crazy title', self.table_data)

