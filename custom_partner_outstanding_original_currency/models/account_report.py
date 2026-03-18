from odoo import models


class AccountReport(models.Model):
    _inherit = "account.report"

    def _postprocess_chatter_for_annotations(self, lines):
        """Make report lines compatible with Odoo's chatter annotation postprocessing.

        Some Odoo 19 builds subscript ``line['move_id'][0]`` without checking if
        the value is truthy or even a sequence. Custom reports (especially section
        headers/subtotals and synthetic ids) may end up with ``move_id=False``.
        """
        self._sanitize_move_id(lines)
        return super()._postprocess_chatter_for_annotations(lines)

    def _sanitize_move_id(self, lines):
        for line in self._walk_line_dicts(lines):
            if "move_id" not in line:
                continue

            value = line.get("move_id")

            if isinstance(value, (list, tuple)):
                if not value:
                    line["move_id"] = (False, "")
                    continue
                move_id = value[0]
                display = value[1] if len(value) > 1 else (line.get("name") or "")
                line["move_id"] = (move_id or False, display or "")
                continue

            if isinstance(value, int):
                line["move_id"] = (value, line.get("name") or "")
                continue

            record_id = getattr(value, "id", False) if value else False
            line["move_id"] = (record_id or False, "")

    def _walk_line_dicts(self, obj):
        """Yield every dict that represents a report line, including nested structures."""
        if isinstance(obj, dict):
            yield obj
            for key in ("children", "lines", "unfolded_lines"):
                nested = obj.get(key)
                if isinstance(nested, list):
                    for item in nested:
                        yield from self._walk_line_dicts(item)
            return

        if isinstance(obj, (list, tuple)):
            for item in obj:
                yield from self._walk_line_dicts(item)
