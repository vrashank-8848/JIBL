import frappe
from jibl.utils import create_channel_partners as __create_channel_partners

@frappe.whitelist()
def create_channel_partners():
    headers = dict(frappe.request.headers)
    data = frappe.form_dict
    return __create_channel_partners(headers,data)
    
