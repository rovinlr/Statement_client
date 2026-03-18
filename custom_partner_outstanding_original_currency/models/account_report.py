from odoo import models


class AccountReport(models.Model):
    _inherit = "account.report"

    def _postprocess_chatter_for_annotations(self, lines):
        """Normalize custom lines before Odoo indexes chatter annotations.

        Some Odoo builds assume ``line['move_id']`` is always a tuple/list and
        subscript it directly. Custom dynamic reports can emit ``False`` for
        section/subtotal rows, which raises ``TypeError: 'bool' object is not
        subscriptable``.
        """
        for line in lines:
            move_id = line.get("move_id")
            if move_id is False:
                line.pop("move_id", None)
            elif isinstance(move_id, int):
                line["move_id"] = (move_id, line.get("name") or "")

        return super()._postprocess_chatter_for_annotations(lines)
