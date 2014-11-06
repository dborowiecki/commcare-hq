from custom.ilsgateway.api import StockTransaction
from custom.ilsgateway.ghana.reminders import PRODUCTS_NOT_SUBMITTED
from custom.ilsgateway.tanzania.handlers.keyword import KeywordHandler


class UndoHandler(KeywordHandler):
    def help(self):
        return self.handle()

    def handle(self):
        # get the last product report (for  single product)
        all_prs = StockTransaction.objects.filter(message__contact=\
                                               self.msg.logistics_contact)\
                                       .order_by("-report_date")
        if not all_prs:
            return self.respond(PRODUCTS_NOT_SUBMITTED)
        last_productreport_message = all_prs[0].message
        sp = all_prs[0].supply_point
        # get all the product reports associated with the last product report message
        prs = StockTransaction.objects.filter(message=last_productreport_message)\
                                   .order_by('-report_date')
        sts = StockTransaction.objects.filter(product_report__in=prs)
        # 1. undo the stock information at the given facility """
        for st in sts:
            product_stock = StockTransaction.objects.get(supply_point=sp,
                                                     product=st.product)
            product_stock.quantity = st.beginning_balance
            product_stock.save()
            # 2 delete the stock transaction
            st.delete()
        # 3 delete the product report
        for pr in prs:
            pr.delete()
        # 4 update auto consumption values
        product_stocks = StockTransaction.objects.filter(supply_point=sp)
        for ps in product_stocks:
            ps.update_auto_consumption()
        return self.respond(
            "Success. Your previous report has been removed. It was: %(report)s",
            report=last_productreport_message.text)
