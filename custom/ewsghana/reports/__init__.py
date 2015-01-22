from django.core.urlresolvers import reverse
from sqlagg.filters import EQ
from corehq.apps.reports.commtrack.standard import CommtrackReportMixin
from corehq.apps.reports.sqlreport import SqlData, DataFormatter, TableDataFormat
from corehq.apps.reports.standard import CustomProjectReport, ProjectReportParametersMixin, DatespanMixin
from dimagi.utils.decorators.memoized import memoized
from corehq.apps.locations.models import Location

REORDER_LEVEL = 1.5
MAXIMUM_LEVEL = 3


def get_url(view_name, text, domain):
    return '<a href="%s">%s</a>' % (reverse(view_name, args=[domain]), text)


class EWSData(object):
    show_table = False
    show_chart = False
    title = ''
    slug = ''
    use_datatables = False

    def __init__(self, config=None):
        self.config = config or {}
        super(EWSData, self).__init__()

    def percent_fn(self, x, y):
        return "%(p).2f%%" % \
            {
                "p": (100 * float(y or 0) / float(x or 1))
            }

    @property
    def headers(self):
        return []

    @property
    def rows(self):
        raise NotImplementedError

    @property
    def sublocations(self):
        location = Location.get(self.config['location_id'])
        if location.children:
            return location.children
        else:
            return [location]


class EWSSqlData(SqlData):
    show_table = True
    show_total = False
    use_datatables = False
    show_chart = False
    no_value = {'sort_key': 0, 'html': 0}
    title = ''
    slug = ''

    @property
    def filters(self):
        return [EQ('location_id', 'location_id'), EQ('domain', 'domain')]

    @property
    def group_by(self):
        return []

    @property
    def columns(self):
        return []

    @property
    def headers(self):
        return []

    @property
    def rows(self):
        formatter = DataFormatter(TableDataFormat(self.columns, no_value=self.no_value))
        return list(formatter.format(self.data, keys=self.keys, group_by=self.group_by))


class MultiReport(CustomProjectReport, CommtrackReportMixin, ProjectReportParametersMixin, DatespanMixin):
    title = ''
    report_template_path = "ewsghana/multi_report.html"
    flush_layout = True
    split = True

    @property
    @memoized
    def rendered_report_title(self):
        return self.title

    @property
    @memoized
    def data_providers(self):
        return []

    @property
    def report_config(self):
        return dict(
            domain=self.domain,
            startdate=self.datespan.startdate,
            enddate=self.datespan.enddate,
            location_id=self.request.GET.get('location_id'),
        )

    @property
    def report_context(self):
        context = {
            'reports': [self.get_report_context(dp) for dp in self.data_providers],
            'title': self.title,
            'split': self.split,
        }
        return context

    def get_report_context(self, data_provider):
        total_row = []
        headers = []
        rows = []

        if not self.needs_filters and data_provider.show_table:
            headers = data_provider.headers
            rows = data_provider.rows

        context = dict(
            report_table=dict(
                title=data_provider.title,
                slug=data_provider.slug,
                headers=headers,
                rows=rows,
                total_row=total_row,
                start_at_row=0,
                use_datatables=data_provider.use_datatables,
            ),
            show_table=data_provider.show_table,
            show_chart=data_provider.show_chart,
            charts=data_provider.charts if data_provider.show_chart else [],
            chart_span=12,
        )

        return context
