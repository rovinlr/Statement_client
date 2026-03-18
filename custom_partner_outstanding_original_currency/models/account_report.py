from odoo import models


class AccountReport(models.Model):
    _inherit = "account.report"

    def _postprocess_chatter_for_annotations(self, lines):
        """Normalize report lines before Odoo indexes chatter annotations.

        Some Odoo 19 builds assume ``line['move_id']`` is always a 2-tuple/list
        like ``(id, display_name)`` and subscript it directly. Custom dynamic
        reports often emit section/subtotal rows without a move, and the core
        pipeline may end up with ``move_id=False`` on those rows, raising:

            TypeError: 'bool' object is not subscriptable
        """
        for line in self._iter_report_lines(lines):
            self._normalize_move_id_for_chatter(line)

        return super()._postprocess_chatter_for_annotations(lines)

    def _iter_report_lines(self, lines):
        """Yield all dict lines, including nested structures when present."""
        if not lines:
            return
        stack = list(lines)
        while stack:
            line = stack.pop()
            if not isinstance(line, dict):
                continue

            yield line

            for key in ("children", "unfolded_lines", "lines"):
                nested = line.get(key)
                if isinstance(nested, list) and nested:
                    stack.extend(nested)

    def _normalize_move_id_for_chatter(self, line):
        """Ensure ``move_id`` is always a subscriptable 2-tuple for Odoo core."""
        name = line.get("name") or ""

        if "move_id" not in line:
            line["move_id"] = (False, "")
            return

        move_id = line.get("move_id")

        if move_id is False or move_id in (None, "") or isinstance(move_id, bool):
            line["move_id"] = (False, "")
            return

        if isinstance(move_id, int):
            line["move_id"] = (move_id, name)
            return

        if isinstance(move_id, (list, tuple)):
            if not move_id:
                line["move_id"] = (False, "")
                return
            move_id_value = move_id[0]
            move_display = move_id[1] if len(move_id) > 1 else name
            line["move_id"] = (move_id_value, move_display or "")
            return

        record_id = getattr(move_id, "id", False)
        line["move_id"] = (record_id or False, name)
