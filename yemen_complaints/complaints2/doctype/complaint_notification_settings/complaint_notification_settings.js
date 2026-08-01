frappe.ui.form.on('Complaint Notification Settings', {
  refresh(frm) {
    frm.set_intro(__('Configure email, SMS, and WhatsApp endpoints for complaint notifications.'), 'blue');
  },
});
