from custom.abt.reports.late_pmt import LatePmtReport
from custom.inddex.reports.exceptions_report import ExceptionReport
from custom.inddex.reports.summary_statistics_report import SummaryStatisticsReport

CUSTOM_REPORTS = (
    ('CUSTOM REPORTS', (
        ExceptionReport,
        SummaryStatisticsReport,
    )),
)
