frappe.ui.form.on('Complaint Security Event', {
  refresh(frm) {
    frm.set_intro(__('Security events are generated automatically for throttling, abuse protection, and operational monitoring.'), 'orange');
  },
});
