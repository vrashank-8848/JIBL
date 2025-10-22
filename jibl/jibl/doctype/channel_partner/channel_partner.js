// Copyright (c) 2025, JIBL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Channel Partner', {
	address: function(frm) {
		frappe.call({
			method:"frappe.contacts.doctype.address.address.get_address_display",
			args: {"address_dict":frm.doc.address},
			callback : function (response) {
				frm.set_value("address_display",response.message)
			}
	})
	}
});


