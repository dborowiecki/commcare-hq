from custom.ilsgateway.ghana.reminders import REGISTER_MESSAGE, NO_SUPPLY_POINT_MESSAGE, REQ_SUBMITTED, \
    REQ_NOT_SUBMITTED
from custom.ilsgateway.models import RequisitionReport
from custom.ilsgateway.tanzania.handlers.keyword import KeywordHandler


class RequisitionHandler(KeywordHandler):
    keyword = "yes|no|y|n"

    def help(self):
        return self.handle()

    def handle(self):
        #text = text.strip().lower()
        text = self.args[0].strip().lower()
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(REGISTER_MESSAGE)
            return
        if self.msg.logistics_contact.supply_point is None:
            self.respond(NO_SUPPLY_POINT_MESSAGE)
            return
        supply_point = self.msg.logistics_contact.supply_point
        if text[0] == 'y':
            submitted = True
            response = REQ_SUBMITTED
        else:
            submitted = False
            response = REQ_NOT_SUBMITTED

        r = RequisitionReport(supply_point=supply_point, submitted=submitted)
        r.save()

        self.respond(response)