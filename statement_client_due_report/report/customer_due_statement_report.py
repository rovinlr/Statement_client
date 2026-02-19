from odoo import fields, models


class ReportCustomerDueStatement(models.AbstractModel):
    _name = "report.statement_client_due_report.customer_due_statement_document"
    _description = "Customer Due Statement Report"

    def _get_report_values(self, docids, data=None):
        docs = self.env["customer.due.statement.wizard"].browse(docids)
        return {
            "doc_ids": docs.ids,
            "doc_model": "customer.due.statement.wizard",
            "docs": docs,
            "grouped_data": docs._get_grouped_lines(),
            "today": fields.Date.context_today(self),
        }
