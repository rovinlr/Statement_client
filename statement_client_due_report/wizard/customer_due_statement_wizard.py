from collections import defaultdict

from odoo import _, api, fields, models


class CustomerDueStatementWizard(models.TransientModel):
    _name = "customer.due.statement.wizard"
    _description = "Customer Due Statement Wizard"

    partner_id = fields.Many2one("res.partner", required=True, string="Cliente")
    date_from = fields.Date(string="Fecha inicial")
    date_to = fields.Date(string="Fecha final")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref("statement_client_due_report.action_report_customer_due_statement").report_action(self)

    @api.model
    def _is_credit_note(self, move):
        return move.move_type == "out_refund"

    def _build_domain(self):
        self.ensure_one()
        domain = [
            ("state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
            ("partner_id", "child_of", self.partner_id.commercial_partner_id.id),
            ("move_type", "in", ["out_invoice", "out_refund"]),
            ("amount_residual", "!=", 0),
        ]
        if self.date_from:
            domain.append(("invoice_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("invoice_date", "<=", self.date_to))
        return domain

    def _get_grouped_lines(self):
        self.ensure_one()
        groups = defaultdict(lambda: {"currency": False, "lines": [], "total_balance": 0.0})
        moves = self.env["account.move"].search(self._build_domain(), order="invoice_date,invoice_date_due,name,id")

        for move in moves:
            sign = -1 if self._is_credit_note(move) else 1
            currency = move.currency_id
            key = currency.id
            groups[key]["currency"] = currency

            original_amount = sign * move.amount_total
            balance_amount = sign * move.amount_residual
            groups[key]["total_balance"] += balance_amount
            groups[key]["lines"].append(
                {
                    "invoice_date": move.invoice_date,
                    "invoice_date_due": move.invoice_date_due,
                    "invoice_name": move.fp_consecutive_number or move.name,
                    "original_amount": original_amount,
                    "balance_amount": balance_amount,
                }
            )

        return sorted(groups.values(), key=lambda item: item["currency"].name)

