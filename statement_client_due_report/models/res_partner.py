from odoo import _, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_open_customer_due_statement(self):
        self.ensure_one()
        return {
            "name": _("Adeudado del cliente"),
            "type": "ir.actions.act_window",
            "res_model": "customer.due.statement.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.id,
                "default_company_id": self.env.company.id,
            },
        }
