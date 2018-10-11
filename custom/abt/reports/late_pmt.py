from __future__ import absolute_import
from __future__ import unicode_literals

from sqlalchemy.sql.functions import count

from corehq.apps.reports.datatables import DataTablesHeader, DataTablesColumn
from corehq.apps.reports.generic import GenericTabularReport
from corehq.apps.reports.standard import CustomProjectReport
from django.utils.translation import ugettext as _

from corehq.apps.sms.models import SMSBase, INCOMING, MessagingSubEvent, MessagingEvent


class LatePmtReport(CustomProjectReport, GenericTabularReport):
    report_title = "Late PMT"
    exportable = False
    emailable = False

    @property
    def headers(self):
        return DataTablesHeader(
            DataTablesColumn(_("Username")),
            DataTablesColumn(_("Phone Number")),
            DataTablesColumn(_("No PMT?")),
            DataTablesColumn(_("Modify PMT?")),
            DataTablesColumn(_("Country")),
            DataTablesColumn(_("Level 1")),
            DataTablesColumn(_("Level 2")),
            DataTablesColumn(_("Level 3")),
            DataTablesColumn(_("Level 4")),
        )


    @property
    def rows(self):
        users = self.get_all_users_by_domain
        users_pmt_group_A = SMSBase.objects.filter(
            domain=self.domain,
            couch_recipient_doc_type='CommCareUser',
            direction=INCOMING
        ).values('couch_recipient').annotate(
            number_of_sms=count('couch_recipient')
        )
        users_pmt_group_C = MessagingSubEvent.objects.filter(
            parent__domain=self.domain,
            parent__recipient_type=MessagingEvent.RECIPIENT_MOBILE_WORKER,
            parent__source=MessagingEvent.SOURCE_KEYWORD,
            xforms_session__isnull=False,
            xforms_session__submission_id__isnull=False
        ).values('recipient_id')
        return []
