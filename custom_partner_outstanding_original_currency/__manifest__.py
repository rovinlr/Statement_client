{
    "name": "Estado de cuenta por cobrar (Moneda original)",
    "summary": "Reporte dinámico de cuentas por cobrar por cliente y moneda original",
    "version": "19.0.1.0.0",
    "category": "Accounting/Accounting",
    "license": "LGPL-3",
    "depends": ["account_reports"],
    "data": [
        "security/ir.model.access.csv",
        "data/account_report.xml",
        "views/account_report_templates.xml",
    ],
    "installable": True,
    "application": False,
}
