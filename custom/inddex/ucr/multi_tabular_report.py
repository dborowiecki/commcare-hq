from memoized import memoized

from corehq.apps.reports.generic import GenericTabularReport
from corehq.apps.reports.standard import CustomProjectReport


class MultiTabularReport(CustomProjectReport, GenericTabularReport):
    title = ''
    report_template_path = "inddex/multi_report.html"
    flush_layout = True
    export_format_override = 'csv'

    @property
    @memoized
    def rendered_report_title(self):
        return self.title

    @property
    @memoized
    def data_providers(self):
        return []

    @property
    def report_context(self):
        context = {
            'reports': [self.get_report_context(dp) for dp in self.data_providers],
            'title': self.title
        }

        return context

    def get_report_context(self, data_provider):
        total_row = []
        self.data_source = data_provider
        if self.needs_filters:
            headers = []
            rows = []
        else:
            rows = data_provider.rows
            headers = data_provider.headers
            total_row = data_provider.total_row

        context = dict(
            report_table=dict(
                title=data_provider.title,
                slug=data_provider.slug,
                headers=headers,
                rows=rows,
            #    total_row=total_row,
            #    default_rows=self.default_rows,
            #    datatables=True,
            #    fix_column=False
            )
        )

        return context

    @property
    def report_config(self):
        return {
            'domain': self.domain,
            'startdate': self.startdate,
            'enddate': self.enddate,
            'user_id': self.request.GET.get('user_id', ''),
            'country': self.request.GET.get('country', ''),
            'level_1': self.request.GET.get('level_1', ''),
            'level_4': self.request.GET.get('level_4', ''),
            'submission_status': self.request.GET.get('submission_status', '')
        }

    @property
    def startdate(self):
        return self.request.datespan.startdate

    @property
    def enddate(self):
        return self.request.datespan.end_of_end_day
