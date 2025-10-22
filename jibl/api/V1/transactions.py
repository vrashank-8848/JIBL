import frappe
# from jibl.utils import create_sales_invoice as __create_sales_invoice

@frappe.whitelist()
def get_sales_invoice():
    headers = dict(frappe.request.headers)
    data = frappe.form_dict
    pass
    