import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _attach_pos_ticket_pdf_if_missing(self):
        """Attach POS ticket PDF to outgoing emails when not already attached.

        This targets ``mail.mail`` linked to ``pos.order`` records and only adds
        a PDF when the email has none, preventing duplicate attachments and
        preserving FE/TE XML payloads.
        """
        pos_mails = self.filtered(
            lambda mail: mail.model == "pos.order" and mail.res_id and mail.state in ("outgoing", "exception")
        )
        if not pos_mails:
            return

        orders = self.env["pos.order"].browse(pos_mails.mapped("res_id")).exists()
        orders_by_id = {order.id: order for order in orders}

        for mail in pos_mails:
            order = orders_by_id.get(mail.res_id)
            if not order:
                continue

            has_pdf = any(att.mimetype == "application/pdf" for att in mail.attachment_ids)
            if has_pdf:
                continue

            ticket_attachment = order._get_or_create_pos_ticket_pdf_attachment()
            if not ticket_attachment:
                _logger.info(
                    "E-INV CR - No se encontró PDF de tiquete POS para adjuntar en correo de %s (%s).",
                    order.name,
                    order.id,
                )
                continue

            mail.attachment_ids = [(4, ticket_attachment.id)]

    def send(self, auto_commit=False, raise_exception=False):
        self._attach_pos_ticket_pdf_if_missing()
        return super().send(auto_commit=auto_commit, raise_exception=raise_exception)
