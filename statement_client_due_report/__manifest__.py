{
    "name": "Customer Due Statement by Currency",
    "summary": "Customer due statement with invoices and credit notes grouped by original currency",
    "version": "19.0.1.0.0",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/customer_due_statement_wizard_views.xml",
        "views/res_partner_views.xml",
        "report/customer_due_statement_report.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
