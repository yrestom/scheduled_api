// Copyright (c) 2022, Totrox & Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Schedule Request', {
	refresh: function (frm) {
		if (!frm.is_new() && !frm.is_dirty()) {
			frm.add_custom_button('Retry', () => {
				frappe.call({
					method: 'scheduled_api.process.execute',
					args: {
						kwargs: frm.doc.name
					},
					callback: function (r) {
						if (!r.exc) {
							frm.reload_doc();
						}
					}
				});
			});
		}
	}
});
