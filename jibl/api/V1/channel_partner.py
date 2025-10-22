import frappe
from jibl.utils import create_channel_partner as __create_channel_partner

@frappe.whitelist()
def create_channel_partner():
    headers = dict(frappe.request.headers)
    data = frappe.form_dict
    return __create_channel_partner(headers,data)
    
