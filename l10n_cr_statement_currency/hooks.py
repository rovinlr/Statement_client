import logging

_logger = logging.getLogger(__name__)

PARTNER_REPORTS_CANDIDATE_XMLIDS = (
    "account_reports.menu_partner_reports",
    "account_reports.menu_finance_partner_reports",
    "account_reports.account_reports_partners_menu",
    "account_followup.customer_statements_menu",
    "account_followup.account_followup_menu",
)

PARTNER_REPORTS_CANDIDATE_NAMES = (
    "Partner Reports",
    "Partner reports",
    "Informes del contacto",
    "Reportes del contacto",
    "Informes de contactos",
    "Reportes de contactos",
)


def _find_partner_reports_menu(env):
    """Locate the "Partner Reports" sub-menu across Odoo editions/languages."""
    for xmlid in PARTNER_REPORTS_CANDIDATE_XMLIDS:
        menu = env.ref(xmlid, raise_if_not_found=False)
        if menu and menu._name == "ir.ui.menu":
            return menu

    reports_parent = env.ref("account.menu_finance_reports", raise_if_not_found=False)
    if not reports_parent:
        return env["ir.ui.menu"]

    return env["ir.ui.menu"].search(
        [
            ("name", "in", PARTNER_REPORTS_CANDIDATE_NAMES),
            ("parent_id", "child_of", reports_parent.id),
        ],
        limit=1,
    )


def post_init_hook(env):
    """Move the statement menu under the Partner Reports sub-menu if present."""
    statement_menu = env.ref(
        "l10n_cr_statement_currency.menu_statement_report", raise_if_not_found=False
    )
    if not statement_menu:
        return

    partner_menu = _find_partner_reports_menu(env)
    if partner_menu:
        statement_menu.parent_id = partner_menu
        _logger.info(
            "Statement report menu placed under %s (id=%s)", partner_menu.complete_name, partner_menu.id
        )
    else:
        _logger.info(
            "Partner Reports sub-menu not found; statement report stays under the main Reports menu."
        )
