# coding=utf-8

import datetime

from django.utils.functional import cached_property

from custom.intrahealth.filters import DateRangeFilter, RecapPassageTwoProgramFilter, \
    YeksiRecapPassageNaaLocationFilter
from custom.intrahealth.reports.utils import YeksiNaaMonthYearMixin
from custom.intrahealth.sqldata import RecapPassageTwoTables
from custom.intrahealth.reports.tableu_de_board_report_v2 import MultiReport
from dimagi.utils.dates import force_to_date


class RecapPassageTwoReport(YeksiNaaMonthYearMixin, MultiReport):
    slug = 'recap_passage_2'
    comment = 'recap passage 2'
    name = 'Recap Passage 2'
    title = "Recap Passage 2"
    default_rows = 10
    exportable = True

    report_template_path = "intrahealth/multi_report.html"

    @property
    def export_table(self):
        report = [
            [
                'Recap Passage 2',
                [],
            ]
        ]

        table_provider = RecapPassageTwoTables(config=self.config)
        data = [
            table_provider.sumup_context,
            table_provider.billed_consumption_context,
            table_provider.actual_consumption_context,
            table_provider.amt_delivered_convenience_context,
            table_provider.display_total_stock_context,
        ]

        headers = []
        for d in data:
            to_add = []
            for header in d['headers']:
                try:
                    to_add.append(header.html)
                except AttributeError:
                    to_add.append(header)
            headers.append(to_add)

        rows = []
        for d in data:
            to_add = []
            for row in d['rows']:
                try:
                    to_add.append(row.html)
                except AttributeError:
                    to_add.append(row)
            rows.append(to_add)

        length = len(headers)
        for r in range(0, length):
            header = headers[r]
            row = rows[r]
            report[0][1].append(header)
            for one_row in row:
                if one_row is not None:
                    report[0][1].append(one_row)

            if r != length - 1:
                report[0][1].append([])

        return report

    @property
    def fields(self):
        return [DateRangeFilter, RecapPassageTwoProgramFilter, YeksiRecapPassageNaaLocationFilter]

    @cached_property
    def rendered_report_title(self):
        return self.name

    @cached_property
    def data_providers(self):
        table_provider = RecapPassageTwoTables(config=self.config)
        return [
            table_provider.sumup_context,
            table_provider.billed_consumption_context,
            table_provider.actual_consumption_context,
            table_provider.amt_delivered_convenience_context,
            table_provider.display_total_stock_context,
        ]

    def get_report_context(self, table_context):
        self.data_source = table_context
        if self.needs_filters:
            context = dict(
                report_table=dict(
                    rows=[],
                    headers=[]
                )
            )
        else:
            context = dict(
                report_table=table_context
            )
        return context

    @property
    def config(self):
        config = dict(
            domain=self.domain,
        )
        if self.request.GET.get('startdate'):
            startdate = force_to_date(self.request.GET.get('startdate'))
        else:
            startdate = datetime.datetime.now()
        if self.request.GET.get('enddate'):
            enddate = force_to_date(self.request.GET.get('enddate'))
        else:
            enddate = datetime.datetime.now()
        config['startdate'] = startdate
        config['enddate'] = enddate
        config['product_program'] = self.request.GET.get('program')
        config['selected_location'] = self.request.GET.get('location_id')
        return config
