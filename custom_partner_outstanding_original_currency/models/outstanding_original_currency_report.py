from collections import defaultdict

from odoo import _, fields, models


class OutstandingOriginalCurrencyReportHandler(models.AbstractModel):
    _name = "account.outstanding.original.currency.report.handler"
    _inherit = "account.report.custom.handler"
    _description = "Outstanding Receivable in Original Currency Report Handler"

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        options.setdefault("unfold_all", False)

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        grouped_results = self._get_grouped_moves(options)
        lines = []

        unfolded_lines = set(options.get("unfolded_lines", []))
        unfold_all = options.get("unfold_all")

        for partner_key in sorted(grouped_results.keys(), key=lambda key: (key[1] or "").lower()):
            partner_id, partner_name = partner_key
            partner_payload = grouped_results[partner_key]
            partner_line_id = report._get_generic_line_id("res.partner", partner_id, markup="partner")
            partner_is_unfolded = unfold_all or partner_line_id in unfolded_lines

            partner_total_original = sum(
                currency_data["subtotal_original"] for currency_data in partner_payload.values()
            )
            partner_total_residual = sum(
                currency_data["subtotal_residual"] for currency_data in partner_payload.values()
            )

            lines.append(
                {
                    "id": partner_line_id,
                    "name": partner_name or _("No Partner"),
                    "level": 1,
                    "unfoldable": True,
                    "unfolded": bool(partner_is_unfolded),
                    "columns": [
                        {"name": ""},
                        {"name": ""},
                        {"name": ""},
                        {"name": self._format_amount(partner_total_original)},
                        {"name": self._format_amount(partner_total_residual)},
                    ],
                }
            )

            if not partner_is_unfolded:
                continue

            for currency_id, currency_data in sorted(
                partner_payload.items(), key=lambda item: (item[1]["currency_name"] or "")
            ):
                currency = self.env["res.currency"].browse(currency_id)
                currency_line_id = report._get_generic_line_id(
                    "res.currency", currency_id, parent_line_id=partner_line_id, markup="currency"
                )
                currency_is_unfolded = unfold_all or currency_line_id in unfolded_lines

                lines.append(
                    {
                        "id": currency_line_id,
                        "parent_id": partner_line_id,
                        "name": currency_data["currency_name"],
                        "level": 2,
                        "unfoldable": True,
                        "unfolded": bool(currency_is_unfolded),
                        "columns": [
                            {"name": ""},
                            {"name": ""},
                            {"name": _("Subtotal")},
                            {
                                "name": self._format_amount(currency_data["subtotal_original"], currency=currency),
                                "no_format": currency_data["subtotal_original"],
                                "class": "number",
                            },
                            {
                                "name": self._format_amount(currency_data["subtotal_residual"], currency=currency),
                                "no_format": currency_data["subtotal_residual"],
                                "class": "number",
                            },
                        ],
                    }
                )

                if not currency_is_unfolded:
                    continue

                for move in currency_data["moves"]:
                    lines.append(
                        {
                            "id": report._get_generic_line_id("account.move", move["id"], parent_line_id=currency_line_id),
                            "parent_id": currency_line_id,
                            "name": "",
                            "level": 3,
                            "caret_options": "account.move",
                            "columns": [
                                {"name": fields.Date.to_string(move["invoice_date"]) if move["invoice_date"] else ""},
                                {
                                    "name": fields.Date.to_string(move["invoice_date_due"])
                                    if move["invoice_date_due"]
                                    else ""
                                },
                                {"name": move["display_number"]},
                                {
                                    "name": self._format_amount(move["original_amount"], currency=currency),
                                    "no_format": move["original_amount"],
                                    "class": "number",
                                },
                                {
                                    "name": self._format_amount(move["residual_amount"], currency=currency),
                                    "no_format": move["residual_amount"],
                                    "class": "number",
                                },
                            ],
                        }
                    )

        return [(0, line) for line in lines]

    def _get_grouped_moves(self, options):
        query, params = self._get_moves_query(options)
        self.env.cr.execute(query, params)

        partner_currency_map = defaultdict(dict)
        for row in self.env.cr.dictfetchall():
            partner_key = (row["partner_id"], row["partner_name"] or _("No Partner"))
            currency_id = row["currency_id"]
            if currency_id not in partner_currency_map[partner_key]:
                partner_currency_map[partner_key][currency_id] = {
                    "currency_name": row["currency_name"],
                    "subtotal_original": 0.0,
                    "subtotal_residual": 0.0,
                    "moves": [],
                }

            sign = -1 if row["move_type"] == "out_refund" else 1
            original_amount = sign * row["amount_total"]
            residual_amount = sign * row["amount_residual"]

            partner_currency_map[partner_key][currency_id]["subtotal_original"] += original_amount
            partner_currency_map[partner_key][currency_id]["subtotal_residual"] += residual_amount
            partner_currency_map[partner_key][currency_id]["moves"].append(
                {
                    "id": row["id"],
                    "invoice_date": row["invoice_date"],
                    "invoice_date_due": row["invoice_date_due"],
                    "display_number": row["fp_consecutive_number"] or row["name"],
                    "original_amount": original_amount,
                    "residual_amount": residual_amount,
                }
            )

        for partner_data in partner_currency_map.values():
            for currency_payload in partner_data.values():
                currency_payload["moves"].sort(
                    key=lambda move: (move["invoice_date"] or fields.Date.to_date("1900-01-01"), move["id"])
                )

        return partner_currency_map

    def _get_moves_query(self, options):
        domain = [
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("state", "=", "posted"),
            ("amount_residual", "!=", 0.0),
            ("company_id", "in", self.env.companies.ids),
        ]

        date_options = options.get("date") or {}
        date_from = date_options.get("date_from")
        date_to = date_options.get("date_to")
        if date_from:
            domain.append(("invoice_date", ">=", date_from))
        if date_to:
            domain.append(("invoice_date", "<=", date_to))

        selected_journal_ids = [
            journal.get("id")
            for journal in (options.get("journals") or [])
            if journal.get("id") and journal.get("selected")
        ]
        if selected_journal_ids:
            domain.append(("journal_id", "in", selected_journal_ids))

        partner_ids = self._extract_partner_ids(options)
        if partner_ids:
            domain.append(("partner_id", "in", partner_ids))

        query = self.env["account.move"]._where_calc(domain)
        from_clause, where_clause, where_params = query.get_sql()

        sql = f"""
            SELECT
                account_move.id,
                account_move.name,
                account_move.fp_consecutive_number,
                account_move.partner_id,
                rp.name AS partner_name,
                account_move.currency_id,
                rc.name AS currency_name,
                account_move.move_type,
                account_move.invoice_date,
                account_move.invoice_date_due,
                account_move.amount_total,
                account_move.amount_residual
            FROM {from_clause}
            LEFT JOIN res_partner rp ON rp.id = account_move.partner_id
            INNER JOIN res_currency rc ON rc.id = account_move.currency_id
            WHERE {where_clause}
            ORDER BY rp.name, rc.name, account_move.invoice_date, account_move.id
        """
        return sql, where_params

    def _extract_partner_ids(self, options):
        partner_ids = options.get("partner_ids") or []
        if isinstance(partner_ids, str):
            return [int(pid) for pid in partner_ids.split(",") if pid]

        result = []
        for partner_id in partner_ids:
            if isinstance(partner_id, (list, tuple)):
                partner_id = partner_id[0]
            if partner_id:
                result.append(int(partner_id))

        if result:
            return result

        selected_partner_ids = options.get("selected_partner_ids") or []
        return [int(pid) for pid in selected_partner_ids if pid]

    def _format_amount(self, amount, currency=None):
        if currency:
            return self.env["ir.qweb.field.monetary"].value_to_html(
                amount,
                {
                    "display_currency": currency,
                    "company": self.env.company,
                },
            )
        return self.env["ir.qweb.field.float"].value_to_html(amount, {"precision": 2})
